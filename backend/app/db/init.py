"""Database initialization and seeding for FinAlly."""

import os
import uuid
from datetime import datetime, timezone

from app.db.connection import get_db, get_db_path
from app.db.schema import ALL_TABLES, DEFAULT_WATCHLIST_TICKERS


def _utcnow() -> str:
    """Return current UTC time as an ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


def init_db() -> None:
    """
    Create schema and seed default data if needed.

    Safe to call on every startup — uses IF NOT EXISTS and checks before
    inserting seed rows so repeated calls are idempotent.
    """
    db_path = get_db_path()

    # Ensure the parent directory exists (e.g. /app/db/)
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    with get_db() as conn:
        # Create all tables
        for ddl in ALL_TABLES:
            conn.execute(ddl)

        # Seed default user profile if absent
        existing_user = conn.execute(
            "SELECT id FROM users_profile WHERE id = 'default'"
        ).fetchone()
        if existing_user is None:
            conn.execute(
                "INSERT INTO users_profile (id, user_id, cash_balance, created_at) "
                "VALUES ('default', 'default', 10000.0, ?)",
                (_utcnow(),),
            )

        # Seed default watchlist if empty for the default user
        watchlist_count = conn.execute(
            "SELECT COUNT(*) FROM watchlist WHERE user_id = 'default'"
        ).fetchone()[0]
        if watchlist_count == 0:
            for ticker in DEFAULT_WATCHLIST_TICKERS:
                conn.execute(
                    "INSERT INTO watchlist (id, user_id, ticker, added_at) "
                    "VALUES (?, 'default', ?, ?)",
                    (str(uuid.uuid4()), ticker, _utcnow()),
                )

        conn.commit()
