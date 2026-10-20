import secrets
import pytest

@pytest.fixture(autouse=True)
def credentials(monkeypatch):
    monkeypatch.setenv('RADAR_STORAGE', 'sqlite')
    monkeypatch.delenv('TURSO_DATABASE_URL', raising=False)
    monkeypatch.delenv('TURSO_AUTH_TOKEN', raising=False)
    monkeypatch.setenv('RADAR_USERNAME', 'owner')
    monkeypatch.setenv('RADAR_PASSWORD', secrets.token_urlsafe(32))
    monkeypatch.setenv('RADAR_ORIGIN', 'https://radar.example.test')
