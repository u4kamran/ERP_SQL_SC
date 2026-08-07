"""ERP customer mobile contacts from dbo.CUST_SMS (+ optional GL link)."""

from __future__ import annotations

import re
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


def _row_to_dict(row) -> dict[str, Any]:
    return dict(row)


class CustomerContactsRepository:
    def __init__(self, db: Session):
        self.db = db

    def fetch_cust_sms_rows(self, *, q: str = "") -> list[dict[str, Any]]:
        q = (q or "").strip()
        params: dict[str, Any] = {}
        where_sql = ""
        if q:
            where_sql = """
                WHERE (
                    CUST_NAME LIKE :pattern
                    OR MOBILE_NO LIKE :pattern
                    OR MOBILE_NO_TMP LIKE :pattern
                    OR CUST_ADDRESS LIKE :pattern
                    OR CAST(CUST_ID AS VARCHAR(20)) LIKE :pattern
                )
            """
            params["pattern"] = f"%{q}%"

        rows = self.db.execute(
            text(
                f"""
                SELECT
                    CUST_ID,
                    RTRIM(CUST_NAME) AS cust_name,
                    RTRIM(MOBILE_NO) AS mobile_no,
                    RTRIM(MOBILE_NO_TMP) AS mobile_no_tmp,
                    RTRIM(CUST_ADDRESS) AS cust_address,
                    ADDED_DATETIME,
                    STATUS
                FROM dbo.CUST_SMS
                {where_sql}
                ORDER BY ADDED_DATETIME DESC, CUST_ID DESC
                """
            ),
            params,
        ).mappings().all()
        return [_row_to_dict(r) for r in rows]

    def fetch_cust_sms_by_phone(self, phone_core: str) -> list[dict[str, Any]]:
        """Find CUST_SMS rows matching the last 10 digits of a mobile."""
        phone_core = re.sub(r"\D", "", phone_core or "")
        if len(phone_core) > 10:
            phone_core = phone_core[-10:]
        if len(phone_core) < 10:
            return []

        pattern = f"%{phone_core}%"
        rows = self.db.execute(
            text(
                """
                SELECT
                    CUST_ID,
                    RTRIM(CUST_NAME) AS cust_name,
                    RTRIM(MOBILE_NO) AS mobile_no,
                    RTRIM(MOBILE_NO_TMP) AS mobile_no_tmp,
                    RTRIM(CUST_ADDRESS) AS cust_address,
                    ADDED_DATETIME,
                    STATUS
                FROM dbo.CUST_SMS
                WHERE MOBILE_NO LIKE :pattern
                   OR MOBILE_NO_TMP LIKE :pattern
                ORDER BY ADDED_DATETIME DESC, CUST_ID DESC
                """
            ),
            {"pattern": pattern},
        ).mappings().all()
        return [_row_to_dict(r) for r in rows]

    def fetch_cust_sms_by_id(self, cust_sms_id: int) -> dict[str, Any] | None:
        row = self.db.execute(
            text(
                """
                SELECT
                    CUST_ID,
                    RTRIM(CUST_NAME) AS cust_name,
                    RTRIM(MOBILE_NO) AS mobile_no,
                    RTRIM(MOBILE_NO_TMP) AS mobile_no_tmp,
                    RTRIM(CUST_ADDRESS) AS cust_address,
                    ADDED_DATETIME,
                    STATUS
                FROM dbo.CUST_SMS
                WHERE CUST_ID = :cust_sms_id
                """
            ),
            {"cust_sms_id": cust_sms_id},
        ).mappings().first()
        return _row_to_dict(row) if row else None

    def fetch_gl_phone_index_rows(self) -> list[dict[str, Any]]:
        rows = self.db.execute(
            text(
                """
                SELECT
                    g1.ac_id,
                    RTRIM(g1.ac_title) AS name,
                    RTRIM(g1.CREATED_BY) AS created_by,
                    g1.cbal,
                    RTRIM(g5.PHONE) AS cust_phone,
                    RTRIM(g5.CONTACT_PERSON) AS cust_contact,
                    RTRIM(g6.PHONE) AS vend_phone,
                    RTRIM(g6.CONTACT_PERSON) AS vend_contact
                FROM Gl0001 g1
                LEFT JOIN GL0005 g5 ON g5.CUSTOMER_ID = g1.ac_id
                LEFT JOIN GL0006 g6 ON g6.VENDOR_ID = g1.ac_id
                WHERE g1.ac_level = 4
                """
            )
        ).mappings().all()
        return [_row_to_dict(r) for r in rows]
