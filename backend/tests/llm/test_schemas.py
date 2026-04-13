"""Tests for LLM Pydantic schemas."""

import pytest
from pydantic import ValidationError

from app.llm.schemas import AssistantResponse, TradeAction, WatchlistChange


def test_assistant_response_minimal():
    response = AssistantResponse(message="Hello")
    assert response.message == "Hello"
    assert response.trades == []
    assert response.watchlist_changes == []


def test_assistant_response_with_trades():
    data = {
        "message": "Buying AAPL",
        "trades": [{"ticker": "AAPL", "side": "buy", "quantity": 10}],
    }
    response = AssistantResponse(**data)
    assert len(response.trades) == 1
    assert response.trades[0].ticker == "AAPL"
    assert response.trades[0].side == "buy"
    assert response.trades[0].quantity == 10.0


def test_assistant_response_with_watchlist_changes():
    data = {
        "message": "Adding PYPL",
        "watchlist_changes": [{"ticker": "PYPL", "action": "add"}],
    }
    response = AssistantResponse(**data)
    assert len(response.watchlist_changes) == 1
    assert response.watchlist_changes[0].ticker == "PYPL"
    assert response.watchlist_changes[0].action == "add"


def test_assistant_response_from_json():
    json_str = (
        '{"message": "Analysis complete", "trades": [{"ticker": "TSLA", "side": "sell", "quantity": 5.0}], "watchlist_changes": []}'
    )
    response = AssistantResponse.model_validate_json(json_str)
    assert response.message == "Analysis complete"
    assert response.trades[0].ticker == "TSLA"
    assert response.trades[0].side == "sell"


def test_assistant_response_defaults_from_json():
    json_str = '{"message": "Hello there"}'
    response = AssistantResponse.model_validate_json(json_str)
    assert response.message == "Hello there"
    assert response.trades == []
    assert response.watchlist_changes == []


def test_assistant_response_invalid_json():
    with pytest.raises(Exception):
        AssistantResponse.model_validate_json("{not valid json")


def test_assistant_response_missing_message():
    with pytest.raises(ValidationError):
        AssistantResponse(trades=[])


def test_trade_action_model():
    trade = TradeAction(ticker="NVDA", side="buy", quantity=3.5)
    assert trade.ticker == "NVDA"
    assert trade.side == "buy"
    assert trade.quantity == 3.5


def test_watchlist_change_model():
    change = WatchlistChange(ticker="META", action="remove")
    assert change.ticker == "META"
    assert change.action == "remove"
