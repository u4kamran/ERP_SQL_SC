"""Lightweight per-IP rate limit for public item search."""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status

_LOCK = threading.Lock()
_HITS: dict[str, deque[float]] = defaultdict(deque)
_WINDOW = 60.0
_MAX = 45


def check_search_rate(request: Request) -> None:
    ip = "unknown"
    if request.client and request.client.host:
        ip = request.client.host
    forwarded = request.headers.get("x-forwarded-for") or ""
    if forwarded:
        ip = forwarded.split(",")[0].strip()[:64]
    now = time.monotonic()
    with _LOCK:
        bucket = _HITS[ip]
        while bucket and now - bucket[0] > _WINDOW:
            bucket.popleft()
        if len(bucket) >= _MAX:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many searches. Please wait a moment.",
            )
        bucket.append(now)
