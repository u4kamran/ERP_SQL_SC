"""CUST_SMS CRUD API endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, require_permission
from app.database.business_session import get_business_db
from app.schemas import MessageResponse
from app.schemas.cust_sms import CustSmsCreate, CustSmsListResponse, CustSmsResponse, CustSmsUpdate
from app.services.cust_sms_service import CustSmsService

router = APIRouter()


@router.get("/", response_model=CustSmsListResponse)
def list_cust_sms(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    search: Optional[str] = Query(None, max_length=100),
    current_user: CurrentUser = Depends(require_permission("marketing.cust_sms.view")),
    db: Session = Depends(get_business_db),
):
    return CustSmsService(db).list_rows(skip, limit, search)


@router.get("/{cust_id}", response_model=CustSmsResponse)
def get_cust_sms(
    cust_id: int,
    current_user: CurrentUser = Depends(require_permission("marketing.cust_sms.view")),
    db: Session = Depends(get_business_db),
):
    return CustSmsService(db).get_row(cust_id)


@router.post("/", response_model=CustSmsResponse, status_code=201)
def create_cust_sms(
    data: CustSmsCreate,
    current_user: CurrentUser = Depends(require_permission("marketing.cust_sms.create")),
    db: Session = Depends(get_business_db),
):
    return CustSmsService(db).create_row(data)


@router.put("/{cust_id}", response_model=CustSmsResponse)
def update_cust_sms(
    cust_id: int,
    data: CustSmsUpdate,
    current_user: CurrentUser = Depends(require_permission("marketing.cust_sms.update")),
    db: Session = Depends(get_business_db),
):
    return CustSmsService(db).update_row(cust_id, data)


@router.delete("/{cust_id}", response_model=MessageResponse)
def delete_cust_sms(
    cust_id: int,
    current_user: CurrentUser = Depends(require_permission("marketing.cust_sms.delete")),
    db: Session = Depends(get_business_db),
):
    CustSmsService(db).delete_row(cust_id)
    return MessageResponse(message="CUST_SMS record deleted successfully.")
