"""Product image provider interface and shared DTOs."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ProductCandidate:
    provider: str
    image_url: str
    product_name: Optional[str] = None
    barcode: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    product_url: Optional[str] = None
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    search_query: str = ""
    search_level: int = 0
    match_score: int = 0
    availability: Optional[str] = None
    extras: dict = field(default_factory=dict)

    def to_legacy(self) -> "ImageCandidate":
        return ImageCandidate(
            image_url=self.image_url,
            source_url=self.product_url,
            source_name=self.provider,
            search_query=self.search_query,
            product_title=self.product_name,
            product_brand=self.brand,
            product_barcode=self.barcode,
            match_score=self.match_score,
            extras={**self.extras, "search_level": self.search_level, "category": self.category},
        )


@dataclass
class ImageCandidate:
    image_url: str
    source_url: Optional[str] = None
    source_name: str = ""
    search_query: str = ""
    product_title: Optional[str] = None
    product_brand: Optional[str] = None
    product_barcode: Optional[str] = None
    match_score: int = 0
    extras: dict = field(default_factory=dict)


@dataclass
class ItemSearchContext:
    item_id: float
    item_title: str
    barcodeid: Optional[str] = None
    brand: Optional[str] = None
    manual_id: Optional[int] = None


@dataclass
class ScoreResult:
    score: int
    hard_reject: bool = False
    reason: str = ""


class IProductImageProvider(ABC):
    """Pluggable Pakistani / global product image provider."""

    name: str = "base"
    display_name: str = "Base"
    enabled: bool = True
    priority: int = 100

    @abstractmethod
    def search(self, ctx: ItemSearchContext, *, timeout: float = 15.0) -> list[ProductCandidate]:
        raise NotImplementedError


# Backward-compatible alias
IImageSearchProvider = IProductImageProvider
