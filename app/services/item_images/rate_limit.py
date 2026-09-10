"""Simple provider rate limiter (requests per minute + concurrency)."""

from __future__ import annotations

import threading
import time
from collections import deque


class ProviderRateLimiter:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._hits: deque[float] = deque()
        self._inflight = 0

    def acquire(self, *, requests_per_minute: int = 20, max_concurrent: int = 2) -> None:
        rpm = max(1, int(requests_per_minute))
        conc = max(1, int(max_concurrent))
        while True:
            with self._lock:
                now = time.monotonic()
                while self._hits and now - self._hits[0] > 60.0:
                    self._hits.popleft()
                if len(self._hits) < rpm and self._inflight < conc:
                    self._hits.append(now)
                    self._inflight += 1
                    return
                wait = 0.25
                if self._hits:
                    wait = max(0.1, 60.0 - (now - self._hits[0]))
            time.sleep(min(wait, 2.0))

    def release(self) -> None:
        with self._lock:
            self._inflight = max(0, self._inflight - 1)


RATE_LIMITER = ProviderRateLimiter()
