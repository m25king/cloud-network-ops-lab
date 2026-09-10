"""Generate only absent local credentials. Never print secret values."""
import secrets
from pathlib import Path

def main():
    path=Path(__file__).resolve().parents[1]/'.env'
    if path.exists():
        print('.env already exists; preserved.')
        return
    with path.open('x',encoding='utf-8') as stream:
        for name in ['DB_PASSWORD','DB_ROOT_PASSWORD','GRAFANA_PASSWORD']:
            stream.write(f'{name}={secrets.token_hex(24)}\n')
    try: path.chmod(0o600)
    except OSError: pass
    print('Created local .env. Read GRAFANA_PASSWORD locally to sign in; do not commit this file.')

if __name__=='__main__': main()
