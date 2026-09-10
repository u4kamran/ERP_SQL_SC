"""PDF renderer for Detailed Customer Ledger (parallel to gl_ledger_pdf).

Parent ledger rows keep the existing GL format.
Invoice line detail uses a nested table with data-aware column widths.
"""

from __future__ import annotations

from io import BytesIO
from typing import List, Sequence

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Indenter, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

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

LINE_COLOR = colors.HexColor("#666666")
# Item-detail separators only — light grey so the child block is not a heavy dark frame.
DETAIL_LINE_COLOR = colors.HexColor("#D0D0D0")
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

# Nested item-detail columns (child of parent TX; starts under Narration)
DETAIL_SPECS: tuple[ColSpec, ...] = (
    ColSpec("item", "Item Title", min_pt=50, max_pt=380, flex=8.0, font_size=6.5),
    ColSpec("gp", "GP", min_pt=20, max_pt=44, flex=0.15, font_size=6.5),
    ColSpec("bill", "Bill", min_pt=20, max_pt=44, flex=0.15, font_size=6.5),
    ColSpec("qty", "Qty", min_pt=30, max_pt=52, flex=0.1, font_size=6.5),
    ColSpec("rate", "Rate", min_pt=30, max_pt=52, flex=0.1, font_size=6.5),
    ColSpec("value", "Value", min_pt=38, max_pt=68, flex=0.15, font_size=6.5),
    ColSpec("gst", "GST", min_pt=22, max_pt=48, flex=0.1, font_size=6.5),
    ColSpec("total", "Total", min_pt=38, max_pt=72, flex=0.15, font_size=6.5),
)

# Width available to the child detail block = Narration → right edge.
# Leave a small safety margin so Indenter + detail table never overflow the frame
# (overflow makes ReportLab compress the left indent).
DETAIL_AREA_WIDTH = max(120.0, sum(COL_WIDTHS[COL_NARRATION:]) - 2.0)

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
    # Do NOT insert U+200B / &#8203; soft breaks: Helvetica has no glyph for it and
    # PDF viewers render .notdef as solid black rectangular boxes.
    return Paragraph(safe, style)


def _collect_detail_lines(report: GlLedgerDetailedReportData) -> list[GlLedgerInvoiceDetailLine]:
    lines: list[GlLedgerInvoiceDetailLine] = []
    for section in report.accounts:
        for tx in section.transactions:
            lines.extend(tx.line_details)
    return lines


def _detail_cell_strings(line: GlLedgerInvoiceDetailLine) -> tuple[str, str, str, str, str, str, str, str]:
    value = float(line.value or 0)
    gst = float(line.gst or 0)
    line_total = line.line_total
    if line_total is None:
        line_total = value + gst
    return (
        (line.item_title or "").strip() or "Item",
        (line.gate_pass or "").strip() or "-",
        (line.bill_no or "").strip() or "-",
        _qty(line.qty) or "-",
        _money(line.rate or 0) if line.rate is not None else "-",
        _money(value, always=True),
        (line.gst_display or "-").strip() or "-",
        _money(float(line_total), always=True),
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
    """One header row: Item Title | GP | Bill | Qty | Rate | Value | GST | Total."""
    headers = [spec.header for spec in DETAIL_SPECS]
    data = [[_para(h, DETAIL_HEADER_STYLE) for h in headers]]
    table = Table(data, colWidths=widths)
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 6.5),
                ("ALIGN", (0, 0), (2, 0), "LEFT"),
                ("ALIGN", (3, 0), (-1, 0), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 1),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                ("LINEBELOW", (0, 0), (-1, 0), 0.2, DETAIL_LINE_COLOR),
                ("LINEABOVE", (0, 0), (-1, 0), 0.2, DETAIL_LINE_COLOR),
            ]
        )
    )
    return table


def _detail_data_inner(line: GlLedgerInvoiceDetailLine, widths: list[float]) -> Table:
    """One data row: Item Title | GP | Bill | Qty | Rate | Value | GST | Total."""
    item, gp, bill, qty, rate, value, gst, total = _detail_cell_strings(line)
    data = [[
        _para(item, DETAIL_ITEM_STYLE),
        gp,
        bill,
        qty,
        rate,
        value,
        gst,
        total,
    ]]
    table = Table(data, colWidths=widths)
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 6.5),
                ("ALIGN", (0, 0), (2, -1), "LEFT"),
                ("ALIGN", (3, 0), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 1),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                ("LINEBELOW", (0, 0), (-1, -1), 0.15, DETAIL_LINE_COLOR),
            ]
        )
    )
    return table


def _detail_block_flowables(
    lines: list[GlLedgerInvoiceDetailLine],
    detail_widths: list[float],
) -> list:
    """
    Indent item-detail to Narration using ReportLab Indenter.
    Left indent = Date + Voucher + Bn + Voucher + Reference (from parent COL_WIDTHS).
    Detail table width must fit in remaining frame width or ReportLab compresses the indent.
    """
    left_offset = sum(COL_WIDTHS[:COL_NARRATION])
    inner = _detail_transaction_inner(lines, detail_widths)
    return [Indenter(left_offset), inner, Indenter(-left_offset)]


def _detail_transaction_inner(
    lines: list[GlLedgerInvoiceDetailLine],
    widths: list[float],
) -> Table:
    """
    Child item-detail block:
      header once: Item Title | GP | Bill | Qty | Rate | Value | GST | Total
      then one row per item (all columns on the same line)
      then TOTAL row: Qty / Value / GST / Grand Total sums (Rate/GP/Bill blank).
    """
    data: list[list] = []
    data.append([_para(spec.header, DETAIL_HEADER_STYLE) for spec in DETAIL_SPECS])
    sum_qty = 0.0
    sum_value = 0.0
    sum_gst = 0.0
    sum_total = 0.0
    for line in lines:
        item, gp, bill, qty, rate, value, gst, total = _detail_cell_strings(line)
        data.append([_para(item, DETAIL_ITEM_STYLE), gp, bill, qty, rate, value, gst, total])
        sum_qty += float(line.qty or 0)
        sum_value += float(line.value or 0)
        sum_gst += float(line.gst or 0)
        line_total = line.line_total
        if line_total is None:
            line_total = float(line.value or 0) + float(line.gst or 0)
        sum_total += float(line_total)

    # TOTAL row — do not sum GP / Bill / Rate
    data.append(
        [
            _para("TOTAL", DETAIL_HEADER_STYLE),
            "",
            "",
            _qty(sum_qty),
            "",
            _money(sum_value, always=True),
            _money(sum_gst) or "-",
            _money(sum_total, always=True),
        ]
    )

    last_data_row = len(data) - 2
    total_row = len(data) - 1
    table = Table(data, colWidths=widths)
    style_cmds: list[tuple] = [
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 6.5),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), CELL_PAD),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (2, 0), "LEFT"),
        ("ALIGN", (3, 0), (-1, 0), "RIGHT"),
        # Thin light separators only — no BOX / no dark frame / no double rules.
        ("LINEBELOW", (0, 0), (-1, 0), 0.15, DETAIL_LINE_COLOR),
        ("ALIGN", (0, 1), (2, last_data_row), "LEFT"),
        ("ALIGN", (3, 1), (-1, last_data_row), "RIGHT"),
        ("FONTNAME", (0, total_row), (-1, total_row), "Helvetica-Bold"),
        ("ALIGN", (0, total_row), (2, total_row), "LEFT"),
        ("ALIGN", (3, total_row), (-1, total_row), "RIGHT"),
        ("LINEABOVE", (0, total_row), (-1, total_row), 0.2, DETAIL_LINE_COLOR),
        ("LINEBELOW", (0, total_row), (-1, total_row), 0.2, DETAIL_LINE_COLOR),
    ]
    # Horizontal rules between item rows only (not under last item — TOTAL LINEABOVE).
    if last_data_row > 1:
        style_cmds.append(
            ("LINEBELOW", (0, 1), (-1, last_data_row - 1), 0.1, DETAIL_LINE_COLOR)
        )
    table.setStyle(TableStyle(style_cmds))
    return table


def _parent_table(data: list[list], *, header_rows: int = 0, footer_row: int | None = None) -> Table:
    table = Table(data, colWidths=COL_WIDTHS, repeatRows=0)
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
        style.add("SPAN", (0, 0), (-1, 0))
        style.add("LINEABOVE", (0, 0), (-1, 0), 0.5, LINE_COLOR)
    if footer_row is not None:
        style.add("FONTNAME", (0, footer_row), (-1, footer_row), "Helvetica-Bold")
        style.add("LINEABOVE", (0, footer_row), (-1, footer_row), 0.5, LINE_COLOR)
    table.setStyle(style)
    return table


def _account_flowables(
    section: GlLedgerDetailedAccountSection,
    detail_widths: list[float],
) -> list:
    """
    Parent ledger rows and item-detail blocks as sibling flowables.
    Detail is a separate table with an explicit left spacer = Date..Reference,
    so Item Title starts exactly under Narration.
    """
    flowables: list = []

    account_label = _para(f"{section.ac_id_display}  {section.ac_title}", ACCOUNT_STYLE)
    opening_row = _blank_row()
    opening_row[COL_NARRATION] = "Opening Balance :"
    opening_row[COL_DEBIT] = _money(section.opening_debit)
    opening_row[COL_CREDIT] = _money(section.opening_credit)
    opening_row[COL_RUNNING] = _money(section.opening_balance, always=True)

    flowables.append(
        _parent_table(
            [[account_label, "", "", "", "", "", "", "", ""], opening_row],
            header_rows=1,
        )
    )

    for tx in section.transactions:
        flowables.append(_parent_table([_transaction_row(tx)]))
        if tx.line_details:
            flowables.extend(_detail_block_flowables(tx.line_details, detail_widths))

    if section.transaction_count > 0:
        footer = _blank_row()
        footer[COL_VOUCHER_NO] = _count(section.transaction_count)
        footer[COL_NARRATION] = _para(
            f"Number of transaction(s)  |  "
            f"Qty {_qty(section.total_qty)}  |  "
            f"Value {_money(section.total_value, always=True)}  |  "
            f"GST {_money(section.total_gst) or '-'}  |  "
            f"Grand Total {_money(section.grand_total, always=True)}",
            DETAIL_ITEM_STYLE,
        )
        footer[COL_DEBIT] = _money(section.total_debit, always=True)
        footer[COL_CREDIT] = _money(section.total_credit, always=True)
        footer[COL_RUNNING] = "Total:"
        flowables.append(_parent_table([footer], footer_row=0))

    return flowables


def render_gl_ledger_detailed_pdf(report: GlLedgerDetailedReportData) -> bytes:
    # Child detail width is derived from the real parent grid:
    # Narration + Debit + Credit + Running Bal.
    detail_widths = compute_detail_col_widths(
        _collect_detail_lines(report),
        DETAIL_AREA_WIDTH,
    )

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
        for flowable in _account_flowables(section, detail_widths):
            story.append(flowable)
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
