"""Chat route: POST /api/chat — LLM-powered AI assistant."""

import json
import logging
import os

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.db.queries import (
    add_to_watchlist,
    delete_position,
    get_chat_history,
    get_position,
    get_positions,
    get_user_profile,
    get_watchlist,
    record_trade,
    remove_from_watchlist,
    save_message,
    update_cash_balance,
    upsert_position,
)
from app.llm.client import SYSTEM_PROMPT
from app.llm.schemas import AssistantResponse

logger = logging.getLogger(__name__)

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


def build_portfolio_context(price_cache, user_id: str = "default") -> str:
    profile = get_user_profile(user_id)
    positions = get_positions(user_id)
    watchlist = get_watchlist(user_id)
    total_value = profile["cash_balance"]
    position_lines = []
    for pos in positions:
        price_update = price_cache.get(pos["ticker"]) if price_cache else None
        current_price = price_update.price if price_update else pos["avg_cost"]
        value = pos["quantity"] * current_price
        pnl = value - (pos["quantity"] * pos["avg_cost"])
        total_value += value
        ticker = pos["ticker"]
        qty = pos["quantity"]
        avg = pos["avg_cost"]
        position_lines.append(
            f"  {ticker}: {qty} shares @ avg ${avg:.2f}, current ${current_price:.2f}, P&L ${pnl:.2f}"
        )
    watchlist_prices = []
    for w in watchlist:
        pu = price_cache.get(w["ticker"]) if price_cache else None
        ps = f"${pu.price:.2f}" if pu else "N/A"
        t = w["ticker"]
        watchlist_prices.append(f"{t}: {ps}")
    ps2 = "\n".join(position_lines) if position_lines else "  (none)"
    ws = ", ".join(watchlist_prices)
    cb = profile["cash_balance"]
    return (
        f"Portfolio Summary:\n"
        f"Cash: ${cb:.2f}\n"
        f"Total Value: ${total_value:.2f}\n"
        f"Positions:\n{ps2}\n"
        f"Watchlist: {ws}"
    )


def execute_trade(ticker, side, quantity, price_cache, user_id="default"):
    price_update = price_cache.get(ticker) if price_cache else None
    if price_update is None:
        return {
            "ticker": ticker, "side": side, "quantity": quantity,
            "price": None, "success": False, "error": f"No price available for {ticker}",
        }
    current_price = price_update.price
    profile = get_user_profile(user_id)
    if side == "buy":
        cost = quantity * current_price
        if profile["cash_balance"] < cost:
            cash = profile["cash_balance"]
            return {
                "ticker": ticker, "side": side, "quantity": quantity,
                "price": current_price, "success": False,
                "error": f"Insufficient cash: need ${cost:.2f}, have ${cash:.2f}",
            }
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
        return {"ticker": ticker, "side": "buy", "quantity": quantity, "price": current_price, "success": True}
    elif side == "sell":
        existing = get_position(ticker, user_id)
        if existing is None or existing["quantity"] < quantity:
            owned = existing["quantity"] if existing else 0
            return {
                "ticker": ticker, "side": side, "quantity": quantity,
                "price": current_price, "success": False,
                "error": f"Insufficient shares: need {quantity}, have {owned}",
            }
        proceeds = quantity * current_price
        new_balance = profile["cash_balance"] + proceeds
        update_cash_balance(new_balance, user_id)
        new_qty = existing["quantity"] - quantity
        if new_qty < 0.0001:
            delete_position(ticker, user_id)
        else:
            upsert_position(ticker, new_qty, existing["avg_cost"], user_id)
        record_trade(ticker, "sell", quantity, current_price, user_id)
        return {"ticker": ticker, "side": "sell", "quantity": quantity, "price": current_price, "success": True}
    else:
        return {
            "ticker": ticker, "side": side, "quantity": quantity,
            "price": None, "success": False, "error": f"Invalid side: {side!r}",
        }


async def execute_watchlist_change(ticker, action, request, user_id="default"):
    market_data_source = getattr(request.app.state, "market_data_source", None)
    if action == "add":
        try:
            add_to_watchlist(ticker, user_id)
        except Exception:
            pass
        if market_data_source is not None:
            try:
                await market_data_source.add_ticker(ticker)
            except Exception:
                pass
        return {"ticker": ticker, "action": "add", "success": True}
    elif action == "remove":
        position = get_position(ticker, user_id)
        removed = remove_from_watchlist(ticker, user_id)
        if market_data_source is not None and (position is None or position["quantity"] == 0):
            try:
                await market_data_source.remove_ticker(ticker)
            except Exception:
                pass
        return {"ticker": ticker, "action": "remove", "success": removed}
    else:
        return {"ticker": ticker, "action": action, "success": False, "error": f"Invalid action: {action!r}"}


@router.post("/api/chat")
async def chat(chat_request: ChatRequest, request: Request):
    user_message = chat_request.message
    user_id = "default"
    price_cache = getattr(request.app.state, "price_cache", None)

    try:
        portfolio_context = build_portfolio_context(price_cache, user_id)
    except Exception as exc:
        logger.warning("Failed to build portfolio context: %s", exc)
        portfolio_context = "Portfolio data unavailable."

    try:
        chat_history = get_chat_history(user_id, limit=20)
    except Exception as exc:
        logger.warning("Failed to load chat history: %s", exc)
        chat_history = []

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": f"Current portfolio:\n{portfolio_context}"},
    ]
    for msg in chat_history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})

    llm_mock = os.environ.get("LLM_MOCK", "false").lower() == "true"
    if llm_mock:
        from app.llm.mock import get_mock_response
        assistant_response: AssistantResponse = get_mock_response(user_message)
    else:
        from app.llm.client import call_llm
        try:
            assistant_response = call_llm(messages)
        except ValueError as exc:
            logger.error("LLM parse error: %s", exc)
            raise HTTPException(status_code=502, detail="Assistant response could not be processed")
        except Exception as exc:
            logger.error("LLM request failed: %s", exc)
            raise HTTPException(status_code=502, detail=f"LLM request failed: {str(exc)[:100]}")

    executed_trades = []
    for trade in assistant_response.trades:
        result = execute_trade(trade.ticker, trade.side, trade.quantity, price_cache, user_id)
        executed_trades.append(result)

    executed_watchlist_changes = []
    for change in assistant_response.watchlist_changes:
        result = await execute_watchlist_change(change.ticker, change.action, request, user_id)
        executed_watchlist_changes.append(result)

    actions_payload = None
    if executed_trades or executed_watchlist_changes:
        actions_payload = {
            "executed_trades": executed_trades,
            "executed_watchlist_changes": executed_watchlist_changes,
        }

    try:
        save_message("user", user_message, None, user_id)
        save_message("assistant", assistant_response.message, actions_payload, user_id)
    except Exception as exc:
        logger.warning("Failed to save chat messages: %s", exc)

    return {
        "message": assistant_response.message,
        "trades": [t.model_dump() for t in assistant_response.trades],
        "watchlist_changes": [w.model_dump() for w in assistant_response.watchlist_changes],
        "executed_trades": executed_trades,
        "executed_watchlist_changes": executed_watchlist_changes,
    }
