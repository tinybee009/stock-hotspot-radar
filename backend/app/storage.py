"""SQLite repositories: local development or Turso's HTTPS pipeline protocol."""
import os
import sqlite3
from pathlib import Path
from urllib.parse import urlsplit

import httpx

SCHEMA = 'CREATE TABLE IF NOT EXISTS watchlist (code TEXT PRIMARY KEY, name TEXT NOT NULL)'


class StorageError(Exception):
    """Safe public error; never include URLs, credentials or upstream responses."""


class SQLiteStorage:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.execute(SCHEMA)

    def execute(self, sql: str, args: tuple[str, ...] = ()) -> list[dict]:
        conn = sqlite3.connect(self.path, timeout=10)
        conn.row_factory = sqlite3.Row
        try:
            with conn:
                cursor = conn.execute(sql, args)
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error:
            raise StorageError('数据库暂时不可用') from None
        finally:
            conn.close()


class TursoStorage:
    def __init__(self, url: str, token: str, transport: httpx.BaseTransport | None = None):
        parsed = urlsplit(url)
        if (parsed.scheme not in ('libsql', 'https') or not parsed.hostname
                or not parsed.hostname.endswith('.turso.io') or parsed.username
                or parsed.password or parsed.port not in (None, 443)
                or parsed.path not in ('', '/') or parsed.query or parsed.fragment):
            raise ValueError('TURSO_DATABASE_URL 必须为控制台提供的 libsql:// 或 https:// 数据库地址')
        if not token.strip():
            raise ValueError('缺少 TURSO_AUTH_TOKEN；禁止退回临时 SQLite')
        self.endpoint = f'https://{parsed.hostname}/v2/pipeline'
        self._token = token
        self._transport = transport
        self.execute(SCHEMA)

    def execute(self, sql: str, args: tuple[str, ...] = ()) -> list[dict]:
        # One request per operation, close stream explicitly. No redirects or SQL interpolation.
        payload = {'requests': [
            {'type': 'execute', 'stmt': {'sql': sql, 'args': [{'type': 'text', 'value': value} for value in args]}},
            {'type': 'close'},
        ]}
        try:
            with httpx.Client(timeout=15, transport=self._transport, follow_redirects=False) as client:
                response = client.post(self.endpoint, headers={'Authorization': f'Bearer {self._token}'}, json=payload)
                response.raise_for_status()
                result = response.json()['results'][0]
                if result['type'] != 'ok' or result['response']['type'] != 'execute':
                    raise ValueError('upstream query failed')
                data = result['response']['result']
                names = [col['name'] for col in data['cols']]
                return [dict(zip(names, [cell.get('value') for cell in row], strict=True)) for row in data['rows']]
        except (httpx.HTTPError, KeyError, ValueError, TypeError, IndexError):
            raise StorageError('数据库暂时不可用，请稍后重试') from None


def create_storage(db_path: str | Path | None = None):
    if db_path is not None:
        return SQLiteStorage(db_path)
    mode = os.getenv('RADAR_STORAGE', 'sqlite')
    if mode == 'turso':
        return TursoStorage(os.getenv('TURSO_DATABASE_URL', ''), os.getenv('TURSO_AUTH_TOKEN', ''))
    if mode == 'sqlite':
        return SQLiteStorage(os.getenv('RADAR_DB_PATH', 'data/radar.sqlite3'))
    raise ValueError('RADAR_STORAGE 仅支持 turso 或 sqlite')
