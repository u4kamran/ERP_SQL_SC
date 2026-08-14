"""Admin API for voice search abuse controls + audit log."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.deps import CurrentUser, require_permission
from app.schemas.voice_search_control import (
    VoiceSearchDashboard,
    VoiceSearchSettingsUpdate,
)
from app.services import voice_search_control_store as voice_control

router = APIRouter()


@router.get("/dashboard", response_model=VoiceSearchDashboard)
def get_dashboard(
    mobile: str = Query("", max_length=32),
    limit: int = Query(100, ge=1, le=500),
    _user: CurrentUser = Depends(require_permission("marketing.voice_control.view")),
) -> VoiceSearchDashboard:
    return VoiceSearchDashboard(
        **voice_control.dashboard(mobile=mobile, limit=limit)
    )


@router.put("/settings", response_model=VoiceSearchDashboard)
def update_settings(
    body: VoiceSearchSettingsUpdate,
    _user: CurrentUser = Depends(require_permission("marketing.voice_control.manage")),
) -> VoiceSearchDashboard:
    payload = {k: v for k, v in body.model_dump().items() if v is not None}
    voice_control.update_settings(payload)
    return VoiceSearchDashboard(**voice_control.dashboard(limit=100))
