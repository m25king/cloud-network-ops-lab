"""Start the local SQLite demo without installing third-party packages."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys
import urllib.request
import webbrowser
from wsgiref.simple_server import make_server

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8081)
    parser.add_argument('--no-browser', action='store_true')
    args = parser.parse_args()
    if not 0 <= args.port <= 65535:
        parser.error('port must be between 0 and 65535')
    url = f'http://127.0.0.1:{args.port}'
    spec = importlib.util.spec_from_file_location('lab_local_app', ROOT / 'cloud' / 'app.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    try:
        server = make_server('127.0.0.1', args.port, None, server_class=module.LocalServer)
    except OSError:
        # A second click may reuse this demo, but never stop an existing process.
        try:
            with urllib.request.urlopen(url + '/api/status', timeout=2) as response:
                status = json.load(response)
            if status.get('data_kind') != 'synthetic' or status.get('driver') != 'sqlite':
                raise ValueError('different application')
        except Exception:
            print(f'Cannot use port {args.port}. Choose another port with --port.', flush=True)
            return 1
        print(f'An existing local SQLite demo is available: {url}', flush=True)
        if not args.no_browser:
            webbrowser.open(url)
        return 0
    with server:
        data_dir = ROOT / 'artifacts' / 'local-runtime'
        data_dir.mkdir(parents=True, exist_ok=True)
        os.environ['DB_DRIVER'] = 'sqlite'
        os.environ['DB_PATH'] = str(data_dir / 'lab.sqlite3')
        # A fresh run has no drill history until a real drill is performed.
        os.environ.pop('LOCAL_DRILL_REPORT', None)
        server.set_app(module.create_app())
        url = f'http://127.0.0.1:{server.server_port}'
        print(f'Local demo: {url}', flush=True)
        print('Keep this window open. Press Ctrl+C to stop this process.', flush=True)
        if not args.no_browser:
            webbrowser.open(url)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print('Local demo stopped.', flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
