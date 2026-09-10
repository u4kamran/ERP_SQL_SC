"""Default Setup API — configurable business day times."""

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import CurrentUser, require_any_permission, require_permission
from app.schemas.default_setup import BusinessDayConfigResponse, BusinessDayConfigUpdate
from app.services.default_setup_store import get_business_day_state, save_business_day_config

router = APIRouter()

_READ_PERMS = require_any_permission(
    "reports.sales_dashboard.view",
    "inventory.fin_item.view",
    "auth.admin.full",
    "settings.default_setup.view",
    "settings.default_setup.manage",
)


@router.get("/business-day", response_model=BusinessDayConfigResponse)
def get_business_day_settings(
    _user=Depends(_READ_PERMS),
) -> BusinessDayConfigResponse:
    return BusinessDayConfigResponse(**get_business_day_state())


@router.put("/business-day", response_model=BusinessDayConfigResponse)
def update_business_day_settings(
    body: BusinessDayConfigUpdate,
    current_user: CurrentUser = Depends(require_permission("auth.admin.full")),
) -> BusinessDayConfigResponse:
    try:
        state = save_business_day_config(
            body.business_day_start_time,
            body.business_day_end_time,
            username=current_user.username,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return BusinessDayConfigResponse(**state)
