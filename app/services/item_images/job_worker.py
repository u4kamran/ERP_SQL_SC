"""Background bulk image-fetch job worker (asyncio + DB queue)."""

from __future__ import annotations

import asyncio
import threading
from typing import Any, Optional

from app.database.business_session import BusinessSessionLocal
from app.logging.logger import logger
from app.services.item_images.repository import ItemImagesRepository
from app.services.item_images.service import ItemImagesService

_LOCK = threading.Lock()
_TASK: asyncio.Task | None = None
_CURRENT_JOB_ID: int | None = None


def active_job_id() -> int | None:
    return _CURRENT_JOB_ID


async def ensure_worker_for_job(job_id: int) -> None:
    global _TASK, _CURRENT_JOB_ID
    with _LOCK:
        if _TASK and not _TASK.done() and _CURRENT_JOB_ID == job_id:
            return
        _CURRENT_JOB_ID = job_id
        _TASK = asyncio.create_task(_run_job(job_id), name=f"item-image-job-{job_id}")


async def _run_job(job_id: int) -> None:
    logger.info("Item image job %s started", job_id)
    try:
        while True:
            db = BusinessSessionLocal()
            try:
                repo = ItemImagesRepository(db)
                job = repo.get_job(job_id)
                if not job:
                    break
                status = job["status"]
                if status == "PAUSED":
                    await asyncio.sleep(1.5)
                    continue
                if status in ("CANCELLED", "COMPLETED", "FAILED"):
                    break
                if status == "PENDING":
                    repo.set_job_status(job_id, "RUNNING", started_at=True)
                    db.commit()

                item = repo.claim_next_job_item(job_id)
                if not item:
                    repo.set_job_status(job_id, "COMPLETED", finished_at=True)
                    db.commit()
                    break
                db.commit()

                dry_run = bool(job.get("dry_run"))
                service = ItemImagesService(db)
                result_status = "FAILED"
                match_score = None
                err = None
                try:
                    # Skip if already approved (restart-safe) unless dry_run
                    if not dry_run and repo.has_approved_primary(float(item["item_id"])):
                        repo.finish_job_item(
                            int(item["job_item_id"]),
                            status="SKIPPED",
                            result_status="APPROVED",
                        )
                        repo.bump_job_counters(job_id, "APPROVED")
                        db.commit()
                        continue

                    result = await asyncio.to_thread(
                        service.search_item,
                        float(item["item_id"]),
                        force=False,
                        dry_run=dry_run,
                        user_id=job.get("created_by_user_id"),
                        username=job.get("created_by_username"),
                    )
                    if result.get("skipped"):
                        result_status = "APPROVED"
                    elif not result.get("found"):
                        result_status = "NO_IMAGE"
                    elif result.get("auto_linked"):
                        result_status = "APPROVED"
                    elif result.get("decision") == "AUTO_APPROVED":
                        result_status = "APPROVED"
                    elif result.get("decision") in ("REVIEW_RECOMMENDED", "NEEDS_REVIEW"):
                        result_status = "NEEDS_REVIEW"
                    elif result.get("decision") == "NO_RELIABLE_MATCH":
                        result_status = "NO_IMAGE"
                    else:
                        result_status = result.get("decision") or "NEEDS_REVIEW"
                    match_score = result.get("best_score")
                    repo.finish_job_item(
                        int(item["job_item_id"]),
                        status="DONE",
                        result_status=result_status,
                        match_score=match_score,
                    )
                    repo.bump_job_counters(job_id, result_status)
                    db.commit()
                except Exception as exc:
                    err = str(exc)[:400]
                    logger.exception("Item image job item failed item_id=%s", item.get("item_id"))
                    repo.finish_job_item(
                        int(item["job_item_id"]),
                        status="FAILED",
                        result_status="FAILED",
                        error_message=err,
                    )
                    repo.add_error(
                        {
                            "item_id": float(item["item_id"]),
                            "job_id": job_id,
                            "error_code": "JOB_ITEM_FAILED",
                            "error_message": err,
                            "provider_name": None,
                        }
                    )
                    repo.bump_job_counters(job_id, "FAILED")
                    db.commit()
            finally:
                db.close()

            await asyncio.sleep(0.15)
    except Exception:
        logger.exception("Item image job %s crashed", job_id)
        db = BusinessSessionLocal()
        try:
            ItemImagesRepository(db).set_job_status(job_id, "FAILED", finished_at=True)
            db.commit()
        finally:
            db.close()
    finally:
        global _CURRENT_JOB_ID
        with _LOCK:
            if _CURRENT_JOB_ID == job_id:
                _CURRENT_JOB_ID = None
        logger.info("Item image job %s finished", job_id)


def create_bulk_job(
    *,
    scope: str,
    item_ids: list[float],
    dry_run: bool = False,
    test_limit: int | None = None,
    filter_status: str | None = None,
    filter_query: str | None = None,
    user_id: int | None = None,
    username: str | None = None,
) -> dict[str, Any]:
    db = BusinessSessionLocal()
    try:
        repo = ItemImagesRepository(db)
        active = repo.active_job()
        if active and active["status"] in ("PENDING", "RUNNING", "PAUSED"):
            raise ValueError(f"Job {active['job_id']} is already {active['status']}")
        ids = item_ids
        if test_limit:
            ids = ids[: int(test_limit)]
        job_id = repo.create_job(
            {
                "scope": scope[:40],
                "dry_run": 1 if dry_run else 0,
                "test_limit": test_limit,
                "total_count": len(ids),
                "filter_status": filter_status,
                "filter_query": (filter_query or "")[:120] or None,
                "created_by_user_id": user_id,
                "created_by_username": username,
            }
        )
        repo.add_job_items(job_id, ids)
        db.commit()
        return repo.get_job(job_id) or {"job_id": job_id}
    finally:
        db.close()


def set_job_control(job_id: int, action: str) -> dict[str, Any]:
    db = BusinessSessionLocal()
    try:
        repo = ItemImagesRepository(db)
        job = repo.get_job(job_id)
        if not job:
            raise ValueError("Job not found")
        action = action.lower()
        if action == "pause":
            if job["status"] != "RUNNING":
                raise ValueError("Only running jobs can be paused")
            repo.set_job_status(job_id, "PAUSED")
        elif action == "resume":
            if job["status"] != "PAUSED":
                raise ValueError("Only paused jobs can be resumed")
            repo.set_job_status(job_id, "RUNNING")
        elif action == "cancel":
            if job["status"] in ("COMPLETED", "CANCELLED"):
                raise ValueError("Job already finished")
            repo.set_job_status(job_id, "CANCELLED", finished_at=True)
        else:
            raise ValueError("Unknown action")
        db.commit()
        return repo.get_job(job_id) or {}
    finally:
        db.close()
