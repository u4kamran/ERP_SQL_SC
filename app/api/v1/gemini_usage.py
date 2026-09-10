"""Admin API for Gemini token / dollar usage dashboard."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, require_permission
from app.schemas.gemini_usage import GeminiBudgetUpdate, GeminiUsageSummary
from app.services import gemini_usage_store as usage_store

router = APIRouter()


@router.get("/summary", response_model=GeminiUsageSummary)
def get_summary(
    _user: CurrentUser = Depends(require_permission("marketing.gemini_usage.view")),
) -> GeminiUsageSummary:
    return GeminiUsageSummary(**usage_store.summary(limit_recent=40))


@router.put("/budget", response_model=GeminiUsageSummary)
def update_budget(
    body: GeminiBudgetUpdate,
    _user: CurrentUser = Depends(require_permission("marketing.gemini_usage.manage")),
) -> GeminiUsageSummary:
    return GeminiUsageSummary(
        **usage_store.set_budget(body.budget_usd, note=body.note)
    )
