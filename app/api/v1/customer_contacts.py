"""Customer marketing contacts API."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, require_any_permission
from app.database.business_session import get_business_db
from app.schemas.customer_contacts import (
    ContactLookupResponse,
    CustomerContactListResponse,
    CustomerContactRow,
    CustomerContactStats,
    CustomerMarketingLinksUpdate,
)
from app.services.customer_contacts_service import CustomerContactsService

router = APIRouter()

_VIEW_PERMS = require_any_permission(
    "marketing.customer_contacts.view",
    "support.phone_osint.view",
    "auth.admin.full",
)
_MANAGE_PERMS = require_any_permission(
    "marketing.customer_contacts.manage",
    "auth.admin.full",
)


@router.get("/stats", response_model=CustomerContactStats)
def contact_stats(
    _user: CurrentUser = Depends(_VIEW_PERMS),
    db: Session = Depends(get_business_db),
) -> CustomerContactStats:
    return CustomerContactsService(db).stats()


@router.get("/list", response_model=CustomerContactListResponse)
def list_contacts(
    q: str = Query("", max_length=100),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    only_with_phone: bool = Query(False),
    only_with_email: bool = Query(False),
    only_with_social: bool = Query(False),
    only_missing: bool = Query(False),
    _user: CurrentUser = Depends(_VIEW_PERMS),
    db: Session = Depends(get_business_db),
) -> CustomerContactListResponse:
    return CustomerContactsService(db).list_contacts(
        q=q,
        page=page,
        page_size=page_size,
        only_with_phone=only_with_phone,
        only_with_email=only_with_email,
        only_with_social=only_with_social,
        only_missing=only_missing,
    )


@router.get("/lookup", response_model=ContactLookupResponse)
def lookup_contact(
    phone: str = Query("", max_length=30),
    email: str = Query("", max_length=255),
    _user: CurrentUser = Depends(_VIEW_PERMS),
    db: Session = Depends(get_business_db),
) -> ContactLookupResponse:
    """Find customer by mobile number or email, with social media discovery links."""
    return CustomerContactsService(db).lookup_contact(phone=phone, email=email)


@router.get("/export.csv")
def export_contacts_csv(
    q: str = Query("", max_length=100),
    only_with_phone: bool = Query(False),
    only_with_email: bool = Query(False),
    only_with_social: bool = Query(False),
    _user: CurrentUser = Depends(_VIEW_PERMS),
    db: Session = Depends(get_business_db),
) -> PlainTextResponse:
    csv_text = CustomerContactsService(db).export_csv(
        q=q,
        only_with_phone=only_with_phone,
        only_with_email=only_with_email,
        only_with_social=only_with_social,
    )
    return PlainTextResponse(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="customer-contacts.csv"'},
    )


@router.get("/sms/{cust_sms_id}", response_model=CustomerContactRow)
def get_contact(
    cust_sms_id: int,
    _user: CurrentUser = Depends(_VIEW_PERMS),
    db: Session = Depends(get_business_db),
) -> CustomerContactRow:
    return CustomerContactsService(db).get_contact(cust_sms_id)


@router.put("/sms/{cust_sms_id}/marketing", response_model=CustomerContactRow)
def update_marketing_links(
    cust_sms_id: int,
    body: CustomerMarketingLinksUpdate,
    _user: CurrentUser = Depends(_MANAGE_PERMS),
    db: Session = Depends(get_business_db),
) -> CustomerContactRow:
    return CustomerContactsService(db).update_marketing_links(cust_sms_id, body)
