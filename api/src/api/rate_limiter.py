"""
In-memory sliding-window rate limiter for AI generation budget.

Budget: 3.0 tokens per household per 10-minute window.
Costs:  full suggest / refine / regenerate-all = 1.0
        single-slot regenerate = 0.5
"""
import asyncio
import time
from datetime import datetime, timezone
from typing import Optional

BUDGET = 3.0
WINDOW_SECONDS = 600  # 10 minutes


class RateLimiter:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        # household_id (str) -> list of (timestamp: float, cost: float)
        self._events: dict[str, list[tuple[float, float]]] = {}

    async def check_and_consume(
        self, household_id: str, cost: float
    ) -> tuple[bool, float, Optional[datetime]]:
        """
        Check budget and consume `cost` tokens if sufficient.

        Returns:
            (allowed, remaining_after_consume, resets_at)
            - allowed: False means over budget; remaining and resets_at reflect current state
            - resets_at: datetime when the oldest event expires (None when allowed=True)
        """
        async with self._lock:
            now = time.time()
            cutoff = now - WINDOW_SECONDS
            events = self._events.get(household_id, [])

            # Drop expired events
            events = [(ts, c) for ts, c in events if ts > cutoff]

            used = sum(c for _, c in events)
            remaining = BUDGET - used

            if remaining < cost:
                resets_at: Optional[datetime] = None
                if events:
                    oldest_ts = min(ts for ts, _ in events)
                    resets_at = datetime.fromtimestamp(
                        oldest_ts + WINDOW_SECONDS, tz=timezone.utc
                    )
                self._events[household_id] = events
                return False, remaining, resets_at

            events.append((now, cost))
            self._events[household_id] = events
            return True, remaining - cost, None
