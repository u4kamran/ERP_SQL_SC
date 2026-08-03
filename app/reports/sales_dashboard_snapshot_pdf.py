"""PDF snapshot of the sales dashboard month-over-month comparison table."""

from __future__ import annotations

from datetime import datetime
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.schemas.sales_dashboard import DayWiseSalesRow, SalesDashboardSummary
from app.utils.money_format import format_amount

LINE_COLOR = colors.HexColor("#dee2e6")
HEADER_BG = colors.HexColor("#f8f9fa")


def _fmt_change(value: float, is_percent: bool = False) -> str:
    prefix = "+" if value > 0 else ""
    if is_percent:
        return f"{prefix}{format_amount(value)} pts"
    return f"{prefix}{format_amount(value)}"


def _fmt_change_pct(value: float | None) -> str:
    if value is None:
        return "—"
    prefix = "+" if value > 0 else ""
    return f"{prefix}{format_amount(value)}%"


def build_sales_dashboard_snapshot_pdf(
    summary: SalesDashboardSummary,
    *,
    period_label: str,
    compare_label: str,
    day_wise: list[DayWiseSalesRow] | None = None,
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

    rows = [
        ["Metric", "Current", "Last Month", "Change", "Change %"],
        [
            "Total Sale",
            format_amount(summary.total_sale.current),
            format_amount(summary.total_sale.previous),
            _fmt_change(summary.total_sale.change),
            _fmt_change_pct(summary.total_sale.change_percent),
        ],
        [
            "Total Cost",
            format_amount(summary.total_cost.current),
            format_amount(summary.total_cost.previous),
            _fmt_change(summary.total_cost.change),
            _fmt_change_pct(summary.total_cost.change_percent),
        ],
        [
            "Profit",
            format_amount(summary.profit.current),
            format_amount(summary.profit.previous),
            _fmt_change(summary.profit.change),
            _fmt_change_pct(summary.profit.change_percent),
        ],
        [
            "Profit %",
            f"{format_amount(summary.profit_percent.current)}%",
            f"{format_amount(summary.profit_percent.previous)}%",
            _fmt_change(summary.profit_percent.change, is_percent=True),
            "—",
        ],
        [
            "Avg Sale / Day",
            format_amount(summary.avg_sale_per_day.current),
            format_amount(summary.avg_sale_per_day.previous),
            _fmt_change(summary.avg_sale_per_day.change),
            _fmt_change_pct(summary.avg_sale_per_day.change_percent),
        ],
    ]

    table = Table(rows, colWidths=[32 * mm, 34 * mm, 34 * mm, 34 * mm, 28 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, LINE_COLOR),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    story = [
        Paragraph("Month-over-Month Comparison", title_style),
        Paragraph(period_label, sub_style),
        Paragraph(compare_label, sub_style),
    ]
    if business_hours_note:
        story.append(Paragraph(business_hours_note, sub_style))
    story.extend([
        Spacer(1, 8),
        table,
    ])

    if day_wise:
        day_rows = [["Business Day", "Sale", "Cost", "Profit", "Invoices"]]
        for row in day_wise[:31]:
            day_rows.append([
                row.day_label or row.business_date,
                format_amount(row.total_sale),
                format_amount(row.total_cost),
                format_amount(row.profit),
                str(row.invoice_count),
            ])
        day_table = Table(
            day_rows,
            colWidths=[58 * mm, 30 * mm, 30 * mm, 30 * mm, 22 * mm],
        )
        day_table.setStyle(
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
        story.extend([
            Spacer(1, 12),
            Paragraph("Day-wise Sales", title_style),
            day_table,
        ])

    story.extend([
        Spacer(1, 10),
        Paragraph(
            f"Generated: {generated_at.strftime('%d/%m/%Y %H:%M:%S')}",
            sub_style,
        ),
    ])
    doc.build(story)
    return buffer.getvalue()
