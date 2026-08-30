"""Provider registry — PK retailers first, optional global fallbacks."""

from __future__ import annotations

from typing import Any

from app.services.item_images.providers.base import IProductImageProvider
from app.services.item_images.providers.naheed import NaheedProvider
from app.services.item_images.providers.open_food_facts import OpenFoodFactsProvider
from app.services.item_images.providers.metro import MetroProvider
from app.services.item_images.providers.pk_stubs import (
    AlFatahProvider,
    CarrefourProvider,
    ImtiazProvider,
)
from app.services.item_images.providers.upcitemdb import UpcItemDbProvider

ALL_PROVIDER_TYPES: list[type[IProductImageProvider]] = [
    NaheedProvider,
    MetroProvider,
    CarrefourProvider,
    ImtiazProvider,
    AlFatahProvider,
    UpcItemDbProvider,
    OpenFoodFactsProvider,
]


def _flag(cfg: dict[str, Any], key: str, default: bool = False) -> bool:
    if key not in cfg or cfg[key] is None:
        return default
    return bool(cfg[key])


def build_providers(cfg: dict[str, Any] | None = None) -> list[IProductImageProvider]:
    cfg = cfg or {}
    providers: list[IProductImageProvider] = []

    naheed = NaheedProvider()
    naheed.enabled = _flag(cfg, "naheed_enabled", True)
    providers.append(naheed)

    metro = MetroProvider()
    metro.enabled = _flag(cfg, "metro_enabled", True)
    providers.append(metro)

    carrefour = CarrefourProvider()
    carrefour.enabled = _flag(cfg, "carrefour_enabled", False)
    providers.append(carrefour)

    imtiaz = ImtiazProvider()
    imtiaz.enabled = _flag(cfg, "imtiaz_enabled", False)
    providers.append(imtiaz)

    alfatah = AlFatahProvider()
    alfatah.enabled = _flag(cfg, "alfatah_enabled", False)
    providers.append(alfatah)

    upc = UpcItemDbProvider()
    upc.enabled = _flag(cfg, "upcitemdb_enabled", False)
    providers.append(upc)

    off = OpenFoodFactsProvider()
    off.enabled = _flag(cfg, "open_food_facts_enabled", False)
    providers.append(off)

    active = [p for p in providers if getattr(p, "enabled", True)]
    active.sort(key=lambda p: getattr(p, "priority", 100))
    return active
