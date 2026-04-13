"""SQLite connection management for FinAlly backend."""

import os
import sqlite3
from contextlib import contextmanager
from typing import Generator

# Default path inside Docker container; override via DB_PATH env var for tests
DEFAULT_DB_PATH = "/app/db/finally.db"


def get_db_path() -> str:
    """Return the database file path from environment or default."""
    return os.environ.get("DB_PATH", DEFAULT_DB_PATH)


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """
    Yield a SQLite connection with WAL mode, foreign keys, and Row factory.

    Each call opens a new connection and closes it on exit — thread-safe,
    no shared state between requests.
    """
    db_path = get_db_path()

    # Ensure the directory exists (handles first-run outside Docker)
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row

    try:
        # WAL mode allows concurrent reads alongside a single writer
        conn.execute("PRAGMA journal_mode=WAL")
        # Enforce foreign key constraints
        conn.execute("PRAGMA foreign_keys=ON")
        yield conn
    finally:
        conn.close()
