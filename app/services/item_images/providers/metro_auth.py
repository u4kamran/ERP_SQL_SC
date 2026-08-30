"""METRO Online auth headers (public storefront contract)."""

from __future__ import annotations

import hashlib
import math
import random
import time

METRO_API_BASE = "https://admin.metro-online.pk"
METRO_ORIGIN = "https://www.metro-online.pk"
METRO_AUTH_SALT = "metroB2CXcen@!"


def metro_auth_headers(method: str, endpoint: str) -> dict[str, str]:
    """Match metro-online.pk frontend getConfigForAuth signing."""
    ts = int(time.time() * 1000)
    raw = f"{method}{endpoint}{math.pi}{ts}{METRO_AUTH_SALT}"
    digest = hashlib.md5(raw.encode()).hexdigest()
    return {
        "Accept": "application/json, text/plain, */*",
        "Origin": METRO_ORIGIN,
        "Referer": f"{METRO_ORIGIN}/home",
        "bdz-playback-state": f"{ts}_{digest}",
        "ares-last-signal-flush": str(random.random()),
    }
