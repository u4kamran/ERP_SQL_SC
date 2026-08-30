"""Public customer catalog + cart validation API."""

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.database.business_session import get_business_db
from app.schemas.public_catalog import (
    CartValidateRequest,
    CartValidateResponse,
    PublicCatalogPage,
    PublicCategoryPage,
    PublicProduct,
)
from app.schemas.guest_price_lookup import GuestPriceSearchResponse
from app.services.public_catalog_service import PublicCatalogService
from app.services.item_price_search_service import ItemPriceSearchService
from app.services.item_search_rate_limit import check_search_rate

router = APIRouter()


@router.get("/categories", response_model=PublicCategoryPage)
def list_catalog_categories(
    parent_id: int | None = Query(None, ge=1),
    db: Session = Depends(get_business_db),
):
    """ERP FIN_CAT groups. Omit parent_id for shop-by-category (level 1)."""
    return PublicCatalogService(db).list_categories(parent_id=parent_id)


@router.get("/items", response_model=PublicCatalogPage)
def list_catalog_items(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=40),
    promo_only: bool = Query(False),
    q: str | None = Query(None, max_length=120),
    category_id: int | None = Query(None, ge=1),
    db: Session = Depends(get_business_db),
):
    """Paginated public product list for the customer shopping app."""
    return PublicCatalogService(db).list_products(
        page=page,
        page_size=page_size,
        promo_only=promo_only,
        q=q,
        category_id=category_id,
    )


@router.get("/search", response_model=GuestPriceSearchResponse)
def catalog_search_items(
    request: Request,
    q: str = Query(..., min_length=1, max_length=120),
    limit: int = Query(10, ge=1, le=20),
    db: Session = Depends(get_business_db),
):
    """Live autocomplete search over FIN_ITEM (ranked, public-safe fields)."""
    check_search_rate(request)
    return ItemPriceSearchService(db).autocomplete(q, limit=limit, channel="mobile")


@router.get("/items/{manual_id}", response_model=PublicProduct)
def get_catalog_item(manual_id: int, db: Session = Depends(get_business_db)):
    """Single product for product-detail screen (safe fields only)."""
    return PublicCatalogService(db).lookup_manual_id(manual_id)


@router.post("/cart/validate", response_model=CartValidateResponse)
def validate_cart(payload: CartValidateRequest, db: Session = Depends(get_business_db)):
    """Re-price and stock-check cart lines. Server is authoritative."""
    return PublicCatalogService(db).validate_cart(payload)
