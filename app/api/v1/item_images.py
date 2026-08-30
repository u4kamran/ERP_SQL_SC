"""Admin API — Item Image Manager (separate module; FIN_ITEM read-only)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, require_permission
from app.database.business_session import get_business_db
from app.schemas.item_images import BulkFetchRequest, ItemImageSettingsUpdate, JobControlRequest
from app.services.item_images import ensure_product_images_dir
from app.services.item_images.job_worker import (
    create_bulk_job,
    ensure_worker_for_job,
    set_job_control,
)
from app.services.item_images.repository import ItemImagesRepository
from app.services.item_images.service import ItemImagesService

router = APIRouter()


def _svc(db: Session) -> ItemImagesService:
    return ItemImagesService(db)


@router.get("/dashboard")
def dashboard(
    _user: CurrentUser = Depends(require_permission("inventory.item_images.view")),
    db: Session = Depends(get_business_db),
):
    try:
        return _svc(db).dashboard()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Item image tables may be missing. Run scripts/setup_item_images.py",
        ) from exc


@router.get("/settings")
def get_settings(
    _user: CurrentUser = Depends(require_permission("inventory.item_images.view")),
    db: Session = Depends(get_business_db),
):
    return {"settings": _svc(db).get_settings()}


@router.put("/settings")
def update_settings(
    body: ItemImageSettingsUpdate,
    user: CurrentUser = Depends(require_permission("inventory.item_images.manage")),
    db: Session = Depends(get_business_db),
):
    payload = {k: v for k, v in body.model_dump().items() if v is not None}
    return {
        "settings": _svc(db).update_settings(
            payload, user_id=user.user_id, username=user.username
        )
    }


@router.get("/items")
def list_items(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    q: str | None = Query(None, max_length=80),
    status_filter: str | None = Query("ALL", alias="status"),
    _user: CurrentUser = Depends(require_permission("inventory.item_images.view")),
    db: Session = Depends(get_business_db),
):
    return _svc(db).list_items(page=page, page_size=page_size, q=q, status=status_filter)


@router.get("/items/{item_id}")
def item_detail(
    item_id: float,
    _user: CurrentUser = Depends(require_permission("inventory.item_images.view")),
    db: Session = Depends(get_business_db),
):
    try:
        return _svc(db).item_detail(item_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/items/{item_id}/search")
def search_item(
    item_id: float,
    force: bool = Query(False),
    dry_run: bool = Query(False),
    user: CurrentUser = Depends(require_permission("inventory.item_images.manage")),
    db: Session = Depends(get_business_db),
):
    try:
        return _svc(db).search_item(
            item_id,
            force=force,
            dry_run=dry_run,
            user_id=user.user_id,
            username=user.username,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/candidates/{candidate_id}/use")
def use_candidate(
    candidate_id: int,
    approve: bool = Query(True),
    user: CurrentUser = Depends(require_permission("inventory.item_images.manage")),
    db: Session = Depends(get_business_db),
):
    try:
        return _svc(db).use_candidate(
            candidate_id, approve=approve, user_id=user.user_id, username=user.username
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/candidates/{candidate_id}/reject")
def reject_candidate(
    candidate_id: int,
    user: CurrentUser = Depends(require_permission("inventory.item_images.manage")),
    db: Session = Depends(get_business_db),
):
    try:
        return _svc(db).reject_candidate(
            candidate_id, user_id=user.user_id, username=user.username
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/images/{image_id}/approve")
def approve_image(
    image_id: int,
    user: CurrentUser = Depends(require_permission("inventory.item_images.manage")),
    db: Session = Depends(get_business_db),
):
    try:
        return _svc(db).approve_image(image_id, user_id=user.user_id, username=user.username)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.delete("/images/{image_id}")
def delete_image(
    image_id: int,
    user: CurrentUser = Depends(require_permission("inventory.item_images.manage")),
    db: Session = Depends(get_business_db),
):
    try:
        return _svc(db).delete_image(image_id, user_id=user.user_id, username=user.username)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/items/{item_id}/upload")
async def upload_image(
    item_id: float,
    file: UploadFile = File(...),
    user: CurrentUser = Depends(require_permission("inventory.item_images.manage")),
    db: Session = Depends(get_business_db),
):
    ensure_product_images_dir()
    name = (file.filename or "").lower()
    if ".." in name or "/" in name or "\\" in name:
        raise HTTPException(status_code=400, detail="Invalid filename")
    content = await file.read()
    if len(content) > 8_000_000:
        raise HTTPException(status_code=400, detail="File too large (max 8MB)")
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")
    try:
        return _svc(db).upload_manual(
            item_id, content, user_id=user.user_id, username=user.username
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/jobs/bulk")
async def start_bulk(
    body: BulkFetchRequest,
    user: CurrentUser = Depends(require_permission("inventory.item_images.bulk")),
    db: Session = Depends(get_business_db),
):
    repo = ItemImagesRepository(db)
    if body.scope == "selected":
        ids = [float(x) for x in body.selected_item_ids]
        if not ids:
            raise HTTPException(status_code=400, detail="Select at least one item")
    elif body.scope == "test":
        ids = repo.list_item_ids_for_bulk(
            status_filter="NO_IMAGE",
            q=body.q,
            limit=body.test_limit or 5,
            missing_only=True,
        )
    elif body.scope == "filter":
        status = body.status_filter or "ALL"
        ids = repo.list_item_ids_for_bulk(
            status_filter=status if status != "ALL" else None,
            q=body.q,
            limit=500,
            missing_only=(status in (None, "ALL", "NO_IMAGE", "FAILED")),
        )
    else:
        # missing
        ids = repo.list_item_ids_for_bulk(
            status_filter="NO_IMAGE",
            q=body.q,
            limit=500,
            missing_only=True,
        )

    if body.scope == "test":
        ids = ids[: (body.test_limit or 5)]
    if not ids:
        raise HTTPException(status_code=400, detail="No items matched for bulk fetch")
    try:
        job = create_bulk_job(
            scope=body.scope,
            item_ids=ids,
            dry_run=body.dry_run,
            test_limit=body.test_limit if body.scope == "test" else None,
            filter_status=body.status_filter,
            filter_query=body.q,
            user_id=user.user_id,
            username=user.username,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    await ensure_worker_for_job(int(job["job_id"]))
    return {"job": job}


@router.get("/jobs/active")
def active_job(
    _user: CurrentUser = Depends(require_permission("inventory.item_images.view")),
    db: Session = Depends(get_business_db),
):
    return {"job": ItemImagesRepository(db).active_job()}


@router.get("/jobs/{job_id}")
def get_job(
    job_id: int,
    _user: CurrentUser = Depends(require_permission("inventory.item_images.view")),
    db: Session = Depends(get_business_db),
):
    job = ItemImagesRepository(db).get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"job": job}


@router.post("/jobs/{job_id}/control")
async def control_job(
    job_id: int,
    body: JobControlRequest,
    _user: CurrentUser = Depends(require_permission("inventory.item_images.bulk")),
):
    try:
        job = set_job_control(job_id, body.action)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if body.action == "resume":
        await ensure_worker_for_job(job_id)
    return {"job": job}
