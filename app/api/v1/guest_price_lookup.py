"""Public guest price lookup API — no login required."""

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.database.business_session import get_business_db
from app.schemas.guest_price_lookup import (
    GuestPriceLookupResponse,
    GuestPriceSearchResponse,
)
from app.services.guest_price_lookup_service import GuestPriceLookupService
from app.services.item_price_search_service import ItemPriceSearchService
from app.services.item_search_rate_limit import check_search_rate
from app.services import item_search_control_store as search_settings

router = APIRouter()


@router.get("/by-barcode/{barcode}", response_model=GuestPriceLookupResponse)
def guest_lookup_barcode(barcode: str, db: Session = Depends(get_business_db)):
    """Look up item price by retail barcode (public, read-only)."""
    return GuestPriceLookupService(db).lookup_any(barcode)


@router.get("/by-manual-id/{manual_id}", response_model=GuestPriceLookupResponse)
def guest_lookup_manual_id(manual_id: int, db: Session = Depends(get_business_db)):
    """Look up item price by manual ID (public, read-only)."""
    return GuestPriceLookupService(db).lookup_manual_id(manual_id)


@router.get("/search", response_model=GuestPriceSearchResponse)
def guest_search_items(
    request: Request,
    q: str = Query(..., min_length=1, max_length=120),
    limit: int = Query(10, ge=1, le=20),
    db: Session = Depends(get_business_db),
):
    """Advanced public item search with ranking and disambiguation."""
    check_search_rate(request)
    return ItemPriceSearchService(db).autocomplete(q, limit=limit, channel="web")


@router.get("/search-config")
def guest_search_config():
    cfg = search_settings.get_settings()
    return {
        "min_chars": cfg["min_chars"],
        "max_results": cfg["max_results"],
        "debounce_ms": cfg["debounce_ms"],
    }
