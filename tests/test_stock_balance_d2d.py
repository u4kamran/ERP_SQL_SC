"""Unit tests for Stock Balance Date to Date (VB6 RptStD2D / RptStD2DAmtBrand)."""

from datetime import date
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.reports.stock_balance_d2d_pdf import render_stock_balance_d2d_pdf
from app.schemas.stock_balance_d2d import (
    StockBalanceD2DData,
    StockBalanceD2DRequest,
    StockBalanceD2DRow,
    StockBalanceD2DTotals,
)
from app.repositories.stock_balance_d2d_repository import _order_clause
from app.services.stock_balance_d2d_service import StockBalanceD2DService, _passes_zero_filter
from app.utils.gl_format import dash_item


def test_dash_item_3_3_4():
    assert dash_item(1000010001) == "100-001-0001"
    assert dash_item(1000010002) == "100-001-0002"


def test_order_clause():
    assert _order_clause("ac_id", "asc") == "ORDER BY i.ITEM_ID ASC"
    assert _order_clause("ac_id", "desc") == "ORDER BY i.ITEM_ID DESC"
    assert "ITEM_TITLE DESC" in _order_clause("ac_title", "desc")
    assert "ITEM_ID ASC" in _order_clause("ac_title", "desc")


def test_suppress_zero_filter():
    assert _passes_zero_filter(
        qty_opening=0, qty_in=0, qty_out=0, qty_closing=0, suppress_zero=True
    ) is False
    assert _passes_zero_filter(
        qty_opening=100, qty_in=10, qty_out=5, qty_closing=105, suppress_zero=True
    ) is True


def test_invalid_date_range():
    svc = StockBalanceD2DService(MagicMock())
    with pytest.raises(HTTPException) as exc:
        svc.build_report(
            StockBalanceD2DRequest(
                start_item_id=1,
                end_item_id=10,
                date_from=date(2026, 8, 31),
                date_to=date(2026, 8, 1),
            )
        )
    assert exc.value.status_code == 400


def _sample_raw_rows():
    return [
        {
            "item_id": 1000010002,
            "item_title": "NATIONAL IODIEZ SALT 800gm",
            "manualid": 5615,
            "oqty": 8000,
            "pre_qtydr": 500,
            "pre_qtycr": 96,
            "period_qtydr": 2640,
            "period_qtycr": 1887,
            "oamt": 50000,
            "pre_amtdr": 1000,
            "pre_amtcr": 200,
            "period_amtdr": 8000,
            "period_amtcr": 3000,
        },
        {
            "item_id": 1000010021,
            "item_title": "NATIONAL REFINED SALT 800 GM",
            "manualid": 0,
            "oqty": 1184,
            "pre_qtydr": 0,
            "pre_qtycr": 0,
            "period_qtydr": 10920,
            "period_qtycr": 14437,
            "oamt": 2000,
            "pre_amtdr": 0,
            "pre_amtcr": 0,
            "period_amtdr": 500,
            "period_amtcr": 4000,
        },
    ]


def test_build_report_qty_mode():
    repo = MagicMock()
    repo.fetch_item_balances.return_value = _sample_raw_rows()
    svc = StockBalanceD2DService(MagicMock())
    svc.repo = repo

    report = svc.build_report(
        StockBalanceD2DRequest(
            start_item_id=1000010001,
            end_item_id=1000010046,
            date_from=date(2026, 1, 1),
            date_to=date(2026, 8, 31),
        )
    )

    assert report.print_amount is False
    assert report.report_title.endswith(".")
    r0 = report.rows[0]
    assert r0.opening_balance == pytest.approx(8404)
    assert r0.stock_in == pytest.approx(2640)
    assert r0.stock_out == pytest.approx(1887)
    assert r0.net_balance == pytest.approx(753)
    assert r0.closing_balance == pytest.approx(9157)
    assert report.totals.closing_balance == pytest.approx(9157)


def test_build_report_print_amount_amtbrand_layout():
    """RptStD2DAmtBrand: Opening Qty/Amt, Period Qty/Amt (net), Closing Qty/Amt."""
    repo = MagicMock()
    repo.fetch_item_balances.return_value = _sample_raw_rows()
    svc = StockBalanceD2DService(MagicMock())
    svc.repo = repo

    report = svc.build_report(
        StockBalanceD2DRequest(
            start_item_id=1000010001,
            end_item_id=1000010046,
            date_from=date(2026, 1, 1),
            date_to=date(2026, 8, 31),
            print_amount=True,
        )
    )

    assert report.print_amount is True
    assert report.report_title == "Stock Balance Date to Date"
    r0 = report.rows[0]
    assert r0.opening_qty == pytest.approx(8404)
    assert r0.opening_amt == pytest.approx(50800)
    assert r0.period_qty == pytest.approx(753)  # net qty
    assert r0.period_amt == pytest.approx(5000)  # net amt
    assert r0.closing_qty == pytest.approx(9157)
    assert r0.closing_amt == pytest.approx(55800)

    r1 = report.rows[1]
    assert r1.period_qty == pytest.approx(-3517)
    assert r1.period_amt == pytest.approx(-3500)
    assert r1.closing_amt == pytest.approx(-1500)
    assert report.totals.opening_amt == pytest.approx(52800)
    assert report.totals.period_qty == pytest.approx(753 - 3517)
    # Closing Amt total includes negatives (55800 + -1500)
    assert report.totals.closing_amt == pytest.approx(54300)
    assert report.totals.period_amt == pytest.approx(5000 - 3500)


def test_pdf_qty_and_amt_layouts():
    import pymupdf as fitz

    qty_report = StockBalanceD2DData(
        company_name="Shafique Departmental Store.",
        report_title="Stock Balance Date to Date.",
        criteria="From: 1 To: 2 From: 01/01/2026 To: 31/08/2026",
        date_range="From: 01/01/2026 To: 31/08/2026",
        printed_on="12/08/2026",
        print_amount=False,
        rows=[
            StockBalanceD2DRow(
                item_id=1000010002,
                item_id_display="100-001-0002",
                item_title="NATIONAL IODIEZ SALT 800gm",
                brand="5615",
                opening_balance=8404,
                stock_in=2640,
                stock_out=1887,
                net_balance=753,
                closing_balance=9157,
            )
        ],
        total_rows=1,
        totals=StockBalanceD2DTotals(
            opening_balance=8404, stock_in=2640, stock_out=1887,
            net_stock_in=753, closing_balance=9157,
        ),
    )
    qty_pdf = render_stock_balance_d2d_pdf(qty_report)
    qty_doc = fitz.open(stream=qty_pdf, filetype="pdf")
    qty_text = qty_doc[0].get_text()
    assert "Transaction for the Period" in qty_text
    assert "Stock In" in qty_text
    assert abs(qty_doc[0].rect.width - 792) < 1

    amt_report = StockBalanceD2DData(
        company_name="Shafique Departmental Store.",
        report_title="Stock Balance Date to Date",
        criteria="From: 1000010001 To: 1000010045 From: 01/01/2026 To: 31/08/2026",
        date_range="From: 01/01/2026 To: 31/08/2026",
        printed_on="12/08/2026",
        print_amount=True,
        rows=[
            StockBalanceD2DRow(
                item_id=1000010002,
                item_id_display="100-001-0002",
                item_title="NATIONAL IODIEZ SALT 800gm",
                brand="5615",
                opening_qty=8404,
                opening_amt=205704.14,
                period_qty=752,
                period_amt=5000,
                closing_qty=9156,
                closing_amt=210704.14,
            )
        ],
        total_rows=1,
        totals=StockBalanceD2DTotals(
            opening_qty=8404, opening_amt=205704.14,
            period_qty=752, period_amt=5000,
            closing_qty=9156, closing_amt=210704.14,
        ),
    )
    amt_pdf = render_stock_balance_d2d_pdf(amt_report)
    amt_doc = fitz.open(stream=amt_pdf, filetype="pdf")
    amt_text = amt_doc[0].get_text()
    assert "For The Period" in amt_text
    assert "Opening" in amt_text
    assert "Closing" in amt_text
    assert "Qty" in amt_text
    assert "Amt" in amt_text
    assert "205,704.14" in amt_text
    assert "Stock In" not in amt_text  # qty-mode only
