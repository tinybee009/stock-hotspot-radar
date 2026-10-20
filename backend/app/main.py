import os
import re
from pathlib import Path

from fastapi import FastAPI, HTTPException, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from .storage import create_storage, StorageError
from .security import install_security
from pydantic import BaseModel, Field

from .market import MarketProvider, MockMarketProvider


class WatchlistInput(BaseModel):
    code: str = Field(pattern=r"^\d{6}$")


def create_app(db_path: str | Path | None = None, provider: MarketProvider | None = None) -> FastAPI:
    app = FastAPI(title="A股热点雷达", version="0.1.0")
    install_security(app)
    storage = create_storage(db_path)
    market = provider or MockMarketProvider()

    @app.exception_handler(StorageError)
    async def storage_error(request, exc):
        return JSONResponse(status_code=503, content={"detail": "数据库暂时不可用，请稍后重试"})

    @app.get("/api/health")
    def health():
        storage.execute("SELECT 1")
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
        return storage.execute("SELECT code, name FROM watchlist ORDER BY code")

    @app.post("/api/watchlist", status_code=201)
    def add_stock(item: WatchlistInput):
        stocks = {stock["code"]: stock for sector in market.snapshot()["sectors"] for stock in sector["stocks"]}
        stock = stocks.get(item.code)
        if stock is None:
            raise HTTPException(404, "未找到该股票，模拟版本仅支持页面展示的股票")
        storage.execute("INSERT OR IGNORE INTO watchlist(code,name) VALUES (?,?)", (item.code, stock["name"]))
        return {"code": item.code, "name": stock["name"]}

    @app.delete("/api/watchlist/{code}", status_code=204)
    def delete_stock(code: str):
        if not re.fullmatch(r"\d{6}", code):
            raise HTTPException(422, "股票代码应为六位数字")
        storage.execute("DELETE FROM watchlist WHERE code=?", (code,))
        return Response(status_code=204)

    static_dir = Path(os.getenv("RADAR_STATIC_DIR", str(Path(__file__).resolve().parents[2] / "frontend" / "dist")))
    if static_dir.is_dir():
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="frontend")
    return app
