"""Read-only operations demo. SQLite locally; MySQL in Compose. No real assets."""
import json
import os
import socket
from socketserver import ThreadingMixIn
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from time import perf_counter
from wsgiref.simple_server import WSGIServer
from urllib.parse import parse_qs


class LocalServer(ThreadingMixIn, WSGIServer):
    """Loopback learning server: tolerate browser preconnect and own the port."""
    daemon_threads = True
    allow_reuse_address = os.name != 'nt'

    def server_bind(self):
        if os.name == 'nt':
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()

    def get_request(self):
        connection, address = super().get_request()
        connection.settimeout(5)
        return connection, address


class Database:
    def __init__(self, driver='sqlite', path='lab.sqlite3'):
        if driver not in {'sqlite', 'mysql'}:
            raise ValueError('Unsupported database driver')
        self.driver, self.path = driver, path

    @contextmanager
    def connection(self):
        if self.driver == 'sqlite':
            connection = sqlite3.connect(self.path, timeout=2)
        else:
            import pymysql
            connection = pymysql.connect(host=os.environ['DB_HOST'],
                user=os.environ['DB_USER'], password=os.environ['DB_PASSWORD'],
                database=os.environ['DB_NAME'], connect_timeout=2,
                read_timeout=2, write_timeout=2)
        try:
            yield connection
        finally:
            connection.close()

    def initialize_local(self):
        if self.driver != 'sqlite':
            return  # MySQL schema is initialized by the image entrypoint.
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as c:
            c.execute('CREATE TABLE IF NOT EXISTS assets (id INTEGER PRIMARY KEY, name TEXT NOT NULL, zone TEXT NOT NULL)')
            c.executemany('INSERT OR IGNORE INTO assets VALUES (?, ?, ?)',
                [(1, 'demo-core-1', 'management'), (2, 'demo-web-1', 'server'), (3, 'demo-branch-1', 'branch')])
            c.commit()

    def status(self):
        with self.connection() as c:
            cursor = c.cursor()
            cursor.execute('SELECT COUNT(*) FROM assets')
            count = cursor.fetchone()[0]
            cursor.close()
        return {'database': 'available', 'asset_count': count,
                'data_kind': 'synthetic', 'driver': self.driver}

    def assets(self, query):
        """Bounded, parameterized listing for the read-only operations console."""
        values = parse_qs(query, max_num_fields=8)
        if set(values) - {'q', 'zone', 'page', 'page_size', 'sort'}:
            raise ValueError('Unknown filter')
        if any(len(v) != 1 for v in values.values()):
            raise ValueError('Repeated filter')
        value = lambda key, default='': values.get(key, [default])[0]
        q, zone = value('q').strip(), value('zone')
        page, page_size = int(value('page', '1')), int(value('page_size', '10'))
        sort = value('sort', 'id')
        if len(q) > 80 or zone not in {'', 'management', 'server', 'branch'}:
            raise ValueError('Invalid filter')
        if not 1 <= page <= 10000 or not 1 <= page_size <= 100 or sort not in {'id', 'name'}:
            raise ValueError('Invalid pagination')
        marker = '?' if self.driver == 'sqlite' else '%s'
        clauses, parameters = [], []
        if q:
            # Treat wildcard characters as literal input on both supported databases.
            escaped = q.replace('!', '!!').replace('%', '!%').replace('_', '!_')
            clauses.append(f"name LIKE {marker} ESCAPE '!'")
            parameters.append('%' + escaped + '%')
        if zone:
            clauses.append(f'zone = {marker}')
            parameters.append(zone)
        where = ' WHERE ' + ' AND '.join(clauses) if clauses else ''
        order = 'name, id' if sort == 'name' else 'id'
        with self.connection() as connection:
            cursor = connection.cursor()
            cursor.execute('SELECT COUNT(*) FROM assets' + where, parameters)
            total = cursor.fetchone()[0]
            cursor.execute('SELECT id,name,zone FROM assets' + where +
                f' ORDER BY {order} LIMIT {marker} OFFSET {marker}',
                parameters + [page_size, (page - 1) * page_size])
            items = [dict(zip(('id', 'name', 'zone'), row)) for row in cursor.fetchall()]
            cursor.close()
        return {'items': items, 'total': total, 'page': page, 'page_size': page_size,
                'data_kind': 'synthetic'}


class Application:
    def __init__(self, database):
        self.database = database
        self.lock = threading.Lock()
        self.requests = {}

    def __call__(self, environ, start_response):
        started = perf_counter()
        path = environ.get('PATH_INFO', '/')
        route = path if path in {'/', '/healthz', '/readyz', '/api/status', '/api/assets', '/api/drill', '/metrics'} else 'other'
        code = 200
        content_type = 'application/json; charset=utf-8'
        if environ.get('REQUEST_METHOD') != 'GET':
            code, result = 405, {'error': 'read_only_demo'}
        elif path == '/healthz':
            result = {'process': 'alive'}
        elif path == '/':
            content_type = 'text/html; charset=utf-8'
            result = (Path(__file__).parent/'static'/'index.html').read_text(encoding='utf-8')
        elif path == '/api/drill':
            report_path=os.getenv('LOCAL_DRILL_REPORT')
            if report_path and Path(report_path).is_file():
                try:
                    result=json.loads(Path(report_path).read_text(encoding='utf-8'))
                except (OSError,ValueError):
                    code,result=503,{'state':'report_unavailable','stages':[]}
            else:
                result={'state':'not_run','stages':[]}
        elif path == '/api/assets':
            try:
                result = self.database.assets(environ.get('QUERY_STRING', ''))
            except ValueError:
                code, result = 400, {'error': 'invalid_query'}
            except Exception:
                code, result = 503, {'database': 'unavailable'}
        elif path in {'/readyz', '/api/status'}:
            try:
                result = self.database.status()
            except Exception:
                # Errors are deliberately generic: no SQL, passwords or internal exception data.
                code, result = 503, {'database': 'unavailable'}
        elif path == '/metrics':
            content_type = 'text/plain; version=0.0.4; charset=utf-8'
            try:
                self.database.status()
                db_up = 1
            except Exception:
                db_up = 0
            with self.lock:
                snapshot = list(self.requests.items())
            rows = ['# HELP lab_db_up Whether a database query succeeds.',
                    '# TYPE lab_db_up gauge', f'lab_db_up {db_up}',
                    '# HELP lab_http_requests_total Application requests excluding metrics scrapes.',
                    '# TYPE lab_http_requests_total counter']
            for (r, s), count in sorted(snapshot):
                rows.append(f'lab_http_requests_total{{route="{r}",status="{s}"}} {count}')
            result = '\n'.join(rows)+'\n'
        else:
            code, result = 404, {'error': 'not_found'}
        body = (result if isinstance(result, str) else json.dumps(result)).encode('utf-8')
        if route != '/metrics':
            with self.lock:
                key = (route, str(code))
                self.requests[key] = self.requests.get(key, 0)+1
        reason = {200:'OK', 400:'Bad Request', 404:'Not Found', 405:'Method Not Allowed', 503:'Service Unavailable'}[code]
        headers = [('Content-Type',content_type), ('Content-Length',str(len(body))),
                   ('Cache-Control','no-store'), ('X-Content-Type-Options','nosniff')]
        if code == 405:
            headers.append(('Allow','GET'))
        start_response(f'{code} {reason}',headers)
        # Bounded route labels also avoid logging user-controlled paths or query strings.
        print(json.dumps({'route':route,'status':code,'elapsed_ms':round((perf_counter()-started)*1000,3)}),flush=True)
        return [body]


def create_app():
    database = Database(os.getenv('DB_DRIVER','sqlite'),os.getenv('DB_PATH','lab.sqlite3'))
    database.initialize_local()
    return Application(database)


if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    # Single-process local learning mode. Compose uses Gunicorn instead.
    server = make_server('127.0.0.1',int(os.getenv('PORT','8081')),create_app(),server_class=LocalServer)
    print(f'Local demo: http://127.0.0.1:{server.server_port}/',flush=True)
    server.serve_forever()
