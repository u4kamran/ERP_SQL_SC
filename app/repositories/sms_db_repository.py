"""Read SMS outbox records from legacy SMS_DB_ table."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.schemas.sms_email_scheduler import SmsDbRecord


class SmsDbRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_latest_matching(self, keyword: str) -> Optional[SmsDbRecord]:
        keyword = (keyword or "").strip()
        if keyword:
            sql = text(
                """
                SELECT TOP 1
                    ID, BODY, SENDER, RECIPIENT, SENT, STATUS, SUBJECT, AddedDateTime
                FROM dbo.SMS_DB_
                WHERE BODY LIKE :pattern
                ORDER BY ID DESC
                """
            )
            row = self.db.execute(sql, {"pattern": f"%{keyword}%"}).mappings().first()
        else:
            sql = text(
                """
                SELECT TOP 1
                    ID, BODY, SENDER, RECIPIENT, SENT, STATUS, SUBJECT, AddedDateTime
                FROM dbo.SMS_DB_
                ORDER BY ID DESC
                """
            )
            row = self.db.execute(sql).mappings().first()

        if not row:
            return None
        return self._map_row(row)

    def get_by_id(self, record_id: int) -> Optional[SmsDbRecord]:
        sql = text(
            """
            SELECT ID, BODY, SENDER, RECIPIENT, SENT, STATUS, SUBJECT, AddedDateTime
            FROM dbo.SMS_DB_
            WHERE ID = :record_id
            """
        )
        row = self.db.execute(sql, {"record_id": record_id}).mappings().first()
        if not row:
            return None
        return self._map_row(row)

    @staticmethod
    def _map_row(row) -> SmsDbRecord:
        return SmsDbRecord(
            id=int(row["ID"]),
            body=str(row["BODY"] or ""),
            sender=str(row["SENDER"] or ""),
            recipient=str(row["RECIPIENT"] or ""),
            sent=row["SENT"] if isinstance(row["SENT"], datetime) else datetime.min,
            status=int(row["STATUS"] or 0),
            subject=str(row["SUBJECT"] or ""),
            added_at=row["AddedDateTime"]
            if isinstance(row["AddedDateTime"], datetime)
            else datetime.min,
        )
