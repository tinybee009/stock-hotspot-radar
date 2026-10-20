import os
import pytest
from fastapi.testclient import TestClient
from app.main import create_app


def test_every_resource_requires_login(tmp_path, monkeypatch):
    static = tmp_path / 'static'
    static.mkdir()
    (static / 'index.html').write_text('<html>private radar</html>')
    (static / 'bundle.js').write_text('/* private asset */')
    monkeypatch.setenv('RADAR_STATIC_DIR', str(static))
    with TestClient(create_app(tmp_path / 'data.sqlite3')) as client:
        for path in ['/', '/bundle.js', '/api/health', '/api/market', '/api/watchlist', '/docs', '/openapi.json']:
            response = client.get(path)
            assert response.status_code == 401
            assert 'Basic' in response.headers['www-authenticate']
            assert response.headers['cache-control'] == 'no-store'
        assert client.post('/api/watchlist', json={'code': '002230'}).status_code == 401
        assert client.delete('/api/watchlist/002230').status_code == 401
        client.auth = ('owner', os.environ['RADAR_PASSWORD'])
        assert client.get('/').status_code == 200
        assert client.get('/bundle.js').status_code == 200
        assert client.get('/api/market').status_code == 200
        for headers in [{}, {'Origin': 'https://evil.example'}]:
            assert client.post('/api/watchlist', headers=headers, json={'code': '002230'}).status_code == 403
        assert client.post('/api/watchlist', headers={'Origin': os.environ['RADAR_ORIGIN']}, json={'code': '002230'}).status_code == 201


def test_wrong_credentials_and_throttling(tmp_path):
    with TestClient(create_app(tmp_path / 'data.sqlite3')) as client:
        for _ in range(20):
            assert client.get('/api/market', auth=('owner', 'wrong')).status_code == 401
        assert client.get('/api/market').status_code == 429


def test_missing_config_fails_closed(tmp_path, monkeypatch):
    monkeypatch.delenv('RADAR_PASSWORD')
    with pytest.raises(RuntimeError):
        create_app(tmp_path / 'data.sqlite3')


def test_persistent_path_across_new_app(tmp_path, monkeypatch):
    monkeypatch.setenv('RADAR_DB_PATH', str(tmp_path / 'disk' / 'radar.sqlite3'))
    auth = ('owner', os.environ['RADAR_PASSWORD'])
    with TestClient(create_app(), headers={'Origin': os.environ['RADAR_ORIGIN']}) as client:
        client.auth = auth
        assert client.post('/api/watchlist', json={'code': '002230'}).status_code == 201
    with TestClient(create_app()) as client:
        client.auth = auth
        assert client.get('/api/watchlist').json()[0]['code'] == '002230'
