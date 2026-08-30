"""Stub providers for PK retailers — disabled until configured / integrated."""

from __future__ import annotations

from app.services.item_images.providers.base import IProductImageProvider, ItemSearchContext, ProductCandidate


class _DisabledPkProvider(IProductImageProvider):
    def search(self, ctx: ItemSearchContext, *, timeout: float = 15.0) -> list[ProductCandidate]:
        return []


class CarrefourProvider(_DisabledPkProvider):
    name = "carrefour"
    display_name = "Carrefour Pakistan"
    priority = 30
    enabled = False


class ImtiazProvider(_DisabledPkProvider):
    name = "imtiaz"
    display_name = "Imtiaz"
    priority = 40
    enabled = False


class AlFatahProvider(_DisabledPkProvider):
    name = "alfatah"
    display_name = "Al-Fatah"
    priority = 50
    enabled = False
