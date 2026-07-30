"""SMS_DB_ email scheduler business logic."""

from __future__ import annotations

from datetime import datetime, time
from typing import List, Optional

from sqlalchemy.orm import Session

from app.config.settings import settings
from app.database.business_session import BusinessSessionLocal
from app.repositories.sms_db_repository import SmsDbRepository
from app.schemas.sms_email_scheduler import (
    SmsDbRecord,
    SmsEmailSchedulerConfig,
    SmsEmailSchedulerConfigUpdate,
    SmsEmailSchedulerRunResult,
    SmsEmailSchedulerStatus,
)
from app.services.email_service import EmailDeliveryError, EmailNotConfiguredError, EmailService
from app.utils.money_format import format_amounts_in_text
from app.services.sms_email_scheduler_store import get_config, load_state, save_state, update_runtime


def _parse_hhmm(value: str) -> time:
    parts = (value or "00:00").strip().split(":")
    hour = int(parts[0]) if parts else 0
    minute = int(parts[1]) if len(parts) > 1 else 0
    return time(hour=hour, minute=minute)


def is_within_window(now: datetime, window_start: str, window_end: str) -> bool:
    """Return True when current time is inside the monitoring window."""
    start = _parse_hhmm(window_start)
    end = _parse_hhmm(window_end)
    current = now.time()

    if start <= end:
        return start <= current <= end
    return current >= start or current <= end


def parse_recipients(raw: str) -> List[str]:
    return [part.strip() for part in (raw or "").split(",") if part.strip()]


class SmsEmailSchedulerService:
    def get_config(self) -> SmsEmailSchedulerConfig:
        return get_config()

    def save_config(self, payload: SmsEmailSchedulerConfigUpdate) -> SmsEmailSchedulerConfig:
        recipients = parse_recipients(payload.recipients)
        if payload.enabled and not recipients:
            raise ValueError("Enter at least one email address when scheduling is enabled.")

        save_state(
            {
                "enabled": payload.enabled,
                "recipients": ", ".join(recipients),
                "body_keyword": payload.body_keyword.strip() or "Total Sales",
                "window_start": payload.window_start.strip() or "08:00",
                "window_end": payload.window_end.strip() or "01:30",
                "check_interval_minutes": payload.check_interval_minutes,
                "email_subject": payload.email_subject.strip() or "Sales Summary Alert",
            }
        )
        return get_config()

    def get_status(self, *, scheduler_running: bool) -> SmsEmailSchedulerStatus:
        config = get_config()
        state = load_state()
        now = datetime.now()
        email_service = EmailService()

        latest: Optional[SmsDbRecord] = None
        db = BusinessSessionLocal()
        try:
            latest = SmsDbRepository(db).get_latest_matching(config.body_keyword)
        finally:
            db.close()

        last_emailed_id = int(state.get("last_emailed_id") or 0)
        pending = bool(
            config.enabled
            and latest
            and latest.id > last_emailed_id
            and is_within_window(now, config.window_start, config.window_end)
        )

        preview = None
        if latest:
            preview = format_amounts_in_text(
                latest.body.replace("\r\n", "\n").strip()
            )[:300]

        return SmsEmailSchedulerStatus(
            enabled=config.enabled,
            smtp_configured=email_service.is_configured(),
            within_window=is_within_window(now, config.window_start, config.window_end),
            scheduler_running=scheduler_running,
            check_interval_minutes=config.check_interval_minutes,
            window_start=config.window_start,
            window_end=config.window_end,
            body_keyword=config.body_keyword,
            recipients=parse_recipients(config.recipients),
            last_emailed_id=last_emailed_id,
            last_check_at=state.get("last_check_at"),
            last_email_at=state.get("last_email_at"),
            last_email_record_id=state.get("last_email_record_id"),
            last_error=state.get("last_error"),
            next_check_at=state.get("next_check_at"),
            last_check_message=state.get("last_check_message"),
            latest_record_id=latest.id if latest else None,
            latest_record_preview=preview,
            pending_send=pending,
        )

    def run_check(self, *, force: bool = False) -> SmsEmailSchedulerRunResult:
        config = get_config()
        now = datetime.now()

        def finish(result: SmsEmailSchedulerRunResult) -> SmsEmailSchedulerRunResult:
            update_runtime(last_check_at=now, last_check_message=result.message)
            return result

        if not config.enabled and not force:
            return finish(SmsEmailSchedulerRunResult(
                success=True,
                message="Scheduler is disabled.",
                emailed=False,
            ))

        if not force and not is_within_window(now, config.window_start, config.window_end):
            return finish(SmsEmailSchedulerRunResult(
                success=True,
                message="Outside monitoring window — no email sent.",
                emailed=False,
            ))

        recipients = parse_recipients(config.recipients)
        if not recipients:
            update_runtime(last_error="No recipient email addresses configured.")
            return finish(SmsEmailSchedulerRunResult(
                success=False,
                message="No recipient email addresses configured.",
                emailed=False,
            ))

        db = BusinessSessionLocal()
        try:
            record = SmsDbRepository(db).get_latest_matching(config.body_keyword)
        finally:
            db.close()

        if not record:
            update_runtime(last_error=None, clear_error=True)
            return finish(SmsEmailSchedulerRunResult(
                success=True,
                message=f"No SMS_DB_ record found matching '{config.body_keyword}'.",
                emailed=False,
            ))

        state = load_state()
        last_emailed_id = int(state.get("last_emailed_id") or 0)
        if not force and record.id <= last_emailed_id:
            update_runtime(last_error=None, clear_error=True)
            return finish(SmsEmailSchedulerRunResult(
                success=True,
                message=f"Latest record #{record.id} was already emailed — waiting for new SMS.",
                record_id=record.id,
                emailed=False,
            ))

        try:
            self._send_record_email(config, record, recipients)
        except (EmailNotConfiguredError, EmailDeliveryError) as exc:
            update_runtime(last_error=str(exc))
            return finish(SmsEmailSchedulerRunResult(
                success=False,
                message=str(exc),
                record_id=record.id,
                emailed=False,
            ))

        update_runtime(
            last_email_at=datetime.now(),
            last_email_record_id=record.id,
            last_emailed_id=record.id,
            last_error=None,
            clear_error=True,
        )
        return finish(SmsEmailSchedulerRunResult(
            success=True,
            message=f"Emailed record #{record.id} to {', '.join(recipients)}.",
            record_id=record.id,
            emailed=True,
        ))

    def send_test_email(self, to_email: str) -> SmsEmailSchedulerRunResult:
        config = get_config()
        recipients = parse_recipients(to_email)
        if not recipients:
            return SmsEmailSchedulerRunResult(success=False, message="Enter a test email address.")

        db = BusinessSessionLocal()
        try:
            record = SmsDbRepository(db).get_latest_matching(config.body_keyword)
        finally:
            db.close()

        if not record:
            return SmsEmailSchedulerRunResult(
                success=False,
                message=f"No SMS_DB_ record found matching '{config.body_keyword}'.",
            )

        try:
            self._send_record_email(config, record, recipients, test=True)
        except (EmailNotConfiguredError, EmailDeliveryError) as exc:
            return SmsEmailSchedulerRunResult(success=False, message=str(exc), record_id=record.id)

        return SmsEmailSchedulerRunResult(
            success=True,
            message=f"Test email sent for record #{record.id}.",
            record_id=record.id,
            emailed=True,
        )

    def _send_record_email(
        self,
        config: SmsEmailSchedulerConfig,
        record: SmsDbRecord,
        recipients: List[str],
        *,
        test: bool = False,
    ) -> None:
        subject_prefix = "[TEST] " if test else ""
        subject = f"{subject_prefix}{config.email_subject} — {record.sent.strftime('%d/%m/%Y %H:%M')}"

        body_lines = [
            f"{settings.app_name}",
            f"{'=' * 40}",
            "",
            "Automated sales summary from SMS_DB_",
            "",
            f"Record ID : {record.id}",
            f"Sent      : {record.sent.strftime('%d/%m/%Y %H:%M:%S')}",
            f"Recipient : {record.recipient}",
            f"Sender    : {record.sender}",
            f"Status    : {record.status}",
            "",
            "Message body:",
            "-" * 40,
            format_amounts_in_text(record.body.strip()),
            "-" * 40,
            "",
            f"Generated at: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
            "",
            "This is an automated message. Do not reply.",
        ]
        EmailService().send_email(recipients, subject, "\n".join(body_lines))
