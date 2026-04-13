"""Portfolio routes: GET /api/portfolio, POST /api/portfolio/trade, GET /api/portfolio/history."""

import logging

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.db.queries import (
    delete_position,
    get_position,
    get_positions,
    get_snapshots,
    get_user_profile,
    record_snapshot,
    record_trade,
    update_cash_balance,
    upsert_position,
)

logger = logging.getLogger(__name__)

router = APIRouter()


class TradeRequest(BaseModel):
    ticker: str
    quantity: float
    side: str  # "buy" or "sell"


def _calculate_total_value(price_cache, user_id: str = "default") -> float:
    """Calculate current total portfolio value (cash + positions)."""
    profile = get_user_profile(user_id)
    positions = get_positions(user_id)
    total = profile["cash_balance"]
    for pos in positions:
        pu = price_cache.get(pos["ticker"]) if price_cache else None
        price = pu.price if pu else pos["avg_cost"]
        total += pos["quantity"] * price
    return total


@router.get("/api/portfolio")
def get_portfolio(request: Request):
    """Return current portfolio state."""
    user_id = "default"
    price_cache = getattr(request.app.state, "price_cache", None)

    profile = get_user_profile(user_id)
    positions = get_positions(user_id)

    cash = profile["cash_balance"]
    total_value = cash
    total_pnl = 0.0
    enriched_positions = []

    for pos in positions:
        pu = price_cache.get(pos["ticker"]) if price_cache else None
        current_price = pu.price if pu else pos["avg_cost"]
        unrealized_pnl = (current_price - pos["avg_cost"]) * pos["quantity"]
        if pos["avg_cost"] > 0:
            unrealized_pnl_pct = ((current_price - pos["avg_cost"]) / pos["avg_cost"]) * 100
        else:
            unrealized_pnl_pct = 0.0
        position_value = pos["quantity"] * current_price
        total_value += position_value
        total_pnl += unrealized_pnl
        enriched_positions.append({
            "ticker": pos["ticker"],
            "quantity": pos["quantity"],
            "avg_cost": pos["avg_cost"],
            "current_price": current_price,
            "unrealized_pnl": round(unrealized_pnl, 4),
            "unrealized_pnl_pct": round(unrealized_pnl_pct, 4),
        })

    return {
        "cash_balance": cash,
        "positions": enriched_positions,
        "total_value": round(total_value, 4),
        "total_pnl": round(total_pnl, 4),
    }


@router.post("/api/portfolio/trade")
def execute_trade(trade: TradeRequest, request: Request):
    """Execute a market order (buy or sell)."""
    user_id = "default"
    price_cache = getattr(request.app.state, "price_cache", None)

    ticker = trade.ticker.upper().strip()
    quantity = trade.quantity
    side = trade.side.lower()

    if side not in ("buy", "sell"):
        raise HTTPException(status_code=400, detail=f"Invalid side: {side!r}. Must be 'buy' or 'sell'.")

    if quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be positive.")

    # Get current price
    pu = price_cache.get(ticker) if price_cache else None
    if pu is None:
        raise HTTPException(status_code=400, detail=f"No price available for {ticker}. Is it on the watchlist?")
    current_price = pu.price

    profile = get_user_profile(user_id)

    if side == "buy":
        cost = quantity * current_price
        if cost > profile["cash_balance"]:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient cash: need ${cost:.2f}, have ${profile['cash_balance']:.2f}",
            )
        new_balance = profile["cash_balance"] - cost
        update_cash_balance(new_balance, user_id)

        existing = get_position(ticker, user_id)
        if existing and existing["quantity"] > 0:
            total_qty = existing["quantity"] + quantity
            new_avg = (existing["quantity"] * existing["avg_cost"] + quantity * current_price) / total_qty
            upsert_position(ticker, total_qty, new_avg, user_id)
        else:
            upsert_position(ticker, quantity, current_price, user_id)

        record_trade(ticker, "buy", quantity, current_price, user_id)

    elif side == "sell":
        existing = get_position(ticker, user_id)
        if existing is None or existing["quantity"] < quantity:
            owned = existing["quantity"] if existing else 0
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient shares: need {quantity}, have {owned}",
            )
        proceeds = quantity * current_price
        new_balance = profile["cash_balance"] + proceeds
        update_cash_balance(new_balance, user_id)

        new_qty = existing["quantity"] - quantity
        if new_qty < 0.0001:
            delete_position(ticker, user_id)
        else:
            upsert_position(ticker, new_qty, existing["avg_cost"], user_id)

        record_trade(ticker, "sell", quantity, current_price, user_id)

    # Record snapshot immediately after trade
    try:
        total_value = _calculate_total_value(price_cache, user_id)
        record_snapshot(total_value, user_id)
    except Exception as exc:
        logger.warning("Failed to record snapshot after trade: %s", exc)

    updated_profile = get_user_profile(user_id)
    return {
        "success": True,
        "trade": {
            "ticker": ticker,
            "side": side,
            "quantity": quantity,
            "price": current_price,
        },
        "new_cash_balance": updated_profile["cash_balance"],
    }


@router.get("/api/portfolio/history")
def get_portfolio_history(request: Request):
    """Return portfolio value snapshots over time."""
    user_id = "default"
    snapshots = get_snapshots(user_id, limit=500)
    return {
        "snapshots": [
            {"total_value": s["total_value"], "recorded_at": s["recorded_at"]}
            for s in snapshots
        ]
    }
