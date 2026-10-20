from fastapi.testclient import TestClient
from app.main import create_app


def test_market_contract_and_ranking(tmp_path):
    with TestClient(create_app(tmp_path / "test.sqlite3")) as client:
        assert client.get("/api/health").json() == {"status": "ok"}
        data = client.get("/api/market").json()
        assert data["source"] == "mock"
        assert data["updated_at"]
        assert len(data["sectors"]) == 4
        changes = [s["change_pct"] for s in data["sectors"]]
        assert changes == sorted(changes, reverse=True)
        for sector in data["sectors"]:
            assert len(sector["stocks"]) >= 2
            gains = [s["change_pct"] for s in sector["stocks"]]
            assert gains == sorted(gains, reverse=True)


def test_watchlist_persistence_duplicate_and_delete(tmp_path):
    path = tmp_path / "persist.sqlite3"
    with TestClient(create_app(path)) as client:
        assert client.get("/api/watchlist").json() == []
        for _ in range(2):
            assert client.post("/api/watchlist", json={"code": "002230"}).status_code == 201
        assert len(client.get("/api/watchlist").json()) == 1
    with TestClient(create_app(path)) as restarted:
        assert restarted.get("/api/watchlist").json() == [{"code": "002230", "name": "科大讯飞"}]
        assert restarted.delete("/api/watchlist/002230").status_code == 204
        assert restarted.get("/api/watchlist").json() == []


def test_invalid_and_unknown_stock(tmp_path):
    with TestClient(create_app(tmp_path / "test.sqlite3")) as client:
        assert client.post("/api/watchlist", json={"code": "invalid"}).status_code == 422
        assert client.post("/api/watchlist", json={"code": "999999"}).status_code == 404
        assert client.delete("/api/watchlist/invalid").status_code == 422
        assert client.get("/api/watchlist").json() == []
