"""Docker integration acceptance. Run after compose up --wait."""
import json
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

CLOUD=Path(__file__).resolve().parents[1]
def read(url):
    try:
        with urllib.request.urlopen(url,timeout=6) as r:
            return r.status,json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code,json.loads(e.read())
def compose(*args):subprocess.run(['docker','compose',*args],cwd=CLOUD,check=True,timeout=60)
def eventually(check,seconds=55):
    deadline=time.monotonic()+seconds
    last=None
    while time.monotonic()<deadline:
        try:
            last=check()
            if last:return
        except (OSError,ValueError):pass
        time.sleep(2)
    raise AssertionError(f'Condition did not pass within {seconds}s: {last}')
def alert_firing(name):
    code,data=read('http://127.0.0.1:9090/api/v1/alerts')
    return code==200 and any(a['labels']['alertname']==name and a['state']=='firing' for a in data['data']['alerts'])
def main():
    eventually(lambda:read('http://127.0.0.1:3000/api/health')[0]==200)
    code,data=read('http://127.0.0.1:8080/api/status')
    assert code==200 and data['driver']=='mysql' and data['asset_count']==3
    try:
        compose('stop','app1')
        eventually(lambda:read('http://127.0.0.1:8080/readyz')[0]==200)
        eventually(lambda:alert_firing('AppInstanceDown'))
    finally:
        compose('start','app1')
    eventually(lambda:read('http://127.0.0.1:8080/readyz')[0]==200)
    eventually(lambda:not alert_firing('AppInstanceDown'))
    try:
        compose('stop','db')
        eventually(lambda:read('http://127.0.0.1:8080/readyz')[0]==503)
        assert read('http://127.0.0.1:8080/healthz')[0]==200
        eventually(lambda:alert_firing('DatabaseUnavailable'))
        eventually(lambda:alert_firing('BusinessProbeFailed'))
    finally:
        compose('start','db')
    eventually(lambda:read('http://127.0.0.1:8080/readyz')[0]==200)
    eventually(lambda:not alert_firing('DatabaseUnavailable') and not alert_firing('BusinessProbeFailed'))
    try:
        compose('stop','nginx')
        eventually(lambda:alert_firing('BusinessProbeFailed'))
    finally:
        compose('start','nginx')
    eventually(lambda:read('http://127.0.0.1:8080/readyz')[0]==200)
    eventually(lambda:not alert_firing('BusinessProbeFailed'))
    print('Compose acceptance passed: MySQL query, app loss, DB loss, proxy loss and recovery.')
if __name__=='__main__':main()
