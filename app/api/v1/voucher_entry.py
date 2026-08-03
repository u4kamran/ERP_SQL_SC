"""Web voucher entry API — same GL tables as VB6."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, require_permission
from app.database.business_session import get_business_db
from app.database.session import get_db
from app.models.user import UserPreference
from app.schemas.voucher_entry import (
    VoucherAccountLookup,
    VoucherBookOut,
    VoucherConfigOut,
    VoucherDeleteResponse,
    VoucherHeaderOut,
    VoucherLineOut,
    VoucherNarrationLookup,
    VoucherNextNumberOut,
    VoucherSaveRequest,
    VoucherSaveResponse,
)
from app.services.voucher_entry_service import VoucherEntryService

router = APIRouter()


def _legacy_uid(db: Session, user_id: int) -> int:
    from app.config.settings import settings

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
) -> VoucherEntryService:
    return VoucherEntryService(
        business_db,
        username=current_user.username,
        legacy_uid=_legacy_uid(auth_db, current_user.user_id),
        is_admin=current_user.has_permission("auth.admin.full"),
    )


@router.get("/config", response_model=VoucherConfigOut)
def voucher_config(
    current_user: CurrentUser = Depends(require_permission("gl.voucher.view")),
    business_db: Session = Depends(get_business_db),
    auth_db: Session = Depends(get_db),
):
    return _service(current_user, business_db, auth_db).get_config()


@router.get("/books", response_model=list[VoucherBookOut])
def list_books(
    current_user: CurrentUser = Depends(require_permission("gl.voucher.view")),
    business_db: Session = Depends(get_business_db),
    auth_db: Session = Depends(get_db),
):
    return _service(current_user, business_db, auth_db).list_books()


@router.get("/books/{book_id}", response_model=VoucherBookOut)
def get_book(
    book_id: int,
    current_user: CurrentUser = Depends(require_permission("gl.voucher.view")),
    business_db: Session = Depends(get_business_db),
    auth_db: Session = Depends(get_db),
):
    return _service(current_user, business_db, auth_db).get_book(book_id)


@router.get("/accounts/search", response_model=list[VoucherAccountLookup])
def search_accounts(
    q: str = Query(..., min_length=1),
    current_user: CurrentUser = Depends(require_permission("gl.voucher.view")),
    business_db: Session = Depends(get_business_db),
    auth_db: Session = Depends(get_db),
):
    return _service(current_user, business_db, auth_db).search_accounts(q)


@router.get("/accounts/{ac_id}", response_model=VoucherAccountLookup)
def get_account(
    ac_id: int,
    current_user: CurrentUser = Depends(require_permission("gl.voucher.view")),
    business_db: Session = Depends(get_business_db),
    auth_db: Session = Depends(get_db),
):
    return _service(current_user, business_db, auth_db).get_account(ac_id)


@router.get("/narrations/search", response_model=list[VoucherNarrationLookup])
def search_narrations(
    q: str = Query(..., min_length=1),
    ac_id: Optional[int] = None,
    current_user: CurrentUser = Depends(require_permission("gl.voucher.view")),
    business_db: Session = Depends(get_business_db),
    auth_db: Session = Depends(get_db),
):
    return _service(current_user, business_db, auth_db).search_narrations(q, ac_id)


@router.get("/narrations/last/{ac_id}")
def last_narration(
    ac_id: int,
    current_user: CurrentUser = Depends(require_permission("gl.voucher.view")),
    business_db: Session = Depends(get_business_db),
    auth_db: Session = Depends(get_db),
):
    text = _service(current_user, business_db, auth_db).last_narration(ac_id)
    return {"narration": text or ""}


@router.get("/next-number", response_model=VoucherNextNumberOut)
def next_number(
    book_id: int,
    v_mode: int = Query(1, ge=1, le=3),
    fiscal: int = Query(0, ge=0, le=12),
    current_user: CurrentUser = Depends(require_permission("gl.voucher.view")),
    business_db: Session = Depends(get_business_db),
    auth_db: Session = Depends(get_db),
):
    return _service(current_user, business_db, auth_db).next_number(book_id, v_mode, fiscal)


@router.get("/load", response_model=VoucherHeaderOut)
def load_voucher(
    book_id: int,
    voucher_id: int,
    v_mode: int = Query(1, ge=1, le=3),
    fiscal: int = Query(0, ge=0, le=12),
    current_user: CurrentUser = Depends(require_permission("gl.voucher.view")),
    business_db: Session = Depends(get_business_db),
    auth_db: Session = Depends(get_db),
):
    return _service(current_user, business_db, auth_db).load_by_key(book_id, voucher_id, v_mode, fiscal)


@router.get("/by-serial/{serial_no}", response_model=VoucherHeaderOut)
def load_by_serial(
    serial_no: float,
    current_user: CurrentUser = Depends(require_permission("gl.voucher.view")),
    business_db: Session = Depends(get_business_db),
    auth_db: Session = Depends(get_db),
):
    return _service(current_user, business_db, auth_db).load_by_serial(serial_no)


@router.get("/repeat-last/{book_id}", response_model=list[VoucherLineOut])
def repeat_last(
    book_id: int,
    current_user: CurrentUser = Depends(require_permission("gl.voucher.create")),
    business_db: Session = Depends(get_business_db),
    auth_db: Session = Depends(get_db),
):
    return _service(current_user, business_db, auth_db).repeat_last(book_id)


@router.post("", response_model=VoucherSaveResponse)
def create_voucher(
    payload: VoucherSaveRequest,
    current_user: CurrentUser = Depends(require_permission("gl.voucher.create")),
    business_db: Session = Depends(get_business_db),
    auth_db: Session = Depends(get_db),
):
    return _service(current_user, business_db, auth_db).save(payload, editing=False)


@router.put("/{serial_no}", response_model=VoucherSaveResponse)
def update_voucher(
    serial_no: float,
    payload: VoucherSaveRequest,
    current_user: CurrentUser = Depends(require_permission("gl.voucher.edit")),
    business_db: Session = Depends(get_business_db),
    auth_db: Session = Depends(get_db),
):
    payload.serial_no = serial_no
    return _service(current_user, business_db, auth_db).save(payload, editing=True)


@router.delete("/{serial_no}", response_model=VoucherDeleteResponse)
def delete_voucher(
    serial_no: float,
    current_user: CurrentUser = Depends(require_permission("gl.voucher.delete")),
    business_db: Session = Depends(get_business_db),
    auth_db: Session = Depends(get_db),
):
    return _service(current_user, business_db, auth_db).delete(serial_no)
