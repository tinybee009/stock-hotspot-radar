import os
from contextlib import contextmanager
import re
import sqlite3
from pathlib import Path

from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, Field

from .market import MarketProvider, MockMarketProvider


class WatchlistInput(BaseModel):
    code: str = Field(pattern=r"^\d{6}$")


def create_app(db_path: str | Path | None = None, provider: MarketProvider | None = None) -> FastAPI:
    app = FastAPI(title="A股热点雷达", version="0.1.0")
    path = Path(db_path or os.getenv("RADAR_DB_PATH", "data/radar.sqlite3"))
    path.parent.mkdir(parents=True, exist_ok=True)
    market = provider or MockMarketProvider()

    @contextmanager
    def connect():
        conn = sqlite3.connect(path, timeout=10)
        conn.row_factory = sqlite3.Row
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    with connect() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS watchlist (code TEXT PRIMARY KEY, name TEXT NOT NULL)")

    @app.get("/api/health")
    def health():
        with connect() as conn:
            conn.execute("SELECT 1")
        return {"status": "ok"}

    @app.get("/api/market")
    def get_market():
        snapshot = market.snapshot()
        snapshot["sectors"] = sorted(snapshot["sectors"], key=lambda s: s["change_pct"], reverse=True)
        for sector in snapshot["sectors"]:
            sector["stocks"] = sorted(sector["stocks"], key=lambda s: s["change_pct"], reverse=True)
        return snapshot

    @app.get("/api/watchlist")
    def watchlist():
        with connect() as conn:
            return [dict(row) for row in conn.execute("SELECT code, name FROM watchlist ORDER BY code")]

    @app.post("/api/watchlist", status_code=201)
    def add_stock(item: WatchlistInput):
        stocks = {stock["code"]: stock for sector in market.snapshot()["sectors"] for stock in sector["stocks"]}
        stock = stocks.get(item.code)
        if stock is None:
            raise HTTPException(404, "未找到该股票，模拟版本仅支持页面展示的股票")
        with connect() as conn:
            conn.execute("INSERT OR IGNORE INTO watchlist(code,name) VALUES (?,?)", (item.code, stock["name"]))
        return {"code": item.code, "name": stock["name"]}

    @app.delete("/api/watchlist/{code}", status_code=204)
    def delete_stock(code: str):
        if not re.fullmatch(r"\d{6}", code):
            raise HTTPException(422, "股票代码应为六位数字")
        with connect() as conn:
            conn.execute("DELETE FROM watchlist WHERE code=?", (code,))
        return Response(status_code=204)

    return app


app = create_app()
