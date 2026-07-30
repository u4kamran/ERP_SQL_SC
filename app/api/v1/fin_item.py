"""FIN_ITEM CRUD API endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, require_permission
from app.database.business_session import get_business_db
from app.schemas import MessageResponse
from app.schemas.fin_item import FinItemCreate, FinItemListResponse, FinItemResponse, FinItemUpdate
from app.services.fin_item_service import FinItemService

router = APIRouter()


@router.get("/", response_model=FinItemListResponse)
def list_fin_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    search: Optional[str] = Query(None, max_length=100),
    current_user: CurrentUser = Depends(require_permission("inventory.fin_item.view")),
    db: Session = Depends(get_business_db),
):
    return FinItemService(db).list_items(skip, limit, search)


@router.get("/{item_id}", response_model=FinItemResponse)
def get_fin_item(
    item_id: float,
    current_user: CurrentUser = Depends(require_permission("inventory.fin_item.view")),
    db: Session = Depends(get_business_db),
):
    return FinItemService(db).get_item(item_id)


@router.post("/", response_model=FinItemResponse, status_code=201)
def create_fin_item(
    data: FinItemCreate,
    current_user: CurrentUser = Depends(require_permission("inventory.fin_item.create")),
    db: Session = Depends(get_business_db),
):
    return FinItemService(db).create_item(data)


@router.put("/{item_id}", response_model=FinItemResponse)
def update_fin_item(
    item_id: float,
    data: FinItemUpdate,
    current_user: CurrentUser = Depends(require_permission("inventory.fin_item.update")),
    db: Session = Depends(get_business_db),
):
    return FinItemService(db).update_item(item_id, data)


@router.delete("/{item_id}", response_model=MessageResponse)
def delete_fin_item(
    item_id: float,
    current_user: CurrentUser = Depends(require_permission("inventory.fin_item.delete")),
    db: Session = Depends(get_business_db),
):
    FinItemService(db).delete_item(item_id)
    return MessageResponse(message="Item deleted successfully.")
