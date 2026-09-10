"""Optional read-only Huawei SSH adapter. Requires known host keys and real lab access."""
import argparse
import datetime
import difflib
import ipaddress
import json
import os
import re
from pathlib import Path
from vrp import evaluate,redact_config

def main():
    from netmiko import ConnectHandler
    parser=argparse.ArgumentParser()
    parser.add_argument('--inventory',type=Path,required=True)
    parser.add_argument('--known-hosts',type=Path,required=True)
    parser.add_argument('--out',type=Path,default=Path('artifacts/ssh'))
    args=parser.parse_args()
    inventory=json.loads(args.inventory.read_text(encoding='utf-8'))
    if not 1<=len(inventory)<=32:parser.error('Use 1-32 explicit devices')
    if not args.known_hosts.is_file():parser.error('A verified known_hosts file is required')
    user,password=os.environ['LAB_SSH_USER'],os.environ['LAB_SSH_PASSWORD']
    summary=[]
    for device in inventory:
        name=device['name']
        if not re.fullmatch('[A-Za-z0-9_-]{1,64}',name):parser.error('Invalid device name')
        host=str(ipaddress.ip_address(device['host']))
        target=args.out/name
        target.mkdir(parents=True,exist_ok=True)
        try:
            with ConnectHandler(device_type='huawei',host=host,username=user,password=password,
                    ssh_strict=True,system_host_keys=False,alt_host_keys=True,
                    alt_key_file=str(args.known_hosts.resolve()),conn_timeout=5,auth_timeout=5,
                    banner_timeout=5,fast_cli=False) as connection:
                outputs={command:connection.send_command(command,read_timeout=15) for command in
                         ['display version','display ip interface brief','display ip routing-table','display current-configuration']}
            config=redact_config(outputs['display current-configuration'])
            previous=target/'latest-redacted.cfg'
            diff=''.join(difflib.unified_diff(previous.read_text(encoding='utf-8').splitlines(True) if previous.exists() else [],
                                           config.splitlines(True),fromfile='previous',tofile='current'))
            previous.write_text(config,encoding='utf-8')
            (target/'config.diff').write_text(diff,encoding='utf-8')
            result=evaluate(outputs['display ip interface brief'],device.get('expected_up',[]))
            # Only masked output is persisted; output directory remains ignored by Git.
            (target/'commands.json').write_text(json.dumps({k:redact_config(v) for k,v in outputs.items()},indent=2),encoding='utf-8')
            summary.append({'name':name,'collected':True,**result})
        except Exception as error:
            # Exception class is enough; do not dump library exceptions that might echo credentials.
            summary.append({'name':name,'collected':False,'error_type':type(error).__name__})
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/'summary.json').write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'results':summary},indent=2),encoding='utf-8')
    print(f'Collected {sum(r["collected"] for r in summary)}/{len(summary)} devices; local output: {args.out}')
    return int(any(not r.get('ok',False) for r in summary))

if __name__=='__main__':raise SystemExit(main())
