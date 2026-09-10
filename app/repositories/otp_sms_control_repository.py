"""Single-row OTP / SMS master control in the business database."""

from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session


CONTROL_ROW_ID = 1


def _as_bool(value: Any, default: bool = True) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(int(value))
    text_val = str(value).strip().lower()
    if text_val in {"1", "true", "yes", "on", "y"}:
        return True
    if text_val in {"0", "false", "no", "off", "n"}:
        return False
    return default


def _row_to_dict(row) -> dict[str, Any]:
    if row is None:
        return {}
    data = dict(row._mapping) if hasattr(row, "_mapping") else dict(row)
    return {
        "id": int(data.get("id") or CONTROL_ROW_ID),
        "master_otp_enabled": _as_bool(data.get("master_otp_enabled"), True),
        "web_otp_enabled": _as_bool(data.get("web_otp_enabled"), True),
        "mobile_otp_enabled": _as_bool(data.get("mobile_otp_enabled"), True),
        "row_version": int(data.get("row_version") or 1),
        "updated_by_user_id": data.get("updated_by_user_id"),
        "updated_by_username": (data.get("updated_by_username") or "") or None,
        "updated_at": data.get("updated_at"),
        "comment": (data.get("comment") or "") or None,
    }


class OtpSmsControlRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_row(self) -> Optional[dict[str, Any]]:
        row = self.db.execute(
            text(
                """
                SELECT TOP 1
                    id, master_otp_enabled, web_otp_enabled, mobile_otp_enabled,
                    row_version, updated_by_user_id, updated_by_username,
                    updated_at, comment
                FROM dbo.otp_sms_control
                WHERE id = :id
                """
            ),
            {"id": CONTROL_ROW_ID},
        ).fetchone()
        return _row_to_dict(row) if row else None

    def ensure_row(
        self,
        *,
        master_otp_enabled: bool = True,
        web_otp_enabled: bool = True,
        mobile_otp_enabled: bool = True,
    ) -> dict[str, Any]:
        existing = self.get_row()
        if existing:
            return existing
        self.db.execute(
            text(
                """
                INSERT INTO dbo.otp_sms_control (
                    id, master_otp_enabled, web_otp_enabled, mobile_otp_enabled,
                    row_version, updated_at
                )
                VALUES (
                    :id, :master_otp_enabled, :web_otp_enabled, :mobile_otp_enabled,
                    1, SYSDATETIME()
                )
                """
            ),
            {
                "id": CONTROL_ROW_ID,
                "master_otp_enabled": 1 if master_otp_enabled else 0,
                "web_otp_enabled": 1 if web_otp_enabled else 0,
                "mobile_otp_enabled": 1 if mobile_otp_enabled else 0,
            },
        )
        self.db.flush()
        row = self.get_row()
        if not row:
            raise RuntimeError("OTP control row could not be created.")
        return row

    def update_row(
        self,
        *,
        master_otp_enabled: bool,
        web_otp_enabled: bool,
        mobile_otp_enabled: bool,
        expected_version: int,
        updated_by_user_id: Optional[int],
        updated_by_username: Optional[str],
        comment: Optional[str],
    ) -> Optional[dict[str, Any]]:
        result = self.db.execute(
            text(
                """
                UPDATE dbo.otp_sms_control
                SET master_otp_enabled = :master_otp_enabled,
                    web_otp_enabled = :web_otp_enabled,
                    mobile_otp_enabled = :mobile_otp_enabled,
                    row_version = row_version + 1,
                    updated_by_user_id = :updated_by_user_id,
                    updated_by_username = :updated_by_username,
                    updated_at = SYSDATETIME(),
                    comment = :comment
                WHERE id = :id AND row_version = :expected_version
                """
            ),
            {
                "id": CONTROL_ROW_ID,
                "master_otp_enabled": 1 if master_otp_enabled else 0,
                "web_otp_enabled": 1 if web_otp_enabled else 0,
                "mobile_otp_enabled": 1 if mobile_otp_enabled else 0,
                "expected_version": int(expected_version),
                "updated_by_user_id": updated_by_user_id,
                "updated_by_username": (updated_by_username or "")[:100] or None,
                "comment": (comment or "")[:300] or None,
            },
        )
        if int(result.rowcount or 0) != 1:
            return None
        self.db.flush()
        return self.get_row()
