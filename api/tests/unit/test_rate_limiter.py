"""Unit tests for the in-memory rate limiter."""
import asyncio
import time
from unittest.mock import patch

import pytest

from api.rate_limiter import BUDGET, WINDOW_SECONDS, RateLimiter


class TestRateLimiter:
    async def test_first_request_is_allowed(self):
        rl = RateLimiter()
        allowed, remaining, resets_at = await rl.check_and_consume("hh-1", cost=1.0)

        assert allowed is True
        assert remaining == pytest.approx(BUDGET - 1.0)
        assert resets_at is None

    async def test_remaining_decrements_with_each_call(self):
        rl = RateLimiter()
        await rl.check_and_consume("hh-1", cost=1.0)
        _, remaining, _ = await rl.check_and_consume("hh-1", cost=1.0)

        assert remaining == pytest.approx(BUDGET - 2.0)

    async def test_budget_exhausted_returns_false(self):
        rl = RateLimiter()
        await rl.check_and_consume("hh-1", cost=1.0)
        await rl.check_and_consume("hh-1", cost=1.0)
        await rl.check_and_consume("hh-1", cost=1.0)  # uses 3.0 total

        allowed, remaining, resets_at = await rl.check_and_consume("hh-1", cost=0.5)

        assert allowed is False
        assert remaining == pytest.approx(0.0)
        assert resets_at is not None

    async def test_partial_cost_works(self):
        rl = RateLimiter()
        # 6 half-token calls should exhaust the 3.0 budget
        for _ in range(6):
            await rl.check_and_consume("hh-1", cost=0.5)

        allowed, _, _ = await rl.check_and_consume("hh-1", cost=0.5)
        assert allowed is False

    async def test_different_households_have_separate_budgets(self):
        rl = RateLimiter()
        await rl.check_and_consume("hh-A", cost=1.0)
        await rl.check_and_consume("hh-A", cost=1.0)
        await rl.check_and_consume("hh-A", cost=1.0)

        # hh-B should still have full budget
        allowed, remaining, _ = await rl.check_and_consume("hh-B", cost=1.0)
        assert allowed is True
        assert remaining == pytest.approx(BUDGET - 1.0)

    async def test_expired_events_are_not_counted(self):
        rl = RateLimiter()

        # Inject an event in the past (beyond the window)
        past = time.time() - WINDOW_SECONDS - 1
        rl._events["hh-1"] = [(past, 3.0)]  # used full budget, but expired

        allowed, remaining, _ = await rl.check_and_consume("hh-1", cost=1.0)

        assert allowed is True
        assert remaining == pytest.approx(BUDGET - 1.0)

    async def test_resets_at_reflects_oldest_event_expiry(self):
        rl = RateLimiter()
        # Manually place an old event (but still within window)
        old_ts = time.time() - 300  # 5 minutes ago
        rl._events["hh-1"] = [(old_ts, 3.0)]  # used all budget

        allowed, _, resets_at = await rl.check_and_consume("hh-1", cost=0.5)

        assert allowed is False
        assert resets_at is not None
        # Should expire ~5 minutes from now (WINDOW_SECONDS - 300 seconds)
        from datetime import datetime, timezone
        seconds_until_reset = (resets_at - datetime.now(timezone.utc)).total_seconds()
        assert 0 < seconds_until_reset <= 300 + 5  # small tolerance

    async def test_concurrent_requests_are_safe(self):
        rl = RateLimiter()

        async def consume():
            return await rl.check_and_consume("hh-concurrent", cost=1.0)

        results = await asyncio.gather(*[consume() for _ in range(5)])
        allowed_count = sum(1 for allowed, _, _ in results if allowed)

        # Only 3 should be allowed (budget = 3.0, cost = 1.0 each)
        assert allowed_count == 3
