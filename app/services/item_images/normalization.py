"""Search-only title normalization (never writes back to FIN_ITEM)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class PackSize:
    value: float
    unit: str  # g, ml, l, pcs

    def normalized_key(self) -> tuple[str, float]:
        if self.unit == "g":
            return ("mass_g", self.value)
        if self.unit == "ml":
            return ("volume_ml", self.value)
        if self.unit == "l":
            return ("volume_ml", self.value * 1000.0)
        if self.unit == "pcs":
            return ("count", self.value)
        return (self.unit, self.value)


_PACK_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"(\d+(?:\.\d+)?)\s*(?:kg|kilo|kilogram|kilograms)\b", re.I), "g"),
    (re.compile(r"(\d+(?:\.\d+)?)\s*(?:g|gm|gram|grams|gr)\b", re.I), "g"),
    (re.compile(r"(\d+(?:\.\d+)?)\s*(?:ml|milliliter|millilitre|milliliters)\b", re.I), "ml"),
    (re.compile(r"(\d+(?:\.\d+)?)\s*(?:l|ltr|liter|litre|liters|litres)\b", re.I), "l"),
    (re.compile(r"(\d+(?:\.\d+)?)\s*(?:pcs|pc|piece|pieces|pack|pk)\b", re.I), "pcs"),
    (re.compile(r"\bx\s*(\d+)\b", re.I), "pcs"),
]


def normalize_search_text(text: str | None) -> str:
    if not text:
        return ""
    t = text.upper().strip()
    t = re.sub(r"[,/_\-]+", " ", t)
    t = re.sub(
        r"\b(K\.G|K G|KILO|KILOGRAM|KILOGRAMS|GM|GR|GRAM|GRAMS|ML|MILLILITER|MILLILITRE|LTR|LITER|LITRE|PCS|PC|PACK|PK)\b",
        lambda m: {
            "K.G": "KG",
            "K G": "KG",
            "KILO": "KG",
            "KILOGRAM": "KG",
            "KILOGRAMS": "KG",
            "GM": "G",
            "GR": "G",
            "GRAM": "G",
            "GRAMS": "G",
            "ML": "ML",
            "MILLILITER": "ML",
            "MILLILITRE": "ML",
            "LTR": "L",
            "LITER": "L",
            "LITRE": "L",
            "PCS": "PCS",
            "PC": "PCS",
            "PACK": "PCS",
            "PK": "PCS",
        }.get(m.group(0), m.group(0)),
        t,
    )
    return re.sub(r"\s+", " ", t).strip()


def extract_pack_size(text: str | None) -> Optional[PackSize]:
    if not text:
        return None
    t = normalize_search_text(text)
    for pattern, unit in _PACK_PATTERNS:
        m = pattern.search(t)
        if not m:
            continue
        val = float(m.group(1))
        matched = m.group(0).upper()
        if "KG" in matched or "KILO" in matched:
            return PackSize(value=val * 1000.0, unit="g")
        return PackSize(value=val, unit=unit)
    return None


def pack_sizes_compatible(item_title: str | None, candidate_title: str | None) -> tuple[bool, bool]:
    """
    Returns (compatible, both_detected).
    Incompatible when both sides have pack size and they differ materially.
    """
    item_pack = extract_pack_size(item_title)
    cand_pack = extract_pack_size(candidate_title)
    if not item_pack or not cand_pack:
        return True, bool(item_pack and cand_pack)
    a = item_pack.normalized_key()
    b = cand_pack.normalized_key()
    if a[0] != b[0]:
        return False, True
    if a[0] == "mass_g":
        ratio = max(a[1], b[1]) / max(min(a[1], b[1]), 1.0)
        return ratio <= 1.15, True
    if a[0] == "volume_ml":
        ratio = max(a[1], b[1]) / max(min(a[1], b[1]), 1.0)
        return ratio <= 1.15, True
    if a[0] == "count":
        return abs(a[1] - b[1]) <= 0.01, True
    return True, True
