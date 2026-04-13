"""Mock LLM responses for testing (LLM_MOCK=true)."""

import re

from .schemas import AssistantResponse, TradeAction, WatchlistChange


def get_mock_response(user_message: str) -> AssistantResponse:
    """Return a deterministic mock response based on message content.

    Deterministic rules (checked in order):
    - Contains "buy"  → buy 10 shares of AAPL (or extracted ticker)
    - Contains "sell" → sell 5 shares of AAPL (or extracted ticker)
    - Contains "add"  → add extracted ticker to watchlist (default TSLA)
    - Otherwise       → generic portfolio analysis message
    """
    msg_lower = user_message.lower()

    # Try to extract a ticker symbol (2-5 uppercase letters) from the message
    ticker_match = re.search(r"\b([A-Z]{2,5})\b", user_message)
    ticker = ticker_match.group(1) if ticker_match else "AAPL"

    if "buy" in msg_lower:
        return AssistantResponse(
            message=f"Executing a buy order for 10 shares of {ticker} at the current market price.",
            trades=[TradeAction(ticker=ticker, side="buy", quantity=10)],
            watchlist_changes=[],
        )

    if "sell" in msg_lower:
        return AssistantResponse(
            message=f"Executing a sell order for 5 shares of {ticker} at the current market price.",
            trades=[TradeAction(ticker=ticker, side="sell", quantity=5)],
            watchlist_changes=[],
        )

    if "add" in msg_lower:
        add_ticker = ticker if ticker_match else "TSLA"
        return AssistantResponse(
            message=f"Adding {add_ticker} to your watchlist.",
            trades=[],
            watchlist_changes=[WatchlistChange(ticker=add_ticker, action="add")],
        )

    # Generic portfolio analysis response
    return AssistantResponse(
        message=(
            "Here's a summary of your portfolio: your positions are performing within "
            "normal ranges. Your cash balance is available for new positions. "
            "Let me know if you'd like to buy, sell, or analyze specific holdings."
        ),
        trades=[],
        watchlist_changes=[],
    )
