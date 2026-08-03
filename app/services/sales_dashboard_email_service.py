"""Scheduled sales dashboard email reports."""

from __future__ import annotations

from datetime import datetime
from typing import List

from app.config.settings import settings
from app.database.business_session import BusinessSessionLocal
from app.reports.sales_dashboard_snapshot_pdf import build_sales_dashboard_snapshot_pdf
from app.schemas.sales_dashboard import DayWiseSalesRow, SalesDashboardRequest, SalesDashboardSummary
from app.schemas.sales_dashboard_email import (
    SalesDashboardEmailConfig,
    SalesDashboardEmailConfigUpdate,
    SalesDashboardEmailRunResult,
    SalesDashboardEmailStatus,
)
from app.services.email_service import EmailDeliveryError, EmailNotConfiguredError, EmailService
from app.services.sales_dashboard_email_store import get_config, load_state, save_state, update_runtime
from app.services.sales_dashboard_service import SalesDashboardService
from app.utils.business_day import date_range_for_preset
from app.utils.money_format import format_amount


def parse_recipients(raw: str) -> List[str]:
    return [part.strip() for part in (raw or "").split(",") if part.strip()]


def _fmt_change_cell(value: float, is_percent: bool = False) -> str:
    prefix = "+" if value > 0 else ""
    if is_percent:
        return f"{prefix}{format_amount(value)} pts"
    return f"{prefix}{format_amount(value)}"


def _fmt_pct_cell(value: float | None) -> str:
    if value is None:
        return "—"
    prefix = "+" if value > 0 else ""
    return f"{prefix}{format_amount(value)}%"


def build_comparison_html(
    summary: SalesDashboardSummary,
    period_label: str,
    compare_label: str,
    day_wise: list[DayWiseSalesRow] | None = None,
    business_hours_note: str = "",
) -> str:
    rows = [
        ("Total Sale", summary.total_sale, False),
        ("Total Cost", summary.total_cost, False),
        ("Profit", summary.profit, False),
        ("Profit %", summary.profit_percent, True),
        ("Avg Sale / Day", summary.avg_sale_per_day, False),
    ]
    body_rows = []
    for label, metric, is_percent in rows:
        current = f"{format_amount(metric.current)}%" if is_percent else format_amount(metric.current)
        previous = f"{format_amount(metric.previous)}%" if is_percent else format_amount(metric.previous)
        change = _fmt_change_cell(metric.change, is_percent=is_percent)
        pct = "—" if is_percent else _fmt_pct_cell(metric.change_percent)
        body_rows.append(
            f"<tr><td>{label}</td><td class='num'>{current}</td><td class='num'>{previous}</td>"
            f"<td class='num'>{change}</td><td class='num'>{pct}</td></tr>"
        )

    day_section = ""
    if day_wise:
        day_rows_html = "".join(
            f"<tr><td>{row.day_label}</td>"
            f"<td class='num'>{format_amount(row.total_sale)}</td>"
            f"<td class='num'>{format_amount(row.total_cost)}</td>"
            f"<td class='num'>{format_amount(row.profit)}</td>"
            f"<td class='num'>{row.invoice_count}</td></tr>"
            for row in day_wise[:31]
        )
        day_section = f"""
  <h3 style="margin-top:20px;font-size:16px;">Day-wise Sales</h3>
  <p class="meta">{business_hours_note}</p>
  <table>
    <thead><tr>
      <th>Business Day</th><th class="num">Sale</th><th class="num">Cost</th>
      <th class="num">Profit</th><th class="num">Invoices</th>
    </tr></thead>
    <tbody>{day_rows_html}</tbody>
  </table>
"""

    return f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ font-family: Arial, sans-serif; color: #212529; }}
  h2 {{ font-size: 18px; margin-bottom: 4px; }}
  .meta {{ color: #6c757d; font-size: 13px; margin-bottom: 12px; }}
  table {{ border-collapse: collapse; width: 100%; max-width: 760px; margin-bottom: 12px; }}
  th, td {{ border: 1px solid #dee2e6; padding: 8px 10px; font-size: 14px; }}
  th {{ background: #f8f9fa; text-align: left; }}
  td.num, th.num {{ text-align: right; }}
</style>
</head>
<body>
  <h2>Month-over-Month Comparison</h2>
  <div class="meta">{period_label}<br>{compare_label}<br>{business_hours_note}</div>
  <table>
    <thead>
      <tr>
        <th>Metric</th>
        <th class="num">Current</th>
        <th class="num">Last Month</th>
        <th class="num">Change</th>
        <th class="num">Change %</th>
      </tr>
    </thead>
    <tbody>
      {''.join(body_rows)}
    </tbody>
  </table>
  {day_section}
  <p class="meta">PDF snapshot attached. Generated at {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}.</p>
</body>
</html>
"""


class SalesDashboardEmailService:
    def get_config(self) -> SalesDashboardEmailConfig:
        return get_config()

    def save_config(self, payload: SalesDashboardEmailConfigUpdate) -> SalesDashboardEmailConfig:
        recipients = parse_recipients(payload.recipients)
        if payload.enabled and not recipients:
            raise ValueError("Enter at least one email address when scheduling is enabled.")
        save_state(
            {
                "enabled": payload.enabled,
                "recipients": ", ".join(recipients),
                "interval_minutes": payload.interval_minutes,
                "email_subject": payload.email_subject.strip() or "Sales Dashboard — Month-over-Month",
                "date_preset": payload.date_preset.strip() or "this-month",
            }
        )
        return get_config()

    def get_status(self, *, scheduler_running: bool) -> SalesDashboardEmailStatus:
        config = get_config()
        state = load_state()
        return SalesDashboardEmailStatus(
            enabled=config.enabled,
            smtp_configured=EmailService().is_configured(),
            scheduler_running=scheduler_running,
            interval_minutes=config.interval_minutes,
            date_preset=config.date_preset,
            recipients=parse_recipients(config.recipients),
            last_email_at=state.get("last_email_at"),
            last_error=state.get("last_error"),
            next_check_at=state.get("next_check_at"),
            last_check_message=state.get("last_check_message"),
        )

    def _fetch_summary(self, preset: str) -> tuple[SalesDashboardSummary, str, str, list[DayWiseSalesRow], str]:
        start, end = date_range_for_preset(preset)
        db = BusinessSessionLocal()
        try:
            params = SalesDashboardRequest(start_date=start, end_date=end)
            svc = SalesDashboardService(db)
            summary = svc.get_summary(params)
            day_wise_resp = svc.get_day_wise_sales(params)
        finally:
            db.close()

        period_label = (
            f"Current: {summary.current.start_date.strftime('%d/%m/%Y %H:%M')} "
            f"to {summary.current.end_date.strftime('%d/%m/%Y %H:%M')}"
        )
        compare_label = (
            f"Last month: {summary.previous.start_date.strftime('%d/%m/%Y %H:%M')} "
            f"to {summary.previous.end_date.strftime('%d/%m/%Y %H:%M')}"
        )
        return summary, period_label, compare_label, day_wise_resp.items, day_wise_resp.business_hours_note

    def run_check(self, *, force: bool = False) -> SalesDashboardEmailRunResult:
        config = get_config()
        now = datetime.now()

        def finish(result: SalesDashboardEmailRunResult) -> SalesDashboardEmailRunResult:
            update_runtime(last_check_at=now, last_check_message=result.message)
            return result

        if not config.enabled and not force:
            return finish(SalesDashboardEmailRunResult(
                success=True,
                message="Sales dashboard email is disabled.",
                emailed=False,
            ))

        recipients = parse_recipients(config.recipients)
        if not recipients:
            update_runtime(last_error="No recipient email addresses configured.")
            return finish(SalesDashboardEmailRunResult(
                success=False,
                message="No recipient email addresses configured.",
                emailed=False,
            ))

        try:
            summary, period_label, compare_label, day_wise, hours_note = self._fetch_summary(config.date_preset)
            self._send_report(
                config, summary, period_label, compare_label, recipients,
                day_wise=day_wise, business_hours_note=hours_note,
            )
        except (EmailNotConfiguredError, EmailDeliveryError) as exc:
            update_runtime(last_error=str(exc))
            return finish(SalesDashboardEmailRunResult(success=False, message=str(exc), emailed=False))
        except Exception as exc:
            update_runtime(last_error=str(exc))
            return finish(SalesDashboardEmailRunResult(
                success=False,
                message=f"Failed to build or send report: {exc}",
                emailed=False,
            ))

        update_runtime(last_email_at=now, last_error=None, clear_error=True)
        return finish(SalesDashboardEmailRunResult(
            success=True,
            message=f"Emailed sales dashboard snapshot to {', '.join(recipients)}.",
            emailed=True,
        ))

    def send_test_email(self, to_email: str) -> SalesDashboardEmailRunResult:
        config = get_config()
        recipients = parse_recipients(to_email)
        if not recipients:
            return SalesDashboardEmailRunResult(success=False, message="Enter a test email address.")

        try:
            summary, period_label, compare_label, day_wise, hours_note = self._fetch_summary(config.date_preset)
            self._send_report(
                config, summary, period_label, compare_label, recipients,
                day_wise=day_wise, business_hours_note=hours_note, test=True,
            )
        except (EmailNotConfiguredError, EmailDeliveryError) as exc:
            return SalesDashboardEmailRunResult(success=False, message=str(exc))
        except Exception as exc:
            return SalesDashboardEmailRunResult(success=False, message=str(exc))

        return SalesDashboardEmailRunResult(
            success=True,
            message=f"Test email sent to {recipients[0]}.",
            emailed=True,
        )

    def _send_report(
        self,
        config: SalesDashboardEmailConfig,
        summary: SalesDashboardSummary,
        period_label: str,
        compare_label: str,
        recipients: List[str],
        *,
        day_wise: list[DayWiseSalesRow] | None = None,
        business_hours_note: str = "",
        test: bool = False,
    ) -> None:
        now = datetime.now()
        subject_prefix = "[TEST] " if test else ""
        subject = f"{subject_prefix}{config.email_subject} — {now.strftime('%d/%m/%Y %H:%M')}"

        html = build_comparison_html(
            summary, period_label, compare_label,
            day_wise=day_wise, business_hours_note=business_hours_note,
        )
        plain_lines = [
            settings.app_name,
            "Month-over-Month Comparison",
            period_label,
            compare_label,
            "",
            f"Total Sale: {format_amount(summary.total_sale.current)} "
            f"(was {format_amount(summary.total_sale.previous)})",
            f"Profit: {format_amount(summary.profit.current)} "
            f"(was {format_amount(summary.profit.previous)})",
            "",
            "See attached PDF snapshot for full table.",
            f"Generated at: {now.strftime('%d/%m/%Y %H:%M:%S')}",
        ]
        pdf_bytes = build_sales_dashboard_snapshot_pdf(
            summary,
            period_label=period_label,
            compare_label=compare_label,
            day_wise=day_wise,
            business_hours_note=business_hours_note,
            generated_at=now,
        )
        filename = f"sales-dashboard-{now.strftime('%Y%m%d-%H%M')}.pdf"
        EmailService().send_email(
            recipients,
            subject,
            "\n".join(plain_lines),
            body_html=html,
            attachment=(filename, pdf_bytes, "application/pdf"),
        )
