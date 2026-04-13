"""Main FastAPI application for FinAlly."""

import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

from app.db import init_db
from app.db.queries import get_positions, get_watchlist
from app.market import PriceCache, create_market_data_source
from app.llm import chat_router
from app.routes.health import router as health_router
from app.routes.portfolio import router as portfolio_router
from app.routes.watchlist import router as watchlist_router
from app.background import portfolio_snapshot_task

logger = logging.getLogger(__name__)

stream_router = APIRouter(prefix="/api/stream", tags=["streaming"])


@stream_router.get("/prices")
async def stream_prices(request: Request) -> StreamingResponse:
    """SSE endpoint that reads price_cache from app.state at request time."""
    price_cache = getattr(request.app.state, "price_cache", None)

    async def generate():
        yield "retry: 1000\n\n"
        last_version = -1
        client_ip = request.client.host if request.client else "unknown"
        logger.info("SSE client connected: %s", client_ip)
        try:
            while True:
                if await request.is_disconnected():
                    logger.info("SSE client disconnected: %s", client_ip)
                    break
                if price_cache is not None:
                    current_version = price_cache.version
                    if current_version != last_version:
                        last_version = current_version
                        prices = price_cache.get_all()
                        if prices:
                            data = {t: u.to_dict() for t, u in prices.items()}
                            payload = json.dumps(data)
                            yield f"data: {payload}\n\n"
                await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            logger.info("SSE stream cancelled for: %s", client_ip)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("Database initialized")

    price_cache = PriceCache()

    watchlist_tickers = {row["ticker"] for row in get_watchlist()}
    position_tickers = {pos["ticker"] for pos in get_positions() if pos["quantity"] > 0}
    initial_tickers = list(watchlist_tickers | position_tickers)

    market_data_source = create_market_data_source(price_cache)
    await market_data_source.start(initial_tickers)
    logger.info("Market data source started with %d tickers", len(initial_tickers))

    app.state.price_cache = price_cache
    app.state.market_data_source = market_data_source

    snapshot_task = asyncio.create_task(portfolio_snapshot_task(app.state))

    yield

    snapshot_task.cancel()
    try:
        await snapshot_task
    except asyncio.CancelledError:
        pass

    await market_data_source.stop()
    logger.info("Shutdown complete")


app = FastAPI(title="FinAlly API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stream_router)
app.include_router(health_router)
app.include_router(portfolio_router)
app.include_router(watchlist_router)
app.include_router(chat_router)

STATIC_DIR = os.environ.get("STATIC_DIR", "/app/static")
static_path = Path(STATIC_DIR)
if static_path.exists():
    app.mount("/", StaticFiles(directory=str(static_path), html=True), name="static")
else:
    logger.warning("Static directory not found at %s", STATIC_DIR)
