"""Public customer catalog + cart validation API."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.business_session import get_business_db
from app.schemas.public_catalog import (
    CartValidateRequest,
    CartValidateResponse,
    PublicCatalogPage,
    PublicProduct,
)
from app.services.public_catalog_service import PublicCatalogService

router = APIRouter()


@router.get("/items", response_model=PublicCatalogPage)
def list_catalog_items(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=40),
    promo_only: bool = Query(False),
    q: str | None = Query(None, max_length=120),
    db: Session = Depends(get_business_db),
):
    """Paginated public product list for the customer shopping app."""
    return PublicCatalogService(db).list_products(
        page=page,
        page_size=page_size,
        promo_only=promo_only,
        q=q,
    )


@router.get("/items/{manual_id}", response_model=PublicProduct)
def get_catalog_item(manual_id: int, db: Session = Depends(get_business_db)):
    """Single product for product-detail screen (safe fields only)."""
    return PublicCatalogService(db).lookup_manual_id(manual_id)


@router.post("/cart/validate", response_model=CartValidateResponse)
def validate_cart(payload: CartValidateRequest, db: Session = Depends(get_business_db)):
    """Re-price and stock-check cart lines. Server is authoritative."""
    return PublicCatalogService(db).validate_cart(payload)
