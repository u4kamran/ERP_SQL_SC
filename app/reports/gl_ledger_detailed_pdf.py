"""PDF renderer for Detailed Customer Ledger (parallel to gl_ledger_pdf).

Parent ledger rows keep the existing GL format.
Invoice line detail uses a nested table with data-aware column widths.
"""

from __future__ import annotations

from io import BytesIO
from typing import Iterable, List, Sequence

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.schemas.gl_ledger_detailed import (
    GlLedgerDetailedAccountSection,
    GlLedgerDetailedReportData,
    GlLedgerDetailedTransactionRow,
    GlLedgerInvoiceDetailLine,
)
from app.utils.money_format import format_amount
from app.utils.report_col_widths import ColSpec, allocate_widths, measure_content_width

PAGE_WIDTH, PAGE_HEIGHT = landscape(A4)
LEFT_MARGIN = 8 * mm
RIGHT_MARGIN = 8 * mm
TOP_MARGIN = 42 * mm
BOTTOM_MARGIN = 12 * mm
USABLE_WIDTH = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN

ROWS_PER_CHUNK = 20
LINE_COLOR = colors.HexColor("#666666")
DETAIL_BG = colors.HexColor("#F5F7FA")
DETAIL_HEADER_BG = colors.HexColor("#E8EEF5")
CELL_PAD = 3

# Parent: Date | Voucher | Bn | Type | Reference | Narration | Debit | Credit | Running Bal.
COL_DATE = 0
COL_VOUCHER_NO = 1
COL_BN = 2
COL_VOUCHER_TYPE = 3
COL_REFERENCE = 4
COL_NARRATION = 5
COL_DEBIT = 6
COL_CREDIT = 7
COL_RUNNING = 8

_FIXED_COL_MM = 16 + 12 + 8 + 12 + 14 + 22 + 22 + 24
_NARRATION_MM = max(USABLE_WIDTH / mm - _FIXED_COL_MM, 40)
COL_WIDTHS = [
    16 * mm,
    12 * mm,
    8 * mm,
    12 * mm,
    14 * mm,
    _NARRATION_MM * mm,
    22 * mm,
    22 * mm,
    24 * mm,
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

# Nested invoice-detail columns (under each sales TX)
DETAIL_SPECS: tuple[ColSpec, ...] = (
    ColSpec("item", "Item Title", min_pt=55, max_pt=260, flex=8.0, font_size=6.5),
    ColSpec("gp", "GP", min_pt=22, max_pt=48, flex=0.2, font_size=6.5),
    ColSpec("bill", "Bill", min_pt=22, max_pt=48, flex=0.2, font_size=6.5),
    ColSpec("qty", "Qty", min_pt=34, max_pt=58, flex=0.1, font_size=6.5),
    ColSpec("rate", "Rate", min_pt=34, max_pt=58, flex=0.1, font_size=6.5),
    ColSpec("value", "Value", min_pt=42, max_pt=72, flex=0.15, font_size=6.5),
    ColSpec("gst", "GST", min_pt=22, max_pt=42, flex=0.05, font_size=6.5),
)

NARRATION_STYLE = ParagraphStyle(
    "gl_det_narration",
    fontName="Helvetica",
    fontSize=7,
    leading=8,
    alignment=0,
)
DETAIL_ITEM_STYLE = ParagraphStyle(
    "gl_det_item",
    fontName="Helvetica",
    fontSize=6.5,
    leading=7.5,
    alignment=0,
    textColor=colors.HexColor("#222222"),
)
DETAIL_HEADER_STYLE = ParagraphStyle(
    "gl_det_hdr",
    fontName="Helvetica-Bold",
    fontSize=6.5,
    leading=7.5,
    alignment=0,
)
ACCOUNT_STYLE = ParagraphStyle(
    "gl_det_account",
    fontName="Helvetica-Bold",
    fontSize=8,
    leading=9,
    alignment=0,
)


def _money(value: float, *, always: bool = False) -> str:
    return format_amount(value, decimals=2, blank_if_zero=not always)


def _qty(value: float | None) -> str:
    if value is None:
        return ""
    return format_amount(value, decimals=2, blank_if_zero=False)


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
    # Allow soft breaks on long codes without spaces
    safe = safe.replace("***", "***&#8203;")
    safe = safe.replace("-", "-&#8203;")
    return Paragraph(safe, style)


def _collect_detail_lines(report: GlLedgerDetailedReportData) -> list[GlLedgerInvoiceDetailLine]:
    lines: list[GlLedgerInvoiceDetailLine] = []
    for section in report.accounts:
        for tx in section.transactions:
            lines.extend(tx.line_details)
    return lines


def _detail_cell_strings(line: GlLedgerInvoiceDetailLine) -> tuple[str, str, str, str, str, str, str]:
    return (
        (line.item_title or "").strip() or "Item",
        (line.gate_pass or "").strip() or "-",
        (line.bill_no or "").strip() or "-",
        _qty(line.qty) or "-",
        _money(line.rate or 0) if line.rate is not None else "-",
        _money(line.value or 0) if line.value is not None else "-",
        (line.gst_display or "-").strip() or "-",
    )


def compute_detail_col_widths(
    lines: Sequence[GlLedgerInvoiceDetailLine],
    available_pt: float = USABLE_WIDTH,
) -> list[float]:
    """Data-aware widths for the nested detail table from the current report lines."""
    buckets: list[list[str]] = [[] for _ in DETAIL_SPECS]
    for line in lines:
        cells = _detail_cell_strings(line)
        for i, value in enumerate(cells):
            buckets[i].append(value)

    content_widths = [
        measure_content_width(
            buckets[i],
            header=spec.header,
            font_name=spec.font_name,
            font_size=spec.font_size,
            header_font_size=spec.header_font_size,
            pad_pt=spec.pad_pt,
        )
        for i, spec in enumerate(DETAIL_SPECS)
    ]
    return allocate_widths(DETAIL_SPECS, content_widths, available_pt)


def _draw_page_header(canvas, doc, report: GlLedgerDetailedReportData):
    canvas.saveState()
    y = PAGE_HEIGHT - 7 * mm
    canvas.setFont("Helvetica-Bold", 11)
    canvas.drawCentredString(PAGE_WIDTH / 2, y, report.company_name)

    y -= 6 * mm
    canvas.setFont("Helvetica", 8)
    canvas.drawString(LEFT_MARGIN, y, "Ac ID")
    canvas.setFont("Helvetica-Bold", 10)
    canvas.drawCentredString(PAGE_WIDTH / 2, y, report.report_title)
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(PAGE_WIDTH - RIGHT_MARGIN, y, report.printed_on)

    y -= 4.5 * mm
    canvas.drawRightString(PAGE_WIDTH - RIGHT_MARGIN, y, f"Page #:{doc.page}")

    y -= 5 * mm
    canvas.drawString(LEFT_MARGIN, y, report.criteria)

    y -= 4 * mm
    detail_note = "Invoice line detail under sales transactions" if report.include_invoice_detail else ""
    canvas.drawString(LEFT_MARGIN, y, f"Account Title    {detail_note}".rstrip())

    y -= 5 * mm
    canvas.setFont("Helvetica-Bold", 7)
    x = LEFT_MARGIN
    right_aligned = {"Debit", "Credit", "Running Bal."}
    for header, width in zip(HEADERS, COL_WIDTHS):
        if header in right_aligned:
            canvas.drawRightString(x + width - 1 * mm, y, header)
        elif header == "Bn":
            canvas.drawCentredString(x + width / 2, y, header)
        else:
            canvas.drawString(x + 1 * mm, y, header)
        x += width

    y -= 1.5 * mm
    canvas.setStrokeColor(LINE_COLOR)
    canvas.setLineWidth(0.5)
    canvas.line(LEFT_MARGIN, y, PAGE_WIDTH - RIGHT_MARGIN, y)
    canvas.restoreState()


def _blank_row() -> list[str]:
    return [""] * 9


def _transaction_row(tx: GlLedgerDetailedTransactionRow) -> list:
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


def _detail_header_inner(widths: list[float]) -> Table:
    headers = [spec.header for spec in DETAIL_SPECS]
    data = [[_para(h, DETAIL_HEADER_STYLE) for h in headers]]
    table = Table(data, colWidths=widths)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), DETAIL_HEADER_BG),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 6.5),
                ("ALIGN", (3, 0), (-1, 0), "RIGHT"),
                ("ALIGN", (0, 0), (2, 0), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 1),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                ("BOX", (0, 0), (-1, -1), 0.25, LINE_COLOR),
            ]
        )
    )
    return table


def _detail_data_inner(line: GlLedgerInvoiceDetailLine, widths: list[float]) -> Table:
    item, gp, bill, qty, rate, value, gst = _detail_cell_strings(line)
    data = [[
        _para(item, DETAIL_ITEM_STYLE),
        gp,
        bill,
        qty,
        rate,
        value,
        gst,
    ]]
    table = Table(data, colWidths=widths)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), DETAIL_BG),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 6.5),
                ("ALIGN", (0, 0), (2, -1), "LEFT"),
                ("ALIGN", (3, 0), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 1),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                ("BOX", (0, 0), (-1, -1), 0.2, LINE_COLOR),
                ("LINEBELOW", (0, 0), (-1, -1), 0.15, LINE_COLOR),
            ]
        )
    )
    return table


def _spanned_detail_row(inner: Table) -> list:
    """Place nested detail table across the full parent ledger width."""
    row = [""] * 9
    row[0] = inner
    return row


def _flatten_transactions(
    transactions: List[GlLedgerDetailedTransactionRow],
    detail_widths: list[float],
) -> list[tuple[str, list]]:
    """Return list of (kind, row) where kind is tx | detail_hdr | detail."""
    out: list[tuple[str, list]] = []
    for tx in transactions:
        out.append(("tx", _transaction_row(tx)))
        if not tx.line_details:
            continue
        out.append(("detail_hdr", _spanned_detail_row(_detail_header_inner(detail_widths))))
        for line in tx.line_details:
            out.append(("detail", _spanned_detail_row(_detail_data_inner(line, detail_widths))))
    return out


def _chunk_pairs(items: list[tuple[str, list]], size: int) -> Iterable[list[tuple[str, list]]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


def _table_style(
    header_rows: int = 0,
    footer_row: int | None = None,
    span_rows: list[int] | None = None,
) -> TableStyle:
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
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("LINEBELOW", (0, 0), (-1, -1), 0.25, LINE_COLOR),
        ]
    )
    if header_rows:
        style.add("FONTNAME", (0, 0), (-1, header_rows - 1), "Helvetica-Bold")
    for r in span_rows or []:
        style.add("SPAN", (0, r), (-1, r))
        style.add("LEFTPADDING", (0, r), (-1, r), 1)
        style.add("RIGHTPADDING", (0, r), (-1, r), 1)
        style.add("TOPPADDING", (0, r), (-1, r), 1)
        style.add("BOTTOMPADDING", (0, r), (-1, r), 1)
        style.add("LINEBELOW", (0, r), (-1, r), 0, colors.white)
    if footer_row is not None:
        style.add("FONTNAME", (0, footer_row), (-1, footer_row), "Helvetica-Bold")
        style.add("LINEABOVE", (0, footer_row), (-1, footer_row), 0.5, LINE_COLOR)
    return style


def _account_tables(
    section: GlLedgerDetailedAccountSection,
    detail_widths: list[float],
) -> list[Table]:
    tables: list[Table] = []
    account_label = _para(f"{section.ac_id_display}  {section.ac_title}", ACCOUNT_STYLE)
    opening_row = _blank_row()
    opening_row[COL_NARRATION] = "Opening Balance :"
    opening_row[COL_DEBIT] = _money(section.opening_debit)
    opening_row[COL_CREDIT] = _money(section.opening_credit)
    opening_row[COL_RUNNING] = _money(section.opening_balance, always=True)

    flat = _flatten_transactions(section.transactions, detail_widths)
    chunks = list(_chunk_pairs(flat, ROWS_PER_CHUNK)) or [[]]

    for index, chunk in enumerate(chunks):
        footer_row = None
        span_rows: list[int] = []
        if index == 0:
            data = [
                [account_label, "", "", "", "", "", "", "", ""],
                opening_row,
            ]
            header_rows = 1
            start_idx = 2
        else:
            data = []
            header_rows = 0
            start_idx = 0

        for offset, (kind, row) in enumerate(chunk):
            data.append(row)
            if kind in ("detail", "detail_hdr"):
                span_rows.append(start_idx + offset)

        if section.transaction_count > 0 and index == len(chunks) - 1:
            footer = _blank_row()
            footer[COL_VOUCHER_NO] = _count(section.transaction_count)
            footer[COL_NARRATION] = _para(
                f"Number of transaction(s)  |  "
                f"Qty {_qty(section.total_qty)}  |  "
                f"Value {_money(section.total_value, always=True)}  |  "
                f"GST {_money(section.total_gst) or '-'}",
                DETAIL_ITEM_STYLE,
            )
            footer[COL_DEBIT] = _money(section.total_debit, always=True)
            footer[COL_CREDIT] = _money(section.total_credit, always=True)
            footer[COL_RUNNING] = "Total:"
            data.append(footer)
            footer_row = len(data) - 1

        table = Table(data, colWidths=COL_WIDTHS, repeatRows=0)
        style = _table_style(header_rows, footer_row, span_rows)
        if index == 0:
            style.add("SPAN", (0, 0), (-1, 0))
            style.add("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold")
            style.add("LINEABOVE", (0, 0), (-1, 0), 0.5, LINE_COLOR)
        table.setStyle(style)
        tables.append(table)
    return tables


def render_gl_ledger_detailed_pdf(report: GlLedgerDetailedReportData) -> bytes:
    detail_widths = compute_detail_col_widths(_collect_detail_lines(report), USABLE_WIDTH)

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
        for table in _account_tables(section, detail_widths):
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
