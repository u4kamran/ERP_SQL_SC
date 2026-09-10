"""Sales summary queries from V_FIN_SALE_DISC_NEW2."""

from __future__ import annotations

from datetime import date, datetime, timedelta

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.utils.business_day import (
    business_date_for,
    business_day_label,
    cumulative_period_ends,
    cumulative_period_label,
    shift_datetime_months,
    sql_business_date_expr,
)
from app.utils.sales_view import sales_doc_date_column


class SalesDashboardRepository:
    def __init__(self, db: Session):
        self.db = db
        self._date_col = sales_doc_date_column()
        self._biz_date = sql_business_date_expr(self._date_col)

    def get_summary(self, start_date: datetime, end_date: datetime, total_days: int) -> dict:
        date_col = self._date_col
        sql = text(
            f"""
            SELECT
                SUM(TOTAL_AMT) AS total_sale,
                SUM(COST_AMT * QTY) AS total_cost,
                (SUM(TOTAL_AMT)) - (SUM(COST_AMT * QTY)) AS profit,
                CASE
                    WHEN SUM(COST_AMT * QTY) = 0 THEN NULL
                    ELSE ((SUM(TOTAL_AMT)) - (SUM(COST_AMT * QTY)))
                         / (SUM(COST_AMT * QTY)) * 100
                END AS profit_percent,
                (SUM(TOTAL_AMT)) / :total_days AS avg_sale_per_day
            FROM dbo.V_FIN_SALE_DISC_NEW2
            WHERE INV_ID BETWEEN 1 AND 999999999
              AND {date_col} BETWEEN :start_date AND :end_date
            """
        )
        row = self.db.execute(
            sql,
            {
                "start_date": start_date,
                "end_date": end_date,
                "total_days": max(total_days, 1),
            },
        ).mappings().first()

        if not row:
            return {
                "total_sale": 0.0,
                "total_cost": 0.0,
                "profit": 0.0,
                "profit_percent": None,
                "avg_sale_per_day": 0.0,
            }

        return {
            "total_sale": float(row["total_sale"] or 0),
            "total_cost": float(row["total_cost"] or 0),
            "profit": float(row["profit"] or 0),
            "profit_percent": float(row["profit_percent"]) if row["profit_percent"] is not None else None,
            "avg_sale_per_day": float(row["avg_sale_per_day"] or 0),
        }

    def get_daily_sales(self, start_date: datetime, end_date: datetime) -> list[dict]:
        sql = text(
            f"""
            SELECT
                {self._biz_date} AS sale_date,
                SUM(TOTAL_AMT) AS total_sale,
                SUM(COST_AMT * QTY) AS total_cost,
                SUM(TOTAL_AMT) - SUM(COST_AMT * QTY) AS profit
            FROM dbo.V_FIN_SALE_DISC_NEW2
            WHERE INV_ID BETWEEN 1 AND 999999999
              AND {self._date_col} BETWEEN :start_date AND :end_date
            GROUP BY {self._biz_date}
            ORDER BY sale_date
            """
        )
        rows = self.db.execute(
            sql, {"start_date": start_date, "end_date": end_date}
        ).mappings().all()
        return [
            {
                "sale_date": row["sale_date"].isoformat() if row["sale_date"] else "",
                "total_sale": float(row["total_sale"] or 0),
                "total_cost": float(row["total_cost"] or 0),
                "profit": float(row["profit"] or 0),
            }
            for row in rows
        ]

    def get_day_wise_sales(self, start_date: datetime, end_date: datetime) -> list[dict]:
        sql = text(
            f"""
            SELECT
                {self._biz_date} AS business_date,
                SUM(TOTAL_AMT) AS total_sale,
                SUM(COST_AMT * QTY) AS total_cost,
                SUM(TOTAL_AMT) - SUM(COST_AMT * QTY) AS profit,
                COUNT(DISTINCT INV_ID) AS invoice_count
            FROM dbo.V_FIN_SALE_DISC_NEW2
            WHERE INV_ID BETWEEN 1 AND 999999999
              AND {self._date_col} BETWEEN :start_date AND :end_date
            GROUP BY {self._biz_date}
            ORDER BY business_date DESC
            """
        )
        rows = self.db.execute(
            sql, {"start_date": start_date, "end_date": end_date}
        ).mappings().all()
        result = []
        for row in rows:
            bd = row["business_date"]
            iso = bd.isoformat() if bd else ""
            result.append(
                {
                    "business_date": iso,
                    "day_label": business_day_label(bd) if bd else "",
                    "total_sale": float(row["total_sale"] or 0),
                    "total_cost": float(row["total_cost"] or 0),
                    "profit": float(row["profit"] or 0),
                    "invoice_count": int(row["invoice_count"] or 0),
                }
            )
        return result

    @staticmethod
    def _daily_map(rows: list[dict]) -> dict[str, dict]:
        return {str(r.get("business_date", ""))[:10]: r for r in rows if r.get("business_date")}

    @staticmethod
    def _prefix_totals(start_bd: date, end_bd: date, daily_map: dict[str, dict]) -> list[dict]:
        """Running totals per business day from start_bd through end_bd inclusive."""
        totals: list[dict] = []
        rs = rc = rp = 0.0
        ri = 0
        bd = start_bd
        while bd <= end_bd:
            row = daily_map.get(bd.isoformat(), {})
            rs += float(row.get("total_sale", 0) or 0)
            rc += float(row.get("total_cost", 0) or 0)
            rp += float(row.get("profit", 0) or 0)
            ri += int(row.get("invoice_count", 0) or 0)
            totals.append(
                {
                    "total_sale": rs,
                    "total_cost": rc,
                    "profit": rp,
                    "invoice_count": ri,
                }
            )
            bd += timedelta(days=1)
        return totals

    def get_cumulative_sales(
        self, start_date: datetime, end_date: datetime, max_periods: int = 366
    ) -> list[dict]:
        """Cumulative sales using 2 day-wise queries + in-memory running totals."""
        fixed_start, period_ends = cumulative_period_ends(start_date, end_date)
        if not period_ends:
            return []

        if len(period_ends) > max_periods:
            raise ValueError(
                f"Date range spans {len(period_ends)} business days; maximum is {max_periods}."
            )

        prev_fixed_start = shift_datetime_months(fixed_start, -1)
        start_bd = business_date_for(fixed_start)
        end_bd = business_date_for(period_ends[-1])
        prev_start_bd = business_date_for(prev_fixed_start)
        prev_max_end = shift_datetime_months(period_ends[-1], -1)
        prev_end_bd = business_date_for(prev_max_end)

        daily_cur = self._daily_map(self.get_day_wise_sales(fixed_start, period_ends[-1]))
        daily_prev = self._daily_map(self.get_day_wise_sales(prev_fixed_start, prev_max_end))
        cur_prefix = self._prefix_totals(start_bd, end_bd, daily_cur)
        prev_prefix = self._prefix_totals(prev_start_bd, prev_end_bd, daily_prev)

        result: list[dict] = []
        for i, pe in enumerate(period_ends):
            row_num = i + 1
            cur_idx = row_num - 1
            prev_pe = shift_datetime_months(pe, -1)
            prev_idx = (business_date_for(prev_pe) - prev_start_bd).days

            for period_type, p_start, p_end, prefix, idx in (
                ("current", fixed_start, pe, cur_prefix, cur_idx),
                ("last_month", prev_fixed_start, prev_pe, prev_prefix, prev_idx),
            ):
                if idx < 0 or idx >= len(prefix):
                    agg = {"total_sale": 0.0, "total_cost": 0.0, "profit": 0.0, "invoice_count": 0}
                else:
                    agg = prefix[idx]
                total_sale = float(agg["total_sale"])
                total_cost = float(agg["total_cost"])
                profit = float(agg["profit"])
                profit_percent = (profit / total_cost * 100) if total_cost else None
                total_days = max(row_num, 1)
                result.append(
                    {
                        "row_num": row_num,
                        "period_type": period_type,
                        "start_date": p_start,
                        "end_date": p_end,
                        "period_label": cumulative_period_label(p_start, p_end),
                        "total_sale": round(total_sale, 2),
                        "total_cost": round(total_cost, 2),
                        "profit": round(profit, 2),
                        "profit_percent": round(profit_percent, 2) if profit_percent is not None else None,
                        "invoice_count": int(agg["invoice_count"]),
                        "total_days": total_days,
                        "avg_sale_per_day": round(total_sale / total_days, 2),
                    }
                )
        return result

    def get_top_invoices(self, start_date: datetime, end_date: datetime, limit: int = 10) -> list[dict]:
        date_col = self._date_col
        sql = text(
            f"""
            SELECT TOP (:limit)
                INV_ID AS inv_id,
                SUM(TOTAL_AMT) AS total_sale,
                SUM(QTY) AS total_qty,
                SUM(DISC_AMT) AS total_discount
            FROM dbo.V_FIN_SALE_DISC_NEW2
            WHERE INV_ID BETWEEN 1 AND 999999999
              AND {date_col} BETWEEN :start_date AND :end_date
            GROUP BY INV_ID
            ORDER BY SUM(TOTAL_AMT) DESC
            """
        )
        rows = self.db.execute(
            sql,
            {"start_date": start_date, "end_date": end_date, "limit": limit},
        ).mappings().all()
        return [
            {
                "inv_id": int(row["inv_id"] or 0),
                "total_sale": float(row["total_sale"] or 0),
                "total_qty": float(row["total_qty"] or 0),
                "total_discount": float(row["total_discount"] or 0),
            }
            for row in rows
        ]
