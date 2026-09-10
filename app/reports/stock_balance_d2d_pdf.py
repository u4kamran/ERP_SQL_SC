"""PDF renderer for Stock Balance Date to Date.

Qty mode  → VB6 RptStD2D / StockBalDTD.pdf
Amt mode  → VB6 RptStD2DAmtBrand / StockBalDTD_amt.pdf
"""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas

from app.schemas.stock_balance_d2d import StockBalanceD2DData, StockBalanceD2DRow
from app.utils.money_format import format_amount

PAGE_W, PAGE_H = landscape(letter)

COLOR_COMPANY = colors.HexColor("#008000")
COLOR_META = colors.HexColor("#004A67")
COLOR_LINE = colors.HexColor("#000000")
COLOR_ROW_LINE = colors.HexColor("#C8C8C8")
COLOR_ZEBRA = colors.HexColor("#EEEEEE")

ROW_LEADING = 15.7
ROW_LINE_TOP = 9.0
FOOTER_BLOCK_HEIGHT = 36
FONT_DATA = 8
FONT_HDR = 10
FONT_TITLE = 12
FONT_COMPANY = 14

# --- Qty layout (StockBalDTD.pdf) ---
Q_MARGIN = 36.0
Q_AC_ID = 37.6
Q_TITLE = 99.5
Q_BRAND = 276.0
Q_OPENING = 425.7
Q_STOCK_IN = 493.1
Q_STOCK_OUT = 560.7
Q_NET_IN = 623.6
Q_NET_OUT = 686.6
Q_CLOSING = 754.1
Q_RULES = [
    (36.0, 94.6), (99.0, 270.0), (276.0, 320.0),
    (360.0, 427.6), (432.0, 495.0), (499.0, 562.6),
    (567.0, 625.6), (630.0, 688.6), (693.0, 756.0),
]
Q_FOOTER_RULES = [
    (360.0, 427.6), (432.0, 495.0), (499.0, 562.6),
    (567.0, 625.6), (630.0, 688.6), (693.0, 756.0),
]

# --- Amt layout (StockBalDTD_amt.pdf) — tighter left margin ---
A_AC_ID = 17.0
A_TITLE = 78.9
A_BRAND = 242.0
A_OPEN_QTY = 367.0
A_OPEN_AMT = 443.0
A_PER_QTY = 517.5
A_PER_AMT = 578.5
A_CLOSE_QTY = 648.0
A_CLOSE_AMT = 713.5
A_RULES = [
    (17.0, 70.0), (78.0, 235.0), (242.0, 300.0),
    (320.0, 370.0), (375.0, 445.0),
    (455.0, 520.0), (525.0, 585.0),
    (595.0, 655.0), (660.0, 720.0),
]
A_FOOTER_RULES = [
    (320.0, 370.0), (375.0, 445.0),
    (455.0, 520.0), (525.0, 585.0),
    (595.0, 655.0), (660.0, 720.0),
]


@dataclass
class _Layout:
    y: float
    page_num: int
    show_company: bool


def _num(value: float, *, blank_if_zero: bool = False, decimals: int = 2) -> str:
    return format_amount(value, decimals=decimals, blank_if_zero=blank_if_zero)


def _qty_plain(value: float) -> str:
    """Period/closing qty in amt report: show 0 / -3528 / 9156 style."""
    if abs(value - round(value)) < 0.0005:
        return f"{int(round(value)):,}"
    return format_amount(value, decimals=2, blank_if_zero=False)


def _set(
    c: canvas.Canvas,
    color=colors.black,
    size=FONT_DATA,
    bold=False,
    italic=False,
):
    c.setFillColor(color)
    if bold and italic:
        c.setFont("Helvetica-BoldOblique", size)
    elif bold:
        c.setFont("Helvetica-Bold", size)
    elif italic:
        c.setFont("Helvetica-Oblique", size)
    else:
        c.setFont("Helvetica", size)


def _right(c: canvas.Canvas, x: float, y: float, text: str, **font_kw):
    if text is None or text == "":
        return
    _set(c, **font_kw)
    c.drawRightString(x, y, text)


def _hline(c: canvas.Canvas, y: float, x1: float, x2: float, width: float = 0.5):
    c.setStrokeColor(COLOR_LINE)
    c.setLineWidth(width)
    c.line(x1, y, x2, y)


def _draw_title(c: canvas.Canvas, row: StockBalanceD2DRow, y: float, title_x: float, brand_x: float):
    _set(c, colors.black, size=FONT_DATA)
    max_title_w = brand_x - title_x - 6
    words = row.item_title.split()
    line1, line2 = row.item_title, ""
    if c.stringWidth(row.item_title, "Helvetica", FONT_DATA) > max_title_w and len(words) > 1:
        line1 = words[0]
        for w in words[1:]:
            trial = f"{line1} {w}"
            if c.stringWidth(trial, "Helvetica", FONT_DATA) <= max_title_w:
                line1 = trial
            else:
                line2 = " ".join(words[words.index(w):])
                break
        c.drawString(title_x, y, line1)
        if line2:
            c.drawString(title_x, y - 9, line2[:40])
    else:
        title = row.item_title
        while title and c.stringWidth(title, "Helvetica", FONT_DATA) > max_title_w:
            title = title[:-1]
        c.drawString(title_x, y, title[:48])


def _row_band(c: canvas.Canvas, y: float, zebra: bool, x1: float, x2: float):
    top = y + ROW_LINE_TOP
    bottom = y - 4
    if zebra:
        c.setFillColor(COLOR_ZEBRA)
        c.rect(x1 - 2, bottom, x2 - x1 + 4, top - bottom, stroke=0, fill=1)
    c.setStrokeColor(COLOR_ROW_LINE)
    c.setLineWidth(0.35)
    c.line(x1 + 30, top, x2, top)


# ----- Qty mode (RptStD2D) -----

def _draw_qty_header(c: canvas.Canvas, report: StockBalanceD2DData, layout: _Layout):
    y = PAGE_H - Q_MARGIN
    if layout.show_company:
        _set(c, COLOR_COMPANY, size=FONT_COMPANY, bold=True)
        c.drawString(Q_AC_ID, y - 4, report.company_name)
        y -= 22

    _set(c, COLOR_META, size=FONT_TITLE, bold=True)
    c.drawString(Q_AC_ID, y, report.report_title)
    _set(c, COLOR_META, size=8)
    c.drawRightString(Q_CLOSING, y + 4, report.printed_on)
    y -= 14
    c.drawRightString(Q_CLOSING, y, f"Page #:{layout.page_num}")
    y -= 14

    _set(c, colors.black, size=FONT_HDR, italic=True)
    c.drawString(Q_AC_ID, y, report.criteria)
    y -= 18

    _set(c, colors.black, size=FONT_HDR, bold=True)
    c.drawString(361.6, y, "Opening")
    c.drawString(433.0, y, "Transaction for the Period")
    c.drawString(568.0, y, "Net Transaction")
    c.drawString(694.6, y, "Closing")
    y -= 14

    c.drawString(Q_AC_ID, y, "Ac ID")
    c.drawString(Q_TITLE, y, "Account Title")
    c.drawString(Q_BRAND, y, "Brand")
    c.drawString(361.6, y, "Balance")
    c.drawString(433.0, y, "Stock In")
    c.drawString(501.0, y, "Stock Out")
    c.drawString(568.0, y, "Stock In")
    c.drawString(631.0, y, "Stock Out")
    c.drawString(694.6, y, "Balance")

    rule_y = y - 2.5
    for x1, x2 in Q_RULES:
        _hline(c, rule_y, x1, x2, width=0.4)
    layout.y = rule_y - 12


def _draw_qty_row(c: canvas.Canvas, y: float, row: StockBalanceD2DRow, zebra: bool):
    _row_band(c, y, zebra, Q_MARGIN, Q_CLOSING + 2)
    _set(c, colors.black, size=FONT_DATA)
    c.drawString(Q_AC_ID, y, row.item_id_display)
    _draw_title(c, row, y, Q_TITLE, Q_BRAND)
    c.drawString(Q_BRAND, y, row.brand or "Nil")

    net_in = _num(row.net_balance) if row.net_balance > 0 else ""
    net_out = _num(abs(row.net_balance)) if row.net_balance < 0 else ""
    _right(c, Q_OPENING, y, _num(row.opening_balance, blank_if_zero=False))
    _right(c, Q_STOCK_IN, y, _num(row.stock_in, blank_if_zero=True))
    _right(c, Q_STOCK_OUT, y, _num(row.stock_out, blank_if_zero=True))
    _right(c, Q_NET_IN, y, net_in)
    _right(c, Q_NET_OUT, y, net_out)
    _right(c, Q_CLOSING, y, _num(row.closing_balance, blank_if_zero=False))


def _draw_qty_footer(c: canvas.Canvas, report: StockBalanceD2DData, y_after: float):
    totals = report.totals
    sep_y = y_after - 6
    _hline(c, sep_y, 67.6, Q_CLOSING + 2, width=0.5)
    total_y = sep_y - 12
    for x1, x2 in Q_FOOTER_RULES:
        _hline(c, total_y + 8, x1, x2, width=0.4)

    _set(c, COLOR_META, size=FONT_DATA, italic=True)
    c.drawString(Q_AC_ID, total_y, f"Total record(s) Listed: {report.total_rows}")
    _set(c, colors.black, size=FONT_DATA, bold=True, italic=True)
    c.drawString(328.0, total_y, "Total :")
    _right(c, Q_OPENING, total_y, _num(totals.opening_balance), bold=True)
    _right(c, Q_STOCK_IN, total_y, _num(totals.stock_in), bold=True)
    _right(c, Q_STOCK_OUT, total_y, _num(totals.stock_out), bold=True)
    _right(c, Q_NET_IN, total_y, _num(totals.net_stock_in), bold=True)
    _right(c, Q_NET_OUT, total_y, _num(totals.net_stock_out), bold=True)
    _right(c, Q_CLOSING, total_y, _num(totals.closing_balance), bold=True)
    for x1, x2 in Q_FOOTER_RULES:
        _hline(c, total_y - 3, x1, x2, width=0.4)
        _hline(c, total_y - 4.8, x1, x2, width=0.4)


# ----- Amt mode (RptStD2DAmtBrand) -----

def _draw_amt_header(c: canvas.Canvas, report: StockBalanceD2DData, layout: _Layout):
    y = PAGE_H - 36
    if layout.show_company:
        _set(c, COLOR_COMPANY, size=FONT_COMPANY, bold=True)
        c.drawString(A_AC_ID, y - 4, report.company_name)
        y -= 22

    _set(c, COLOR_META, size=FONT_TITLE, bold=True)
    c.drawString(A_AC_ID, y, report.report_title)
    _set(c, COLOR_META, size=8)
    c.drawRightString(A_CLOSE_AMT, y + 4, report.printed_on)
    y -= 14
    c.drawRightString(A_CLOSE_AMT, y, f"Page #:{layout.page_num}")
    y -= 14

    _set(c, colors.black, size=FONT_HDR, italic=True)
    c.drawString(A_AC_ID, y, report.criteria)
    y -= 18

    # Group headers: Opening Stock | For The Period | Closing Stock
    _set(c, colors.black, size=FONT_HDR, bold=True)
    c.drawString(341.0, y, "Opening")
    c.drawString(401.5, y, "Stock")
    c.drawString(497.8, y, "For The Period")
    c.drawString(632.4, y, "Closing")
    c.drawString(671.8, y, "Stock")
    y -= 14

    c.drawString(A_AC_ID, y, "Ac ID")
    c.drawString(A_TITLE, y, "Account Title")
    c.drawString(A_BRAND, y, "Brand")
    c.drawString(341.0, y, "Qty")
    c.drawString(390.5, y, "Amt")
    c.drawString(471.5, y, "Qty")
    c.drawString(530.0, y, "Amt")
    c.drawString(602.0, y, "Qty")
    c.drawString(660.5, y, "Amt")

    rule_y = y - 2.5
    for x1, x2 in A_RULES:
        _hline(c, rule_y, x1, x2, width=0.4)
    layout.y = rule_y - 12


def _draw_amt_row(c: canvas.Canvas, y: float, row: StockBalanceD2DRow, zebra: bool):
    _row_band(c, y, zebra, A_AC_ID, A_CLOSE_AMT + 4)
    _set(c, colors.black, size=FONT_DATA)
    c.drawString(A_AC_ID, y, row.item_id_display)
    _draw_title(c, row, y, A_TITLE, A_BRAND)
    c.drawString(A_BRAND, y, row.brand or "Nil")

    # Opening blank if zero; period/closing always shown (incl. 0)
    _right(c, A_OPEN_QTY, y, _num(row.opening_qty, blank_if_zero=True))
    _right(c, A_OPEN_AMT, y, _num(row.opening_amt, blank_if_zero=True))
    _right(c, A_PER_QTY, y, _qty_plain(row.period_qty))
    _right(c, A_PER_AMT, y, _num(row.period_amt, blank_if_zero=False))
    _right(c, A_CLOSE_QTY, y, _qty_plain(row.closing_qty))
    _right(c, A_CLOSE_AMT, y, _num(row.closing_amt, blank_if_zero=False))


def _draw_amt_footer(c: canvas.Canvas, report: StockBalanceD2DData, y_after: float):
    totals = report.totals
    sep_y = y_after - 6
    _hline(c, sep_y, 50.0, A_CLOSE_AMT + 4, width=0.5)
    total_y = sep_y - 12
    for x1, x2 in A_FOOTER_RULES:
        _hline(c, total_y + 8, x1, x2, width=0.4)

    _set(c, COLOR_META, size=FONT_DATA, italic=True)
    c.drawString(A_AC_ID, total_y, f"Total record(s) Listed: {report.total_rows}")
    _set(c, colors.black, size=FONT_DATA, bold=True, italic=True)
    c.drawString(303.4, total_y, "Total :")

    _right(c, A_OPEN_QTY, total_y, _num(totals.opening_qty), bold=True)
    _right(c, A_OPEN_AMT, total_y, _num(totals.opening_amt), bold=True)
    _right(c, A_PER_QTY, total_y, _num(totals.period_qty), bold=True)
    _right(c, A_PER_AMT, total_y, _num(totals.period_amt), bold=True)
    _right(c, A_CLOSE_QTY, total_y, _num(totals.closing_qty), bold=True)
    _right(c, A_CLOSE_AMT, total_y, _num(totals.closing_amt), bold=True)

    for x1, x2 in A_FOOTER_RULES:
        _hline(c, total_y - 3, x1, x2, width=0.4)
        _hline(c, total_y - 4.8, x1, x2, width=0.4)


def render_stock_balance_d2d_pdf(report: StockBalanceD2DData) -> bytes:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=landscape(letter))
    c.setTitle(report.report_title.rstrip("."))

    amt = report.print_amount
    header_fn = _draw_amt_header if amt else _draw_qty_header
    row_fn = _draw_amt_row if amt else _draw_qty_row
    footer_fn = _draw_amt_footer if amt else _draw_qty_footer

    rows = report.rows
    min_y = 46
    row_i = 0
    page_num = 1
    show_company = True

    while row_i < len(rows):
        layout = _Layout(y=0, page_num=page_num, show_company=show_company)
        header_fn(c, report, layout)
        y = layout.y

        remaining = len(rows) - row_i
        rows_with_footer = int((y - min_y - FOOTER_BLOCK_HEIGHT) / ROW_LEADING)
        bottom = min_y + FOOTER_BLOCK_HEIGHT if remaining <= max(rows_with_footer, 0) else min_y

        last_row_y = y
        zebra = False
        while row_i < len(rows) and y >= bottom:
            last_row_y = y
            row_fn(c, y, rows[row_i], zebra)
            zebra = not zebra
            step = ROW_LEADING + 6 if len(rows[row_i].item_title) > 32 else ROW_LEADING
            y -= step
            row_i += 1

        if row_i >= len(rows):
            footer_fn(c, report, last_row_y)
        else:
            c.showPage()
            page_num += 1
            show_company = True

    c.save()
    return buffer.getvalue()
