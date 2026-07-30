"""PDF renderer for General Ledger report (VB6 GL_LEDGER / PDF_ALrahim layout)."""

from __future__ import annotations

from io import BytesIO
from typing import Iterable, List

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.schemas.gl_ledger_report import GlLedgerAccountSection, GlLedgerReportData, GlLedgerTransactionRow
from app.utils.money_format import format_amount

PAGE_WIDTH, PAGE_HEIGHT = landscape(A4)
LEFT_MARGIN = 10 * mm
RIGHT_MARGIN = 10 * mm
TOP_MARGIN = 42 * mm
BOTTOM_MARGIN = 12 * mm
USABLE_WIDTH = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN

ROWS_PER_CHUNK = 28
LINE_COLOR = colors.HexColor("#666666")
CELL_PAD = 4

# Column order:
# Date | Voucher (no) | Bn | Voucher (type) | Reference | Narration | Debit | Credit | Running Bal.
COL_DATE = 0
COL_VOUCHER_NO = 1
COL_BN = 2
COL_VOUCHER_TYPE = 3
COL_REFERENCE = 4
COL_NARRATION = 5
COL_DEBIT = 6
COL_CREDIT = 7
COL_RUNNING = 8

_FIXED_COL_MM = 18 + 14 + 10 + 14 + 18 + 24 + 24 + 26
_NARRATION_MM = max(USABLE_WIDTH / mm - _FIXED_COL_MM, 50)
COL_WIDTHS = [
    18 * mm,   # Date
    14 * mm,   # Voucher no
    10 * mm,   # Bn
    14 * mm,   # Voucher type
    18 * mm,   # Reference
    _NARRATION_MM * mm,
    24 * mm,   # Debit
    24 * mm,   # Credit
    26 * mm,   # Running Bal.
]
HEADERS = [
    "Date",
    "Voucher",
    "Bn",
    "Voucher",
    "Reference",
    "Narration",
    "Debit",
    "Credit",
    "Running Bal.",
]

NARRATION_STYLE = ParagraphStyle(
    "gl_narration",
    fontName="Helvetica",
    fontSize=7,
    leading=8,
    alignment=0,
)
ACCOUNT_STYLE = ParagraphStyle(
    "gl_account",
    fontName="Helvetica-Bold",
    fontSize=8,
    leading=9,
    alignment=0,
)


def _money(value: float, *, always: bool = False) -> str:
    return format_amount(value, decimals=2, blank_if_zero=not always)


def _count(value: int) -> str:
    return f"{value:,}"


def _fmt_date(value) -> str:
    if not value:
        return ""
    return value.strftime("%d/%m/%Y")


def _para(text: str, style: ParagraphStyle = NARRATION_STYLE) -> Paragraph | str:
    safe = (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    if not safe:
        return ""
    return Paragraph(safe, style)


def _draw_page_header(canvas, doc, report: GlLedgerReportData):
    """Match PDF_ALrahim.pdf page header on every page."""
    canvas.saveState()

    # 1) Company name at the very top, centered.
    y = PAGE_HEIGHT - 7 * mm
    canvas.setFont("Helvetica-Bold", 11)
    canvas.drawCentredString(PAGE_WIDTH / 2, y, report.company_name)

    # 2) Ac ID | report title | print date
    y -= 6 * mm
    canvas.setFont("Helvetica", 8)
    canvas.drawString(LEFT_MARGIN, y, "Ac ID")
    canvas.setFont("Helvetica-Bold", 10)
    canvas.drawCentredString(PAGE_WIDTH / 2, y, report.report_title)
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(PAGE_WIDTH - RIGHT_MARGIN, y, report.printed_on)

    # 3) Page number (right)
    y -= 4.5 * mm
    canvas.drawRightString(PAGE_WIDTH - RIGHT_MARGIN, y, f"Page #:{doc.page}")

    # 4) Selection criteria
    y -= 5 * mm
    canvas.drawString(LEFT_MARGIN, y, report.criteria)

    # 5) Account title label
    y -= 4 * mm
    canvas.drawString(LEFT_MARGIN, y, "Account Title")

    # 6) Column headers
    y -= 5 * mm
    canvas.setFont("Helvetica-Bold", 7)
    x = LEFT_MARGIN
    right_aligned = {"Debit", "Credit", "Running Bal."}
    for i, (header, width) in enumerate(zip(HEADERS, COL_WIDTHS)):
        if header in right_aligned:
            canvas.drawRightString(x + width - 1 * mm, y, header)
        elif header == "Bn":
            canvas.drawCentredString(x + width / 2, y, header)
        else:
            canvas.drawString(x + 1 * mm, y, header)
        x += width

    # Line under column headers
    y -= 1.5 * mm
    canvas.setStrokeColor(LINE_COLOR)
    canvas.setLineWidth(0.5)
    canvas.line(LEFT_MARGIN, y, PAGE_WIDTH - RIGHT_MARGIN, y)

    canvas.restoreState()


def _chunk_rows(items: List[GlLedgerTransactionRow], size: int) -> Iterable[List[GlLedgerTransactionRow]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


def _transaction_row(tx: GlLedgerTransactionRow) -> list:
    row = [""] * 9
    row[COL_DATE] = _fmt_date(tx.voucher_date)
    row[COL_VOUCHER_NO] = tx.voucher_no
    row[COL_BN] = "" if tx.book_id is None else str(tx.book_id)
    row[COL_VOUCHER_TYPE] = tx.voucher_type
    row[COL_REFERENCE] = tx.reference
    row[COL_NARRATION] = _para(tx.narration)
    row[COL_DEBIT] = _money(tx.debit)
    row[COL_CREDIT] = _money(tx.credit)
    row[COL_RUNNING] = _money(tx.balance, always=True)
    return row


def _blank_row() -> list[str]:
    return [""] * 9


def _table_style(header_rows: int = 0, footer_row: int | None = None) -> TableStyle:
    style = TableStyle(
        [
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("ALIGN", (0, 0), (COL_VOUCHER_TYPE, -1), "LEFT"),
            ("ALIGN", (COL_NARRATION, 0), (COL_NARRATION, -1), "LEFT"),
            ("ALIGN", (COL_BN, 0), (COL_BN, -1), "CENTER"),
            ("ALIGN", (COL_DEBIT, 0), (COL_RUNNING, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), CELL_PAD),
            ("RIGHTPADDING", (0, 0), (-1, -1), CELL_PAD),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            # Extra gap before narration and amount columns.
            ("RIGHTPADDING", (COL_REFERENCE, 0), (COL_REFERENCE, -1), CELL_PAD + 4),
            ("LEFTPADDING", (COL_NARRATION, 0), (COL_NARRATION, -1), CELL_PAD + 4),
            ("LEFTPADDING", (COL_DEBIT, 0), (COL_DEBIT, -1), CELL_PAD + 6),
            ("LINEBELOW", (0, 0), (-1, -1), 0.25, LINE_COLOR),
        ]
    )
    if header_rows:
        style.add("FONTNAME", (0, 0), (-1, header_rows - 1), "Helvetica-Bold")
    if footer_row is not None:
        style.add("FONTNAME", (0, footer_row), (-1, footer_row), "Helvetica-Bold")
        style.add("LINEABOVE", (0, footer_row), (-1, footer_row), 0.5, LINE_COLOR)
        style.add("ALIGN", (COL_NARRATION, footer_row), (COL_NARRATION, footer_row), "LEFT")
        style.add("ALIGN", (COL_RUNNING, footer_row), (COL_RUNNING, footer_row), "RIGHT")
    return style


def _account_tables(section: GlLedgerAccountSection) -> list[Table]:
    tables: list[Table] = []
    account_label = _para(f"{section.ac_id_display}  {section.ac_title}", ACCOUNT_STYLE)
    opening_row = _blank_row()
    opening_row[COL_NARRATION] = "Opening Balance :"
    opening_row[COL_DEBIT] = _money(section.opening_debit)
    opening_row[COL_CREDIT] = _money(section.opening_credit)
    opening_row[COL_RUNNING] = _money(section.opening_balance, always=True)
    chunks = list(_chunk_rows(section.transactions, ROWS_PER_CHUNK)) or [[]]

    for index, chunk in enumerate(chunks):
        footer_row = None
        if index == 0:
            data = [
                [account_label, "", "", "", "", "", "", "", ""],
                opening_row,
            ]
            data.extend(_transaction_row(tx) for tx in chunk)
            header_rows = 1
        else:
            data = [_transaction_row(tx) for tx in chunk]
            header_rows = 0

        if section.transaction_count > 0 and index == len(chunks) - 1:
            footer = _blank_row()
            footer[COL_VOUCHER_NO] = _count(section.transaction_count)
            footer[COL_NARRATION] = "Number of transaction(s):"
            footer[COL_DEBIT] = _money(section.total_debit, always=True)
            footer[COL_CREDIT] = _money(section.total_credit, always=True)
            footer[COL_RUNNING] = "Total:"
            data.append(footer)
            footer_row = len(data) - 1

        table = Table(data, colWidths=COL_WIDTHS, repeatRows=0)
        style = _table_style(header_rows, footer_row)
        if index == 0:
            style.add("SPAN", (0, 0), (-1, 0))
            style.add("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold")
            style.add("LINEABOVE", (0, 0), (-1, 0), 0.5, LINE_COLOR)
        table.setStyle(style)
        tables.append(table)
    return tables


def render_gl_ledger_pdf(report: GlLedgerReportData) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=LEFT_MARGIN,
        rightMargin=RIGHT_MARGIN,
        topMargin=TOP_MARGIN,
        bottomMargin=BOTTOM_MARGIN,
        title=report.report_title,
    )
    footer_style = ParagraphStyle("footer", fontName="Helvetica", fontSize=8, alignment=2)
    story: list = []

    for idx, section in enumerate(report.accounts):
        for table in _account_tables(section):
            story.append(table)
            story.append(Spacer(1, 1 * mm))
        if report.page_wise and idx < len(report.accounts) - 1:
            story.append(PageBreak())

    story.append(
        Paragraph(
            f"Total account(s) listed: {report.total_accounts:,}",
            footer_style,
        )
    )

    doc.build(
        story,
        onFirstPage=lambda c, d: _draw_page_header(c, d, report),
        onLaterPages=lambda c, d: _draw_page_header(c, d, report),
    )
    return buffer.getvalue()
