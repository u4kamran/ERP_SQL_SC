"""PDF renderer for Trial Balance Date to Date — matches VB6 / ERP screen layout."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas

from app.schemas.trial_balance_d2d import TrialBalanceD2DData, TrialBalanceD2DRow
from app.utils.money_format import format_amount

PAGE_W, PAGE_H = landscape(A4)
MARGIN = 36

COLOR_COMPANY = colors.HexColor("#006400")
COLOR_META = colors.HexColor("#00008B")
COLOR_LINE = colors.HexColor("#000000")
COLOR_DASH = colors.HexColor("#CCCCCC")
COLOR_ROW_LINE = colors.HexColor("#BBBBBB")

ROW_LEADING = 11.5
ROW_GAP_BEFORE_FOOTER = 5   # gap from last record baseline to separator line
FOOTER_DEBIT_OFFSET = 7     # debit row below separator line
FOOTER_DEBIT_TO_CREDIT = 11   # credit row baseline — tight under debit underline
FOOTER_CREDIT_TO_DIFF = 11    # difference row baseline — tight under credit underline
FOOTER_RECORD_BELOW_DEBIT = 5
FOOTER_RULE_ABOVE = 7
FOOTER_UNDERLINE_DROP = 3
ROW_LINE_TOP = 7.5  # light line at top of row band (above values, not below)
FONT_DATA = 7
FONT_HDR = 8
FONT_TITLE = 10
FONT_COMPANY = 12

COL_AC_ID = MARGIN
COL_TITLE = MARGIN + 62
# Right edges — Opening | Trans Dr | Trans Cr | Net Dr | Net Cr | Closing (last)
COL_OPENING = 406
COL_TRANS_DR = 486
COL_TRANS_CR = 561
COL_NET_DR = 661
COL_NET_CR = 731
COL_CLOSING = PAGE_W - MARGIN

LABEL_END = 285
DIVIDER_X = [310, COL_OPENING, COL_TRANS_CR, COL_NET_CR, COL_CLOSING]
FOOTER_BLOCK_HEIGHT = 44
RULE_WIDTH = 64
FOOTER_AMOUNT_LEFT = 340  # left edge of full total rule (matches VB6)
COL_RULE_LEFT = {
    COL_OPENING: 340,
    COL_TRANS_DR: 420,
    COL_TRANS_CR: 495,
    COL_NET_DR: 595,
    COL_NET_CR: 665,
    COL_CLOSING: PAGE_W - MARGIN - RULE_WIDTH,
}


@dataclass
class _Layout:
    y: float
    page_num: int
    show_company: bool


def _money(value: float, *, blank_if_zero: bool = True) -> str:
    return format_amount(value, decimals=2, blank_if_zero=blank_if_zero)


def _signed(value: float) -> str:
    if value == 0:
        return ""
    return format_amount(value, decimals=2, blank_if_zero=False)


def _set(
    c: canvas.Canvas,
    color=colors.black,
    font="Helvetica",
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
        c.setFont(font, size)


def _right(c: canvas.Canvas, x: float, y: float, text: str, **font_kw):
    if not text:
        return
    _set(c, **font_kw)
    c.drawRightString(x, y, text)


def _label(c: canvas.Canvas, y: float, text: str, **font_kw):
    _set(c, **font_kw)
    c.drawRightString(LABEL_END, y, text)


def _dash_verticals(c: canvas.Canvas, y_top: float, y_bottom: float):
    c.setStrokeColor(COLOR_DASH)
    c.setDash(2, 2)
    c.setLineWidth(0.4)
    for x in DIVIDER_X:
        c.line(x, y_bottom, x, y_top)
    c.setDash()


def _hline(c: canvas.Canvas, y: float, width: float = 0.5):
    c.setStrokeColor(COLOR_LINE)
    c.setLineWidth(width)
    c.line(MARGIN, y, PAGE_W - MARGIN, y)


def _draw_top_header(c: canvas.Canvas, report: TrialBalanceD2DData, layout: _Layout):
    y = PAGE_H - MARGIN

    if layout.show_company:
        _set(c, COLOR_COMPANY, size=FONT_COMPANY, bold=True)
        c.drawString(MARGIN, y, report.company_name)
        y -= 18

    _set(c, COLOR_META, size=FONT_TITLE, bold=True)
    c.drawString(MARGIN, y, report.report_title)
    _set(c, COLOR_META, size=FONT_HDR)
    c.drawRightString(PAGE_W - MARGIN, y, report.printed_on)
    y -= 13

    c.drawRightString(PAGE_W - MARGIN, y, f"Page #:{layout.page_num}")
    y -= 13

    _set(c, colors.black, size=FONT_HDR, italic=True)
    c.drawString(MARGIN, y, report.criteria)
    y -= 14

    header_top = y + 2
    _hline(c, y)
    y -= 12

    if report.short_format:
        _set(c, colors.black, size=7, bold=True)
        c.drawString(COL_AC_ID, y, "Ac ID")
        c.drawString(COL_TITLE, y, "Account Title")
        _right(c, COL_TRANS_DR, y, "Debit", bold=True, size=7)
        _right(c, COL_TRANS_CR, y, "Credit", bold=True, size=7)
        y -= 10
        _right(c, COL_TRANS_DR, y, "Closing", bold=True, size=7)
    else:
        # Row 1 — Opening Balance | groups | Closing Balance
        _set(c, colors.black, size=7, bold=True)
        c.drawString(COL_AC_ID, y, "Ac ID")
        c.drawString(COL_TITLE, y, "Account Title")
        _right(c, COL_OPENING, y, "Opening Balance", bold=True, size=7)
        c.drawCentredString((COL_TRANS_DR + COL_TRANS_CR) / 2, y, "Transaction for the Period")
        c.drawCentredString((COL_NET_DR + COL_NET_CR) / 2, y, "Net Transaction")
        _right(c, COL_CLOSING, y, "Closing Balance", bold=True, size=7)
        y -= 10

        # Row 2 — Debit / Credit under transaction and net only
        _right(c, COL_TRANS_DR, y, "Debit", bold=True, size=7)
        _right(c, COL_TRANS_CR, y, "Credit", bold=True, size=7)
        _right(c, COL_NET_DR, y, "Debit", bold=True, size=7)
        _right(c, COL_NET_CR, y, "Credit", bold=True, size=7)

    y -= 4
    _hline(c, y)
    _dash_verticals(c, header_top, y)
    y -= 8
    layout.y = y


def _draw_data_row(c: canvas.Canvas, y: float, row: TrialBalanceD2DRow):
    _set(c, colors.black, size=FONT_DATA)
    c.drawString(COL_AC_ID, y, row.ac_id_display)
    c.drawString(COL_TITLE, y, row.ac_title[:72])

    net_dr = _money(row.net_balance) if row.net_balance > 0 else ""
    net_cr = _money(abs(row.net_balance)) if row.net_balance < 0 else ""

    _right(c, COL_OPENING, y, _signed(row.opening_balance))
    _right(c, COL_TRANS_DR, y, _money(row.period_debit))
    _right(c, COL_TRANS_CR, y, _money(row.period_credit))
    _right(c, COL_NET_DR, y, net_dr)
    _right(c, COL_NET_CR, y, net_cr)
    _right(c, COL_CLOSING, y, _signed(row.closing_balance))


def _draw_short_row(c: canvas.Canvas, y: float, row: TrialBalanceD2DRow):
    _set(c, colors.black, size=FONT_DATA)
    c.drawString(COL_AC_ID, y, row.ac_id_display)
    c.drawString(COL_TITLE, y, row.ac_title[:72])
    cl_dr = _money(row.closing_balance) if row.closing_balance > 0 else ""
    cl_cr = _money(abs(row.closing_balance)) if row.closing_balance < 0 else ""
    _right(c, COL_TRANS_DR, y, cl_dr)
    _right(c, COL_TRANS_CR, y, cl_cr)


def _row_light_line_above(c: canvas.Canvas, y: float):
    """Light separator at top of row band — above values, not dangling below them."""
    line_y = y + ROW_LINE_TOP
    c.setStrokeColor(COLOR_ROW_LINE)
    c.setLineWidth(0.25)
    c.line(MARGIN, line_y, PAGE_W - MARGIN, line_y)


def _footer_full_rule(c: canvas.Canvas, y: float):
    """Single continuous rule above Total Debit spanning all amount columns."""
    c.setStrokeColor(COLOR_LINE)
    c.setLineWidth(0.5)
    c.line(FOOTER_AMOUNT_LEFT, y, COL_CLOSING, y)


def _footer_rule(c: canvas.Canvas, y: float, cols: list[float]):
    c.setStrokeColor(COLOR_LINE)
    c.setLineWidth(0.5)
    for x in cols:
        left = COL_RULE_LEFT.get(x, x - RULE_WIDTH)
        c.line(left, y, x, y)


def _footer_double_rule(c: canvas.Canvas, y: float, cols: list[float]):
    c.setStrokeColor(COLOR_LINE)
    c.setLineWidth(0.5)
    for x in cols:
        left = COL_RULE_LEFT.get(x, x - RULE_WIDTH)
        c.line(left, y, x, y)
        c.line(left, y - 2, x, y - 2)


def _draw_footer_row(
    c: canvas.Canvas,
    y: float,
    label: str,
    pairs: list[tuple[float, str]],
    *,
    full_rule_above: bool = False,
    single_under: list[float] | None = None,
    double_under: list[float] | None = None,
):
    """One footer row — VB6 style: full rule above debit; underlines on opening/closing only."""
    if full_rule_above:
        _footer_full_rule(c, y + FOOTER_RULE_ABOVE)
    if label:
        _label(c, y, label, bold=True, italic=True, size=7)
    for col, text in pairs:
        if text:
            _right(c, col, y, text, bold=True, size=7)
    if single_under:
        _footer_rule(c, y - FOOTER_UNDERLINE_DROP, single_under)
    if double_under:
        _footer_double_rule(c, y - FOOTER_UNDERLINE_DROP, double_under)


def _draw_footer(c: canvas.Canvas, report: TrialBalanceD2DData, y_after_data: float):
    totals = report.totals
    sep_y = y_after_data - ROW_GAP_BEFORE_FOOTER
    _hline(c, sep_y)

    debit_y = sep_y - FOOTER_DEBIT_OFFSET
    opening_closing = [COL_OPENING, COL_CLOSING]
    all_amount_cols = [
        COL_OPENING, COL_TRANS_DR, COL_TRANS_CR, COL_NET_DR, COL_NET_CR, COL_CLOSING,
    ]

    if report.short_format:
        _draw_footer_row(
            c, debit_y, "Total Debit :",
            [
                (COL_TRANS_DR, _money(totals.closing_debit)),
                (COL_TRANS_CR, _money(totals.closing_credit)),
            ],
            full_rule_above=True,
            single_under=[COL_TRANS_DR, COL_TRANS_CR],
        )
        _set(c, COLOR_META, size=7, italic=True)
        c.drawString(MARGIN, debit_y - FOOTER_RECORD_BELOW_DEBIT,
                     f"Total record(s) Listed: {report.total_rows:,}")
        credit_y = debit_y - FOOTER_DEBIT_TO_CREDIT
        _draw_footer_row(
            c, credit_y, "Total Credit :",
            [(COL_TRANS_CR, _money(totals.closing_credit))],
            single_under=[COL_TRANS_CR],
        )
        diff_y = credit_y - FOOTER_CREDIT_TO_DIFF
        _draw_footer_row(
            c, diff_y, "Difference :",
            [(COL_TRANS_CR, _signed(totals.diff_closing))],
            double_under=[COL_TRANS_CR],
        )
        _dash_verticals(c, debit_y + FOOTER_RULE_ABOVE + 2, diff_y - 6)
        return

    _draw_footer_row(
        c, debit_y, "Total Debit :",
        [
            (COL_OPENING, _money(totals.opening_debit)),
            (COL_TRANS_DR, _money(totals.period_debit)),
            (COL_TRANS_CR, _money(totals.period_credit)),
            (COL_NET_DR, _money(totals.net_debit)),
            (COL_NET_CR, _money(totals.net_credit)),
            (COL_CLOSING, _money(totals.closing_debit)),
        ],
        full_rule_above=True,
        single_under=all_amount_cols,
    )
    _set(c, COLOR_META, size=7, italic=True)
    c.drawString(MARGIN, debit_y - FOOTER_RECORD_BELOW_DEBIT,
                 f"Total record(s) Listed: {report.total_rows:,}")

    credit_y = debit_y - FOOTER_DEBIT_TO_CREDIT
    _draw_footer_row(
        c, credit_y, "Total Credit :",
        [
            (COL_OPENING, _signed(totals.opening_credit_signed)),
            (COL_CLOSING, _money(totals.closing_credit)),
        ],
        single_under=opening_closing,
    )
    diff_y = credit_y - FOOTER_CREDIT_TO_DIFF
    _draw_footer_row(
        c, diff_y, "Difference :",
        [
            (COL_OPENING, _signed(totals.diff_opening)),
            (COL_CLOSING, _signed(totals.diff_closing)),
        ],
        double_under=opening_closing,
    )
    _dash_verticals(c, debit_y + FOOTER_RULE_ABOVE + 2, diff_y - 6)


def render_trial_balance_d2d_pdf(report: TrialBalanceD2DData) -> bytes:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=landscape(A4))
    c.setTitle(report.report_title)

    rows = report.rows
    short = report.short_format
    row_fn = _draw_short_row if short else _draw_data_row
    min_y = MARGIN + 8

    row_i = 0
    page_num = 1
    show_company = True

    while row_i < len(rows):
        layout = _Layout(y=0, page_num=page_num, show_company=show_company)
        _draw_top_header(c, report, layout)
        y = layout.y

        remaining = len(rows) - row_i
        rows_with_footer = int((y - min_y - FOOTER_BLOCK_HEIGHT) / ROW_LEADING)
        if remaining <= max(rows_with_footer, 0):
            bottom = min_y + FOOTER_BLOCK_HEIGHT
        else:
            bottom = min_y

        last_row_y = y
        while row_i < len(rows) and y >= bottom:
            last_row_y = y
            _row_light_line_above(c, y)
            row_fn(c, y, rows[row_i])
            y -= ROW_LEADING
            row_i += 1

        if row_i >= len(rows):
            _draw_footer(c, report, last_row_y)
        else:
            c.showPage()
            page_num += 1
            show_company = False

    c.save()
    return buffer.getvalue()
