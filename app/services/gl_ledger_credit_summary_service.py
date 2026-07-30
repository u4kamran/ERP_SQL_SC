"""Credit summary ledger — all transactions with daily credit sum on last row per date."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.repositories.gl_ledger_report_repository import GlLedgerReportRepository
from app.schemas.gl_ledger_credit_summary import (
    GlLedgerCreditSummaryData,
    GlLedgerCreditSummaryRequest,
    GlLedgerCreditSummarySection,
    GlLedgerCreditTransactionRow,
)
from app.utils.gl_format import dash_gl, format_voucher_no, format_voucher_type

MAX_AC_ID = 99999999


def _annotate_daily_credit_sums(
    transactions: list[GlLedgerCreditTransactionRow],
) -> None:
    """Set daily_credit_sum on the last transaction row of each date."""
    if not transactions:
        return

    daily_totals: dict[date, float] = defaultdict(float)
    last_index_by_date: dict[date, int] = {}

    for index, tx in enumerate(transactions):
        if tx.voucher_date is None:
            continue
        daily_totals[tx.voucher_date] += tx.credit
        last_index_by_date[tx.voucher_date] = index

    for voucher_date, last_index in last_index_by_date.items():
        total = daily_totals[voucher_date]
        if total > 0:
            transactions[last_index].daily_credit_sum = total


class GlLedgerCreditSummaryService:
    def __init__(self, db: Session):
        self.repo = GlLedgerReportRepository(db)

    def build_report(self, params: GlLedgerCreditSummaryRequest) -> GlLedgerCreditSummaryData:
        if params.date_to < params.date_from:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date range: From date must be on or before To date.",
            )

        start_ac_id = 1 if params.complete_report else params.start_ac_id
        end_ac_id = MAX_AC_ID if params.complete_report else params.end_ac_id

        accounts = self.repo.fetch_accounts(start_ac_id, end_ac_id, params.suppress_zero_bal)
        if not accounts:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No accounts found in the selected range.",
            )

        opening_map = self.repo.fetch_opening_totals(start_ac_id, end_ac_id, params.date_from)
        tx_rows = self.repo.fetch_transactions(
            start_ac_id, end_ac_id, params.date_from, params.date_to
        )

        tx_by_account: dict[int, list] = defaultdict(list)
        for row in tx_rows:
            tx_by_account[int(row["ac_id"])].append(row)

        sections: list[GlLedgerCreditSummarySection] = []
        for account in accounts:
            ac_id = int(account["ac_id"])
            obal = float(account.get("obal") or 0)
            opening_parts = opening_map.get(ac_id, {"tdebit": 0.0, "tcredit": 0.0})
            opening_balance = obal + opening_parts["tdebit"] - opening_parts["tcredit"]
            opening_credit = abs(opening_balance) if opening_balance < 0 else 0.0

            running = opening_balance
            total_credit = 0.0
            transactions: list[GlLedgerCreditTransactionRow] = []

            for row in tx_by_account.get(ac_id, []):
                debit = float(row.get("DEBIT") or 0)
                credit = float(row.get("CREDIT") or 0)
                running += debit - credit
                total_credit += credit

                voucher_date = row.get("VOUCHER_DATE")
                if isinstance(voucher_date, datetime):
                    voucher_date = voucher_date.date()

                ref = row.get("EXTERNAL_ID")
                if ref in (None, ""):
                    ref = row.get("ADCN")
                if ref in (None, ""):
                    ref = row.get("REF_ID")

                transactions.append(
                    GlLedgerCreditTransactionRow(
                        voucher_date=voucher_date,
                        voucher_no=format_voucher_no(row.get("VOUCHER_ID"), row.get("FISCAL")),
                        voucher_type=format_voucher_type(row.get("VOUCHER_ABBR"), row.get("v_mode")),
                        narration=str(row.get("NARRATION") or "").strip(),
                        book_id=int(row["book_id"]) if row.get("book_id") is not None else None,
                        reference=str(ref or "").strip(),
                        credit=credit,
                        balance=running,
                    )
                )

            _annotate_daily_credit_sums(transactions)

            sections.append(
                GlLedgerCreditSummarySection(
                    ac_id=ac_id,
                    ac_id_display=dash_gl(ac_id),
                    ac_title=str(account.get("ac_title") or ""),
                    opening_balance=opening_balance,
                    opening_credit=opening_credit,
                    transactions=transactions,
                    total_credit=total_credit,
                    transaction_count=len(transactions),
                )
            )

        date_range = (
            f"From: {params.date_from.strftime('%d/%m/%Y')} "
            f"To: {params.date_to.strftime('%d/%m/%Y')}"
        )
        criteria = f"From: {start_ac_id} To: {end_ac_id} {date_range}"

        return GlLedgerCreditSummaryData(
            company_name=settings.company_name,
            report_title="Ledger Credit Summary",
            criteria=criteria,
            date_range=date_range,
            printed_on=datetime.now().strftime("%d/%m/%Y"),
            accounts=sections,
            total_accounts=len(sections),
            page_wise=params.page_wise,
        )
