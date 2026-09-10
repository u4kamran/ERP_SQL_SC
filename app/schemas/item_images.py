"""Pydantic schemas for Item Image Manager."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ItemImageSettingsUpdate(BaseModel):
    auto_accept_min: Optional[int] = Field(default=None, ge=50, le=100)
    review_min: Optional[int] = Field(default=None, ge=20, le=99)
    no_match_min: Optional[int] = Field(default=None, ge=0, le=75)
    requests_per_minute: Optional[int] = Field(default=None, ge=1, le=120)
    max_concurrent: Optional[int] = Field(default=None, ge=1, le=8)
    timeout_seconds: Optional[int] = Field(default=None, ge=5, le=60)
    retry_count: Optional[int] = Field(default=None, ge=0, le=5)
    min_width: Optional[int] = Field(default=None, ge=32, le=500)
    min_height: Optional[int] = Field(default=None, ge=32, le=500)
    download_enabled: Optional[bool] = None
    naheed_enabled: Optional[bool] = None
    metro_enabled: Optional[bool] = None
    carrefour_enabled: Optional[bool] = None
    imtiaz_enabled: Optional[bool] = None
    alfatah_enabled: Optional[bool] = None
    open_food_facts_enabled: Optional[bool] = None
    upcitemdb_enabled: Optional[bool] = None


class BulkFetchRequest(BaseModel):
    scope: str = Field(default="missing", pattern="^(missing|selected|filter|test)$")
    selected_item_ids: list[float] = Field(default_factory=list, max_length=2000)
    status_filter: Optional[str] = None
    q: Optional[str] = Field(default=None, max_length=80)
    test_limit: Optional[int] = Field(default=None, ge=1, le=25)
    dry_run: bool = False


class JobControlRequest(BaseModel):
    action: str = Field(..., pattern="^(pause|resume|cancel)$")
