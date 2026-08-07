"""Database operations for finalized customer-import records."""

from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


class CustomerImportRepository:
    def __init__(self, db: Session):
        self.db = db

    def find_by_mobile_key(self, mobile_key: str) -> dict[str, Any] | None:
        row = self.db.execute(
            text(
                """
                SELECT TOP 1
                    CUST_ID AS cust_id,
                    RTRIM(ISNULL(CUST_NAME, '')) AS cust_name,
                    RTRIM(ISNULL(MOBILE_NO, '')) AS mobile_no
                FROM dbo.CUST_SMS
                WHERE LEN(LTRIM(RTRIM(ISNULL(MOBILE_NO, '')))) >= 10
                  AND RIGHT(
                      REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
                          LTRIM(RTRIM(MOBILE_NO)),
                          ' ', ''), '-', ''), '(', ''), ')', ''), '+', ''),
                      10
                  ) = :mobile_key
                ORDER BY CUST_ID DESC
                """
            ),
            {"mobile_key": mobile_key},
        ).mappings().first()
        return dict(row) if row else None

    def create_customer(
        self,
        *,
        name: str,
        mobile: str,
        address: str,
    ) -> int:
        row = self.db.execute(
            text(
                """
                INSERT INTO dbo.CUST_SMS (
                    CUST_NAME, MOBILE_NO, MOBILE_NO_TMP, CUST_ADDRESS,
                    STATUS, ADDED_DATETIME,
                    STAR_RATING, STAR_RATING_VALUE,
                    STAR_RATING_VISIT, STAR_RATING_VISIT_VALUE,
                    STAR_RATING_TSALES, STAR_RATING_TSALES_VALUE
                )
                OUTPUT INSERTED.CUST_ID
                VALUES (
                    :name, :mobile, NULL, :address,
                    1, GETDATE(),
                    NULL, NULL, NULL, NULL, NULL, NULL
                )
                """
            ),
            {"name": name, "mobile": mobile, "address": address},
        ).first()
        return int(row[0])
