"""Repository for dbo.CUST_SMS CRUD."""

from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


_SELECT_COLS = """
    CUST_ID AS cust_id,
    RTRIM(ISNULL(CUST_NAME, '')) AS cust_name,
    RTRIM(ISNULL(MOBILE_NO, '')) AS mobile_no,
    RTRIM(ISNULL(MOBILE_NO_TMP, '')) AS mobile_no_tmp,
    RTRIM(ISNULL(CUST_ADDRESS, '')) AS cust_address,
    STATUS AS status,
    ADDED_DATETIME AS added_datetime,
    RTRIM(ISNULL(STAR_RATING, '')) AS star_rating,
    RTRIM(ISNULL(STAR_RATING_VALUE, '')) AS star_rating_value,
    RTRIM(ISNULL(STAR_RATING_VISIT, '')) AS star_rating_visit,
    RTRIM(ISNULL(STAR_RATING_VISIT_VALUE, '')) AS star_rating_visit_value,
    RTRIM(ISNULL(STAR_RATING_TSALES, '')) AS star_rating_tsales,
    RTRIM(ISNULL(STAR_RATING_TSALES_VALUE, '')) AS star_rating_tsales_value
"""


class CustSmsRepository:
    def __init__(self, db: Session):
        self.db = db

    def count(self, *, search: str = "") -> int:
        where_sql, params = self._search_clause(search)
        row = self.db.execute(
            text(f"SELECT COUNT(1) AS cnt FROM dbo.CUST_SMS {where_sql}"),
            params,
        ).mappings().first()
        return int(row["cnt"] if row else 0)

    def list_rows(self, *, skip: int = 0, limit: int = 50, search: str = "") -> list[dict[str, Any]]:
        where_sql, params = self._search_clause(search)
        # SQL Server 2008-compatible paging (no OFFSET/FETCH)
        end_row = skip + limit
        params["start_row"] = skip + 1
        params["end_row"] = end_row
        rows = self.db.execute(
            text(
                f"""
                SELECT *
                FROM (
                    SELECT
                        {_SELECT_COLS},
                        ROW_NUMBER() OVER (ORDER BY ADDED_DATETIME DESC, CUST_ID DESC) AS rn
                    FROM dbo.CUST_SMS
                    {where_sql}
                ) AS ranked
                WHERE rn BETWEEN :start_row AND :end_row
                ORDER BY rn
                """
            ),
            params,
        ).mappings().all()
        return [dict(r) for r in rows]

    def get_by_id(self, cust_id: int) -> dict[str, Any] | None:
        row = self.db.execute(
            text(
                f"""
                SELECT {_SELECT_COLS}
                FROM dbo.CUST_SMS
                WHERE CUST_ID = :cust_id
                """
            ),
            {"cust_id": cust_id},
        ).mappings().first()
        return dict(row) if row else None

    def find_by_mobile(self, mobile_no: str, *, exclude_cust_id: int | None = None) -> dict[str, Any] | None:
        params: dict[str, Any] = {"mobile_no": mobile_no.strip()}
        exclude_sql = ""
        if exclude_cust_id is not None:
            exclude_sql = " AND CUST_ID <> :exclude_cust_id"
            params["exclude_cust_id"] = exclude_cust_id
        row = self.db.execute(
            text(
                f"""
                SELECT {_SELECT_COLS}
                FROM dbo.CUST_SMS
                WHERE RTRIM(MOBILE_NO) = :mobile_no
                {exclude_sql}
                """
            ),
            params,
        ).mappings().first()
        return dict(row) if row else None

    def create(self, data: dict[str, Any]) -> int:
        row = self.db.execute(
            text(
                """
                INSERT INTO dbo.CUST_SMS (
                    CUST_NAME,
                    MOBILE_NO,
                    MOBILE_NO_TMP,
                    CUST_ADDRESS,
                    STATUS,
                    ADDED_DATETIME,
                    STAR_RATING,
                    STAR_RATING_VALUE,
                    STAR_RATING_VISIT,
                    STAR_RATING_VISIT_VALUE,
                    STAR_RATING_TSALES,
                    STAR_RATING_TSALES_VALUE
                )
                OUTPUT INSERTED.CUST_ID
                VALUES (
                    :cust_name,
                    :mobile_no,
                    :mobile_no_tmp,
                    :cust_address,
                    :status,
                    GETDATE(),
                    :star_rating,
                    :star_rating_value,
                    :star_rating_visit,
                    :star_rating_visit_value,
                    :star_rating_tsales,
                    :star_rating_tsales_value
                )
                """
            ),
            data,
        ).first()
        self.db.commit()
        return int(row[0])

    def update(self, cust_id: int, data: dict[str, Any]) -> bool:
        result = self.db.execute(
            text(
                """
                UPDATE dbo.CUST_SMS
                SET
                    CUST_NAME = :cust_name,
                    MOBILE_NO = :mobile_no,
                    MOBILE_NO_TMP = :mobile_no_tmp,
                    CUST_ADDRESS = :cust_address,
                    STATUS = :status,
                    STAR_RATING = :star_rating,
                    STAR_RATING_VALUE = :star_rating_value,
                    STAR_RATING_VISIT = :star_rating_visit,
                    STAR_RATING_VISIT_VALUE = :star_rating_visit_value,
                    STAR_RATING_TSALES = :star_rating_tsales,
                    STAR_RATING_TSALES_VALUE = :star_rating_tsales_value
                WHERE CUST_ID = :cust_id
                """
            ),
            {**data, "cust_id": cust_id},
        )
        self.db.commit()
        return result.rowcount > 0

    def delete(self, cust_id: int) -> bool:
        result = self.db.execute(
            text("DELETE FROM dbo.CUST_SMS WHERE CUST_ID = :cust_id"),
            {"cust_id": cust_id},
        )
        self.db.commit()
        return result.rowcount > 0

    @staticmethod
    def _search_clause(search: str) -> tuple[str, dict[str, Any]]:
        search = (search or "").strip()
        if not search:
            return "", {}
        return (
            """
            WHERE (
                CUST_NAME LIKE :pattern
                OR MOBILE_NO LIKE :pattern
                OR MOBILE_NO_TMP LIKE :pattern
                OR CUST_ADDRESS LIKE :pattern
                OR CAST(CUST_ID AS VARCHAR(20)) LIKE :pattern
            )
            """,
            {"pattern": f"%{search}%"},
        )
