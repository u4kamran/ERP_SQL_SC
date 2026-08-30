"""Core Item Image search / link / review service. FIN_ITEM is read-only."""

from __future__ import annotations

import time
import uuid
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.item_images import DEFAULT_SETTINGS, public_image_url
from app.services.item_images.providers import build_providers
from app.services.item_images.providers.base import ImageCandidate, ItemSearchContext, ProductCandidate
from app.services.item_images.rate_limit import RATE_LIMITER
from app.services.item_images.repository import ItemImagesRepository
from app.services.item_images.scoring import decide_status, score_product
from app.services.item_images.validation import download_and_validate, validate_upload_bytes


class ItemImagesService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ItemImagesRepository(db)

    def _settings(self) -> dict[str, Any]:
        cfg = dict(DEFAULT_SETTINGS)
        cfg.update({k: v for k, v in (self.repo.get_settings() or {}).items() if v is not None})
        # Normalize bit fields
        for bit in (
            "download_enabled",
            "naheed_enabled",
            "metro_enabled",
            "carrefour_enabled",
            "imtiaz_enabled",
            "alfatah_enabled",
            "open_food_facts_enabled",
            "upcitemdb_enabled",
        ):
            if bit in cfg:
                cfg[bit] = bool(cfg[bit])
        return cfg

    def get_settings(self) -> dict[str, Any]:
        return self._settings()

    def update_settings(
        self, fields: dict[str, Any], *, user_id: int | None, username: str | None
    ) -> dict[str, Any]:
        updated = self.repo.update_settings(fields, user_id=user_id, username=username)
        self.db.commit()
        return self._settings() if not updated else self._settings()

    def dashboard(self) -> dict[str, Any]:
        return self.repo.dashboard_stats()

    def list_items(
        self, *, page: int = 1, page_size: int = 25, q: str | None = None, status: str | None = None
    ) -> dict[str, Any]:
        rows, total = self.repo.list_items_page(
            page=page, page_size=page_size, q=q, status_filter=status or "ALL"
        )
        items = []
        for r in rows:
            items.append(
                {
                    **r,
                    "preview_url": public_image_url(r.get("thumb_path") or r.get("local_image_path"))
                    or r.get("image_url"),
                }
            )
        return {
            "items": items,
            "page": page,
            "page_size": page_size,
            "total": total,
            "has_more": page * page_size < total,
        }

    def item_detail(self, item_id: float) -> dict[str, Any]:
        item = self.repo.get_fin_item(item_id)
        if not item:
            raise ValueError("Item not found")
        status = self.repo.get_status(item_id) or {"status": "NO_IMAGE"}
        images = []
        for img in self.repo.list_images(item_id):
            images.append(
                {
                    **img,
                    "preview_url": public_image_url(img.get("thumb_path") or img.get("local_image_path"))
                    or img.get("image_url"),
                }
            )
        candidates = self.repo.list_candidates(item_id)
        return {
            "item": item,
            "status": status,
            "images": images,
            "candidates": candidates,
        }

    def search_item(
        self,
        item_id: float,
        *,
        force: bool = False,
        dry_run: bool = False,
        user_id: int | None = None,
        username: str | None = None,
    ) -> dict[str, Any]:
        item = self.repo.get_fin_item(item_id)
        if not item:
            raise ValueError("Item not found")

        if not force and self.repo.has_approved_primary(item_id) and not dry_run:
            return {
                "skipped": True,
                "reason": "Approved image already linked. Use Search Again to force.",
                "detail": self.item_detail(item_id),
            }

        cfg = self._settings()
        ctx = ItemSearchContext(
            item_id=float(item["item_id"]),
            item_title=(item.get("item_title") or "").strip(),
            barcodeid=(item.get("barcodeid") or None),
            brand=(item.get("brand") or None),
            manual_id=int(item["manual_id"]) if item.get("manual_id") is not None else None,
        )

        if not dry_run:
            self.repo.upsert_status(
                item_id,
                manual_id=ctx.manual_id,
                status="SEARCHING",
                mark_searched=True,
            )
            self.db.commit()

        providers = build_providers(cfg)
        if not providers:
            if not dry_run:
                self.repo.upsert_status(
                    item_id,
                    manual_id=ctx.manual_id,
                    status="FAILED",
                    last_error="No image providers enabled",
                    mark_searched=True,
                )
                self.repo.add_error(
                    {
                        "item_id": item_id,
                        "job_id": None,
                        "error_code": "PROVIDER_UNAVAILABLE",
                        "error_message": "No image providers enabled",
                        "provider_name": None,
                    }
                )
                self.db.commit()
            raise ValueError("No image providers enabled")

        raw: list[ProductCandidate] = []
        timeout = float(cfg.get("timeout_seconds") or 15)
        retries = int(cfg.get("retry_count") or 2)
        rpm = int(cfg.get("requests_per_minute") or 12)
        conc = int(cfg.get("max_concurrent") or 1)
        no_match_min = int(cfg.get("no_match_min") or 50)

        for provider in providers:
            attempt = 0
            while attempt <= retries:
                attempt += 1
                acquired = False
                try:
                    RATE_LIMITER.acquire(requests_per_minute=rpm, max_concurrent=conc)
                    acquired = True
                    raw.extend(provider.search(ctx, timeout=timeout))
                    break
                except Exception as exc:
                    if attempt > retries:
                        self.repo.add_error(
                            {
                                "item_id": item_id,
                                "job_id": None,
                                "error_code": "PROVIDER_ERROR",
                                "error_message": str(exc)[:500],
                                "provider_name": provider.name,
                            }
                        )
                    else:
                        time.sleep(min(2 ** attempt, 8))
                finally:
                    if acquired:
                        RATE_LIMITER.release()

        scored: list[ProductCandidate] = []
        for cand in raw:
            result = score_product(ctx, cand)
            if result.hard_reject:
                continue
            cand.match_score = result.score
            scored.append(cand)
        scored.sort(key=lambda c: c.match_score, reverse=True)
        scored = [c for c in scored if c.match_score >= no_match_min][:12]

        session_key = uuid.uuid4().hex[:24]
        if not dry_run:
            self.repo.clear_candidates(item_id)
            self.repo.insert_candidates(
                [
                    {
                        "item_id": item_id,
                        "image_url": c.image_url[:1000],
                        "source_url": (c.product_url or "")[:1000] or None,
                        "source_name": (c.provider or "")[:80] or None,
                        "search_query": (c.search_query or "")[:200] or None,
                        "match_score": c.match_score,
                        "product_title": (c.product_name or "")[:200] or None,
                        "product_brand": (c.brand or "")[:120] or None,
                        "product_barcode": (c.barcode or "")[:50] or None,
                        "session_key": session_key,
                    }
                    for c in scored
                ]
            )

        if not scored:
            hint = "No reliable match from enabled providers. Try Search Again or upload manually."
            if raw:
                best_raw = max(
                    (score_product(ctx, c) for c in raw),
                    key=lambda r: r.score,
                    default=None,
                )
                if best_raw and not best_raw.hard_reject:
                    hint = (
                        f"Store returned {len(raw)} image(s) but best score was {best_raw.score} "
                        f"(minimum {no_match_min}). Lower “Min candidate score” in Settings or upload manually."
                    )
            if not (ctx.barcodeid or "").strip() or str(ctx.barcodeid).strip() in ("0", ""):
                hint = "This item has no barcode — name search was used. Upload manually if nothing matches."
            if not dry_run:
                self.repo.upsert_status(
                    item_id,
                    manual_id=ctx.manual_id,
                    status="FAILED",
                    last_error="No image found",
                    last_search_query=(ctx.barcodeid or ctx.item_title or "")[:200],
                    mark_searched=True,
                )
                self.repo.add_error(
                    {
                        "item_id": item_id,
                        "job_id": None,
                        "error_code": "NO_IMAGE_FOUND",
                        "error_message": "No image found from enabled providers",
                        "provider_name": None,
                    }
                )
                self.repo.add_audit(
                    {
                        "item_id": item_id,
                        "image_id": None,
                        "action": "SEARCH_FAILED",
                        "source_name": None,
                        "detail": hint,
                        "user_id": user_id,
                        "username": username,
                    }
                )
                self.db.commit()
            return {
                "found": False,
                "hint": hint,
                "candidates": [],
                "dry_run": dry_run,
                "detail": None if dry_run else self.item_detail(item_id),
            }

        best = scored[0]
        auto_min = int(cfg.get("auto_accept_min") or 90)
        review_min = int(cfg.get("review_min") or 75)
        decision = decide_status(
            best.match_score,
            auto_accept_min=auto_min,
            review_min=review_min,
            no_match_min=no_match_min,
        )

        linked = None
        if not dry_run and decision == "AUTO_APPROVED" and bool(cfg.get("download_enabled", True)):
            try:
                linked = self._link_candidate(
                    item,
                    best,
                    status="APPROVED",
                    make_primary=True,
                    user_id=user_id,
                    username=username,
                    cfg=cfg,
                )
            except Exception as exc:
                decision = "NEEDS_REVIEW"
                self.repo.add_error(
                    {
                        "item_id": item_id,
                        "job_id": None,
                        "error_code": "DOWNLOAD_FAILED",
                        "error_message": str(exc)[:500],
                        "provider_name": best.provider,
                    }
                )

        if not dry_run:
            item_status = "FAILED"
            if decision == "AUTO_APPROVED" and linked:
                item_status = "APPROVED"
            elif decision in ("REVIEW_RECOMMENDED", "NEEDS_REVIEW"):
                item_status = "NEEDS_REVIEW"
            elif scored:
                item_status = "IMAGE_FOUND"

            self.repo.upsert_status(
                item_id,
                manual_id=ctx.manual_id,
                status=item_status,
                primary_image_id=linked["image_id"] if linked else None,
                last_match_score=best.match_score,
                last_source_name=best.provider,
                last_search_query=(best.search_query or "")[:200],
                last_error=None,
                mark_searched=True,
            )
            self.repo.add_audit(
                {
                    "item_id": item_id,
                    "image_id": linked["image_id"] if linked else None,
                    "action": "IMAGE_FOUND" if scored else "SEARCH_FAILED",
                    "source_name": best.provider,
                    "detail": f"score={best.match_score}; decision={decision}",
                    "user_id": user_id,
                    "username": username,
                }
            )
            self.db.commit()

        return {
            "found": True,
            "decision": decision,
            "best_score": best.match_score,
            "auto_linked": bool(linked),
            "dry_run": dry_run,
            "candidates": [
                {
                    "image_url": c.image_url,
                    "source_url": c.product_url,
                    "source_name": c.provider,
                    "match_score": c.match_score,
                    "product_title": c.product_name,
                    "product_brand": c.brand,
                    "product_barcode": c.barcode,
                    "search_query": c.search_query,
                    "search_level": c.search_level,
                }
                for c in scored
            ],
            "detail": None if dry_run else self.item_detail(item_id),
        }

    def _link_candidate(
        self,
        item: dict[str, Any],
        cand: ProductCandidate | ImageCandidate,
        *,
        status: str,
        make_primary: bool,
        user_id: int | None,
        username: str | None,
        cfg: dict[str, Any],
    ) -> dict[str, Any]:
        legacy = cand.to_legacy() if isinstance(cand, ProductCandidate) else cand
        item_id = float(item["item_id"])
        dup = self.repo.find_duplicate(
            item_id, image_url=legacy.image_url, source_url=legacy.source_url
        )
        if dup:
            if make_primary:
                self.repo.clear_primary(item_id)
                self.repo.update_image_status(int(dup["image_id"]), status, is_primary=True)
            return {"image_id": int(dup["image_id"]), "duplicate": True}

        local_path = None
        thumb_path = None
        content_hash = None
        width = None
        height = None
        mime = None
        if bool(cfg.get("download_enabled", True)):
            validated = download_and_validate(
                legacy.image_url,
                item_id,
                timeout=float(cfg.get("timeout_seconds") or 15),
                min_width=int(cfg.get("min_width") or 80),
                min_height=int(cfg.get("min_height") or 80),
                filename_stem="primary" if make_primary else f"img_{int(time.time())}",
            )
            content_hash = validated.content_hash
            dup_hash = self.repo.find_duplicate(item_id, content_hash=content_hash)
            if dup_hash:
                if make_primary:
                    self.repo.clear_primary(item_id)
                    self.repo.update_image_status(int(dup_hash["image_id"]), status, is_primary=True)
                return {"image_id": int(dup_hash["image_id"]), "duplicate": True}
            local_path = validated.relative_primary
            thumb_path = validated.relative_thumb
            width = validated.width
            height = validated.height
            mime = validated.mime_type

        if make_primary:
            self.repo.clear_primary(item_id)

        image_id = self.repo.insert_image(
            {
                "item_id": item_id,
                "image_url": legacy.image_url[:1000],
                "local_image_path": local_path,
                "thumb_path": thumb_path,
                "source_url": (legacy.source_url or "")[:1000] or None,
                "source_name": (legacy.source_name or "")[:80] or None,
                "search_query": (legacy.search_query or "")[:200] or None,
                "match_score": legacy.match_score,
                "status": status,
                "is_primary": 1 if make_primary else 0,
                "content_hash": content_hash,
                "width_px": width,
                "height_px": height,
                "mime_type": mime,
                "created_by_user_id": user_id,
                "created_by_username": username,
            }
        )
        return {"image_id": image_id, "duplicate": False}

    def use_candidate(
        self,
        candidate_id: int,
        *,
        approve: bool = True,
        user_id: int | None = None,
        username: str | None = None,
    ) -> dict[str, Any]:
        cand_row = self.repo.get_candidate(candidate_id)
        if not cand_row:
            raise ValueError("Candidate not found")
        item = self.repo.get_fin_item(float(cand_row["item_id"]))
        if not item:
            raise ValueError("Item not found")
        cfg = self._settings()
        cand = ImageCandidate(
            image_url=cand_row["image_url"],
            source_url=cand_row.get("source_url"),
            source_name=cand_row.get("source_name") or "manual_pick",
            search_query=cand_row.get("search_query") or "",
            product_title=cand_row.get("product_title"),
            product_brand=cand_row.get("product_brand"),
            product_barcode=cand_row.get("product_barcode"),
            match_score=int(cand_row.get("match_score") or 0),
        )
        status = "APPROVED" if approve else "IMAGE_FOUND"
        linked = self._link_candidate(
            item,
            cand,
            status=status,
            make_primary=True,
            user_id=user_id,
            username=username,
            cfg=cfg,
        )
        self.repo.upsert_status(
            float(item["item_id"]),
            manual_id=int(item["manual_id"]) if item.get("manual_id") is not None else None,
            status=status if approve else "IMAGE_FOUND",
            primary_image_id=linked["image_id"],
            last_match_score=cand.match_score,
            last_source_name=cand.source_name,
            last_search_query=cand.search_query,
            mark_searched=True,
        )
        self.repo.add_audit(
            {
                "item_id": float(item["item_id"]),
                "image_id": linked["image_id"],
                "action": "IMAGE_APPROVED" if approve else "IMAGE_SELECTED",
                "source_name": cand.source_name,
                "detail": f"candidate_id={candidate_id}",
                "user_id": user_id,
                "username": username,
            }
        )
        self.db.commit()
        return self.item_detail(float(item["item_id"]))

    def reject_candidate(
        self, candidate_id: int, *, user_id: int | None = None, username: str | None = None
    ) -> dict[str, Any]:
        cand = self.repo.get_candidate(candidate_id)
        if not cand:
            raise ValueError("Candidate not found")
        item_id = float(cand["item_id"])
        self.db.execute(
            text("DELETE FROM dbo.item_image_candidates WHERE candidate_id = :cid"),
            {"cid": candidate_id},
        )
        self.repo.add_audit(
            {
                "item_id": item_id,
                "image_id": None,
                "action": "IMAGE_REJECTED",
                "source_name": cand.get("source_name"),
                "detail": f"candidate_id={candidate_id}",
                "user_id": user_id,
                "username": username,
            }
        )
        self.db.commit()
        return self.item_detail(item_id)

    def approve_image(
        self, image_id: int, *, user_id: int | None = None, username: str | None = None
    ) -> dict[str, Any]:
        img = self.repo.get_image(image_id)
        if not img:
            raise ValueError("Image not found")
        item_id = float(img["item_id"])
        self.repo.clear_primary(item_id)
        self.repo.update_image_status(image_id, "APPROVED", is_primary=True)
        item = self.repo.get_fin_item(item_id)
        self.repo.upsert_status(
            item_id,
            manual_id=int(item["manual_id"]) if item and item.get("manual_id") is not None else None,
            status="APPROVED",
            primary_image_id=image_id,
            last_match_score=img.get("match_score"),
            last_source_name=img.get("source_name"),
        )
        self.repo.add_audit(
            {
                "item_id": item_id,
                "image_id": image_id,
                "action": "IMAGE_APPROVED",
                "source_name": img.get("source_name"),
                "detail": None,
                "user_id": user_id,
                "username": username,
            }
        )
        self.db.commit()
        return self.item_detail(item_id)

    def delete_image(
        self, image_id: int, *, user_id: int | None = None, username: str | None = None
    ) -> dict[str, Any]:
        img = self.repo.delete_image(image_id)
        if not img:
            raise ValueError("Image not found")
        item_id = float(img["item_id"])
        remaining = self.repo.list_images(item_id)
        primary = next((x for x in remaining if x.get("is_primary")), remaining[0] if remaining else None)
        if primary:
            self.repo.upsert_status(
                item_id,
                status="APPROVED" if primary.get("status") == "APPROVED" else "IMAGE_FOUND",
                primary_image_id=int(primary["image_id"]),
            )
        else:
            self.repo.upsert_status(item_id, status="NO_IMAGE", primary_image_id=None, last_error=None)
            # clear primary_image_id explicitly
            self.db.execute(
                text(
                    """
                    UPDATE dbo.item_image_status
                    SET primary_image_id = NULL, status = N'NO_IMAGE', updated_at = SYSDATETIME()
                    WHERE item_id = :item_id
                    """
                ),
                {"item_id": item_id},
            )
        self.repo.add_audit(
            {
                "item_id": item_id,
                "image_id": image_id,
                "action": "IMAGE_DELETED",
                "source_name": img.get("source_name"),
                "detail": None,
                "user_id": user_id,
                "username": username,
            }
        )
        self.db.commit()
        return self.item_detail(item_id)

    def upload_manual(
        self,
        item_id: float,
        content: bytes,
        *,
        user_id: int | None = None,
        username: str | None = None,
    ) -> dict[str, Any]:
        item = self.repo.get_fin_item(item_id)
        if not item:
            raise ValueError("Item not found")
        cfg = self._settings()
        validated = validate_upload_bytes(
            content,
            item_id,
            min_width=int(cfg.get("min_width") or 80),
            min_height=int(cfg.get("min_height") or 80),
            filename_stem="manual",
        )
        dup = self.repo.find_duplicate(item_id, content_hash=validated.content_hash)
        if dup:
            raise ValueError("Duplicate image already linked to this item")
        self.repo.clear_primary(item_id)
        image_id = self.repo.insert_image(
            {
                "item_id": item_id,
                "image_url": None,
                "local_image_path": validated.relative_primary,
                "thumb_path": validated.relative_thumb,
                "source_url": None,
                "source_name": "manual_upload",
                "search_query": None,
                "match_score": 100,
                "status": "MANUAL",
                "is_primary": 1,
                "content_hash": validated.content_hash,
                "width_px": validated.width,
                "height_px": validated.height,
                "mime_type": validated.mime_type,
                "created_by_user_id": user_id,
                "created_by_username": username,
            }
        )
        self.repo.upsert_status(
            item_id,
            manual_id=int(item["manual_id"]) if item.get("manual_id") is not None else None,
            status="APPROVED",
            primary_image_id=image_id,
            last_match_score=100,
            last_source_name="manual_upload",
            mark_searched=True,
        )
        self.repo.add_audit(
            {
                "item_id": item_id,
                "image_id": image_id,
                "action": "MANUAL_UPLOAD",
                "source_name": "manual_upload",
                "detail": validated.relative_primary,
                "user_id": user_id,
                "username": username,
            }
        )
        self.db.commit()
        return self.item_detail(item_id)

    def resolve_public_url_for_manual_id(self, manual_id: int) -> Optional[str]:
        row = self.repo.primary_image_for_manual_id(manual_id)
        if not row:
            return None
        return public_image_url(row.get("thumb_path") or row.get("local_image_path")) or row.get(
            "image_url"
        )
