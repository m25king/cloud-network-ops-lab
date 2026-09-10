"""Restore a backup into a NEW isolated database, compare data, retain evidence."""
import argparse
import datetime
import hashlib
import json
import subprocess
from pathlib import Path

CLOUD=Path(__file__).resolve().parents[1]
PREFIX=['docker','compose','exec','-T','db','sh','-c']

def sql(query):
    return subprocess.run(PREFIX+['MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysql -u root --batch --skip-column-names'],
        cwd=CLOUD,input=query.encode(),stdout=subprocess.PIPE,check=True,timeout=60).stdout.decode().strip()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('backup',type=Path)
    args=parser.parse_args()
    source=args.backup.resolve()
    if source.parent != (CLOUD/'backups').resolve() or source.suffix!='.sql':
        parser.error('Choose a .sql produced in cloud/backups by backup.py')
    manifest=json.loads(source.with_suffix('.json').read_text(encoding='utf-8'))
    if hashlib.sha256(source.read_bytes()).hexdigest()!=manifest['sha256']:
        raise RuntimeError('Checksum mismatch; no restore attempted')
    database='restore_'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d%H%M%S%f')
    sql(f'CREATE DATABASE `{database}`;')
    with source.open('rb') as stream:
        subprocess.run(PREFIX+[f'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysql -u root {database}'],
            cwd=CLOUD,stdin=stream,check=True,timeout=120)
    before=sql('SELECT id,name,zone FROM lab.assets ORDER BY id;')
    after=sql(f'SELECT id,name,zone FROM {database}.assets ORDER BY id;')
    result={'backup':source.name,'restore_database':database,'equal_to_current_synthetic_dataset':before==after,
            'rows_restored':len(after.splitlines()),'note':'Comparison assumes the read-only fixture has not changed since backup.'}
    out=source.with_suffix('.restore.json')
    out.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result))
    if before!=after or not after:
        raise SystemExit(1)

if __name__=='__main__': main()
