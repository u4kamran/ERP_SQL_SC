"""Repository for customer_app_otp + SMS_DB_ queue inserts."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


class CustomerAppOtpRepository:
    def __init__(self, db: Session):
        self.db = db

    def supersede_pending(self, mobile_key: str) -> None:
        self.db.execute(
            text(
                """
                UPDATE dbo.customer_app_otp
                SET status = N'SUPERSEDED'
                WHERE mobile_key = :mobile_key
                  AND status = N'PENDING'
                """
            ),
            {"mobile_key": mobile_key},
        )

    def count_recent_requests(self, mobile_key: str, *, window_minutes: int) -> int:
        row = self.db.execute(
            text(
                """
                SELECT COUNT(1) AS cnt
                FROM dbo.customer_app_otp
                WHERE mobile_key = :mobile_key
                  AND created_at >= DATEADD(minute, -:window_minutes, SYSDATETIME())
                """
            ),
            {"mobile_key": mobile_key, "window_minutes": window_minutes},
        ).mappings().first()
        return int(row["cnt"] if row else 0)

    def seconds_since_last_request(self, mobile_key: str) -> float | None:
        row = self.db.execute(
            text(
                """
                SELECT TOP 1
                    DATEDIFF(second, created_at, SYSDATETIME()) AS secs
                FROM dbo.customer_app_otp
                WHERE mobile_key = :mobile_key
                ORDER BY id DESC
                """
            ),
            {"mobile_key": mobile_key},
        ).mappings().first()
        if not row or row["secs"] is None:
            return None
        return float(row["secs"])

    def latest_pending(self, mobile_key: str) -> dict[str, Any] | None:
        row = self.db.execute(
            text(
                """
                SELECT TOP 1 *
                FROM dbo.customer_app_otp
                WHERE mobile_key = :mobile_key
                  AND status = N'PENDING'
                ORDER BY id DESC
                """
            ),
            {"mobile_key": mobile_key},
        ).mappings().first()
        return dict(row) if row else None

    def get_by_request_id(self, request_id: str) -> dict[str, Any] | None:
        row = self.db.execute(
            text(
                """
                SELECT TOP 1 *
                FROM dbo.customer_app_otp
                WHERE request_id = :request_id
                """
            ),
            {"request_id": request_id},
        ).mappings().first()
        return dict(row) if row else None

    def is_verified(self, mobile_key: str) -> bool:
        row = self.db.execute(
            text(
                """
                SELECT TOP 1 id
                FROM dbo.customer_app_otp
                WHERE mobile_key = :mobile_key
                  AND status = N'VERIFIED'
                  AND verified_until IS NOT NULL
                  AND verified_until > SYSDATETIME()
                ORDER BY verified_at DESC, id DESC
                """
            ),
            {"mobile_key": mobile_key},
        ).first()
        return row is not None

    def insert_otp(
        self,
        *,
        request_id: str,
        mobile_key: str,
        mobile_display: str,
        otp_hash: str,
        salt: str,
        expires_at: datetime,
        max_attempts: int,
        client_ip: str | None,
    ) -> int:
        row = self.db.execute(
            text(
                """
                INSERT INTO dbo.customer_app_otp (
                    request_id, mobile_key, mobile_display, otp_hash, salt,
                    created_at, expires_at, attempt_count, max_attempts,
                    status, client_ip
                )
                OUTPUT INSERTED.id
                VALUES (
                    :request_id, :mobile_key, :mobile_display, :otp_hash, :salt,
                    SYSDATETIME(), :expires_at, 0, :max_attempts,
                    N'PENDING', :client_ip
                )
                """
            ),
            {
                "request_id": request_id,
                "mobile_key": mobile_key,
                "mobile_display": mobile_display,
                "otp_hash": otp_hash,
                "salt": salt,
                "expires_at": expires_at,
                "max_attempts": max_attempts,
                "client_ip": client_ip,
            },
        ).first()
        return int(row[0])

    def attach_sms_id(self, otp_id: int, sms_db_id: int) -> None:
        self.db.execute(
            text(
                """
                UPDATE dbo.customer_app_otp
                SET sms_db_id = :sms_db_id
                WHERE id = :otp_id
                """
            ),
            {"otp_id": otp_id, "sms_db_id": sms_db_id},
        )

    def bump_attempt(self, otp_id: int, attempt_count: int) -> None:
        self.db.execute(
            text(
                """
                UPDATE dbo.customer_app_otp
                SET attempt_count = :attempt_count
                WHERE id = :otp_id
                """
            ),
            {"otp_id": otp_id, "attempt_count": attempt_count},
        )

    def mark_blocked(self, otp_id: int) -> None:
        self.db.execute(
            text(
                """
                UPDATE dbo.customer_app_otp
                SET status = N'BLOCKED'
                WHERE id = :otp_id
                """
            ),
            {"otp_id": otp_id},
        )

    def mark_expired(self, otp_id: int) -> None:
        self.db.execute(
            text(
                """
                UPDATE dbo.customer_app_otp
                SET status = N'EXPIRED'
                WHERE id = :otp_id AND status = N'PENDING'
                """
            ),
            {"otp_id": otp_id},
        )

    def mark_verified(self, otp_id: int, *, verified_until: datetime) -> None:
        self.db.execute(
            text(
                """
                UPDATE dbo.customer_app_otp
                SET status = N'VERIFIED',
                    verified_at = SYSDATETIME(),
                    verified_until = :verified_until
                WHERE id = :otp_id
                """
            ),
            {"otp_id": otp_id, "verified_until": verified_until},
        )

    def insert_sms_db_(
        self,
        *,
        body: str,
        sender: str,
        recipient: str,
    ) -> int:
        """Queue SMS for the existing sender. STATUS=1 = pending (DB default / live convention)."""
        row = self.db.execute(
            text(
                """
                INSERT INTO dbo.SMS_DB_ (
                    BODY, SENDER, RECIPIENT, SENT, STATUS, SUBJECT, AddedDateTime
                )
                OUTPUT INSERTED.ID
                VALUES (
                    :body, :sender, :recipient, GETDATE(), 1, N'NIL', SYSDATETIME()
                )
                """
            ),
            {"body": body, "sender": sender, "recipient": recipient},
        ).first()
        return int(row[0])
