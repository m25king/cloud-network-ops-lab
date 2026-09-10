"""Run real local tests, render local probe evidence, explicitly bound validation claims."""
import datetime
import importlib.util
import io
import json
import platform
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer

ROOT=Path(__file__).resolve().parents[1]

def main():
    report_dir=ROOT/'evidence'
    report_dir.mkdir(exist_ok=True)
    log=io.StringIO()
    suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'))
    result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    (report_dir/'test-output.txt').write_text(log.getvalue(),encoding='utf-8')
    probe=sys.modules['lab_probe']
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(503 if self.path=='/dependency-down' else 200)
            self.end_headers()
            self.wfile.write(b'Local synthetic verification endpoint')
        def log_message(self,*args):pass
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        port=server.server_port
        report=probe.run([
            probe.Target('local-healthy','http',f'http://127.0.0.1:{port}/healthy'),
            probe.Target('local-dependency-down','http',f'http://127.0.0.1:{port}/dependency-down'),
            probe.Target('local-tcp-listener','tcp',f'127.0.0.1:{port}')],attempts=3)
        report['note']='真实本机HTTP/TCP请求；服务和故障为测试脚本创建的模拟对象，非eNSP设备或生产业务。请求失败比例不是ICMP丢包率。临时端口在脚本结束后关闭。'
        probe.save(report,report_dir/'local-probe')
    finally:
        server.shutdown();server.server_close();thread.join()
    summary={'generated_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
      'environment':{'os':platform.system(),'python':platform.python_version()},
      'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
      'passed':result.wasSuccessful(),
      'verified':['Python/SQLite behavior','Local loopback HTTP and TCP probes','Report escaping','Supported synthetic VRP parser fixtures','Network address/config static invariants'],
      'not_verified':['eNSP/VRP device command acceptance','Network failover timing','Docker Compose runtime','MySQL backup/restore execution','Prometheus rules execution','Grafana runtime','Real device SSH']}
    (report_dir/'verification.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    if not result.wasSuccessful():print(log.getvalue())
    return int(not result.wasSuccessful())

if __name__=='__main__':raise SystemExit(main())
