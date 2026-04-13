"""Tests for database query functions."""

import pytest

from app.db.init import init_db
from app.db.queries import (
    add_to_watchlist,
    delete_position,
    get_position,
    get_positions,
    get_snapshots,
    get_user_profile,
    get_watchlist,
    record_snapshot,
    record_trade,
    remove_from_watchlist,
    update_cash_balance,
    upsert_position,
)


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    path = tmp_path / "test.db"
    monkeypatch.setenv("DB_PATH", str(path))
    init_db()


def test_get_user_profile():
    profile = get_user_profile()
    assert profile["cash_balance"] == 10000.0


def test_update_cash_balance():
    update_cash_balance(5000.0)
    assert get_user_profile()["cash_balance"] == 5000.0


def test_watchlist_operations():
    initial = get_watchlist()
    assert len(initial) == 10
    add_to_watchlist("PYPL")
    assert len(get_watchlist()) == 11
    removed = remove_from_watchlist("PYPL")
    assert removed is True
    assert len(get_watchlist()) == 10
    not_found = remove_from_watchlist("PYPL")
    assert not_found is False


def test_position_operations():
    assert get_positions() == []
    upsert_position("AAPL", 10, 150.0)
    pos = get_position("AAPL")
    assert pos is not None
    assert pos["quantity"] == 10
    assert pos["avg_cost"] == 150.0
    upsert_position("AAPL", 15, 155.0)
    pos = get_position("AAPL")
    assert pos["quantity"] == 15
    delete_position("AAPL")
    assert get_position("AAPL") is None


def test_record_trade():
    trade_id = record_trade("AAPL", "buy", 10, 150.0)
    assert isinstance(trade_id, str) and len(trade_id) > 0


def test_snapshots():
    record_snapshot(10500.0)
    snaps = get_snapshots()
    assert len(snaps) == 1
    assert snaps[0]["total_value"] == 10500.0
