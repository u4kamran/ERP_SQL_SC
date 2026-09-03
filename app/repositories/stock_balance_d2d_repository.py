"""Data access for Stock Balance Date to Date (VB6 FrmPrintInvL / RptStD2D).

READ-ONLY: no temp tables, no UPDATEs to FIN_ITEM.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Literal, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

MAX_ITEM_ID = 9_999_999_999

_SORT_COLUMNS: dict[str, str] = {
    "ac_id": "i.ITEM_ID",
    "ac_title": "i.ITEM_TITLE",
}


def _row_to_dict(row) -> Dict[str, Any]:
    return dict(row)


def _order_clause(
    sort_by: Literal["ac_id", "ac_title"],
    sort_order: Literal["asc", "desc"],
) -> str:
    col = _SORT_COLUMNS.get(sort_by, "i.ITEM_ID")
    direction = "DESC" if sort_order == "desc" else "ASC"
    if sort_by == "ac_title":
        return f"ORDER BY {col} {direction}, i.ITEM_ID ASC"
    return f"ORDER BY {col} {direction}"


class StockBalanceD2DRepository:
    def __init__(self, db: Session):
        self.db = db

    def fetch_item_balances(
        self,
        start_item_id: int,
        end_item_id: int,
        date_from: date,
        date_to: date,
        *,
        store_ledger: bool = False,
        sort_by: Literal["ac_id", "ac_title"] = "ac_id",
        sort_order: Literal["asc", "desc"] = "asc",
    ) -> List[Dict[str, Any]]:
        """Aggregate fin_ldgr qty + cost amount movement per item.

        Opening base: OQTY/OAMT (or OQTY1/OAMT1 when store_ledger).
        Amounts use cost_amtdr / cost_amtcr (VB6 FrmPrintInvL).
        """
        oqty_col = "ISNULL(i.OQTY1, 0)" if store_ledger else "ISNULL(i.OQTY, 0)"
        oamt_col = "ISNULL(i.OAMT1, 0)" if store_ledger else "ISNULL(i.OAMT, 0)"
        order_clause = _order_clause(sort_by, sort_order)
        rows = self.db.execute(
            text(
                f"""
                SELECT
                    CAST(i.ITEM_ID AS BIGINT) AS item_id,
                    i.ITEM_TITLE AS item_title,
                    ISNULL(i.manualid, 0) AS manualid,
                    {oqty_col} AS oqty,
                    {oamt_col} AS oamt,
                    ISNULL(t.pre_qtydr, 0) AS pre_qtydr,
                    ISNULL(t.pre_qtycr, 0) AS pre_qtycr,
                    ISNULL(t.period_qtydr, 0) AS period_qtydr,
                    ISNULL(t.period_qtycr, 0) AS period_qtycr,
                    ISNULL(t.pre_amtdr, 0) AS pre_amtdr,
                    ISNULL(t.pre_amtcr, 0) AS pre_amtcr,
                    ISNULL(t.period_amtdr, 0) AS period_amtdr,
                    ISNULL(t.period_amtcr, 0) AS period_amtcr
                FROM FIN_ITEM i
                LEFT JOIN (
                    SELECT
                        item_id,
                        SUM(CASE WHEN DOC_DATE < :date_from THEN ISNULL(qtydr, 0) ELSE 0 END) AS pre_qtydr,
                        SUM(CASE WHEN DOC_DATE < :date_from THEN ISNULL(qtycr, 0) ELSE 0 END) AS pre_qtycr,
                        SUM(CASE
                            WHEN DOC_DATE >= :date_from AND DOC_DATE <= :date_to
                            THEN ISNULL(qtydr, 0) ELSE 0
                        END) AS period_qtydr,
                        SUM(CASE
                            WHEN DOC_DATE >= :date_from AND DOC_DATE <= :date_to
                            THEN ISNULL(qtycr, 0) ELSE 0
                        END) AS period_qtycr,
                        SUM(CASE WHEN DOC_DATE < :date_from THEN ISNULL(cost_amtdr, 0) ELSE 0 END) AS pre_amtdr,
                        SUM(CASE WHEN DOC_DATE < :date_from THEN ISNULL(cost_amtcr, 0) ELSE 0 END) AS pre_amtcr,
                        SUM(CASE
                            WHEN DOC_DATE >= :date_from AND DOC_DATE <= :date_to
                            THEN ISNULL(cost_amtdr, 0) ELSE 0
                        END) AS period_amtdr,
                        SUM(CASE
                            WHEN DOC_DATE >= :date_from AND DOC_DATE <= :date_to
                            THEN ISNULL(cost_amtcr, 0) ELSE 0
                        END) AS period_amtcr
                    FROM fin_ldgr
                    WHERE item_id >= :start_item_id AND item_id <= :end_item_id
                    GROUP BY item_id
                ) t ON i.ITEM_ID = t.item_id
                WHERE i.AC_LEVEL = 4
                  AND ISNULL(i.ED_STATUS, 0) = 0
                  AND i.ITEM_ID >= :start_item_id
                  AND i.ITEM_ID <= :end_item_id
                {order_clause}
                """
            ),
            {
                "date_from": date_from,
                "date_to": date_to,
                "start_item_id": start_item_id,
                "end_item_id": end_item_id,
            },
        ).mappings().all()
        return [_row_to_dict(r) for r in rows]

    def lookup_item(self, item_id: int) -> Optional[Dict[str, Any]]:
        row = self.db.execute(
            text(
                """
                SELECT TOP 1
                    CAST(ITEM_ID AS BIGINT) AS item_id,
                    ITEM_TITLE AS item_title,
                    ISNULL(manualid, 0) AS manualid
                FROM FIN_ITEM
                WHERE AC_LEVEL = 4
                  AND ITEM_ID = :item_id
                """
            ),
            {"item_id": item_id},
        ).mappings().first()
        return _row_to_dict(row) if row else None

    def search_items(self, q: str, *, limit: int = 40) -> List[Dict[str, Any]]:
        pattern = f"%{q.strip()}%"
        exact = q.strip()
        rows = self.db.execute(
            text(
                """
                SELECT TOP (:limit)
                    CAST(ITEM_ID AS BIGINT) AS item_id,
                    ITEM_TITLE AS item_title,
                    ISNULL(manualid, 0) AS manualid
                FROM FIN_ITEM
                WHERE AC_LEVEL = 4
                  AND (
                        CAST(CAST(ITEM_ID AS BIGINT) AS VARCHAR(30)) LIKE :pattern
                     OR ITEM_TITLE LIKE :pattern
                     OR CAST(ISNULL(manualid, 0) AS VARCHAR(30)) LIKE :pattern
                     OR CAST(CAST(ITEM_ID AS BIGINT) AS VARCHAR(30)) = :exact
                     OR CAST(ISNULL(manualid, 0) AS VARCHAR(30)) = :exact
                  )
                ORDER BY ITEM_ID ASC
                """
            ),
            {"pattern": pattern, "exact": exact, "limit": limit},
        ).mappings().all()
        return [_row_to_dict(r) for r in rows]
