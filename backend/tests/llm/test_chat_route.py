"""Tests for POST /api/chat route."""

import os
import pytest
from unittest.mock import MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

os.environ["LLM_MOCK"] = "true"
os.environ["DB_PATH"] = ":memory:"

from app.llm.schemas import AssistantResponse, TradeAction, WatchlistChange
from app.routes.chat import router, ChatRequest


def make_app(price_cache=None, market_data_source=None):
    app = FastAPI()
    app.include_router(router)
    app.state.price_cache = price_cache
    app.state.market_data_source = market_data_source
    return app


def make_price_cache(prices: dict):
    cache = MagicMock()
    def get_price(ticker):
        if ticker in prices:
            update = MagicMock()
            update.price = prices[ticker]
            return update
        return None
    cache.get = get_price
    return cache


MOCK_PROFILE = {"id": "default", "cash_balance": 10000.0, "created_at": "2024-01-01T00:00:00+00:00"}
MOCK_POSITIONS = []
MOCK_WATCHLIST = [
    {"id": "1", "user_id": "default", "ticker": "AAPL", "added_at": "2024-01-01T00:00:00+00:00"},
]
MOCK_CHAT_HISTORY = []


@pytest.fixture
def db_mocks():
    with (
        patch("app.routes.chat.get_user_profile", return_value=MOCK_PROFILE),
        patch("app.routes.chat.get_positions", return_value=MOCK_POSITIONS),
        patch("app.routes.chat.get_watchlist", return_value=MOCK_WATCHLIST),
        patch("app.routes.chat.get_chat_history", return_value=MOCK_CHAT_HISTORY),
        patch("app.routes.chat.save_message", return_value="mock-id"),
        patch("app.routes.chat.get_position", return_value=None),
        patch("app.routes.chat.update_cash_balance"),
        patch("app.routes.chat.upsert_position"),
        patch("app.routes.chat.delete_position"),
        patch("app.routes.chat.record_trade", return_value="trade-id"),
        patch("app.routes.chat.add_to_watchlist", return_value=True),
        patch("app.routes.chat.remove_from_watchlist", return_value=True),
    ):
        yield


def test_chat_valid_message_returns_200(db_mocks):
    price_cache = make_price_cache({"AAPL": 150.0})
    app = make_app(price_cache=price_cache)
    client = TestClient(app)
    response = client.post("/api/chat", json={"message": "What is in my portfolio?"})
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert isinstance(data["message"], str)
    assert len(data["message"]) > 0
    assert "trades" in data
    assert "watchlist_changes" in data
    assert "executed_trades" in data
    assert "executed_watchlist_changes" in data


def test_chat_missing_message_returns_422():
    app = make_app()
    client = TestClient(app)
    response = client.post("/api/chat", json={})
    assert response.status_code == 422


def test_chat_empty_body_returns_422():
    app = make_app()
    client = TestClient(app)
    response = client.post("/api/chat", content=b"", headers={"Content-Type": "application/json"})
    assert response.status_code == 422


def test_chat_buy_message_executes_trade(db_mocks):
    price_cache = make_price_cache({"AAPL": 150.0})
    app = make_app(price_cache=price_cache)
    client = TestClient(app)
    # The mock returns a buy trade for messages containing "buy"
    response = client.post("/api/chat", json={"message": "buy AAPL"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["trades"]) >= 1
    assert data["trades"][0]["side"] == "buy"
    # The trade should have been executed
    assert len(data["executed_trades"]) >= 1
    exec_trade = data["executed_trades"][0]
    assert exec_trade["success"] is True
    assert exec_trade["price"] == 150.0


def test_chat_sell_message_with_position(db_mocks):
    price_cache = make_price_cache({"GOOGL": 175.0})
    existing_pos = {"id": "pos-1", "user_id": "default", "ticker": "GOOGL", "quantity": 20.0, "avg_cost": 160.0, "updated_at": "2024-01-01T00:00:00+00:00"}
    app = make_app(price_cache=price_cache)
    client = TestClient(app)
    with patch("app.routes.chat.get_position", return_value=existing_pos):
        response = client.post("/api/chat", json={"message": "sell GOOGL"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["executed_trades"]) >= 1


def test_chat_watchlist_add_via_mock(db_mocks):
    price_cache = make_price_cache({"AAPL": 150.0})
    app = make_app(price_cache=price_cache)
    client = TestClient(app)
    response = client.post("/api/chat", json={"message": "add PYPL to watchlist"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["watchlist_changes"]) >= 1
    assert data["executed_watchlist_changes"][0]["action"] == "add"
    assert data["executed_watchlist_changes"][0]["success"] is True


def test_chat_buy_insufficient_cash(db_mocks):
    # Price is very high so we cannot afford even 10 shares
    price_cache = make_price_cache({"AAPL": 99999.0})
    poor_profile = {"id": "default", "cash_balance": 10.0, "created_at": "2024-01-01T00:00:00+00:00"}
    app = make_app(price_cache=price_cache)
    client = TestClient(app)
    with patch("app.routes.chat.get_user_profile", return_value=poor_profile):
        with patch("app.routes.chat.get_positions", return_value=MOCK_POSITIONS):
            with patch("app.routes.chat.get_watchlist", return_value=MOCK_WATCHLIST):
                with patch("app.routes.chat.get_chat_history", return_value=MOCK_CHAT_HISTORY):
                    with patch("app.routes.chat.save_message", return_value="mid"):
                        with patch("app.routes.chat.get_position", return_value=None):
                            response = client.post("/api/chat", json={"message": "buy AAPL"})
    assert response.status_code == 200
    data = response.json()
    exec_trades = data["executed_trades"]
    if exec_trades:
        assert exec_trades[0]["success"] is False
        assert "Insufficient cash" in exec_trades[0]["error"]


def test_chat_llm_failure_returns_502(db_mocks):
    price_cache = make_price_cache({"AAPL": 150.0})
    app = make_app(price_cache=price_cache)
    client = TestClient(app)
    with patch.dict(os.environ, {"LLM_MOCK": "false"}):
        with patch("app.llm.client.call_llm", side_effect=Exception("timeout")):
            response = client.post("/api/chat", json={"message": "hello"})
    assert response.status_code == 502
    assert "LLM request failed" in response.json()["detail"]
