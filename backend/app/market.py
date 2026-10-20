"""行情提供器边界：接入真实行情时实现 MarketProvider 并注入 create_app。"""
from datetime import datetime, timezone
from typing import Protocol


class MarketProvider(Protocol):
    def snapshot(self) -> dict: ...


class MockMarketProvider:
    def snapshot(self) -> dict:
        return {
            "source": "mock",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "sectors": [
                {"id": "ai", "name": "人工智能", "change_pct": 4.82, "stocks": [
                    {"code": "002230", "name": "科大讯飞", "price": 52.36, "change_pct": 9.99},
                    {"code": "300418", "name": "昆仑万维", "price": 38.52, "change_pct": 7.28}]},
                {"id": "chip", "name": "半导体", "change_pct": 3.65, "stocks": [
                    {"code": "688981", "name": "中芯国际", "price": 89.60, "change_pct": 8.36},
                    {"code": "002371", "name": "北方华创", "price": 425.30, "change_pct": 6.12}]},
                {"id": "robot", "name": "机器人", "change_pct": 2.91, "stocks": [
                    {"code": "300024", "name": "机器人", "price": 18.75, "change_pct": 6.85},
                    {"code": "002747", "name": "埃斯顿", "price": 22.16, "change_pct": 5.23}]},
                {"id": "energy", "name": "新能源", "change_pct": 1.76, "stocks": [
                    {"code": "300750", "name": "宁德时代", "price": 256.80, "change_pct": 4.12},
                    {"code": "002594", "name": "比亚迪", "price": 312.45, "change_pct": 3.56}]},
            ],
        }
