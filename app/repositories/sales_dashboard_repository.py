"""Sales summary queries from V_FIN_SALE_DISC_NEW2."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.utils.business_day import business_day_label, sql_business_date_expr
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
