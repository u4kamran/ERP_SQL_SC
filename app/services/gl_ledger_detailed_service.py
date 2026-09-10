"""Detailed Customer Ledger — parallel report; does not modify existing GL Ledger service."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.repositories.gl_ledger_detailed_repository import GlLedgerDetailedReportRepository
from app.schemas.gl_ledger_detailed import (
    GlAccountLookup,
    GlLedgerDetailedAccountSection,
    GlLedgerDetailedReportData,
    GlLedgerDetailedReportRequest,
    GlLedgerDetailedTransactionRow,
    GlLedgerInvoiceDetailLine,
    GlWhatsAppContactLookup,
)
from app.services.gl_ledger_report_service import GlLedgerReportService
from app.utils.gl_format import dash_gl, format_voucher_no, format_voucher_type

MAX_AC_ID = 99999999


def _gst_display(stax_amt: float | None) -> str:
    if stax_amt is None or abs(float(stax_amt)) < 0.0005:
        return "-"
    return f"{float(stax_amt):,.2f}"


class GlLedgerDetailedReportService:
    """Same accounting as GL Ledger, plus optional invoice line detail under each TX."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = GlLedgerDetailedReportRepository(db)
        self._base = GlLedgerReportService(db)

    def search_whatsapp_contacts(self, q: str) -> list[GlWhatsAppContactLookup]:
        return self._base.search_whatsapp_contacts(q)

    def lookup_whatsapp_contact(self, ac_id: int) -> GlWhatsAppContactLookup:
        return self._base.lookup_whatsapp_contact(ac_id)

    def search_accounts(self, q: str) -> list[GlAccountLookup]:
        return self._base.search_accounts(q)

    def lookup_account(self, ac_id: int) -> GlAccountLookup:
        return self._base.lookup_account(ac_id)

    def build_report(self, params: GlLedgerDetailedReportRequest) -> GlLedgerDetailedReportData:
        if not settings.gl_ledger_detailed_enabled:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "Detailed Customer Ledger is disabled "
                    "(GL_LEDGER_DETAILED_ENABLED=false). Existing GL Ledger is unchanged."
                ),
            )

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
        # Classify serials by voucher abbreviation for targeted detail lookups
        serials_inv: list[int] = []
        serials_srt: list[int] = []
        serials_pur: list[int] = []
        serials_purr: list[int] = []
        _ABBR_INV = {"INV"}
        _ABBR_SRT = {"SRT"}
        _ABBR_PUR = {"PUR"}
        _ABBR_PURR = {"PURR", "PRT", "PRT_"}
        for row in tx_rows:
            ac = int(row["ac_id"])
            tx_by_account[ac].append(row)
            sn = row.get("SERIAL_NO")
            if sn is None:
                continue
            sn_int = int(sn)
            abbr = str(row.get("VOUCHER_ABBR") or "").strip().upper()
            if abbr in _ABBR_INV:
                serials_inv.append(sn_int)
            elif abbr in _ABBR_SRT:
                serials_srt.append(sn_int)
            elif abbr in _ABBR_PUR:
                serials_pur.append(sn_int)
            elif abbr in _ABBR_PURR:
                serials_purr.append(sn_int)

        # Fetch detail from the correct source tables per voucher type
        headers_by_serial: dict[int, dict] = {}
        lines_by_serial: dict[int, list] = {}
        # Track which value column name each serial uses (SALE_AMT vs PUR_AMT)
        _val_col_by_serial: dict[int, str] = {}

        if params.include_invoice_detail:
            # INV — Sales Invoice
            if serials_inv:
                inv_hdrs = self.repo.fetch_invoice_headers_by_serials(serials_inv)
                headers_by_serial.update(inv_hdrs)
                inv_lines = self.repo.fetch_invoice_lines_by_serials(list(inv_hdrs.keys()))
                lines_by_serial.update(inv_lines)
                for sn in inv_hdrs:
                    _val_col_by_serial[sn] = "SALE_AMT"
            # SRT — Sale Return
            if serials_srt:
                srt_hdrs = self.repo.fetch_sale_return_headers_by_serials(serials_srt)
                # Normalize header keys: INV_ID → doc_id for display
                for sn, hdr in srt_hdrs.items():
                    headers_by_serial[sn] = hdr
                srt_lines = self.repo.fetch_sale_return_lines_by_serials(list(srt_hdrs.keys()))
                lines_by_serial.update(srt_lines)
                for sn in srt_hdrs:
                    _val_col_by_serial[sn] = "SALE_AMT"
            # PUR — GRN / Purchase Receipt
            if serials_pur:
                pur_hdrs = self.repo.fetch_purchase_headers_by_serials(serials_pur)
                # Normalize: PROD_ID → INV_ID key for uniform header access
                for sn, hdr in pur_hdrs.items():
                    hdr["INV_ID"] = hdr.get("PROD_ID", "")
                    headers_by_serial[sn] = hdr
                pur_lines = self.repo.fetch_purchase_lines_by_serials(list(pur_hdrs.keys()))
                lines_by_serial.update(pur_lines)
                for sn in pur_hdrs:
                    _val_col_by_serial[sn] = "PUR_AMT"
            # PURR — Purchase Return
            if serials_purr:
                purr_hdrs = self.repo.fetch_purchase_return_headers_by_serials(serials_purr)
                for sn, hdr in purr_hdrs.items():
                    hdr["INV_ID"] = hdr.get("PROD_ID", "")
                    headers_by_serial[sn] = hdr
                purr_lines = self.repo.fetch_purchase_return_lines_by_serials(list(purr_hdrs.keys()))
                lines_by_serial.update(purr_lines)
                for sn in purr_hdrs:
                    _val_col_by_serial[sn] = "PUR_AMT"

        sections: list[GlLedgerDetailedAccountSection] = []
        for account in accounts:
            ac_id = int(account["ac_id"])
            obal = float(account.get("obal") or 0)
            opening_parts = opening_map.get(ac_id, {"tdebit": 0.0, "tcredit": 0.0})
            opening_balance = obal + opening_parts["tdebit"] - opening_parts["tcredit"]

            if opening_balance >= 0:
                opening_debit = opening_balance
                opening_credit = 0.0
            else:
                opening_debit = 0.0
                opening_credit = abs(opening_balance)

            running = opening_balance
            account_debit = opening_debit
            account_credit = opening_credit
            total_qty = 0.0
            total_value = 0.0
            total_gst = 0.0
            grand_total = 0.0
            transactions: list[GlLedgerDetailedTransactionRow] = []

            for row in tx_by_account.get(ac_id, []):
                debit = float(row.get("DEBIT") or 0)
                credit = float(row.get("CREDIT") or 0)
                running += debit - credit
                account_debit += debit
                account_credit += credit
                voucher_date = row.get("VOUCHER_DATE")
                if isinstance(voucher_date, datetime):
                    voucher_date = voucher_date.date()
                ref = row.get("EXTERNAL_ID")
                if ref in (None, "", 0, "0"):
                    ref = row.get("ADCN")
                if ref in (None, "", 0, "0"):
                    ref = row.get("REF_ID")
                if ref in (0, "0"):
                    ref = ""

                serial_no = int(row["SERIAL_NO"]) if row.get("SERIAL_NO") is not None else None
                line_details: list[GlLedgerInvoiceDetailLine] = []
                if (
                    params.include_invoice_detail
                    and serial_no is not None
                    and serial_no in headers_by_serial
                ):
                    header = headers_by_serial[serial_no]
                    gate_pass = str(header.get("GP_ID") or "").strip()
                    bill_no = str(header.get("INV_ID") or "").strip()
                    val_col = _val_col_by_serial.get(serial_no, "SALE_AMT")
                    for line in lines_by_serial.get(serial_no, []):
                        qty = float(line.get("QTY") or 0)
                        rate = float(line.get("RATE") or 0)
                        # Value is GST-exclusive: Qty × Rate (matches SALE_AMT/PUR_AMT).
                        value = round(qty * rate, 4)
                        stored_amt = float(line.get(val_col) or 0)
                        if abs(stored_amt) >= 0.0005 and abs(stored_amt - value) > 0.02:
                            # Prefer stored exclusive amount if qty×rate drifts (rare rounding).
                            value = stored_amt
                        # Actual GST amount from the document line (not a guessed %).
                        gst = float(line.get("STAX_AMT") or 0)
                        # TOTAL_AMT in source = exclusive amt + STAX_AMT when GST applies.
                        stored_total = float(line.get("TOTAL_AMT") or 0)
                        line_total = round(value + gst, 4)
                        if abs(stored_total) >= 0.0005 and abs(stored_total - line_total) <= 0.02:
                            line_total = stored_total
                        total_qty += qty
                        total_value += value
                        total_gst += gst
                        grand_total += line_total
                        line_details.append(
                            GlLedgerInvoiceDetailLine(
                                item_title=str(line.get("ITEM_TITLE") or "").strip(),
                                gate_pass=gate_pass,
                                bill_no=bill_no,
                                qty=qty,
                                rate=rate,
                                value=value,
                                gst=gst if abs(gst) >= 0.0005 else None,
                                gst_display=_gst_display(gst),
                                line_total=line_total,
                            )
                        )

                transactions.append(
                    GlLedgerDetailedTransactionRow(
                        voucher_date=voucher_date,
                        voucher_no=format_voucher_no(row.get("VOUCHER_ID"), row.get("FISCAL")),
                        voucher_type=format_voucher_type(row.get("VOUCHER_ABBR"), row.get("v_mode")),
                        narration=str(row.get("NARRATION") or "").strip(),
                        book_id=int(row["book_id"]) if row.get("book_id") is not None else None,
                        reference=str(ref or "").strip(),
                        serial_no=serial_no,
                        debit=debit,
                        credit=credit,
                        balance=running,
                        line_details=line_details,
                    )
                )

            sections.append(
                GlLedgerDetailedAccountSection(
                    ac_id=ac_id,
                    ac_id_display=dash_gl(ac_id),
                    ac_title=str(account.get("ac_title") or ""),
                    opening_balance=opening_balance,
                    opening_debit=opening_debit,
                    opening_credit=opening_credit,
                    transactions=transactions,
                    total_debit=account_debit,
                    total_credit=account_credit,
                    transaction_count=len(transactions),
                    total_qty=total_qty,
                    total_value=total_value,
                    total_gst=total_gst,
                    grand_total=grand_total,
                )
            )

        date_range = (
            f"From: {params.date_from.strftime('%d/%m/%Y')} "
            f"To: {params.date_to.strftime('%d/%m/%Y')}"
        )
        criteria = f"From: {start_ac_id} To: {end_ac_id} {date_range}"

        return GlLedgerDetailedReportData(
            company_name=settings.company_name,
            report_title="Customer Ledger (Detailed)",
            criteria=criteria,
            date_range=date_range,
            printed_on=datetime.now().strftime("%d/%m/%Y"),
            accounts=sections,
            total_accounts=len(sections),
            page_wise=params.page_wise,
            include_invoice_detail=params.include_invoice_detail,
        )
