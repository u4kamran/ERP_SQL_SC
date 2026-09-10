"""PDF export for day-wise sales report."""

from __future__ import annotations

from datetime import datetime
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.schemas.sales_dashboard import DayWiseSalesRow
from app.utils.money_format import format_amount

LINE_COLOR = colors.HexColor("#dee2e6")
HEADER_BG = colors.HexColor("#f8f9fa")


def build_day_wise_sales_pdf(
    items: list[DayWiseSalesRow],
    *,
    period_label: str,
    business_hours_note: str = "",
    generated_at: datetime | None = None,
) -> bytes:
    generated_at = generated_at or datetime.now()
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=14 * mm,
        rightMargin=14 * mm,
        topMargin=16 * mm,
        bottomMargin=14 * mm,
    )

    title_style = ParagraphStyle(
        "title",
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        spaceAfter=4,
    )
    sub_style = ParagraphStyle(
        "sub",
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#6c757d"),
    )

    rows = [["Business Day", "Sale", "Cost", "Profit", "Invoices"]]
    for row in items:
        rows.append([
            row.day_label or row.business_date,
            format_amount(row.total_sale),
            format_amount(row.total_cost),
            format_amount(row.profit),
            format_amount(row.invoice_count, decimals=0),
        ])
    if len(rows) == 1:
        rows.append(["—", "—", "—", "—", "—"])

    table = Table(rows, colWidths=[70 * mm, 30 * mm, 30 * mm, 30 * mm, 22 * mm], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, LINE_COLOR),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )

    story = [
        Paragraph("Day-wise Sales Report", title_style),
        Paragraph(period_label, sub_style),
    ]
    if business_hours_note:
        story.append(Paragraph(business_hours_note, sub_style))
    story.append(Paragraph(f"Generated: {generated_at.strftime('%d %b %Y %H:%M')}", sub_style))
    story.extend([Spacer(1, 8), table])

    doc.build(story)
    return buffer.getvalue()
