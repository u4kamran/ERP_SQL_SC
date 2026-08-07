"""Public guest price lookup API — no login required."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.business_session import get_business_db
from app.schemas.guest_price_lookup import (
    GuestPriceLookupResponse,
    GuestPriceSearchResponse,
)
from app.services.guest_price_lookup_service import GuestPriceLookupService
from app.services.item_price_search_service import ItemPriceSearchService

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
    q: str = Query(..., min_length=1, max_length=120),
    limit: int = Query(8, ge=1, le=20),
    db: Session = Depends(get_business_db),
):
    """Advanced public item search with ranking and disambiguation."""
    return ItemPriceSearchService(db).search(q, limit=limit)
