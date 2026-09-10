"""Item search aliases and anonymous search analytics."""

from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session


class ItemSearchSupportRepository:
    def __init__(self, db: Session):
        self.db = db

    def lookup_alias(self, alias_text: str) -> Optional[str]:
        key = (alias_text or "").strip().lower()
        if not key:
            return None
        row = self.db.execute(
            text(
                """
                SELECT TOP 1 expand_text
                FROM dbo.item_search_alias
                WHERE is_active = 1 AND LOWER(alias_text) = :alias_text
                """
            ),
            {"alias_text": key[:80]},
        ).fetchone()
        if not row:
            return None
        return str(row[0] or "").strip() or None

    def list_aliases(self) -> list[dict[str, Any]]:
        rows = self.db.execute(
            text(
                """
                SELECT id, alias_text, expand_text, is_active
                FROM dbo.item_search_alias
                ORDER BY alias_text
                """
            )
        ).mappings().all()
        return [dict(r) for r in rows]

    def upsert_alias(self, alias_text: str, expand_text: str) -> None:
        alias = (alias_text or "").strip().lower()[:80]
        expand = (expand_text or "").strip().lower()[:120]
        if not alias or not expand:
            raise ValueError("Alias and expand text are required.")
        existing = self.db.execute(
            text("SELECT id FROM dbo.item_search_alias WHERE LOWER(alias_text) = :alias_text"),
            {"alias_text": alias},
        ).fetchone()
        if existing:
            self.db.execute(
                text(
                    """
                    UPDATE dbo.item_search_alias
                    SET expand_text = :expand_text, is_active = 1
                    WHERE id = :id
                    """
                ),
                {"expand_text": expand, "id": int(existing[0])},
            )
        else:
            self.db.execute(
                text(
                    """
                    INSERT INTO dbo.item_search_alias (alias_text, expand_text, is_active)
                    VALUES (:alias_text, :expand_text, 1)
                    """
                ),
                {"alias_text": alias, "expand_text": expand},
            )
        self.db.flush()

    def delete_alias(self, alias_id: int) -> None:
        self.db.execute(
            text("DELETE FROM dbo.item_search_alias WHERE id = :id"),
            {"id": int(alias_id)},
        )
        self.db.flush()

    def log_search(
        self,
        *,
        query_text: str,
        cleaned_query: str,
        result_count: int,
        selected_manual_id: Optional[int] = None,
        channel: str = "web",
    ) -> None:
        try:
            self.db.execute(
                text(
                    """
                    INSERT INTO dbo.item_search_log (
                        query_text, cleaned_query, result_count, selected_manual_id, channel
                    )
                    VALUES (:query_text, :cleaned_query, :result_count, :selected_manual_id, :channel)
                    """
                ),
                {
                    "query_text": (query_text or "")[:120],
                    "cleaned_query": (cleaned_query or "")[:120],
                    "result_count": int(result_count),
                    "selected_manual_id": selected_manual_id,
                    "channel": (channel or "web")[:20],
                },
            )
            self.db.commit()
        except Exception:
            self.db.rollback()

    def no_result_report(self, *, days: int = 30, limit: int = 80) -> list[dict[str, Any]]:
        rows = self.db.execute(
            text(
                """
                SELECT TOP (:limit)
                    LOWER(LTRIM(RTRIM(ISNULL(cleaned_query, query_text)))) AS search_term,
                    COUNT(*) AS searches
                FROM dbo.item_search_log
                WHERE result_count = 0
                  AND created_at >= DATEADD(DAY, :neg_days, SYSDATETIME())
                  AND LEN(LTRIM(RTRIM(ISNULL(cleaned_query, query_text)))) >= 2
                GROUP BY LOWER(LTRIM(RTRIM(ISNULL(cleaned_query, query_text))))
                ORDER BY COUNT(*) DESC
                """
            ),
            {"neg_days": -max(1, min(int(days), 365)), "limit": max(1, min(int(limit), 200))},
        ).mappings().all()
        return [dict(r) for r in rows]
