"""Create an atomic MySQL logical backup in the local ignored backup directory."""
import datetime
import hashlib
import json
import subprocess
from pathlib import Path

CLOUD=Path(__file__).resolve().parents[1]

def main():
    directory=CLOUD/'backups'
    directory.mkdir(exist_ok=True)
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    target=directory/f'lab-{stamp}.sql'
    partial=target.with_suffix('.partial')
    command=['docker','compose','exec','-T','db','sh','-c',
      'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysqldump -u root --single-transaction --no-tablespaces --set-gtid-purged=OFF lab']
    try:
        with partial.open('xb') as stream:
            subprocess.run(command,cwd=CLOUD,stdout=stream,check=True,timeout=120)
        if partial.stat().st_size<100:
            raise RuntimeError('Dump unexpectedly small')
        partial.replace(target)
        digest=hashlib.sha256(target.read_bytes()).hexdigest()
        manifest={'file':target.name,'sha256':digest,'bytes':target.stat().st_size,
                  'utc':stamp,'restore_verified':False}
        target.with_suffix('.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
        print(json.dumps(manifest))
    finally:
        partial.unlink(missing_ok=True)

if __name__=='__main__': main()
