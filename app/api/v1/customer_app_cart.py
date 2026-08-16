"""Public + staff APIs for Customer App Carts (saved baskets, not invoices)."""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, require_permission
from app.database.business_session import get_business_db
from app.schemas.customer_app_cart import (
    CartDetailOut,
    CartListPage,
    CustomerLookupRequest,
    CustomerLookupResponse,
    CustomerRegisterRequest,
    CustomerRegisterResponse,
    SaveCartRequest,
    SaveCartResponse,
    StaffStatusUpdateRequest,
)
from app.schemas.whatsapp_bot import (
    MobileOtpResponse,
    MobileOtpSendRequest,
    MobileOtpVerifyRequest,
)
from app.services.customer_app_cart_service import CustomerAppCartService
from app.services.customer_app_otp_service import CustomerAppOtpService

public_router = APIRouter()
router = APIRouter()


def _client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for") or ""
    if forwarded:
        return forwarded.split(",")[0].strip()[:64]
    if request.client:
        return (request.client.host or "")[:64]
    return None


@public_router.post("/mobile-otp/send", response_model=MobileOtpResponse)
def send_mobile_otp(
    body: MobileOtpSendRequest,
    request: Request,
    db: Session = Depends(get_business_db),
):
    """One-time mobile proof via SMS_DB_ queue. Never returns the OTP in production."""
    try:
        result = CustomerAppOtpService(db).request_otp(
            body.phone, client_ip=_client_ip(request)
        )
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return MobileOtpResponse(**result)


@public_router.post("/mobile-otp/verify", response_model=MobileOtpResponse)
def verify_mobile_otp(body: MobileOtpVerifyRequest, db: Session = Depends(get_business_db)):
    try:
        result = CustomerAppOtpService(db).verify_otp(
            body.phone, body.code, request_id=body.request_id
        )
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return MobileOtpResponse(**result)


@public_router.get("/mobile-otp/status")
def mobile_otp_status(
    mobile: str = Query(..., min_length=10, max_length=20),
    db: Session = Depends(get_business_db),
):
    return CustomerAppOtpService(db).status(mobile)


@public_router.post("/customers/lookup", response_model=CustomerLookupResponse)
def lookup_customer(payload: CustomerLookupRequest, db: Session = Depends(get_business_db)):
    return CustomerAppCartService(db).lookup_customer(payload.mobile)


@public_router.post("/customers/register", response_model=CustomerRegisterResponse)
def register_customer(payload: CustomerRegisterRequest, db: Session = Depends(get_business_db)):
    return CustomerAppCartService(db).register_customer(payload)


@public_router.post("/carts", response_model=SaveCartResponse)
def save_cart(payload: SaveCartRequest, db: Session = Depends(get_business_db)):
    """Save a customer cart into ERP. Does NOT create a sales invoice or post stock."""
    return CustomerAppCartService(db).save_cart(payload)


@public_router.get("/carts", response_model=CartListPage)
def list_my_carts(
    mobile: str = Query(..., min_length=10, max_length=20),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_business_db),
):
    return CustomerAppCartService(db).list_my_carts(mobile=mobile, page=page, page_size=page_size)


@public_router.get("/carts/{cart_ref}", response_model=CartDetailOut)
def get_my_cart(
    cart_ref: str,
    mobile: str = Query(..., min_length=10, max_length=20),
    db: Session = Depends(get_business_db),
):
    return CustomerAppCartService(db).get_my_cart(cart_ref=cart_ref, mobile=mobile)


@router.get("", response_model=CartListPage)
def staff_list_carts(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    status: str | None = Query(None),
    source: str | None = Query("MOBILE_APP"),
    search: str | None = Query(None, max_length=120),
    date_from: str | None = Query(None, description="YYYY-MM-DD"),
    date_to: str | None = Query(None, description="YYYY-MM-DD"),
    _user: CurrentUser = Depends(require_permission("marketing.customer_app_carts.view")),
    db: Session = Depends(get_business_db),
):
    return CustomerAppCartService(db).staff_list(
        page=page,
        page_size=page_size,
        status_filter=status,
        source=source,
        search=search,
        date_from=date_from,
        date_to=date_to,
    )


@router.get("/{cart_id}", response_model=CartDetailOut)
def staff_get_cart(
    cart_id: int,
    _user: CurrentUser = Depends(require_permission("marketing.customer_app_carts.view")),
    db: Session = Depends(get_business_db),
):
    return CustomerAppCartService(db).staff_get(cart_id)


@router.put("/{cart_id}/status", response_model=CartDetailOut)
def staff_update_status(
    cart_id: int,
    payload: StaffStatusUpdateRequest,
    current_user: CurrentUser = Depends(require_permission("marketing.customer_app_carts.update")),
    db: Session = Depends(get_business_db),
):
    allow_cancel = current_user.has_permission("marketing.customer_app_carts.cancel")

    return CustomerAppCartService(db).staff_update_status(
        cart_id=cart_id,
        new_status=payload.status,
        actor_username=current_user.username or str(current_user.user_id),
        remarks=payload.remarks,
        allow_cancel=allow_cancel,
    )


@router.post("/{cart_id}/convert")
def staff_convert(
    cart_id: int,
    _user: CurrentUser = Depends(require_permission("marketing.customer_app_carts.convert")),
    db: Session = Depends(get_business_db),
):
    CustomerAppCartService(db).staff_convert_stub(cart_id)
