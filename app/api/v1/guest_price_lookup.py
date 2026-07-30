"""Public guest price lookup API — no login required."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.business_session import get_business_db
from app.schemas.guest_price_lookup import GuestPriceLookupResponse
from app.services.guest_price_lookup_service import GuestPriceLookupService

router = APIRouter()


@router.get("/by-barcode/{barcode}", response_model=GuestPriceLookupResponse)
def guest_lookup_barcode(barcode: str, db: Session = Depends(get_business_db)):
    """Look up item price by retail barcode (public, read-only)."""
    return GuestPriceLookupService(db).lookup_any(barcode)


@router.get("/by-manual-id/{manual_id}", response_model=GuestPriceLookupResponse)
def guest_lookup_manual_id(manual_id: int, db: Session = Depends(get_business_db)):
    """Look up item price by manual ID (public, read-only)."""
    return GuestPriceLookupService(db).lookup_manual_id(manual_id)
