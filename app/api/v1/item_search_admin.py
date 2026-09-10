"""Admin API for item search settings, aliases, and no-result report."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, require_permission
from app.database.business_session import get_business_db
from app.repositories.item_search_support_repository import ItemSearchSupportRepository
from app.services import item_search_control_store as search_settings

router = APIRouter()


class ItemSearchSettingsUpdate(BaseModel):
    min_chars: int | None = Field(default=None, ge=1, le=5)
    max_results: int | None = Field(default=None, ge=5, le=20)
    debounce_ms: int | None = Field(default=None, ge=120, le=800)
    fuzzy_enabled: bool | None = None
    alias_enabled: bool | None = None
    barcode_enabled: bool | None = None
    notes: str | None = Field(default=None, max_length=300)


class ItemSearchAliasIn(BaseModel):
    alias_text: str = Field(..., min_length=2, max_length=80)
    expand_text: str = Field(..., min_length=2, max_length=120)


@router.get("/dashboard")
def dashboard(
    days: int = Query(30, ge=1, le=365),
    _user: CurrentUser = Depends(require_permission("marketing.item_search.view")),
    db: Session = Depends(get_business_db),
):
    repo = ItemSearchSupportRepository(db)
    aliases = []
    no_results = []
    try:
        aliases = repo.list_aliases()
        no_results = repo.no_result_report(days=days, limit=80)
    except Exception:
        db.rollback()
    return {
        "settings": search_settings.get_settings(),
        "aliases": aliases,
        "no_results": no_results,
    }


@router.put("/settings")
def update_settings(
    body: ItemSearchSettingsUpdate,
    _user: CurrentUser = Depends(require_permission("marketing.item_search.manage")),
):
    payload = {k: v for k, v in body.model_dump().items() if v is not None}
    return {"settings": search_settings.update_settings(payload)}


@router.post("/aliases")
def save_alias(
    body: ItemSearchAliasIn,
    _user: CurrentUser = Depends(require_permission("marketing.item_search.manage")),
    db: Session = Depends(get_business_db),
):
    repo = ItemSearchSupportRepository(db)
    try:
        repo.upsert_alias(body.alias_text, body.expand_text)
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save alias.",
        ) from exc
    return {"aliases": repo.list_aliases()}


@router.delete("/aliases/{alias_id}")
def delete_alias(
    alias_id: int,
    _user: CurrentUser = Depends(require_permission("marketing.item_search.manage")),
    db: Session = Depends(get_business_db),
):
    repo = ItemSearchSupportRepository(db)
    repo.delete_alias(alias_id)
    db.commit()
    return {"aliases": repo.list_aliases()}
