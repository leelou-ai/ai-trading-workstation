"""Tests for portfolio routes."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from app.routes.portfolio import router


def make_app(price_cache=None, market_data_source=None):
    """Create a test FastAPI app with mocked state."""
    app = FastAPI()
    app.include_router(router)
    if price_cache is not None:
        app.state.price_cache = price_cache
    if market_data_source is not None:
        app.state.market_data_source = market_data_source
    return app


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    from app.db.init import init_db
    init_db()


def make_price_cache(prices: dict):
    """Return a mock price cache that returns PriceUpdate-like objects."""
    cache = MagicMock()
    def _get(ticker):
        if ticker in prices:
            pu = MagicMock()
            pu.price = prices[ticker]
            return pu
        return None
    cache.get.side_effect = _get
    return cache


class TestGetPortfolio:
    def test_returns_correct_shape(self):
        app = make_app(price_cache=make_price_cache({}))
        client = TestClient(app)
        response = client.get("/api/portfolio")
        assert response.status_code == 200
        data = response.json()
        assert "cash_balance" in data
        assert "positions" in data
        assert "total_value" in data
        assert "total_pnl" in data
        assert data["cash_balance"] == 10000.0
        assert data["positions"] == []

    def test_includes_positions_with_prices(self, tmp_path):
        from app.db.queries import upsert_position
        upsert_position("AAPL", 10, 150.0)
        pc = make_price_cache({"AAPL": 160.0})
        app = make_app(price_cache=pc)
        client = TestClient(app)
        response = client.get("/api/portfolio")
        assert response.status_code == 200
        data = response.json()
        assert len(data["positions"]) == 1
        pos = data["positions"][0]
        assert pos["ticker"] == "AAPL"
        assert pos["current_price"] == 160.0
        assert pos["unrealized_pnl"] == pytest.approx(100.0)


class TestExecuteTrade:
    def test_buy_success(self):
        pc = make_price_cache({"AAPL": 100.0})
        app = make_app(price_cache=pc)
        client = TestClient(app)
        response = client.post("/api/portfolio/trade", json={"ticker": "AAPL", "quantity": 10, "side": "buy"})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["trade"]["ticker"] == "AAPL"
        assert data["trade"]["side"] == "buy"
        assert data["new_cash_balance"] == pytest.approx(9000.0)

    def test_buy_insufficient_cash(self):
        pc = make_price_cache({"AAPL": 2000.0})
        app = make_app(price_cache=pc)
        client = TestClient(app)
        # 2000 * 10 = 20000 > 10000
        response = client.post("/api/portfolio/trade", json={"ticker": "AAPL", "quantity": 10, "side": "buy"})
        assert response.status_code == 400
        assert "Insufficient cash" in response.json()["detail"]

    def test_sell_no_position(self):
        pc = make_price_cache({"AAPL": 100.0})
        app = make_app(price_cache=pc)
        client = TestClient(app)
        response = client.post("/api/portfolio/trade", json={"ticker": "AAPL", "quantity": 5, "side": "sell"})
        assert response.status_code == 400
        assert "Insufficient shares" in response.json()["detail"]

    def test_sell_success(self):
        from app.db.queries import upsert_position
        upsert_position("AAPL", 10, 100.0)
        pc = make_price_cache({"AAPL": 120.0})
        app = make_app(price_cache=pc)
        client = TestClient(app)
        response = client.post("/api/portfolio/trade", json={"ticker": "AAPL", "quantity": 5, "side": "sell"})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # 10000 + 5 * 120 = 10600
        assert data["new_cash_balance"] == pytest.approx(10600.0)

    def test_no_price_returns_400(self):
        pc = make_price_cache({})
        app = make_app(price_cache=pc)
        client = TestClient(app)
        response = client.post("/api/portfolio/trade", json={"ticker": "UNKNOWN", "quantity": 1, "side": "buy"})
        assert response.status_code == 400


class TestPortfolioHistory:
    def test_returns_snapshots(self):
        from app.db.queries import record_snapshot
        record_snapshot(10500.0)
        app = make_app(price_cache=make_price_cache({}))
        client = TestClient(app)
        response = client.get("/api/portfolio/history")
        assert response.status_code == 200
        data = response.json()
        assert "snapshots" in data
        assert len(data["snapshots"]) == 1
        assert data["snapshots"][0]["total_value"] == 10500.0
