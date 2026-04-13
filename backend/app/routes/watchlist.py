"""Watchlist routes: GET/POST /api/watchlist, DELETE /api/watchlist/{ticker}."""

import logging
import re

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel

from app.db.queries import (
    add_to_watchlist,
    get_position,
    get_watchlist,
    remove_from_watchlist,
)

logger = logging.getLogger(__name__)

router = APIRouter()


class WatchlistAddRequest(BaseModel):
    ticker: str


@router.get("/api/watchlist")
def get_watchlist_route(request: Request):
    """Return watchlist with live prices."""
    user_id = "default"
    price_cache = getattr(request.app.state, "price_cache", None)

    entries = get_watchlist(user_id)
    tickers = []
    for entry in entries:
        ticker = entry["ticker"]
        pu = price_cache.get(ticker) if price_cache else None
        if pu:
            tickers.append({
                "ticker": ticker,
                "price": pu.price,
                "change": pu.change,
                "change_percent": pu.change_percent,
                "direction": pu.direction,
            })
        else:
            tickers.append({
                "ticker": ticker,
                "price": None,
                "change": None,
                "change_percent": None,
                "direction": None,
            })
    return {"tickers": tickers}


@router.post("/api/watchlist", status_code=201)
async def add_watchlist_ticker(body: WatchlistAddRequest, request: Request):
    """Add a ticker to the watchlist."""
    user_id = "default"
    ticker = body.ticker.upper().strip()

    if not re.match(r"^[A-Z]{1,10}$", ticker):
        raise HTTPException(status_code=422, detail="Ticker must be 1-10 uppercase letters only.")

    added = add_to_watchlist(ticker, user_id)
    if not added:
        raise HTTPException(status_code=409, detail=f"{ticker} is already on the watchlist.")

    market_data_source = getattr(request.app.state, "market_data_source", None)
    if market_data_source is not None:
        try:
            await market_data_source.add_ticker(ticker)
        except Exception as exc:
            logger.warning("Failed to add %s to market data source: %s", ticker, exc)

    from app.db.queries import get_watchlist as _get_wl
    entries = _get_wl(user_id)
    entry = next((e for e in entries if e["ticker"] == ticker), None)
    return {"ticker": ticker, "added_at": entry["added_at"] if entry else None}


@router.delete("/api/watchlist/{ticker}", status_code=204)
async def remove_watchlist_ticker(ticker: str, request: Request):
    """Remove a ticker from the watchlist."""
    user_id = "default"
    ticker = ticker.upper().strip()

    removed = remove_from_watchlist(ticker, user_id)
    if not removed:
        raise HTTPException(status_code=404, detail=f"{ticker} not found on watchlist.")

    position = get_position(ticker, user_id)
    has_position = position is not None and position.get("quantity", 0) > 0

    if not has_position:
        market_data_source = getattr(request.app.state, "market_data_source", None)
        if market_data_source is not None:
            try:
                await market_data_source.remove_ticker(ticker)
            except Exception as exc:
                logger.warning("Failed to remove %s from market data source: %s", ticker, exc)

    return Response(status_code=204)
