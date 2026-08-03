"""Data access for Trial Balance Date to Date report."""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Literal

from sqlalchemy import text
from sqlalchemy.orm import Session

_SORT_COLUMNS: dict[str, str] = {
    "ac_id": "g1.ac_id",
    "ac_title": "g1.ac_title",
}


def _order_clause(
    sort_by: Literal["ac_id", "ac_title"],
    sort_order: Literal["asc", "desc"],
) -> str:
    col = _SORT_COLUMNS.get(sort_by, "g1.ac_id")
    direction = "DESC" if sort_order == "desc" else "ASC"
    if sort_by == "ac_title":
        return f"ORDER BY {col} {direction}, g1.ac_id ASC"
    return f"ORDER BY {col} {direction}"


def _row_to_dict(row) -> Dict[str, Any]:
    return dict(row)


class TrialBalanceD2DRepository:
    def __init__(self, db: Session):
        self.db = db

    def fetch_account_balances(
        self,
        start_ac_id: int,
        end_ac_id: int,
        date_from: date,
        date_to: date,
        sort_by: Literal["ac_id", "ac_title"] = "ac_id",
        sort_order: Literal["asc", "desc"] = "asc",
    ) -> List[Dict[str, Any]]:
        """Aggregate Gl0003 movement per account (VB6 FrmPrintListL TB Date to Date)."""
        order_clause = _order_clause(sort_by, sort_order)
        rows = self.db.execute(
            text(
                f"""
                SELECT
                    g1.ac_id,
                    g1.ac_title,
                    g1.obal,
                    ISNULL(t.pre_debit, 0) AS pre_debit,
                    ISNULL(t.pre_credit, 0) AS pre_credit,
                    ISNULL(t.period_debit, 0) AS period_debit,
                    ISNULL(t.period_credit, 0) AS period_credit
                FROM Gl0001 g1
                LEFT JOIN (
                    SELECT
                        ac_id,
                        SUM(CASE WHEN vdate < :date_from THEN ISNULL(DEBIT, 0) ELSE 0 END) AS pre_debit,
                        SUM(CASE WHEN vdate < :date_from THEN ISNULL(CREDIT, 0) ELSE 0 END) AS pre_credit,
                        SUM(CASE
                            WHEN vdate >= :date_from AND vdate <= :date_to THEN ISNULL(DEBIT, 0)
                            ELSE 0
                        END) AS period_debit,
                        SUM(CASE
                            WHEN vdate >= :date_from AND vdate <= :date_to THEN ISNULL(CREDIT, 0)
                            ELSE 0
                        END) AS period_credit
                    FROM Gl0003
                    WHERE ac_id >= :start_ac_id AND ac_id <= :end_ac_id
                    GROUP BY ac_id
                ) t ON g1.ac_id = t.ac_id
                WHERE g1.ac_level = 4
                  AND g1.ac_id >= :start_ac_id
                  AND g1.ac_id <= :end_ac_id
                {order_clause}
                """
            ),
            {
                "date_from": date_from,
                "date_to": date_to,
                "start_ac_id": start_ac_id,
                "end_ac_id": end_ac_id,
            },
        ).mappings().all()
        return [_row_to_dict(r) for r in rows]
