"""Item image module settings helpers and project paths."""

from __future__ import annotations

from pathlib import Path

from app.config.settings import settings

# app/services/item_images/__init__.py -> repo root is 4 levels up
PROJECT_ROOT = Path(__file__).resolve().parents[3]
PRODUCT_IMAGES_DIR = PROJECT_ROOT / "data" / "ProductImages"

STATUSES = (
    "NO_IMAGE",
    "SEARCHING",
    "IMAGE_FOUND",
    "NEEDS_REVIEW",
    "APPROVED",
    "FAILED",
)

IMAGE_STATUSES = (
    "IMAGE_FOUND",
    "NEEDS_REVIEW",
    "APPROVED",
    "REJECTED",
    "FAILED",
    "MANUAL",
)

DEFAULT_SETTINGS = {
    "auto_accept_min": 90,
    "review_min": 75,
    "no_match_min": 30,
    "requests_per_minute": 12,
    "max_concurrent": 1,
    "timeout_seconds": 15,
    "retry_count": 2,
    "min_width": 80,
    "min_height": 80,
    "download_enabled": True,
    "naheed_enabled": True,
    "metro_enabled": True,
    "carrefour_enabled": False,
    "imtiaz_enabled": False,
    "alfatah_enabled": False,
    "open_food_facts_enabled": False,
    "upcitemdb_enabled": False,
}


def ensure_product_images_dir() -> Path:
    PRODUCT_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    return PRODUCT_IMAGES_DIR


def item_image_dir(item_id: float) -> Path:
    # Use integer-like folder when ITEM_ID is whole; else sanitized float string.
    if float(item_id).is_integer():
        folder = str(int(item_id))
    else:
        folder = str(item_id).replace(".", "_")
    path = ensure_product_images_dir() / folder
    path.mkdir(parents=True, exist_ok=True)
    return path


def public_image_url(relative_path: str | None) -> str | None:
    if not relative_path:
        return None
    rel = relative_path.replace("\\", "/").lstrip("/")
    if rel.startswith("data/ProductImages/"):
        rel = rel[len("data/") :]
    elif rel.startswith("ProductImages/"):
        pass
    else:
        rel = f"ProductImages/{rel}"
    base = settings.base_url.rstrip("/")
    return f"{base}/media/{rel}"
