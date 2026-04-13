"""Tests for mock LLM response generation."""

from app.llm.mock import get_mock_response
from app.llm.schemas import AssistantResponse


def test_mock_returns_valid_response():
    response = get_mock_response("How is my portfolio doing?")
    assert isinstance(response, AssistantResponse)
    assert isinstance(response.message, str)
    assert len(response.message) > 0
    assert isinstance(response.trades, list)
    assert isinstance(response.watchlist_changes, list)


def test_mock_buy_intent_includes_buy_trade():
    response = get_mock_response("I want to buy some AAPL shares")
    assert len(response.trades) >= 1
    assert response.trades[0].side == "buy"
    assert response.trades[0].quantity > 0


def test_mock_sell_intent_includes_sell_trade():
    response = get_mock_response("Please sell TSLA")
    assert len(response.trades) >= 1
    assert response.trades[0].side == "sell"
    assert response.trades[0].quantity > 0


def test_mock_add_intent_includes_watchlist_add():
    response = get_mock_response("add PYPL to my watchlist")
    assert len(response.watchlist_changes) >= 1
    assert response.watchlist_changes[0].action == "add"


def test_mock_generic_message_returns_analysis():
    response = get_mock_response("What do you think about my holdings?")
    assert isinstance(response.message, str)
    assert len(response.message) > 0
    # No trades or watchlist changes for generic questions
    assert response.trades == []
    assert response.watchlist_changes == []


def test_mock_deterministic_same_input():
    r1 = get_mock_response("buy MSFT")
    r2 = get_mock_response("buy MSFT")
    assert r1.message == r2.message
    assert len(r1.trades) == len(r2.trades)
    if r1.trades:
        assert r1.trades[0].ticker == r2.trades[0].ticker
        assert r1.trades[0].side == r2.trades[0].side


def test_mock_buy_extracts_ticker():
    response = get_mock_response("buy NVDA")
    assert response.trades[0].ticker == "NVDA"


def test_mock_sell_extracts_ticker():
    response = get_mock_response("sell GOOGL shares")
    assert response.trades[0].ticker == "GOOGL"
