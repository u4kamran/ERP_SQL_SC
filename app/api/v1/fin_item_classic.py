"""VB6-style Fin_Item API (separate from /fin-items)."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, require_permission
from app.database.business_session import get_business_db
from app.schemas import MessageResponse
from app.schemas.fin_item_classic import (
    FinItemClassicDefaults,
    FinItemClassicDetail,
    FinItemClassicHistory,
    FinItemClassicLookup,
    FinItemClassicSave,
    FinItemClassicSaveResponse,
    FinItemClassicStats,
)
from app.services.fin_item_classic_service import FinItemClassicService

router = APIRouter()


@router.get("/stats", response_model=FinItemClassicStats)
def classic_stats(
    current_user: CurrentUser = Depends(require_permission("inventory.fin_item.view")),
    db: Session = Depends(get_business_db),
):
    return FinItemClassicService(db).get_stats()


@router.get("/defaults", response_model=FinItemClassicDefaults)
def classic_defaults(
    current_user: CurrentUser = Depends(require_permission("inventory.fin_item.create")),
    db: Session = Depends(get_business_db),
):
    return FinItemClassicService(db).get_defaults()


@router.get("/search", response_model=list[FinItemClassicLookup])
def classic_search(
    q: str = Query(..., min_length=1),
    current_user: CurrentUser = Depends(require_permission("inventory.fin_item.view")),
    db: Session = Depends(get_business_db),
):
    return FinItemClassicService(db).search_items(q)


@router.get("/by-item-id/{item_id}", response_model=FinItemClassicDetail)
def classic_by_item_id(
    item_id: float,
    history_limit: Optional[int] = Query(default=0, ge=0, le=50),
    current_user: CurrentUser = Depends(require_permission("inventory.fin_item.view")),
    db: Session = Depends(get_business_db),
):
    return FinItemClassicService(db).load_item_id(item_id, history_limit if history_limit is not None else 0)


@router.get("/by-manual-id/{manual_id}", response_model=FinItemClassicDetail)
def classic_by_manual_id(
    manual_id: int,
    history_limit: Optional[int] = Query(default=0, ge=0, le=50),
    current_user: CurrentUser = Depends(require_permission("inventory.fin_item.view")),
    db: Session = Depends(get_business_db),
):
    return FinItemClassicService(db).load_manual_id(manual_id, history_limit if history_limit is not None else 0)


@router.get("/by-barcode/{barcode}", response_model=FinItemClassicDetail)
def classic_by_barcode(
    barcode: str,
    history_limit: Optional[int] = Query(default=0, ge=0, le=50),
    current_user: CurrentUser = Depends(require_permission("inventory.fin_item.view")),
    db: Session = Depends(get_business_db),
):
    return FinItemClassicService(db).load_barcode(barcode, history_limit if history_limit is not None else 0)


@router.get("/by-ws-barcode/{barcode}", response_model=FinItemClassicDetail)
def classic_by_ws_barcode(
    barcode: str,
    history_limit: Optional[int] = Query(default=0, ge=0, le=50),
    current_user: CurrentUser = Depends(require_permission("inventory.fin_item.view")),
    db: Session = Depends(get_business_db),
):
    return FinItemClassicService(db).load_ws_barcode(barcode, history_limit if history_limit is not None else 0)


@router.get("/history/{item_id}", response_model=FinItemClassicHistory)
def classic_history(
    item_id: float,
    limit: Optional[int] = Query(default=5, ge=0, le=50),
    current_user: CurrentUser = Depends(require_permission("inventory.fin_item.view")),
    db: Session = Depends(get_business_db),
):
    rows = 5 if limit is None or limit <= 0 else limit
    return FinItemClassicService(db).get_history(item_id, rows)


@router.get("/lookup/{kind}/{lookup_id}", response_model=FinItemClassicLookup)
def classic_lookup(
    kind: str,
    lookup_id: int,
    current_user: CurrentUser = Depends(require_permission("inventory.fin_item.view")),
    db: Session = Depends(get_business_db),
):
    return FinItemClassicService(db).lookup(kind, lookup_id)


@router.post("/save", response_model=FinItemClassicSaveResponse)
def classic_save(
    data: FinItemClassicSave,
    current_user: CurrentUser = Depends(require_permission("inventory.fin_item.view")),
    db: Session = Depends(get_business_db),
):
    from fastapi import HTTPException

    service = FinItemClassicService(db)
    existing = service.repo.get_fin_item_row(data.item_id)
    if existing:
        if not current_user.has_permission("inventory.fin_item.update"):
            raise HTTPException(status_code=403, detail="Update permission required.")
    elif not current_user.has_permission("inventory.fin_item.create"):
        raise HTTPException(status_code=403, detail="Create permission required.")
    return service.save(data)


@router.delete("/{item_id}", response_model=MessageResponse)
def classic_delete(
    item_id: float,
    current_user: CurrentUser = Depends(require_permission("inventory.fin_item.delete")),
    db: Session = Depends(get_business_db),
):
    FinItemClassicService(db).delete(item_id)
    return MessageResponse(message="Item deleted successfully.")
