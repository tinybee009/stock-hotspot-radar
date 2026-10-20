import json
import secrets
import sqlite3

import httpx
import pytest
from fastapi.testclient import TestClient

from app.storage import StorageError, TursoStorage, create_storage
from app.main import create_app


def remote_db(tmp_path, token):
    """Simulate the documented HTTP wire contract backed by an independent SQLite file."""
    path = tmp_path / 'remote.sqlite3'

    def handler(request):
        assert request.url.scheme == 'https'
        assert request.url.path == '/v2/pipeline'
        assert request.headers['Authorization'] == f'Bearer {token}'
        payload = json.loads(request.content)
        assert payload['requests'][1] == {'type': 'close'}
        stmt = payload['requests'][0]['stmt']
        args = [arg['value'] for arg in stmt['args']]
        assert all(arg['type'] == 'text' for arg in stmt['args'])
        with sqlite3.connect(path) as conn:
            cursor = conn.execute(stmt['sql'], args)
            cols = [{'name': col[0]} for col in (cursor.description or [])]
            rows = [[{'type': 'text', 'value': str(value)} for value in row] for row in cursor.fetchall()]
        return httpx.Response(200, json={'results': [
            {'type': 'ok', 'response': {'type': 'execute', 'result': {'cols': cols, 'rows': rows}}},
            {'type': 'ok', 'response': {'type': 'close'}},
        ]})
    return httpx.MockTransport(handler)


def test_turso_persistence_duplicates_and_bound_parameters(tmp_path):
    token = secrets.token_urlsafe(32)
    transport = remote_db(tmp_path, token)
    def store():
        return TursoStorage('libsql://sample-owner.turso.io', token, transport)
    first = store()
    name = "测试'); DROP TABLE watchlist; --"
    for _ in range(2):
        first.execute('INSERT OR IGNORE INTO watchlist VALUES (?,?)', ('002230', name))
    second = store()
    assert second.execute('SELECT code,name FROM watchlist') == [{'code': '002230', 'name': name}]
    second.execute('DELETE FROM watchlist WHERE code=?', ('002230',))
    assert store().execute('SELECT code,name FROM watchlist') == []


@pytest.mark.parametrize('url', ['http://sample.turso.io', 'https://evil.example', 'libsql://user:password@sample.turso.io', 'https://sample.turso.io?token=secret'])
def test_reject_unsafe_database_url(url):
    with pytest.raises(ValueError):
        TursoStorage(url, secrets.token_urlsafe(32))


def test_turso_never_falls_back_to_ephemeral_disk(monkeypatch):
    monkeypatch.setenv('RADAR_STORAGE', 'turso')
    monkeypatch.setenv('TURSO_DATABASE_URL', 'libsql://sample-owner.turso.io')
    with pytest.raises(ValueError):
        create_storage()


@pytest.mark.parametrize('failure', ['http', 'sql', 'malformed', 'timeout'])
def test_upstream_errors_are_sanitized(failure):
    token = secrets.token_urlsafe(32)
    def handler(request):
        if failure == 'timeout':
            raise httpx.ReadTimeout(token, request=request)
        if failure == 'http':
            return httpx.Response(401, text=token)
        if failure == 'malformed':
            return httpx.Response(200, text=token)
        return httpx.Response(200, json={'results': [{'type': 'error', 'error': {'message': token}}]})
    with pytest.raises(StorageError) as caught:
        TursoStorage('libsql://sample-owner.turso.io', token, httpx.MockTransport(handler))
    assert token not in str(caught.value)


def test_api_reports_remote_outage_without_losing_data(tmp_path, monkeypatch):
    token = secrets.token_urlsafe(32)
    storage = TursoStorage('libsql://sample-owner.turso.io', token, remote_db(tmp_path, token))
    monkeypatch.setattr('app.main.create_storage', lambda _: storage)
    import os
    with TestClient(create_app()) as client:
        client.auth = ('owner', os.environ['RADAR_PASSWORD'])
        def fail(request):
            return httpx.Response(503, text=token)
        storage._transport = httpx.MockTransport(fail)
        response = client.get('/api/watchlist')
        assert response.status_code == 503
        assert token not in response.text
