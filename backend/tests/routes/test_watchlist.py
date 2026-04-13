"""Tests for watchlist routes."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from app.routes.watchlist import router


def make_app(price_cache=None, market_data_source=None):
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
    cache = MagicMock()
    def _get(ticker):
        if ticker in prices:
            pu = MagicMock()
            pu.price = prices[ticker]
            pu.change = 0.5
            pu.change_percent = 0.3
            pu.direction = "up"
            return pu
        return None
    cache.get.side_effect = _get
    return cache


class TestGetWatchlist:
    def test_returns_10_default_tickers(self):
        pc = make_price_cache({})
        app = make_app(price_cache=pc)
        client = TestClient(app)
        response = client.get("/api/watchlist")
        assert response.status_code == 200
        data = response.json()
        assert "tickers" in data
        assert len(data["tickers"]) == 10

    def test_enriches_with_prices(self):
        pc = make_price_cache({"AAPL": 190.0})
        app = make_app(price_cache=pc)
        client = TestClient(app)
        response = client.get("/api/watchlist")
        data = response.json()
        aapl = next((t for t in data["tickers"] if t["ticker"] == "AAPL"), None)
        assert aapl is not None
        assert aapl["price"] == 190.0
        assert aapl["direction"] == "up"

    def test_null_price_for_uncached_ticker(self):
        pc = make_price_cache({})
        app = make_app(price_cache=pc)
        client = TestClient(app)
        response = client.get("/api/watchlist")
        data = response.json()
        # All tickers should be present but prices will be None
        assert all(t["price"] is None for t in data["tickers"])


class TestAddWatchlist:
    def test_add_new_ticker(self):
        mds = MagicMock()
        pc = make_price_cache({})
        app = make_app(price_cache=pc, market_data_source=mds)
        client = TestClient(app)
        response = client.post("/api/watchlist", json={"ticker": "pypl"})
        assert response.status_code == 201
        data = response.json()
        assert data["ticker"] == "PYPL"
        mds.add_ticker.assert_called_once_with("PYPL")

    def test_duplicate_returns_409(self):
        pc = make_price_cache({})
        app = make_app(price_cache=pc)
        client = TestClient(app)
        # AAPL is already in the default watchlist
        response = client.post("/api/watchlist", json={"ticker": "AAPL"})
        assert response.status_code == 409

    def test_invalid_ticker_returns_422(self):
        pc = make_price_cache({})
        app = make_app(price_cache=pc)
        client = TestClient(app)
        response = client.post("/api/watchlist", json={"ticker": "INVALID123"})
        assert response.status_code == 422


class TestRemoveWatchlist:
    def test_remove_existing_ticker(self):
        mds = MagicMock()
        pc = make_price_cache({})
        app = make_app(price_cache=pc, market_data_source=mds)
        client = TestClient(app)
        response = client.delete("/api/watchlist/AAPL")
        assert response.status_code == 204

    def test_remove_nonexistent_returns_404(self):
        pc = make_price_cache({})
        app = make_app(price_cache=pc)
        client = TestClient(app)
        response = client.delete("/api/watchlist/NOTREAL")
        assert response.status_code == 404
