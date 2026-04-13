"""Background tasks for FinAlly backend."""

import asyncio
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


async def portfolio_snapshot_task(app_state) -> None:
    """Record portfolio snapshot every 30s; purge old snapshots every hour."""
    from app.db.queries import (
        delete_old_snapshots,
        get_positions,
        get_user_profile,
        record_snapshot,
    )

    last_cleanup = datetime.now(timezone.utc)

    while True:
        try:
            await asyncio.sleep(30)

            profile = get_user_profile()
            positions = get_positions()
            total_value = profile["cash_balance"]

            price_cache = getattr(app_state, "price_cache", None)
            for pos in positions:
                price_update = price_cache.get(pos["ticker"]) if price_cache else None
                if price_update:
                    total_value += pos["quantity"] * price_update.price
                else:
                    total_value += pos["quantity"] * pos["avg_cost"]

            record_snapshot(total_value)

            now = datetime.now(timezone.utc)
            if (now - last_cleanup).total_seconds() >= 3600:
                delete_old_snapshots(days=7)
                last_cleanup = now

        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.warning("Portfolio snapshot error: %s", exc)
