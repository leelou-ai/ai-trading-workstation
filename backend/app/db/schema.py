"""SQL DDL statements for FinAlly database schema."""

CREATE_USERS_PROFILE = """
CREATE TABLE IF NOT EXISTS users_profile (
    id           TEXT PRIMARY KEY DEFAULT 'default',
    user_id      TEXT NOT NULL DEFAULT 'default',
    cash_balance REAL NOT NULL DEFAULT 10000.0,
    created_at   TEXT NOT NULL
)
"""

CREATE_WATCHLIST = """
CREATE TABLE IF NOT EXISTS watchlist (
    id       TEXT PRIMARY KEY,
    user_id  TEXT NOT NULL DEFAULT 'default',
    ticker   TEXT NOT NULL,
    added_at TEXT NOT NULL,
    UNIQUE(user_id, ticker)
)
"""

CREATE_POSITIONS = """
CREATE TABLE IF NOT EXISTS positions (
    id         TEXT PRIMARY KEY,
    user_id    TEXT NOT NULL DEFAULT 'default',
    ticker     TEXT NOT NULL,
    quantity   REAL NOT NULL DEFAULT 0,
    avg_cost   REAL NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL,
    UNIQUE(user_id, ticker)
)
"""

CREATE_TRADES = """
CREATE TABLE IF NOT EXISTS trades (
    id          TEXT PRIMARY KEY,
    user_id     TEXT NOT NULL DEFAULT 'default',
    ticker      TEXT NOT NULL,
    side        TEXT NOT NULL,
    quantity    REAL NOT NULL,
    price       REAL NOT NULL,
    executed_at TEXT NOT NULL
)
"""

CREATE_PORTFOLIO_SNAPSHOTS = """
CREATE TABLE IF NOT EXISTS portfolio_snapshots (
    id          TEXT PRIMARY KEY,
    user_id     TEXT NOT NULL DEFAULT 'default',
    total_value REAL NOT NULL,
    recorded_at TEXT NOT NULL
)
"""

CREATE_CHAT_MESSAGES = """
CREATE TABLE IF NOT EXISTS chat_messages (
    id         TEXT PRIMARY KEY,
    user_id    TEXT NOT NULL DEFAULT 'default',
    role       TEXT NOT NULL,
    content    TEXT NOT NULL,
    actions    TEXT,
    created_at TEXT NOT NULL
)
"""

# All DDL statements in creation order
ALL_TABLES = [
    CREATE_USERS_PROFILE,
    CREATE_WATCHLIST,
    CREATE_POSITIONS,
    CREATE_TRADES,
    CREATE_PORTFOLIO_SNAPSHOTS,
    CREATE_CHAT_MESSAGES,
]

# Default tickers for the watchlist seed
DEFAULT_WATCHLIST_TICKERS = [
    "AAPL",
    "GOOGL",
    "MSFT",
    "AMZN",
    "TSLA",
    "NVDA",
    "META",
    "JPM",
    "V",
    "NFLX",
]
