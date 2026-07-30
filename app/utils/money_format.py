"""Money and amount formatting."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


def format_amount(
    value: float | int | str | Decimal | None,
    *,
    decimals: int = 2,
    blank_if_zero: bool = False,
) -> str:
    """Format as 999,999,999.00"""
    if value is None or value == "":
        return ""

    try:
        number = Decimal(str(value).replace(",", "").strip())
    except (InvalidOperation, ValueError):
        return str(value)

    if blank_if_zero and number.copy_abs() < Decimal("0.0005"):
        return ""

    quantize_exp = Decimal("1").scaleb(-decimals)
    number = number.quantize(quantize_exp, rounding=ROUND_HALF_UP)
    text = f"{number:,.{decimals}f}"
    return text


# Sales SMS lines: "Total Sales: 123", "nasir : 123.45"
_LABELED_AMOUNT_RE = re.compile(
    r"(Total Sales\s*:\s*)(\d+(?:\.\d+)?)",
    re.IGNORECASE,
)
_PERSON_AMOUNT_RE = re.compile(
    r"([A-Za-z][A-Za-z ]*\s*:\s*)(\d+\.\d+)",
)


def format_amounts_in_text(text: str) -> str:
    """Add thousand separators to sales amounts inside SMS body text."""

    if not text:
        return text

    def repl(match: re.Match[str]) -> str:
        return match.group(1) + format_amount(match.group(2))

    out = _LABELED_AMOUNT_RE.sub(repl, text)
    out = _PERSON_AMOUNT_RE.sub(repl, out)
    return out
