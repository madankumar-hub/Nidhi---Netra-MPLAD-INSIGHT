"""In-process rate limiting for the endpoints worth protecting.

Why this is hand-rolled
-----------------------
The obvious dependency (`slowapi`) pulls in `limits` and, for anything shared,
Redis. This deployment is a single uvicorn process backed by one database, so
an in-process sliding-window counter is both sufficient and honest about what it
is. It is deliberately NOT presented as a distributed rate limiter: if the API
is ever run with multiple workers, each worker keeps its own counters and the
effective limit multiplies by the worker count. `docs/SECURITY.md` says so, and
the fix at that point is a shared store, not a bigger in-memory dict.

What it protects
----------------
Credential endpoints, where the threat is online guessing and OTP-mailbox
abuse, and the citizen report endpoint, where the threat is spam. Read-only
public endpoints are not limited: throttling citizens browsing a transparency
portal is the wrong trade.

This module is deliberately framework-free so it can be unit-tested without a
web framework installed. The FastAPI dependency that uses it lives next door in
`rate_limit_deps.py`; keeping them apart is what stops a type annotation here
from being invisible to FastAPI at runtime.
"""
from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any, Deque, Dict


@dataclass(frozen=True)
class RateLimit:
    """`max_requests` permitted within any `window_seconds` sliding window."""

    max_requests: int
    window_seconds: int

    @property
    def description(self) -> str:
        return f"{self.max_requests} requests per {self.window_seconds}s"


#: Tuned to stop scripted abuse while never interrupting a real person.
#: Signing in eight times in a minute is a forgotten password; eighty is a script.
LOGIN_LIMIT = RateLimit(max_requests=8, window_seconds=60)
OTP_REQUEST_LIMIT = RateLimit(max_requests=4, window_seconds=300)
SIGNUP_LIMIT = RateLimit(max_requests=5, window_seconds=600)
REPORT_LIMIT = RateLimit(max_requests=6, window_seconds=300)
ACCESS_REQUEST_LIMIT = RateLimit(max_requests=3, window_seconds=3600)


class SlidingWindowLimiter:
    """Thread-safe sliding-window counter keyed by caller identity."""

    def __init__(self) -> None:
        self._hits: Dict[str, Deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str, limit: RateLimit) -> tuple[bool, int]:
        """Record a hit. Returns (allowed, seconds_until_retry)."""
        now = time.monotonic()
        cutoff = now - limit.window_seconds

        with self._lock:
            hits = self._hits[key]
            while hits and hits[0] <= cutoff:
                hits.popleft()

            if len(hits) >= limit.max_requests:
                retry_after = int(hits[0] + limit.window_seconds - now) + 1
                return False, max(retry_after, 1)

            hits.append(now)

            # Opportunistic cleanup so a long-running process does not grow a
            # dictionary entry for every caller it has ever seen.
            if len(self._hits) > 4096:
                self._evict_idle(cutoff)

            return True, 0

    def _evict_idle(self, cutoff: float) -> None:
        """Drop keys whose most recent hit has fallen out of every window."""
        stale = [key for key, hits in self._hits.items() if not hits or hits[-1] <= cutoff]
        for key in stale:
            del self._hits[key]

    def reset(self) -> None:
        """Clear all counters. Used by the tests."""
        with self._lock:
            self._hits.clear()


limiter = SlidingWindowLimiter()


def client_identity(request: Any) -> str:
    """Best-effort caller identity.

    Behind a proxy the socket address is the proxy, so the first entry of
    X-Forwarded-For is preferred. That header is client-controlled and is only
    trusted here because the alternative - limiting every caller behind a proxy
    as one - is worse. It is never used for authorisation.
    """
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        first = forwarded.split(",")[0].strip()
        if first:
            return first
    client = request.client
    return client.host if client else "unknown"


def check(request: Any, limit: RateLimit, scope: str) -> tuple[bool, int]:
    """Decide whether this caller may proceed.

    Returns (allowed, retry_after_seconds). Raising the HTTP error is the
    caller's job - see `rate_limit_deps.rate_limit`.
    """
    key = f"{scope}:{client_identity(request)}"
    return limiter.check(key, limit)
