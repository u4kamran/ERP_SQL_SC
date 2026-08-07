"""Promotion hub API — compose and send marketing messages."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, require_any_permission
from app.database.business_session import get_business_db
from app.schemas.promotion_hub import (
    PromotionChannelStatus,
    PromotionComposeResponse,
    SendPromotionRequest,
    SendPromotionResponse,
)
from app.services.promotion_hub_service import PromotionHubService

router = APIRouter()

_VIEW_PERMS = require_any_permission(
    "marketing.promotion.view",
    "marketing.customer_contacts.view",
    "auth.admin.full",
)
_SEND_PERMS = require_any_permission(
    "marketing.promotion.send",
    "marketing.customer_contacts.manage",
    "auth.admin.full",
)


@router.get("/channels", response_model=PromotionChannelStatus)
def channel_status(
    _user: CurrentUser = Depends(_VIEW_PERMS),
    db: Session = Depends(get_business_db),
) -> PromotionChannelStatus:
    return PromotionHubService(db).channel_status()


@router.get("/compose", response_model=PromotionComposeResponse)
def compose_promotion(
    phone: str = Query("", max_length=30),
    email: str = Query("", max_length=255),
    cust_sms_id: int | None = Query(None),
    template_id: str = Query("sale", max_length=50),
    _user: CurrentUser = Depends(_VIEW_PERMS),
    db: Session = Depends(get_business_db),
) -> PromotionComposeResponse:
    return PromotionHubService(db).compose(
        phone=phone,
        email=email,
        cust_sms_id=cust_sms_id,
        template_id=template_id,
    )


@router.post("/send", response_model=SendPromotionResponse)
def send_promotion(
    body: SendPromotionRequest,
    _user: CurrentUser = Depends(_SEND_PERMS),
    db: Session = Depends(get_business_db),
) -> SendPromotionResponse:
    return PromotionHubService(db).send(body)
