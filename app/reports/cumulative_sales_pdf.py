"""PDF export for cumulative sales report."""

from __future__ import annotations

from datetime import datetime
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.schemas.sales_dashboard import CumulativeSalesRow
from app.utils.money_format import format_amount

LINE_COLOR = colors.HexColor("#dee2e6")
HEADER_BG = colors.HexColor("#f8f9fa")
PREV_BG = colors.HexColor("#f1f3f5")


def build_cumulative_sales_pdf(
    items: list[CumulativeSalesRow],
    *,
    period_label: str,
    business_hours_note: str = "",
    generated_at: datetime | None = None,
) -> bytes:
    generated_at = generated_at or datetime.now()
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=10 * mm,
        rightMargin=10 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
    )

    title_style = ParagraphStyle(
        "title",
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        spaceAfter=4,
    )
    sub_style = ParagraphStyle(
        "sub",
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#6c757d"),
    )

    table_rows = [[
        "#", "Period", "Cumulative Business Period",
        "Sale", "Cost", "Profit", "Profit %", "Avg Sale / Day", "Invoices",
    ]]
    row_styles: list[tuple] = []

    for idx, row in enumerate(items, start=1):
        is_current = row.period_type == "current"
        profit_pct = (
            f"{format_amount(row.profit_percent)}%"
            if row.profit_percent is not None
            else "—"
        )
        table_rows.append([
            str(row.row_num) if is_current else "",
            "Current" if is_current else "Last Month",
            row.period_label,
            format_amount(row.total_sale),
            format_amount(row.total_cost),
            format_amount(row.profit),
            profit_pct,
            format_amount(row.avg_sale_per_day),
            format_amount(row.invoice_count, decimals=0),
        ])
        if not is_current:
            row_styles.append(("BACKGROUND", (0, idx), (-1, idx), PREV_BG))

    col_widths = [8 * mm, 16 * mm, 62 * mm, 24 * mm, 24 * mm, 24 * mm, 16 * mm, 24 * mm, 18 * mm]
    table = Table(table_rows, colWidths=col_widths, repeatRows=1)
    style_commands = [
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("GRID", (0, 0), (-1, -1), 0.25, LINE_COLOR),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (3, 0), (-1, -1), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    style_commands.extend(row_styles)
    table.setStyle(TableStyle(style_commands))

    story = [
        Paragraph("Cumulative Sales Report", title_style),
        Paragraph(period_label, sub_style),
    ]
    if business_hours_note:
        story.append(Paragraph(business_hours_note, sub_style))
    story.append(Paragraph(f"Generated: {generated_at.strftime('%d %b %Y %H:%M')}", sub_style))
    story.extend([Spacer(1, 6), table])

    doc.build(story)
    return buffer.getvalue()
