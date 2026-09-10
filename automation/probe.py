"""Small bounded HTTP/TCP inspector. No shell, ping parsing or configuration writes."""
import argparse
import concurrent.futures
import csv
import datetime
import html
import ipaddress
import json
import math
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class Target:
    name: str
    kind: str
    target: str
    expected_status: int = 200


def validate(target):
    if not target.name or len(target.name)>100:
        raise ValueError('Name must contain 1-100 characters')
    if target.kind=='http':
        url=urllib.parse.urlsplit(target.target)
        if url.scheme not in {'http','https'} or not url.hostname or url.username or url.password or url.fragment:
            raise ValueError('Use an HTTP(S) URL without credentials or fragments')
        if url.port is not None and not 1<=url.port<=65535:
            raise ValueError('Invalid port')
        if not 100<=target.expected_status<=599:
            raise ValueError('Invalid expected HTTP status')
    elif target.kind=='tcp':
        host,sep,port=target.target.rpartition(':')
        if not sep or not host or not 1<=int(port)<=65535:
            raise ValueError('TCP target must be hostname:port or [IPv6]:port')
    else:
        raise ValueError('kind must be http or tcp')
    return target


def read_inventory(path):
    with Path(path).open(encoding='utf-8-sig',newline='') as stream:
        rows=list(csv.DictReader(stream))
    targets=[validate(Target(r['name'],r['kind'],r['target'],int(r.get('expected_status') or 200))) for r in rows]
    if not 1<=len(targets)<=256 or len({t.name for t in targets})!=len(targets):
        raise ValueError('Inventory must contain 1-256 uniquely named targets')
    return targets


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):
        return None


def once(target,timeout):
    started=time.perf_counter()
    status=None
    try:
        if target.kind=='tcp':
            host,_,port=target.target.rpartition(':')
            with socket.create_connection((host.strip('[]'),int(port)),timeout=timeout):
                pass
        else:
            # Explicit inventory targets only; do not follow a redirect to a different destination.
            opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
            with opener.open(target.target,timeout=timeout) as response:
                status=response.status
            if status!=target.expected_status:
                return False,'unexpected_http_status',status,(time.perf_counter()-started)*1000
        return True,'ok',status,(time.perf_counter()-started)*1000
    except urllib.error.HTTPError as error:
        status=error.code
        ok=status==target.expected_status
        return ok,'ok' if ok else 'unexpected_http_status',status,(time.perf_counter()-started)*1000
    except (OSError,ValueError) as error:
        underlying=getattr(error,'reason',error)
        if isinstance(underlying,socket.gaierror):reason='dns_error'
        elif isinstance(underlying,(TimeoutError,socket.timeout)):reason='timeout'
        elif isinstance(underlying,ConnectionRefusedError):reason='connection_refused'
        else:reason='connection_error'
        return False,reason,status,(time.perf_counter()-started)*1000


def check(target,attempts=3,timeout=2):
    samples=[]
    for _ in range(attempts):
        ok,reason,status,elapsed=once(target,timeout)
        samples.append({'ok':ok,'reason':reason,'http_status':status,'latency_ms':round(elapsed,3)})
    successes=sum(x['ok'] for x in samples)
    return {**asdict(target),'attempts':attempts,'successes':successes,
            'request_failure_ratio':(attempts-successes)/attempts,
            'state':'OK' if successes==attempts else 'DEGRADED' if successes else 'FAILED',
            'samples':samples}


def run(targets,attempts=3,timeout=2,workers=4):
    if not 1<=attempts<=10 or not math.isfinite(timeout) or not 0.1<=timeout<=10 or not 1<=workers<=8:
        raise ValueError('Use attempts 1-10, timeout 0.1-10 seconds, workers 1-8')
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        results=list(pool.map(lambda t:check(validate(t),attempts,timeout),targets))
    return {'generated_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'mode':'live_explicit_inventory','method':'HTTP status / TCP handshake',
            'note':'Request failure ratio is not ICMP packet loss. No automatic repair.',
            'results':results}


def render(report):
    esc=lambda x:html.escape(str(x),quote=True)
    rows=[]
    for r in report['results']:
        rows.append('<tr>'+''.join(f'<td>{esc(x)}</td>' for x in [r['name'],r['kind'],r['target'],r['state'],f"{r['successes']}/{r['attempts']}",','.join(s['reason'] for s in r['samples'])])+'</tr>')
    return '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>巡检报告</title><style>body{font:16px system-ui,sans-serif;max-width:1180px;margin:45px auto;padding:0 24px;color:#193047}h1{color:#116b78}table{border-collapse:collapse;width:100%}td,th{padding:12px;text-align:left;border-bottom:1px solid #ccd7de}p{line-height:1.7}</style><h1>云网服务巡检报告</h1><p>'+esc(report['generated_at_utc'])+'</p><p>'+esc(report['note'])+'</p><table><tr><th>对象</th><th>方式</th><th>目标</th><th>状态</th><th>成功/请求</th><th>诊断</th></tr>'+''.join(rows)+'</table></html>'


def save(report,directory):
    directory=Path(directory)
    directory.mkdir(parents=True,exist_ok=True)
    (directory/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    (directory/'report.html').write_text(render(report),encoding='utf-8')
    with (directory/'report.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.writer(stream)
        writer.writerow(['name','kind','target','state','successes','attempts','request_failure_ratio'])
        for r in report['results']:
            values=[r[k] for k in ['name','kind','target','state','successes','attempts','request_failure_ratio']]
            # Prevent spreadsheet formula interpretation of user-controlled inventory fields.
            writer.writerow(["'"+v if isinstance(v,str) and v.startswith(('=','+','-','@','\t','\r')) else v for v in values])


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--inventory',type=Path,required=True)
    parser.add_argument('--live',action='store_true',help='Execute probes only against this explicit inventory')
    parser.add_argument('--out',type=Path,default=Path('artifacts/inspection'))
    parser.add_argument('--attempts',type=int,default=3)
    parser.add_argument('--timeout',type=float,default=2)
    parser.add_argument('--workers',type=int,default=4)
    args=parser.parse_args()
    if not args.live:parser.error('Review the target list, then add --live to execute')
    report=run(read_inventory(args.inventory),args.attempts,args.timeout,args.workers)
    save(report,args.out)
    print(json.dumps({'targets':len(report['results']),'failed':sum(r['state']!='OK' for r in report['results']),'out':str(args.out)}))
    return int(any(r['state']!='OK' for r in report['results']))

if __name__=='__main__':raise SystemExit(main())
