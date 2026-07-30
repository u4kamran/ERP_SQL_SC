"""Short-lived tokens for mobile PDF viewing (no auth header needed in browser)."""

from __future__ import annotations

import secrets
import threading
from datetime import datetime, timedelta
from typing import Optional, Tuple

_LOCK = threading.Lock()
_TOKENS: dict[str, tuple[bytes, str, datetime]] = {}


def store_pdf(pdf_bytes: bytes, filename: str, *, ttl_minutes: int = 15) -> str:
    token = secrets.token_urlsafe(32)
    expires = datetime.now() + timedelta(minutes=ttl_minutes)
    with _LOCK:
        _purge_expired_unlocked()
        _TOKENS[token] = (pdf_bytes, filename, expires)
    return token


def get_pdf(token: str) -> Optional[Tuple[bytes, str]]:
    with _LOCK:
        _purge_expired_unlocked()
        entry = _TOKENS.get(token)
        if not entry:
            return None
        pdf_bytes, filename, expires = entry
        if datetime.now() >= expires:
            _TOKENS.pop(token, None)
            return None
        return pdf_bytes, filename


def _purge_expired_unlocked() -> None:
    now = datetime.now()
    expired = [key for key, (_, _, exp) in _TOKENS.items() if now >= exp]
    for key in expired:
        _TOKENS.pop(key, None)
