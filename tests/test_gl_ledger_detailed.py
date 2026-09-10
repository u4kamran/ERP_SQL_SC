"""Tests for Detailed Customer Ledger (parallel report; existing GL Ledger untouched)."""

from __future__ import annotations

from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.schemas.gl_ledger_detailed import GlLedgerDetailedReportRequest
from app.services.gl_ledger_detailed_service import GlLedgerDetailedReportService
from app.reports.gl_ledger_detailed_pdf import render_gl_ledger_detailed_pdf
from app.schemas.gl_ledger_detailed import (
    GlLedgerDetailedAccountSection,
    GlLedgerDetailedReportData,
    GlLedgerDetailedTransactionRow,
    GlLedgerInvoiceDetailLine,
)


def _params(**kwargs):
    base = dict(
        start_ac_id=20010159,
        end_ac_id=20010159,
        date_from=date(2026, 8, 1),
        date_to=date(2026, 8, 29),
        include_invoice_detail=True,
    )
    base.update(kwargs)
    return GlLedgerDetailedReportRequest(**base)


def test_build_report_opening_running_and_invoice_detail():
    """B M Steel-style sample: opening + Dr - Cr and invoice lines under INV."""
    db = MagicMock()
    svc = GlLedgerDetailedReportService(db)

    svc.repo.fetch_accounts = MagicMock(
        return_value=[{"ac_id": 20010159, "ac_title": "B M STEEL", "obal": 13059.999, "cbal": 59.999}]
    )
    svc.repo.fetch_opening_totals = MagicMock(return_value={})  # no pre-period txs
    svc.repo.fetch_transactions = MagicMock(
        return_value=[
            {
                "ac_id": 20010159,
                "VOUCHER_ID": 6,
                "book_id": 1,
                "v_mode": 3,
                "VOUCHER_DATE": date(2026, 8, 3),
                "FISCAL": 2,
                "SERIAL_NO": 688,
                "serial_order": 1,
                "NARRATION": "Cash Rec From B M Steel",
                "DEBIT": 0,
                "CREDIT": 29700,
                "ADCN": "",
                "EXTERNAL_ID": 0,
                "REF_ID": 0,
                "VOUCHER_ABBR": "CV",
            },
            {
                "ac_id": 20010159,
                "VOUCHER_ID": 264,
                "book_id": 121,
                "v_mode": 1,
                "VOUCHER_DATE": date(2026, 8, 3),
                "FISCAL": 0,
                "SERIAL_NO": 704,
                "serial_order": 1,
                "NARRATION": "Invoice No.  264",
                "DEBIT": 23450,
                "CREDIT": 0,
                "ADCN": "7918",
                "EXTERNAL_ID": 0,
                "REF_ID": 0,
                "VOUCHER_ABBR": "INV",
            },
        ]
    )
    svc.repo.fetch_invoice_headers_by_serials = MagicMock(
        return_value={704: {"SERIAL_NO": 704, "INV_ID": 264, "GP_ID": "7918"}}
    )
    svc.repo.fetch_invoice_lines_by_serials = MagicMock(
        return_value={
            704: [
                {
                    "SERIAL_NO": 704,
                    "INV_ID": 264,
                    "SERIAL_ORDER": 1,
                    "QTY": 5,
                    "RATE": 1200,
                    "SALE_AMT": 6000,
                    "STAX_AMT": 0,
                    "ITEM_TITLE": "SILICONE RODE",
                },
                {
                    "SERIAL_NO": 704,
                    "INV_ID": 264,
                    "SERIAL_ORDER": 2,
                    "QTY": 5,
                    "RATE": 550,
                    "SALE_AMT": 2750,
                    "STAX_AMT": 0,
                    "ITEM_TITLE": "COMBUSTION TUBE",
                },
                {
                    "SERIAL_NO": 704,
                    "INV_ID": 264,
                    "SERIAL_ORDER": 3,
                    "QTY": 200,
                    "RATE": 21.5,
                    "SALE_AMT": 4300,
                    "STAX_AMT": 0,
                    "ITEM_TITLE": "TIN METAL",
                },
                {
                    "SERIAL_NO": 704,
                    "INV_ID": 264,
                    "SERIAL_ORDER": 4,
                    "QTY": 500,
                    "RATE": 19,
                    "SALE_AMT": 9500,
                    "STAX_AMT": 0,
                    "ITEM_TITLE": "COMBUSTION BOATS",
                },
                {
                    "SERIAL_NO": 704,
                    "INV_ID": 264,
                    "SERIAL_ORDER": 5,
                    "QTY": 6,
                    "RATE": 150,
                    "SALE_AMT": 900,
                    "STAX_AMT": 0,
                    "ITEM_TITLE": "SILICONE CARK",
                },
            ]
        }
    )

    with patch("app.services.gl_ledger_detailed_service.settings") as mock_settings:
        mock_settings.gl_ledger_detailed_enabled = True
        mock_settings.company_name = "Test Co"
        report = svc.build_report(_params())

    assert report.total_accounts == 1
    section = report.accounts[0]
    assert section.opening_balance == pytest.approx(13059.999)
    assert len(section.transactions) == 2

    cash, inv = section.transactions
    assert cash.credit == pytest.approx(29700)
    assert cash.balance == pytest.approx(13059.999 - 29700)
    assert cash.line_details == []

    assert inv.debit == pytest.approx(23450)
    assert inv.balance == pytest.approx(13059.999 - 29700 + 23450)
    assert len(inv.line_details) == 5
    assert inv.line_details[0].gate_pass == "7918"
    assert inv.line_details[0].bill_no == "264"
    assert inv.line_details[0].gst_display == "-"
    assert inv.line_details[0].line_total == pytest.approx(6000)  # value + 0 GST
    # Value from qty×rate for first mock line (5×1200); remaining lines use SALE_AMT from mock
    assert sum(d.value or 0 for d in inv.line_details) == pytest.approx(23450)
    assert section.total_value == pytest.approx(23450)
    assert section.grand_total == pytest.approx(section.total_value + section.total_gst)


def test_item_value_gst_and_grand_total_calculation():
    """Value = Qty×Rate (GST exclusive); Item Total = Value + GST; Grand = SUM."""
    db = MagicMock()
    svc = GlLedgerDetailedReportService(db)
    svc.repo.fetch_accounts = MagicMock(
        return_value=[{"ac_id": 1, "ac_title": "TEST", "obal": 0, "cbal": 0}]
    )
    svc.repo.fetch_opening_totals = MagicMock(return_value={})
    svc.repo.fetch_transactions = MagicMock(
        return_value=[
            {
                "ac_id": 1,
                "VOUCHER_ID": 202,
                "book_id": 121,
                "v_mode": 1,
                "VOUCHER_DATE": date(2026, 7, 24),
                "FISCAL": 0,
                "SERIAL_NO": 999,
                "serial_order": 1,
                "NARRATION": "Invoice No.  202",
                "DEBIT": 9500,
                "CREDIT": 0,
                "ADCN": "7855",
                "EXTERNAL_ID": 0,
                "REF_ID": 0,
                "VOUCHER_ABBR": "INV",
            }
        ]
    )
    svc.repo.fetch_invoice_headers_by_serials = MagicMock(
        return_value={999: {"SERIAL_NO": 999, "INV_ID": 202, "GP_ID": "7855"}}
    )
    svc.repo.fetch_invoice_lines_by_serials = MagicMock(
        return_value={
            999: [
                {
                    "SERIAL_NO": 999,
                    "QTY": 50,
                    "RATE": 46,
                    "SALE_AMT": 2300,
                    "STAX_AMT": 414,
                    "TOTAL_AMT": 2714,
                    "ITEM_TITLE": "POTASIUM IODIDE ***P-211",
                },
                {
                    "SERIAL_NO": 999,
                    "QTY": 6,
                    "RATE": 1200,
                    "SALE_AMT": 7200,
                    "STAX_AMT": 1296,
                    "TOTAL_AMT": 8496,
                    "ITEM_TITLE": "SILICONE RODE ***P-236",
                },
            ]
        }
    )
    with patch("app.services.gl_ledger_detailed_service.settings") as mock_settings:
        mock_settings.gl_ledger_detailed_enabled = True
        mock_settings.company_name = "Test Co"
        report = svc.build_report(_params(start_ac_id=1, end_ac_id=1))

    section = report.accounts[0]
    a, b = section.transactions[0].line_details
    assert a.value == pytest.approx(50 * 46)
    assert a.gst == pytest.approx(414)
    assert a.line_total == pytest.approx(2714)
    assert b.value == pytest.approx(6 * 1200)
    assert b.gst == pytest.approx(1296)
    assert b.line_total == pytest.approx(8496)
    assert section.total_qty == pytest.approx(56)
    assert section.total_value == pytest.approx(9500)
    assert section.total_gst == pytest.approx(1710)
    assert section.grand_total == pytest.approx(11210)
    assert section.grand_total == pytest.approx(section.total_value + section.total_gst)
    # Parent debit unchanged by item totals
    assert section.transactions[0].debit == pytest.approx(9500)


def test_feature_flag_disables_report():
    db = MagicMock()
    svc = GlLedgerDetailedReportService(db)
    with patch("app.services.gl_ledger_detailed_service.settings") as mock_settings:
        mock_settings.gl_ledger_detailed_enabled = False
        with pytest.raises(Exception) as exc:
            svc.build_report(_params())
    assert getattr(exc.value, "status_code", None) == 503


def test_pdf_includes_detail_and_parent_columns():
    report = GlLedgerDetailedReportData(
        company_name="Al Haram Steel Lab",
        report_title="Customer Ledger (Detailed)",
        criteria="From: 20010159 To: 20010159 From: 01/08/2026 To: 29/08/2026",
        date_range="From: 01/08/2026 To: 29/08/2026",
        printed_on="03/09/2026",
        include_invoice_detail=True,
        total_accounts=1,
        accounts=[
            GlLedgerDetailedAccountSection(
                ac_id=20010159,
                ac_id_display="20-01-0159",
                ac_title="B M STEEL",
                opening_balance=13059.999,
                opening_debit=13059.999,
                transactions=[
                    GlLedgerDetailedTransactionRow(
                        voucher_date=date(2026, 8, 3),
                        voucher_no="264",
                        voucher_type="INV",
                        narration="Invoice No.  264",
                        book_id=121,
                        reference="7918",
                        debit=23450,
                        credit=0,
                        balance=6809.999,
                        line_details=[
                            GlLedgerInvoiceDetailLine(
                                item_title="SILICONE RODE ***P-236",
                                gate_pass="7918",
                                bill_no="264",
                                qty=5,
                                rate=1200,
                                value=6000,
                                gst_display="-",
                                line_total=6000,
                            ),
                            GlLedgerInvoiceDetailLine(
                                item_title="COOPER MOULD TUBE 1000-90 RS-12 (7-4)",
                                gate_pass="7918",
                                bill_no="264",
                                qty=1500,
                                rate=190,
                                value=285000,
                                gst=51300,
                                gst_display="51,300.00",
                                line_total=336300,
                            ),
                        ],
                    )
                ],
                total_debit=36509.999,
                total_credit=0,
                transaction_count=1,
                total_qty=1505,
                total_value=291000,
                total_gst=51300,
                grand_total=342300,
            )
        ],
    )
    from app.reports.gl_ledger_detailed_pdf import (
        DETAIL_AREA_WIDTH,
        USABLE_WIDTH,
        compute_detail_col_widths,
    )

    widths = compute_detail_col_widths(report.accounts[0].transactions[0].line_details)
    assert len(widths) == 8
    assert abs(sum(widths) - USABLE_WIDTH) < 1.0
    assert widths[0] == max(widths)  # item title prioritized

    detail_widths = compute_detail_col_widths(
        report.accounts[0].transactions[0].line_details,
        DETAIL_AREA_WIDTH,
    )
    assert abs(sum(detail_widths) - DETAIL_AREA_WIDTH) < 1.0
    assert detail_widths[0] == max(detail_widths)

    pdf = render_gl_ledger_detailed_pdf(report)
    assert pdf[:4] == b"%PDF"
    assert len(pdf) > 800
    # Pipe-joined compact layout must not be used as primary detail format
    assert b"GP:7918 | Bill:264" not in pdf

