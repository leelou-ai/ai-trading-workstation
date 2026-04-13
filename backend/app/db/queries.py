"""Database query functions for FinAlly backend."""

import uuid
from datetime import datetime, timezone

from app.db.connection import get_db


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_user_profile(user_id: str = "default") -> dict:
    with get_db() as conn:
        row = conn.execute(
            "SELECT id, cash_balance, created_at FROM users_profile WHERE id = ?",
            (user_id,),
        ).fetchone()
        if row is None:
            return {"id": user_id, "cash_balance": 10000.0, "created_at": _utcnow()}
        return dict(row)


def get_positions(user_id: str = "default") -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, user_id, ticker, quantity, avg_cost, updated_at "
            "FROM positions WHERE user_id = ? AND quantity > 0",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_position(ticker: str, user_id: str = "default") -> dict | None:
    with get_db() as conn:
        row = conn.execute(
            "SELECT id, user_id, ticker, quantity, avg_cost, updated_at "
            "FROM positions WHERE user_id = ? AND ticker = ?",
            (user_id, ticker),
        ).fetchone()
        return dict(row) if row else None


def get_watchlist(user_id: str = "default") -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, user_id, ticker, added_at FROM watchlist WHERE user_id = ? ORDER BY added_at",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_chat_history(user_id: str = "default", limit: int = 50) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, user_id, role, content, actions, created_at "
            "FROM chat_messages WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
        return list(reversed([dict(r) for r in rows]))


def save_message(
    role: str,
    content: str,
    actions: str | None = None,
    user_id: str = "default",
) -> str:
    msg_id = str(uuid.uuid4())
    with get_db() as conn:
        conn.execute(
            "INSERT INTO chat_messages (id, user_id, role, content, actions, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (msg_id, user_id, role, content, actions, _utcnow()),
        )
        conn.commit()
    return msg_id


def get_snapshots(user_id: str = "default", limit: int = 500) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, user_id, total_value, recorded_at "
            "FROM portfolio_snapshots WHERE user_id = ? ORDER BY recorded_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
        return list(reversed([dict(r) for r in rows]))


def update_cash_balance(new_balance: float, user_id: str = "default") -> None:
    with get_db() as conn:
        conn.execute(
            "UPDATE users_profile SET cash_balance = ? WHERE id = ?",
            (new_balance, user_id),
        )
        conn.commit()


def upsert_position(
    ticker: str,
    quantity: float,
    avg_cost: float,
    user_id: str = "default",
) -> None:
    pos_id = str(uuid.uuid4())
    now = _utcnow()
    with get_db() as conn:
        conn.execute(
            """INSERT INTO positions (id, user_id, ticker, quantity, avg_cost, updated_at)
               VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(user_id, ticker) DO UPDATE SET
                 quantity = excluded.quantity,
                 avg_cost = excluded.avg_cost,
                 updated_at = excluded.updated_at""",
            (pos_id, user_id, ticker, quantity, avg_cost, now),
        )
        conn.commit()


def delete_position(ticker: str, user_id: str = "default") -> None:
    with get_db() as conn:
        conn.execute(
            "DELETE FROM positions WHERE user_id = ? AND ticker = ?",
            (user_id, ticker),
        )
        conn.commit()


def record_trade(
    ticker: str,
    side: str,
    quantity: float,
    price: float,
    user_id: str = "default",
) -> str:
    trade_id = str(uuid.uuid4())
    with get_db() as conn:
        conn.execute(
            "INSERT INTO trades (id, user_id, ticker, side, quantity, price, executed_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (trade_id, user_id, ticker, side, quantity, price, _utcnow()),
        )
        conn.commit()
    return trade_id


def add_to_watchlist(ticker: str, user_id: str = "default") -> bool:
    """Add ticker to watchlist. Returns True if added, False if already present."""
    entry_id = str(uuid.uuid4())
    try:
        with get_db() as conn:
            conn.execute(
                "INSERT INTO watchlist (id, user_id, ticker, added_at) VALUES (?, ?, ?, ?)",
                (entry_id, user_id, ticker, _utcnow()),
            )
            conn.commit()
        return True
    except Exception:
        return False


def remove_from_watchlist(ticker: str, user_id: str = "default") -> bool:
    """Remove ticker from watchlist. Returns True if removed."""
    with get_db() as conn:
        cursor = conn.execute(
            "DELETE FROM watchlist WHERE user_id = ? AND ticker = ?",
            (user_id, ticker),
        )
        conn.commit()
        return cursor.rowcount > 0


def record_snapshot(total_value: float, user_id: str = "default") -> None:
    """Record a portfolio value snapshot."""
    snap_id = str(uuid.uuid4())
    with get_db() as conn:
        conn.execute(
            "INSERT INTO portfolio_snapshots (id, user_id, total_value, recorded_at) VALUES (?, ?, ?, ?)",
            (snap_id, user_id, total_value, _utcnow()),
        )
        conn.commit()


def delete_old_snapshots(days: int = 7, user_id: str = "default") -> None:
    """Delete portfolio snapshots older than `days` days."""
    from datetime import timedelta
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    with get_db() as conn:
        conn.execute(
            "DELETE FROM portfolio_snapshots WHERE user_id = ? AND recorded_at < ?",
            (user_id, cutoff),
        )
        conn.commit()
