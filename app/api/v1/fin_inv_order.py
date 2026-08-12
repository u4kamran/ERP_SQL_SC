"""Purchase Order API — VB6 Fin_InvM_Order parity."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, require_permission
from app.config.settings import settings
from app.database.business_session import get_business_db
from app.database.session import get_db
from app.models.user import UserPreference
from app.schemas.fin_inv_order import (
    FinInvOrderAddSupplierItemRequest,
    FinInvOrderAddSupplierItemResponse,
    FinInvOrderConfigOut,
    FinInvOrderDeleteResponse,
    FinInvOrderDocumentOut,
    FinInvOrderHistoryRow,
    FinInvOrderItemOut,
    FinInvOrderLookupRow,
    FinInvOrderPoHistoryRow,
    FinInvOrderPrintOut,
    FinInvOrderPrintRow,
    FinInvOrderSaveRequest,
    FinInvOrderSaveResponse,
    FinInvOrderSupplierItemOut,
    FinInvOrderSupplierOut,
)
from app.services.fin_inv_order_service import FinInvOrderService

router = APIRouter()


def _legacy_uid(db: Session, user_id: int) -> int:
    row = db.execute(
        select(UserPreference).where(
            UserPreference.UserId == user_id,
            UserPreference.PreferenceKey == "legacy_contpl_uid",
            UserPreference.IsDeleted == False,  # noqa: E712
        )
    ).scalar_one_or_none()
    if row and row.PreferenceValue:
        try:
            return int(row.PreferenceValue)
        except ValueError:
            pass
    return settings.voucher_legacy_uid


def _service(
    current_user: CurrentUser,
    business_db: Session,
    auth_db: Session,
) -> FinInvOrderService:
    # JWT inventory.fin_inv_order.* already gates this API; that supersedes ContPL Gc0003 book ACL.
    module_ok = (
        current_user.has_permission("inventory.fin_inv_order.view")
        or current_user.has_permission("inventory.fin_inv_order.create")
        or current_user.has_permission("inventory.fin_inv_order.edit")
        or current_user.has_permission("inventory.fin_inv_order.delete")
    )
    return FinInvOrderService(
        business_db,
        username=current_user.username,
        legacy_uid=_legacy_uid(auth_db, current_user.user_id),
        is_admin=current_user.has_permission("auth.admin.full"),
        web_module_authorized=module_ok,
    )


@router.get("/config", response_model=FinInvOrderConfigOut)
def get_config(
    current_user: CurrentUser = Depends(require_permission("inventory.fin_inv_order.view")),
    business_db: Session = Depends(get_business_db),
    auth_db: Session = Depends(get_db),
):
    return _service(current_user, business_db, auth_db).get_config()


@router.get("/documents/{inv_id}", response_model=FinInvOrderDocumentOut)
def load_document(
    inv_id: int,
    current_user: CurrentUser = Depends(require_permission("inventory.fin_inv_order.view")),
    business_db: Session = Depends(get_business_db),
    auth_db: Session = Depends(get_db),
):
    return _service(current_user, business_db, auth_db).load_document(inv_id)


@router.post("/documents", response_model=FinInvOrderSaveResponse)
def save_document(
    payload: FinInvOrderSaveRequest,
    current_user: CurrentUser = Depends(require_permission("inventory.fin_inv_order.view")),
    business_db: Session = Depends(get_business_db),
    auth_db: Session = Depends(get_db),
):
    is_edit = bool(payload.inv_id and payload.inv_id > 0)
    if is_edit:
        if not (
            current_user.has_permission("inventory.fin_inv_order.edit")
            or current_user.has_permission("auth.admin.full")
        ):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions.")
    else:
        if not (
            current_user.has_permission("inventory.fin_inv_order.create")
            or current_user.has_permission("auth.admin.full")
        ):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions.")
    return _service(current_user, business_db, auth_db).save_document(payload)


@router.delete("/documents/{inv_id}", response_model=FinInvOrderDeleteResponse)
def delete_document(
    inv_id: int,
    current_user: CurrentUser = Depends(require_permission("inventory.fin_inv_order.delete")),
    business_db: Session = Depends(get_business_db),
    auth_db: Session = Depends(get_db),
):
    return _service(current_user, business_db, auth_db).delete_document(inv_id)


@router.get("/next-id")
def next_id(
    current_user: CurrentUser = Depends(require_permission("inventory.fin_inv_order.view")),
    business_db: Session = Depends(get_business_db),
    auth_db: Session = Depends(get_db),
):
    return _service(current_user, business_db, auth_db).next_id_preview()


@router.get("/suppliers/{supplier_id}", response_model=FinInvOrderSupplierOut)
def get_supplier(
    supplier_id: int,
    current_user: CurrentUser = Depends(require_permission("inventory.fin_inv_order.view")),
    business_db: Session = Depends(get_business_db),
    auth_db: Session = Depends(get_db),
):
    return _service(current_user, business_db, auth_db).get_supplier(supplier_id)


@router.get("/suppliers", response_model=List[FinInvOrderLookupRow])
def search_suppliers(
    q: str = Query(..., min_length=1),
    current_user: CurrentUser = Depends(require_permission("inventory.fin_inv_order.view")),
    business_db: Session = Depends(get_business_db),
    auth_db: Session = Depends(get_db),
):
    return _service(current_user, business_db, auth_db).search_suppliers(q)


@router.get("/suppliers/{supplier_id}/items", response_model=List[FinInvOrderSupplierItemOut])
def supplier_items(
    supplier_id: int,
    current_user: CurrentUser = Depends(require_permission("inventory.fin_inv_order.view")),
    business_db: Session = Depends(get_business_db),
    auth_db: Session = Depends(get_db),
):
    return _service(current_user, business_db, auth_db).get_supplier_items(supplier_id)


@router.post("/suppliers/{supplier_id}/items", response_model=FinInvOrderAddSupplierItemResponse)
def add_supplier_item(
    supplier_id: int,
    payload: FinInvOrderAddSupplierItemRequest,
    current_user: CurrentUser = Depends(require_permission("inventory.fin_inv_order.edit")),
    business_db: Session = Depends(get_business_db),
    auth_db: Session = Depends(get_db),
):
    svc = _service(current_user, business_db, auth_db)
    result = svc.add_supplier_item(supplier_id, payload.manual_id)
    business_db.commit()
    return result


@router.delete("/suppliers/{supplier_id}/items/{item_id}")
def remove_supplier_item(
    supplier_id: int,
    item_id: float,
    current_user: CurrentUser = Depends(require_permission("inventory.fin_inv_order.edit")),
    business_db: Session = Depends(get_business_db),
    auth_db: Session = Depends(get_db),
):
    svc = _service(current_user, business_db, auth_db)
    result = svc.remove_supplier_item(supplier_id, item_id)
    business_db.commit()
    return result


@router.get("/items/by-id/{item_id}", response_model=FinInvOrderItemOut)
def item_by_id(
    item_id: float,
    supplier_id: Optional[int] = Query(None),
    current_user: CurrentUser = Depends(require_permission("inventory.fin_inv_order.view")),
    business_db: Session = Depends(get_business_db),
    auth_db: Session = Depends(get_db),
):
    return _service(current_user, business_db, auth_db).get_item(supplier_id=supplier_id, item_id=item_id)


@router.get("/items/by-manual/{manual_id}", response_model=FinInvOrderItemOut)
def item_by_manual(
    manual_id: float,
    supplier_id: Optional[int] = Query(None),
    current_user: CurrentUser = Depends(require_permission("inventory.fin_inv_order.view")),
    business_db: Session = Depends(get_business_db),
    auth_db: Session = Depends(get_db),
):
    return _service(current_user, business_db, auth_db).get_item(supplier_id=supplier_id, manual_id=manual_id)


@router.get("/items/by-barcode/{barcode}", response_model=FinInvOrderItemOut)
def item_by_barcode(
    barcode: str,
    supplier_id: Optional[int] = Query(None),
    current_user: CurrentUser = Depends(require_permission("inventory.fin_inv_order.view")),
    business_db: Session = Depends(get_business_db),
    auth_db: Session = Depends(get_db),
):
    return _service(current_user, business_db, auth_db).get_item(supplier_id=supplier_id, barcode=barcode)


@router.get("/items/search", response_model=List[FinInvOrderLookupRow])
def search_items(
    q: str = Query(..., min_length=1),
    current_user: CurrentUser = Depends(require_permission("inventory.fin_inv_order.view")),
    business_db: Session = Depends(get_business_db),
    auth_db: Session = Depends(get_db),
):
    return _service(current_user, business_db, auth_db).search_items(q)


@router.get("/items/{item_id}/history")
def item_history(
    item_id: float,
    limit: int = Query(5, ge=1, le=20),
    current_user: CurrentUser = Depends(require_permission("inventory.fin_inv_order.view")),
    business_db: Session = Depends(get_business_db),
    auth_db: Session = Depends(get_db),
):
    return _service(current_user, business_db, auth_db).item_history(item_id, limit)


@router.get("/suppliers/{supplier_id}/po-history", response_model=List[FinInvOrderPoHistoryRow])
def po_history(
    supplier_id: int,
    limit: int = Query(5, ge=1, le=20),
    current_user: CurrentUser = Depends(require_permission("inventory.fin_inv_order.view")),
    business_db: Session = Depends(get_business_db),
    auth_db: Session = Depends(get_db),
):
    return _service(current_user, business_db, auth_db).po_history(supplier_id, limit)


@router.get("/print/{inv_id}", response_model=FinInvOrderPrintOut)
def print_data(
    inv_id: int,
    current_user: CurrentUser = Depends(require_permission("inventory.fin_inv_order.view")),
    business_db: Session = Depends(get_business_db),
    auth_db: Session = Depends(get_db),
):
    return _service(current_user, business_db, auth_db).get_print_data(inv_id)
