"""Trial Balance Date to Date — VB6 RptTBD2D / FrmPrintListL logic."""

from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.repositories.trial_balance_d2d_repository import TrialBalanceD2DRepository
from app.schemas.trial_balance_d2d import (
    TrialBalanceD2DData,
    TrialBalanceD2DRequest,
    TrialBalanceD2DRow,
    TrialBalanceD2DTotals,
)
from app.services.gl_ledger_report_service import MAX_AC_ID
from app.utils.gl_format import dash_gl


def _split_dr_cr(amount: float) -> tuple[float, float]:
    if amount >= 0:
        return float(amount), 0.0
    return 0.0, abs(float(amount))


def _passes_zero_filter(
    row: TrialBalanceD2DRow,
    suppress_zero: bool,
    short_format: bool,
) -> bool:
    """VB6 Option_Check1 + ChkDtlTrial filter on v_glmast."""
    if not suppress_zero and not short_format:
        return True
    if suppress_zero and not short_format:
        return (
            row.opening_balance != 0
            or row.period_debit != 0
            or row.period_credit != 0
            or row.closing_balance != 0
        )
    if not suppress_zero and short_format:
        return (
            row.opening_balance != 0
            or row.period_debit != 0
            or row.period_credit != 0
            or row.closing_balance != 0
        )
    # suppress + short: closing only
    return row.closing_balance != 0


class TrialBalanceD2DService:
    def __init__(self, db: Session):
        self.repo = TrialBalanceD2DRepository(db)

    def build_report(self, params: TrialBalanceD2DRequest) -> TrialBalanceD2DData:
        if params.date_to < params.date_from:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date range: From date must be on or before To date.",
            )

        start_ac_id = 1 if params.complete_report else params.start_ac_id
        end_ac_id = MAX_AC_ID if params.complete_report else params.end_ac_id

        raw_rows = self.repo.fetch_account_balances(
            start_ac_id,
            end_ac_id,
            params.date_from,
            params.date_to,
            sort_by=params.sort_by,
            sort_order=params.sort_order,
        )
        if not raw_rows:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No accounts found in the selected range.",
            )

        rows: list[TrialBalanceD2DRow] = []
        totals = TrialBalanceD2DTotals()

        for raw in raw_rows:
            obal = float(raw.get("obal") or 0)
            pre_debit = float(raw.get("pre_debit") or 0)
            pre_credit = float(raw.get("pre_credit") or 0)
            period_debit = float(raw.get("period_debit") or 0)
            period_credit = float(raw.get("period_credit") or 0)

            opening = obal + pre_debit - pre_credit
            net_balance = period_debit - period_credit
            closing = opening + net_balance

            row = TrialBalanceD2DRow(
                ac_id=int(raw["ac_id"]),
                ac_id_display=dash_gl(raw["ac_id"]),
                ac_title=str(raw.get("ac_title") or "").strip(),
                opening_balance=opening,
                period_debit=period_debit,
                period_credit=period_credit,
                net_balance=net_balance,
                closing_balance=closing,
            )

            if not _passes_zero_filter(row, params.suppress_zero_bal, params.short_format):
                continue

            rows.append(row)

            op_dr, op_cr = _split_dr_cr(opening)
            net_dr, net_cr = _split_dr_cr(net_balance)
            cl_dr, cl_cr = _split_dr_cr(closing)

            totals.opening_debit += op_dr
            totals.opening_credit += op_cr
            if opening < 0:
                totals.opening_credit_signed += opening
            totals.period_debit += period_debit
            totals.period_credit += period_credit
            totals.net_debit += net_dr
            totals.net_credit += net_cr
            totals.closing_debit += cl_dr
            totals.closing_credit += cl_cr

        if not rows:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No accounts match the selected filters.",
            )

        totals.diff_opening = totals.opening_debit - totals.opening_credit
        totals.diff_closing = totals.closing_debit - totals.closing_credit

        date_range = (
            f"From: {params.date_from.strftime('%m/%d/%Y')} "
            f"To: {params.date_to.strftime('%m/%d/%Y')}"
        )
        criteria = (
            f"From: {start_ac_id} To: {end_ac_id} "
            f"From: {params.date_from.strftime('%m/%d/%Y')} "
            f"To: {params.date_to.strftime('%m/%d/%Y')}"
        )

        return TrialBalanceD2DData(
            company_name=settings.company_name,
            report_title="Trial Balance Date to Date",
            criteria=criteria,
            date_range=date_range,
            printed_on=datetime.now().strftime("%d/%m/%Y"),
            short_format=params.short_format,
            rows=rows,
            total_rows=len(rows),
            totals=totals,
        )
