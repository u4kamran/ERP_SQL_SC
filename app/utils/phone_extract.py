"""Extract Pakistan mobile numbers from legacy free-text fields."""

from __future__ import annotations

import re

from app.services.whatsapp_service import normalize_pk_phone

_JUNK = {"", "nil", "0", "1", "none", "na", "n/a", "+", "+92", "."}
# Match PK mobiles inside free text, e.g. +92-303-4488923, 0303-4886451
_MOBILE_PATTERN = re.compile(r"(?:\+?92[-\s]?|0)?3\d{2}[-\s]?\d{7}")


def extract_pk_mobiles(*texts: str) -> list[str]:
    """Return unique normalized numbers (92XXXXXXXXXX) from messy text."""
    seen: set[str] = set()
    results: list[str] = []

    def add_candidate(chunk: str) -> None:
        chunk = chunk.strip()
        if not chunk or chunk.lower() in _JUNK:
            return
        normalized = normalize_pk_phone(chunk)
        if normalized and normalized not in seen:
            seen.add(normalized)
            results.append(normalized)

    for text in texts:
        if text is None:
            continue
        raw = str(text).strip()
        if raw.lower() in _JUNK:
            continue

        for match in _MOBILE_PATTERN.finditer(raw):
            add_candidate(match.group())

        for chunk in re.split(r"[/|,;\s]+", raw):
            add_candidate(chunk)

    return results


def pk_phone_for_input(normalized: str) -> str:
    """Convert 92XXXXXXXXXX to local digits for +92 input field."""
    digits = re.sub(r"\D", "", normalized or "")
    if digits.startswith("92") and len(digits) >= 12:
        return digits[2:]
    if digits.startswith("0"):
        return digits[1:]
    return digits


def format_pk_phone_display(normalized: str) -> str:
    """Human-friendly display for search results."""
    digits = re.sub(r"\D", "", normalized or "")
    if digits.startswith("92") and len(digits) == 12:
        return f"0{digits[2:]}"
    if digits.startswith("0"):
        return digits
    return f"+{digits}" if digits else ""
