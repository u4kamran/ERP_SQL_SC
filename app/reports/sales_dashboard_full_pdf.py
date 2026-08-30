"""Full Sales Dashboard PDF — KPIs, MoM, top invoices, day-wise, cumulative."""

from __future__ import annotations

from datetime import datetime
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.schemas.sales_dashboard import (
    CumulativeSalesResponse,
    DayWiseSalesResponse,
    SalesDashboardSummary,
    TopInvoicesResponse,
)
from app.utils.money_format import format_amount

LINE_COLOR = colors.HexColor("#dee2e6")
HEADER_BG = colors.HexColor("#f8f9fa")
PREV_BG = colors.HexColor("#f1f3f5")


def _section_title(text: str) -> Paragraph:
    return Paragraph(
        text,
        ParagraphStyle(
            "section",
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            spaceBefore=10,
            spaceAfter=4,
        ),
    )


def _sub(text: str) -> Paragraph:
    return Paragraph(
        text,
        ParagraphStyle(
            "sub",
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#6c757d"),
        ),
    )


def _table_style(header_rows: int = 1) -> TableStyle:
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, header_rows - 1), HEADER_BG),
            ("FONTNAME", (0, 0), (-1, header_rows - 1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("GRID", (0, 0), (-1, -1), 0.25, LINE_COLOR),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]
    )


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


def build_full_sales_dashboard_pdf(
    summary: SalesDashboardSummary,
    top_invoices: TopInvoicesResponse,
    day_wise: DayWiseSalesResponse,
    cumulative: CumulativeSalesResponse | None,
    *,
    period_label: str,
    compare_label: str,
    app_name: str = "Sales Dashboard",
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
        fontSize=14,
        leading=18,
        spaceAfter=4,
    )

    story = [
        Paragraph(app_name, title_style),
        _sub(period_label),
        _sub(compare_label),
    ]
    if day_wise.business_hours_note:
        story.append(_sub(day_wise.business_hours_note))
    story.append(_sub(f"Generated: {generated_at.strftime('%d %b %Y %H:%M')}"))

    cur = summary.current
    kpi_rows = [
        ["Metric", "Value"],
        ["Total Sale", format_amount(cur.total_sale)],
        ["Total Cost", format_amount(cur.total_cost)],
        ["Profit", format_amount(cur.profit)],
        ["Profit %", f"{format_amount(cur.profit_percent or 0)}%" if cur.profit_percent is not None else "—"],
        ["Avg Sale / Day", format_amount(cur.avg_sale_per_day)],
        ["Business Days", str(cur.total_days)],
    ]
    kpi_table = Table(kpi_rows, colWidths=[40 * mm, 50 * mm])
    kpi_table.setStyle(_table_style())
    story.extend([_section_title("Summary (Current Period)"), kpi_table])

    mom_rows = [
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
    mom_table = Table(mom_rows, colWidths=[36 * mm, 32 * mm, 32 * mm, 32 * mm, 28 * mm])
    mom_table.setStyle(_table_style())
    story.extend([Spacer(1, 6), _section_title("Month-over-Month Comparison"), mom_table])

    inv_rows = [["Inv #", "Sale", "Qty", "Discount"]]
    for inv in top_invoices.items:
        inv_rows.append([
            str(inv.inv_id),
            format_amount(inv.total_sale),
            format_amount(inv.total_qty, decimals=0),
            format_amount(inv.total_discount),
        ])
    if len(inv_rows) == 1:
        inv_rows.append(["—", "—", "—", "—"])
    inv_table = Table(inv_rows, colWidths=[24 * mm, 40 * mm, 30 * mm, 30 * mm])
    inv_table.setStyle(_table_style())
    story.extend([Spacer(1, 6), _section_title("Top 10 Invoices"), inv_table])

    day_rows = [["Business Day", "Sale", "Cost", "Profit", "Invoices"]]
    for row in day_wise.items:
        day_rows.append([
            row.day_label or row.business_date,
            format_amount(row.total_sale),
            format_amount(row.total_cost),
            format_amount(row.profit),
            format_amount(row.invoice_count, decimals=0),
        ])
    if len(day_rows) == 1:
        day_rows.append(["—", "—", "—", "—", "—"])
    day_table = Table(day_rows, colWidths=[70 * mm, 32 * mm, 32 * mm, 32 * mm, 22 * mm], repeatRows=1)
    day_table.setStyle(_table_style())
    story.extend([Spacer(1, 6), _section_title("Day-wise Sales"), day_table])

    cum_rows = [[
        "#", "Period", "Cumulative Business Period",
        "Sale", "Cost", "Profit", "Profit %", "Avg Sale / Day", "Invoices",
    ]]
    cum_styles: list[tuple] = []
    if cumulative and cumulative.items:
        for idx, row in enumerate(cumulative.items, start=1):
            is_current = row.period_type == "current"
            profit_pct = (
                f"{format_amount(row.profit_percent)}%"
                if row.profit_percent is not None
                else "—"
            )
            cum_rows.append([
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
                cum_styles.append(("BACKGROUND", (0, idx), (-1, idx), PREV_BG))
    else:
        cum_rows.append(["—", "—", "Not loaded", "—", "—", "—", "—", "—", "—"])
    cum_table = Table(
        cum_rows,
        colWidths=[8 * mm, 16 * mm, 58 * mm, 24 * mm, 24 * mm, 24 * mm, 16 * mm, 24 * mm, 18 * mm],
        repeatRows=1,
    )
    cum_style = _table_style()
    cum_style.add("ALIGN", (0, 0), (0, -1), "CENTER")
    for cmd in cum_styles:
        cum_style.add(*cmd)
    cum_table.setStyle(cum_style)
    story.extend([Spacer(1, 6), _section_title("Cumulative Sales (Current + Last Month)"), cum_table])

    doc.build(story)
    return buffer.getvalue()
