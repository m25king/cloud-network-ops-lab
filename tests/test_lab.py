import contextlib
import importlib.util
import io
import ipaddress
import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.request
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from wsgiref.simple_server import make_server

ROOT=Path(__file__).resolve().parents[1]
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    mod=importlib.util.module_from_spec(spec)
    sys.modules[name]=mod
    spec.loader.exec_module(mod)
    return mod
app=module('lab_app','cloud/app.py')
probe=module('lab_probe','automation/probe.py')
vrp=module('lab_vrp','automation/vrp.py')


class AppTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db=app.Database(path=str(Path(self.temp.name)/'test.db'))
        self.db.initialize_local()
        self.application=app.Application(self.db)

    def request(self,path,method='GET',query=''):
        status=[]
        with contextlib.redirect_stdout(io.StringIO()):
            body=b''.join(self.application({'PATH_INFO':path,'REQUEST_METHOD':method,'QUERY_STRING':query},lambda s,h:status.append(s)))
        return int(status[0].split()[0]),body

    def test_real_sqlite_seed_is_idempotent(self):
        self.db.initialize_local()
        code,body=self.request('/api/status')
        self.assertEqual(code,200)
        self.assertEqual(json.loads(body)['asset_count'],3)
        self.assertEqual(json.loads(body)['data_kind'],'synthetic')

    def test_dashboard_and_default_drill_report(self):
        code,body=self.request('/')
        self.assertEqual(code,200)
        self.assertIn(b'<html',body)
        self.assertIn(b'/api/status',body)
        self.assertEqual(json.loads(self.request('/api/drill')[1])['state'],'not_run')

    def test_dependency_failure_does_not_hide_process_or_metrics(self):
        with self.db.connection() as c:
            c.execute('DROP TABLE assets')
            c.commit()
        self.assertEqual(self.request('/healthz')[0],200)
        self.assertEqual(self.request('/readyz')[0],503)
        code,body=self.request('/metrics')
        self.assertEqual(code,200)
        self.assertIn(b'lab_db_up 0',body)
        self.assertNotIn(b'no such table',self.request('/readyz')[1])

    def test_no_mutation_endpoint(self):
        self.assertEqual(self.request('/api/status','POST')[0],405)
        self.assertEqual(self.request('/../../.env')[0],404)

    def test_asset_filters_and_pagination(self):
        code,body=self.request('/api/assets',query='q=demo&zone=server&page_size=1')
        data=json.loads(body)
        self.assertEqual((code,data['total'],data['items'][0]['name']),(200,1,'demo-web-1'))
        data=json.loads(self.request('/api/assets',query='page=2&page_size=2')[1])
        self.assertEqual((data['total'],len(data['items']),data['items'][0]['id']),(3,1,3))

    def test_asset_input_does_not_expand_query(self):
        for query in ['q=%25','q=%27%20OR%201%3D1--','q=%5F']:
            self.assertEqual(json.loads(self.request('/api/assets',query=query)[1])['total'],0)
        for query in ['page=0','page_size=101','sort=name;DROP','zone=unknown','page=1&page=2','private=x']:
            self.assertEqual(self.request('/api/assets',query=query)[0],400)

    def test_asset_failure_is_explicit_and_read_only(self):
        self.assertEqual(self.request('/api/assets','POST')[0],405)
        with self.db.connection() as c:
            c.execute('DROP TABLE assets');c.commit()
        code,body=self.request('/api/assets')
        self.assertEqual((code,json.loads(body)),(503,{'database':'unavailable'}))

    def test_metric_labels_are_bounded(self):
        self.request('/untrusted-high-cardinality-path')
        body=self.request('/metrics')[1]
        self.assertNotIn(b'untrusted-high-cardinality-path',body)
        self.assertIn(b'route="other"',body)

    def test_counters_safe_under_threads(self):
        def work():
            self.request('/healthz')
        with contextlib.redirect_stdout(io.StringIO()):
            workers=[threading.Thread(target=work) for _ in range(20)]
            for worker in workers:worker.start()
            for worker in workers:worker.join()
        self.assertEqual(self.application.requests[('/healthz','200')],20)

    def test_local_server_handles_idle_browser_connection(self):
        server=make_server('127.0.0.1',0,self.application,server_class=app.LocalServer)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        idle=socket.create_connection(server.server_address,timeout=2)
        try:
            with urllib.request.urlopen(f'http://127.0.0.1:{server.server_port}/readyz',timeout=2) as response:
                self.assertEqual(response.status,200)
        finally:
            idle.close();server.shutdown();server.server_close();thread.join(timeout=3)

    def test_second_local_listener_cannot_claim_same_port(self):
        with make_server('127.0.0.1',0,self.application,server_class=app.LocalServer) as server:
            with self.assertRaises(OSError):
                with make_server('127.0.0.1',server.server_port,self.application,server_class=app.LocalServer):
                    pass


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(503 if self.path=='/fail' else 302 if self.path=='/redirect' else 200)
        if self.path=='/redirect':self.send_header('Location','http://127.0.0.1:1/should-not-follow')
        self.end_headers()
        self.wfile.write(b'fixture')
    def log_message(self,*args):pass


class ProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        cls.port=cls.server.server_port
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join()

    def target(self,path):return probe.Target('fixture','http',f'http://127.0.0.1:{self.port}{path}')

    def test_http_and_tcp_reachability(self):
        report=probe.run([self.target('/ok'),probe.Target('tcp','tcp',f'127.0.0.1:{self.port}')],attempts=2)
        self.assertTrue(all(r['state']=='OK' for r in report['results']))

    def test_http_failure_is_not_tcp_failure(self):
        result=probe.check(self.target('/fail'),attempts=2)
        self.assertEqual(result['state'],'FAILED')
        self.assertEqual(result['samples'][0]['http_status'],503)
        self.assertEqual(result['request_failure_ratio'],1)

    def test_expected_error_status_can_pass(self):
        target=probe.Target('expected-failure','http',f'http://127.0.0.1:{self.port}/fail',503)
        self.assertEqual(probe.check(target,1)['state'],'OK')

    def test_redirect_not_followed(self):
        self.assertEqual(probe.check(self.target('/redirect'),1)['samples'][0]['http_status'],302)

    def test_invalid_target_and_limits_rejected(self):
        for target in [probe.Target('x','http','file:///etc/passwd'),probe.Target('x','http','http://user:pass@localhost'),probe.Target('x','tcp','localhost:70000')]:
            with self.assertRaises(ValueError):probe.validate(target)
        with self.assertRaises(ValueError):probe.run([self.target('/ok')],timeout=float('nan'))
        with self.assertRaises(ValueError):probe.run([self.target('/ok')],workers=99)

    def test_reports_escape_untrusted_input(self):
        report=probe.run([self.target('/ok')],attempts=1)
        report['results'][0]['name']='<script>alert(1)</script>'
        self.assertNotIn('<script>',probe.render(report))
        report['results'][0]['name']='=1+1'
        with tempfile.TemporaryDirectory() as directory:
            probe.save(report,directory)
            self.assertIn("'=1+1",(Path(directory)/'report.csv').read_text(encoding='utf-8-sig'))
            self.assertTrue((Path(directory)/'report.json').is_file())

    def test_inventory_duplicates_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'inventory.csv'
            path.write_text('name,kind,target\na,tcp,localhost:80\na,tcp,localhost:81\n')
            with self.assertRaises(ValueError):probe.read_inventory(path)

    def test_real_cli_process_and_output(self):
        with tempfile.TemporaryDirectory() as directory:
            inventory=Path(directory)/'inventory.csv'
            inventory.write_text(f'name,kind,target\ncli,http,http://127.0.0.1:{self.port}/ok\n',encoding='utf-8')
            result=subprocess.run([sys.executable,str(ROOT/'automation/probe.py'),'--inventory',str(inventory),'--live','--attempts','1','--out',str(Path(directory)/'out')],capture_output=True,text=True,timeout=10)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(json.loads((Path(directory)/'out/report.json').read_text())['results'][0]['state'],'OK')


class VRPTests(unittest.TestCase):
    def test_expected_down_and_unused_down_distinguished(self):
        text=(ROOT/'automation/fixtures/interface-brief.txt').read_text()
        self.assertTrue(vrp.evaluate(text,['Vlanif10'])['ok'])
        self.assertEqual(vrp.evaluate(text,['Vlanif102'])['unexpected_down'],['Vlanif102'])

    def test_unknown_and_missing_never_green(self):
        self.assertFalse(vrp.evaluate('unknown output',[])['ok'])
        self.assertEqual(vrp.evaluate('Vlanif10 up up',['Vlanif99'])['missing_expected'],['Vlanif99'])

    def test_secrets_redacted(self):
        text='sysname DEMO\nlocal-user lab password irreversible-cipher abc123\nsnmp-agent community read private123\ninterface Vlanif10'
        result=vrp.redact_config(text)
        self.assertNotIn('abc123',result);self.assertNotIn('private123',result)
        self.assertIn('interface Vlanif10',result)


class NetworkDesignTests(unittest.TestCase):
    def test_transit_addresses_valid_unique_nonoverlapping(self):
        plan=json.loads((ROOT/'network/plan.json').read_text())
        networks=[];addresses=[]
        for link in plan['links']:
            a,b=ipaddress.ip_interface(link['a_ip']),ipaddress.ip_interface(link['b_ip'])
            self.assertEqual(a.network,b.network)
            self.assertEqual(a.network.prefixlen,30)
            self.assertIn(a.ip,list(a.network.hosts()));self.assertIn(b.ip,list(b.network.hosts()))
            self.assertNotEqual(a.ip,b.ip)
            addresses.extend([str(a.ip),str(b.ip)]);networks.append(a.network)
        self.assertEqual(len(addresses),len(set(addresses)))
        for i,n in enumerate(networks):
            for other in networks[i+1:]:self.assertFalse(n.overlaps(other))

    def test_both_cores_advertise_and_filter_business_networks(self):
        for name in ['CORE1','CORE2']:
            config=(ROOT/f'network/configs/{name}.cfg').read_text()
            for vlan in [10,20,30,40,99]:
                self.assertIn(f'network 192.168.{vlan}.0 0.0.0.255',config)
                self.assertIn(f'vrrp vrid {vlan} virtual-ip 192.168.{vlan}.254',config)
            self.assertIn('traffic-filter inbound acl 3000',config)
            self.assertNotIn('port trunk allow-pass vlan 10 20 30 40 99 101',config)

    def test_artifacts_state_validation_limits(self):
        self.assertEqual(len(list((ROOT/'network/configs').glob('*.cfg'))),10)
        self.assertEqual(len(list((ROOT/'network/faults').glob('N*.md'))),8)
        self.assertIn('generated_not_device_validated',(ROOT/'network/plan.json').read_text())


if __name__=='__main__':unittest.main(verbosity=2)
