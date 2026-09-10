"""Data access for item image tables. FIN_ITEM is SELECT-only."""

from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session


class ItemImagesRepository:
    def __init__(self, db: Session):
        self.db = db

    # ----- settings -----
    def get_settings(self) -> dict[str, Any]:
        row = self.db.execute(
            text(
                """
                SELECT TOP 1
                    auto_accept_min, review_min, no_match_min, requests_per_minute, max_concurrent,
                    timeout_seconds, retry_count, min_width, min_height,
                    download_enabled,
                    naheed_enabled, metro_enabled, carrefour_enabled, imtiaz_enabled, alfatah_enabled,
                    open_food_facts_enabled, upcitemdb_enabled,
                    updated_by_username, updated_at
                FROM dbo.item_image_settings WHERE id = 1
                """
            )
        ).mappings().first()
        if not row:
            return {}
        return dict(row)

    def update_settings(self, fields: dict[str, Any], *, user_id: int | None, username: str | None) -> dict[str, Any]:
        allowed = {
            "auto_accept_min",
            "review_min",
            "no_match_min",
            "requests_per_minute",
            "max_concurrent",
            "timeout_seconds",
            "retry_count",
            "min_width",
            "min_height",
            "download_enabled",
            "naheed_enabled",
            "metro_enabled",
            "carrefour_enabled",
            "imtiaz_enabled",
            "alfatah_enabled",
            "open_food_facts_enabled",
            "upcitemdb_enabled",
        }
        sets = []
        params: dict[str, Any] = {"uid": user_id, "uname": username}
        for key, val in fields.items():
            if key not in allowed or val is None:
                continue
            sets.append(f"{key} = :{key}")
            params[key] = val
        if not sets:
            return self.get_settings()
        sets.append("updated_by_user_id = :uid")
        sets.append("updated_by_username = :uname")
        sets.append("updated_at = SYSDATETIME()")
        self.db.execute(
            text(f"UPDATE dbo.item_image_settings SET {', '.join(sets)} WHERE id = 1"),
            params,
        )
        return self.get_settings()

    # ----- FIN_ITEM read-only -----
    def get_fin_item(self, item_id: float) -> Optional[dict[str, Any]]:
        row = self.db.execute(
            text(
                """
                SELECT TOP 1
                    i.ITEM_ID AS item_id,
                    i.manualid AS manual_id,
                    i.ITEM_TITLE AS item_title,
                    i.ITEM_SHORT AS item_short,
                    i.barcodeid AS barcodeid,
                    i.BARCODEID_WS AS barcodeid_ws,
                    i.co_id AS co_id,
                    c.co_TITLE AS brand
                FROM dbo.FIN_ITEM i
                LEFT JOIN dbo.Co c ON c.Co_id = i.co_id
                WHERE i.ITEM_ID = :item_id
                """
            ),
            {"item_id": item_id},
        ).mappings().first()
        return dict(row) if row else None

    def list_items_page(
        self,
        *,
        page: int = 1,
        page_size: int = 25,
        q: str | None = None,
        status_filter: str | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        page = max(1, page)
        page_size = max(1, min(100, page_size))
        offset = (page - 1) * page_size
        params: dict[str, Any] = {"offset": offset, "limit": page_size}
        where = ["1=1"]
        if q:
            params["q"] = f"%{q.strip()[:80]}%"
            params["q_exact"] = q.strip()[:80]
            where.append(
                """(
                    i.ITEM_TITLE LIKE :q
                    OR i.barcodeid LIKE :q
                    OR CAST(i.manualid AS VARCHAR(20)) = :q_exact
                    OR CAST(CAST(i.ITEM_ID AS BIGINT) AS VARCHAR(30)) = :q_exact
                )"""
            )

        status_join = "LEFT JOIN dbo.item_image_status s ON s.item_id = i.ITEM_ID"
        if status_filter == "NO_IMAGE":
            where.append("(s.status IS NULL OR s.status = N'NO_IMAGE')")
        elif status_filter and status_filter != "ALL":
            where.append("s.status = :status_filter")
            params["status_filter"] = status_filter

        where_sql = " AND ".join(where)
        count_row = self.db.execute(
            text(
                f"""
                SELECT COUNT(1) AS cnt
                FROM dbo.FIN_ITEM i
                {status_join}
                WHERE {where_sql}
                """
            ),
            params,
        ).mappings().first()
        total = int(count_row["cnt"] if count_row else 0)

        params["start_row"] = offset + 1
        params["end_row"] = offset + page_size
        rows = self.db.execute(
            text(
                f"""
                SELECT * FROM (
                    SELECT
                        i.ITEM_ID AS item_id,
                        i.manualid AS manual_id,
                        i.ITEM_TITLE AS item_title,
                        i.barcodeid AS barcodeid,
                        ISNULL(s.status, N'NO_IMAGE') AS image_status,
                        s.last_match_score AS match_score,
                        s.last_source_name AS source_name,
                        s.primary_image_id AS primary_image_id,
                        img.image_url AS image_url,
                        img.local_image_path AS local_image_path,
                        img.thumb_path AS thumb_path,
                        ROW_NUMBER() OVER (ORDER BY i.ITEM_TITLE, i.ITEM_ID) AS rn
                    FROM dbo.FIN_ITEM i
                    {status_join}
                    LEFT JOIN dbo.item_images img ON img.image_id = s.primary_image_id
                    WHERE {where_sql}
                ) x
                WHERE x.rn BETWEEN :start_row AND :end_row
                ORDER BY x.rn
                """
            ),
            params,
        ).mappings().all()
        return [dict(r) for r in rows], total

    def list_item_ids_for_bulk(
        self,
        *,
        status_filter: str | None = None,
        q: str | None = None,
        selected_ids: list[float] | None = None,
        limit: int | None = None,
        missing_only: bool = True,
    ) -> list[float]:
        params: dict[str, Any] = {}
        where = ["1=1"]
        status_join = "LEFT JOIN dbo.item_image_status s ON s.item_id = i.ITEM_ID"
        if selected_ids:
            # Build IN list safely
            placeholders = []
            for idx, iid in enumerate(selected_ids[:2000]):
                key = f"id{idx}"
                placeholders.append(f":{key}")
                params[key] = float(iid)
            where.append(f"i.ITEM_ID IN ({', '.join(placeholders)})")
        else:
            if missing_only or status_filter in (None, "NO_IMAGE", "FAILED"):
                where.append(
                    "(s.status IS NULL OR s.status IN (N'NO_IMAGE', N'FAILED'))"
                )
            elif status_filter and status_filter != "ALL":
                where.append("s.status = :status_filter")
                params["status_filter"] = status_filter
            if q:
                params["q"] = f"%{q.strip()[:80]}%"
                where.append("(i.ITEM_TITLE LIKE :q OR i.barcodeid LIKE :q)")

        top = f"TOP ({int(limit)})" if limit else "TOP (5000)"
        rows = self.db.execute(
            text(
                f"""
                SELECT {top} i.ITEM_ID AS item_id
                FROM dbo.FIN_ITEM i
                {status_join}
                WHERE {' AND '.join(where)}
                ORDER BY i.ITEM_ID
                """
            ),
            params,
        ).mappings().all()
        return [float(r["item_id"]) for r in rows]

    # ----- status / images -----
    def upsert_status(
        self,
        item_id: float,
        *,
        manual_id: int | None = None,
        status: str,
        primary_image_id: int | None = None,
        last_match_score: int | None = None,
        last_source_name: str | None = None,
        last_search_query: str | None = None,
        last_error: str | None = None,
        mark_searched: bool = False,
    ) -> None:
        self.db.execute(
            text(
                """
                MERGE dbo.item_image_status AS t
                USING (SELECT :item_id AS item_id) AS s
                ON t.item_id = s.item_id
                WHEN MATCHED THEN UPDATE SET
                    manual_id = COALESCE(:manual_id, t.manual_id),
                    status = :status,
                    primary_image_id = COALESCE(:primary_image_id, t.primary_image_id),
                    last_match_score = COALESCE(:last_match_score, t.last_match_score),
                    last_source_name = COALESCE(:last_source_name, t.last_source_name),
                    last_search_query = COALESCE(:last_search_query, t.last_search_query),
                    last_error = :last_error,
                    last_searched_at = CASE WHEN :mark_searched = 1 THEN SYSDATETIME() ELSE t.last_searched_at END,
                    updated_at = SYSDATETIME()
                WHEN NOT MATCHED THEN INSERT (
                    item_id, manual_id, status, primary_image_id, last_match_score,
                    last_source_name, last_search_query, last_error, last_searched_at
                ) VALUES (
                    :item_id, :manual_id, :status, :primary_image_id, :last_match_score,
                    :last_source_name, :last_search_query, :last_error,
                    CASE WHEN :mark_searched = 1 THEN SYSDATETIME() ELSE NULL END
                );
                """
            ),
            {
                "item_id": item_id,
                "manual_id": manual_id,
                "status": status,
                "primary_image_id": primary_image_id,
                "last_match_score": last_match_score,
                "last_source_name": last_source_name,
                "last_search_query": last_search_query,
                "last_error": last_error,
                "mark_searched": 1 if mark_searched else 0,
            },
        )

    def get_status(self, item_id: float) -> Optional[dict[str, Any]]:
        row = self.db.execute(
            text("SELECT * FROM dbo.item_image_status WHERE item_id = :item_id"),
            {"item_id": item_id},
        ).mappings().first()
        return dict(row) if row else None

    def has_approved_primary(self, item_id: float) -> bool:
        row = self.db.execute(
            text(
                """
                SELECT TOP 1 image_id
                FROM dbo.item_images
                WHERE item_id = :item_id AND is_primary = 1 AND status = N'APPROVED'
                """
            ),
            {"item_id": item_id},
        ).first()
        return row is not None

    def find_duplicate(
        self,
        item_id: float,
        *,
        image_url: str | None = None,
        source_url: str | None = None,
        content_hash: str | None = None,
    ) -> Optional[dict[str, Any]]:
        row = self.db.execute(
            text(
                """
                SELECT TOP 1 *
                FROM dbo.item_images
                WHERE item_id = :item_id
                  AND (
                        (:image_url IS NOT NULL AND image_url = :image_url)
                     OR (:source_url IS NOT NULL AND source_url = :source_url)
                     OR (:content_hash IS NOT NULL AND content_hash = :content_hash)
                  )
                """
            ),
            {
                "item_id": item_id,
                "image_url": image_url,
                "source_url": source_url,
                "content_hash": content_hash,
            },
        ).mappings().first()
        return dict(row) if row else None

    def clear_primary(self, item_id: float) -> None:
        self.db.execute(
            text("UPDATE dbo.item_images SET is_primary = 0, updated_at = SYSDATETIME() WHERE item_id = :item_id"),
            {"item_id": item_id},
        )

    def insert_image(self, payload: dict[str, Any]) -> int:
        row = self.db.execute(
            text(
                """
                INSERT INTO dbo.item_images (
                    item_id, image_url, local_image_path, thumb_path, source_url, source_name,
                    search_query, match_score, status, is_primary, content_hash,
                    width_px, height_px, mime_type, created_by_user_id, created_by_username
                )
                OUTPUT INSERTED.image_id
                VALUES (
                    :item_id, :image_url, :local_image_path, :thumb_path, :source_url, :source_name,
                    :search_query, :match_score, :status, :is_primary, :content_hash,
                    :width_px, :height_px, :mime_type, :created_by_user_id, :created_by_username
                )
                """
            ),
            payload,
        ).first()
        return int(row[0])

    def get_image(self, image_id: int) -> Optional[dict[str, Any]]:
        row = self.db.execute(
            text("SELECT * FROM dbo.item_images WHERE image_id = :image_id"),
            {"image_id": image_id},
        ).mappings().first()
        return dict(row) if row else None

    def list_images(self, item_id: float) -> list[dict[str, Any]]:
        rows = self.db.execute(
            text(
                """
                SELECT * FROM dbo.item_images
                WHERE item_id = :item_id
                ORDER BY is_primary DESC, match_score DESC, image_id DESC
                """
            ),
            {"item_id": item_id},
        ).mappings().all()
        return [dict(r) for r in rows]

    def update_image_status(self, image_id: int, status: str, *, is_primary: bool | None = None) -> None:
        if is_primary is None:
            self.db.execute(
                text(
                    "UPDATE dbo.item_images SET status = :status, updated_at = SYSDATETIME() WHERE image_id = :image_id"
                ),
                {"image_id": image_id, "status": status},
            )
        else:
            self.db.execute(
                text(
                    """
                    UPDATE dbo.item_images
                    SET status = :status, is_primary = :is_primary, updated_at = SYSDATETIME()
                    WHERE image_id = :image_id
                    """
                ),
                {"image_id": image_id, "status": status, "is_primary": 1 if is_primary else 0},
            )

    def delete_image(self, image_id: int) -> Optional[dict[str, Any]]:
        row = self.get_image(image_id)
        if not row:
            return None
        self.db.execute(
            text("DELETE FROM dbo.item_images WHERE image_id = :image_id"),
            {"image_id": image_id},
        )
        return row

    def clear_candidates(self, item_id: float) -> None:
        self.db.execute(
            text("DELETE FROM dbo.item_image_candidates WHERE item_id = :item_id"),
            {"item_id": item_id},
        )

    def insert_candidates(self, rows: list[dict[str, Any]]) -> None:
        for r in rows:
            self.db.execute(
                text(
                    """
                    INSERT INTO dbo.item_image_candidates (
                        item_id, image_url, source_url, source_name, search_query,
                        match_score, product_title, product_brand, product_barcode, session_key
                    ) VALUES (
                        :item_id, :image_url, :source_url, :source_name, :search_query,
                        :match_score, :product_title, :product_brand, :product_barcode, :session_key
                    )
                    """
                ),
                r,
            )

    def list_candidates(self, item_id: float) -> list[dict[str, Any]]:
        rows = self.db.execute(
            text(
                """
                SELECT * FROM dbo.item_image_candidates
                WHERE item_id = :item_id
                ORDER BY match_score DESC, candidate_id ASC
                """
            ),
            {"item_id": item_id},
        ).mappings().all()
        return [dict(r) for r in rows]

    def get_candidate(self, candidate_id: int) -> Optional[dict[str, Any]]:
        row = self.db.execute(
            text("SELECT * FROM dbo.item_image_candidates WHERE candidate_id = :cid"),
            {"cid": candidate_id},
        ).mappings().first()
        return dict(row) if row else None

    def add_audit(self, payload: dict[str, Any]) -> None:
        self.db.execute(
            text(
                """
                INSERT INTO dbo.item_image_audit (
                    item_id, image_id, action, source_name, detail, user_id, username
                ) VALUES (
                    :item_id, :image_id, :action, :source_name, :detail, :user_id, :username
                )
                """
            ),
            payload,
        )

    def add_error(self, payload: dict[str, Any]) -> None:
        self.db.execute(
            text(
                """
                INSERT INTO dbo.item_image_errors (
                    item_id, job_id, error_code, error_message, provider_name
                ) VALUES (
                    :item_id, :job_id, :error_code, :error_message, :provider_name
                )
                """
            ),
            payload,
        )

    def dashboard_stats(self) -> dict[str, Any]:
        total = self.db.execute(text("SELECT COUNT(1) AS c FROM dbo.FIN_ITEM")).scalar() or 0
        rows = self.db.execute(
            text(
                """
                SELECT status, COUNT(1) AS c
                FROM dbo.item_image_status
                GROUP BY status
                """
            )
        ).mappings().all()
        by_status = {r["status"]: int(r["c"]) for r in rows}
        with_images = int(by_status.get("APPROVED", 0)) + int(by_status.get("IMAGE_FOUND", 0))
        # Coverage = approved / total
        approved = int(by_status.get("APPROVED", 0))
        tracked = sum(by_status.values())
        without = max(0, int(total) - tracked) + int(by_status.get("NO_IMAGE", 0))
        # Items never in status table count as without images
        never = max(0, int(total) - tracked)
        without_images = never + int(by_status.get("NO_IMAGE", 0))
        coverage = round((approved / float(total)) * 100.0, 1) if total else 0.0
        return {
            "total_items": int(total),
            "with_images": with_images,
            "without_images": without_images,
            "approved": approved,
            "needs_review": int(by_status.get("NEEDS_REVIEW", 0)),
            "failed": int(by_status.get("FAILED", 0)),
            "searching": int(by_status.get("SEARCHING", 0)),
            "image_found": int(by_status.get("IMAGE_FOUND", 0)),
            "coverage_pct": coverage,
            "by_status": by_status,
        }

    # ----- jobs -----
    def create_job(self, payload: dict[str, Any]) -> int:
        row = self.db.execute(
            text(
                """
                INSERT INTO dbo.item_image_jobs (
                    scope, status, dry_run, test_limit, total_count,
                    filter_status, filter_query, created_by_user_id, created_by_username
                )
                OUTPUT INSERTED.job_id
                VALUES (
                    :scope, N'PENDING', :dry_run, :test_limit, :total_count,
                    :filter_status, :filter_query, :created_by_user_id, :created_by_username
                )
                """
            ),
            payload,
        ).first()
        return int(row[0])

    def add_job_items(self, job_id: int, item_ids: list[float]) -> None:
        for iid in item_ids:
            self.db.execute(
                text(
                    """
                    INSERT INTO dbo.item_image_job_items (job_id, item_id, status)
                    VALUES (:job_id, :item_id, N'PENDING')
                    """
                ),
                {"job_id": job_id, "item_id": iid},
            )

    def get_job(self, job_id: int) -> Optional[dict[str, Any]]:
        row = self.db.execute(
            text("SELECT * FROM dbo.item_image_jobs WHERE job_id = :job_id"),
            {"job_id": job_id},
        ).mappings().first()
        return dict(row) if row else None

    def set_job_status(self, job_id: int, status: str, **extra: Any) -> None:
        sets = ["status = :status", "updated_at = SYSDATETIME()"]
        params: dict[str, Any] = {"job_id": job_id, "status": status}
        for key in (
            "processed_count",
            "found_count",
            "approved_count",
            "review_count",
            "not_found_count",
            "failed_count",
            "started_at",
            "finished_at",
        ):
            if key in extra and extra[key] is not None:
                if key in ("started_at", "finished_at") and extra[key] is True:
                    sets.append(f"{key} = SYSDATETIME()")
                else:
                    sets.append(f"{key} = :{key}")
                    params[key] = extra[key]
        self.db.execute(
            text(f"UPDATE dbo.item_image_jobs SET {', '.join(sets)} WHERE job_id = :job_id"),
            params,
        )

    def claim_next_job_item(self, job_id: int) -> Optional[dict[str, Any]]:
        row = self.db.execute(
            text(
                """
                SELECT TOP 1 job_item_id, item_id
                FROM dbo.item_image_job_items WITH (UPDLOCK, READPAST)
                WHERE job_id = :job_id AND status = N'PENDING'
                ORDER BY job_item_id
                """
            ),
            {"job_id": job_id},
        ).mappings().first()
        if not row:
            return None
        self.db.execute(
            text(
                """
                UPDATE dbo.item_image_job_items
                SET status = N'PROCESSING'
                WHERE job_item_id = :jid
                """
            ),
            {"jid": row["job_item_id"]},
        )
        return dict(row)

    def finish_job_item(
        self,
        job_item_id: int,
        *,
        status: str,
        result_status: str | None = None,
        match_score: int | None = None,
        error_message: str | None = None,
    ) -> None:
        self.db.execute(
            text(
                """
                UPDATE dbo.item_image_job_items
                SET status = :status,
                    result_status = :result_status,
                    match_score = :match_score,
                    error_message = :error_message,
                    processed_at = SYSDATETIME()
                WHERE job_item_id = :job_item_id
                """
            ),
            {
                "job_item_id": job_item_id,
                "status": status,
                "result_status": result_status,
                "match_score": match_score,
                "error_message": error_message,
            },
        )

    def bump_job_counters(self, job_id: int, result_status: str) -> None:
        col = {
            "APPROVED": "approved_count",
            "NEEDS_REVIEW": "review_count",
            "IMAGE_FOUND": "found_count",
            "FAILED": "failed_count",
            "NO_IMAGE": "not_found_count",
        }.get(result_status, "found_count")
        self.db.execute(
            text(
                f"""
                UPDATE dbo.item_image_jobs
                SET processed_count = processed_count + 1,
                    {col} = {col} + 1,
                    updated_at = SYSDATETIME()
                WHERE job_id = :job_id
                """
            ),
            {"job_id": job_id},
        )

    def active_job(self) -> Optional[dict[str, Any]]:
        row = self.db.execute(
            text(
                """
                SELECT TOP 1 * FROM dbo.item_image_jobs
                WHERE status IN (N'PENDING', N'RUNNING', N'PAUSED')
                ORDER BY job_id DESC
                """
            )
        ).mappings().first()
        return dict(row) if row else None

    def primary_image_for_manual_id(self, manual_id: int) -> Optional[dict[str, Any]]:
        row = self.db.execute(
            text(
                """
                SELECT TOP 1 img.image_url, img.local_image_path, img.thumb_path, img.status
                FROM dbo.FIN_ITEM i
                INNER JOIN dbo.item_image_status s ON s.item_id = i.ITEM_ID
                INNER JOIN dbo.item_images img ON img.image_id = s.primary_image_id
                WHERE i.manualid = :manual_id
                  AND img.status IN (N'APPROVED', N'IMAGE_FOUND', N'MANUAL')
                """
            ),
            {"manual_id": manual_id},
        ).mappings().first()
        return dict(row) if row else None
