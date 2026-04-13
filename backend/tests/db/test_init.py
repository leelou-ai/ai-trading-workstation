"""Tests for database initialization."""

import sqlite3

import pytest

from app.db.init import init_db


@pytest.fixture
def db_path(tmp_path, monkeypatch):
    path = tmp_path / "test.db"
    monkeypatch.setenv("DB_PATH", str(path))
    return path


def test_init_creates_all_tables(db_path):
    init_db()
    conn = sqlite3.connect(str(db_path))
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}
    expected = {"users_profile", "watchlist", "positions", "trades", "portfolio_snapshots", "chat_messages"}
    assert expected.issubset(tables)
    conn.close()


def test_init_idempotent(db_path):
    init_db()
    init_db()  # Should not raise


def test_init_seeds_default_user(db_path):
    init_db()
    conn = sqlite3.connect(str(db_path))
    row = conn.execute("SELECT cash_balance FROM users_profile WHERE id='default'").fetchone()
    assert row is not None
    assert row[0] == 10000.0
    conn.close()


def test_init_seeds_watchlist(db_path):
    init_db()
    conn = sqlite3.connect(str(db_path))
    count = conn.execute("SELECT COUNT(*) FROM watchlist WHERE user_id='default'").fetchone()[0]
    assert count == 10
    conn.close()
