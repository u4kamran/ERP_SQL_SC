"""Schemas for Gemini usage dashboard."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class GeminiBudgetUpdate(BaseModel):
    budget_usd: float = Field(..., ge=0, le=100000)
    note: str = Field("", max_length=200)


class GeminiUsageSummary(BaseModel):
    model: str = ""
    budget_usd: float = 0
    budget_note: str = ""
    budget_updated_at: str = ""
    spent_usd: float = 0
    remaining_usd: float | None = None
    calls_total: int = 0
    calls_failed: int = 0
    prompt_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    today_calls: int = 0
    today_tokens: int = 0
    today_cost_usd: float = 0
    by_feature: list[dict[str, Any]] = Field(default_factory=list)
    recent: list[dict[str, Any]] = Field(default_factory=list)
    rates: dict[str, Any] = Field(default_factory=dict)
    note: str = ""
    billing_url: str = ""
