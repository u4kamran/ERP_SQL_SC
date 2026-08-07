"""Data access for VB6-style Fin_Item form."""

from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import bindparam, text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import Session

from app.models.business.fin_item import FinItem


def _row_to_dict(row) -> Dict[str, Any]:
    if row is None:
        return {}
    data = dict(row._mapping) if hasattr(row, "_mapping") else dict(row)
    for key, value in list(data.items()):
        if value is None:
            continue
        if hasattr(value, "__float__") and not isinstance(value, (bool, int, float, str)):
            try:
                data[key] = float(value)
            except (TypeError, ValueError):
                pass
    return data


_VIEW_ITEM_COLUMNS = """
    item_id, ITEM_TITLE, ITEM_SHORT, ITEM_OEM, manualid, barcodeid, BARCODEID_WS,
    VISACARD_RATE, UOM_ID, UOM_ABBR, UOM_TITLE, COUNTRY_ID, COUNTRY_TITLE,
    ITEM_NATURE, MIN_LEVEL, MAX_LEVEL, RO_QTY, CRITICAL_LEVEL,
    SALES_RATE, COST_RATE, OAMT1, CAMT1, CQTY1, DISC_P1, DISC_P4,
    GL_SALES_ID, GL_PUR_ID, GL_CONS_ID, GL_DISC_ID, GL_STAX_ID,
    GL_SALES_TITLE, GL_PUR_TITLE, GL_CONS_TITLE, GL_DISC_TITLE, GL_STAX_TITLE,
    STAX_REG, STAX_UNREG, OQTY, CQTY, OAMT, CAMT, REMARKS, co_id, co_TITLE,
    ED_STATUS
"""


_ITEM_COLUMNS = """
    ITEM_ID, ITEM_TITLE, ITEM_SHORT, AC_LEVEL, ED_STATUS, ITEM_OEM,
    manualid, barcodeid, BARCODEID_WS, VISACARD_RATE, UOM_ID, COUNTRY_ID,
    ITEM_NATURE, MIN_LEVEL, MAX_LEVEL, RO_QTY, CRITICAL_LEVEL,
    SALES_RATE, COST_RATE, OAMT1, CAMT1, CQTY1, DISC_P1, DISC_P4,
    GL_SALES_ID, GL_PUR_ID, GL_CONS_ID, GL_DISC_ID, GL_STAX_ID,
    STAX_REG, STAX_UNREG, OQTY, CQTY, OAMT, CAMT, REMARKS, co_id,
    MIN_LEVEL1, MAX_LEVEL1, RO_QTY1, CRITICAL_LEVEL1
"""


class FinItemClassicRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_stats(self) -> Tuple[int, Optional[float]]:
        row = self.db.execute(
            text("SELECT COUNT(*) AS cRecTotal, MAX(ITEM_ID) AS cLastId FROM FIN_ITEM")
        ).mappings().first()
        data = _row_to_dict(row)
        return int(data.get("cRecTotal") or 0), data.get("cLastId")

    def next_manual_id(self) -> int:
        row = self.db.execute(text("SELECT MAX(manualid) AS manualid FROM FIN_ITEM")).mappings().first()
        current = _row_to_dict(row).get("manualid") or 0
        return int(current) + 1

    def get_fin_cat(self, item_id: float) -> Optional[Dict[str, Any]]:
        row = self.db.execute(
            text("SELECT item_id, Item_Title, Ac_Level FROM fin_cat WHERE item_id = :item_id"),
            {"item_id": item_id},
        ).mappings().first()
        return _row_to_dict(row) or None

    def get_item_dict(self, item_id: float) -> Optional[Dict[str, Any]]:
        """VB6 TxtID_Validate reads v_fin_item first."""
        view = self.get_view_item_row(item_id)
        if view:
            return view
        row = self.db.execute(
            text(f"SELECT {_ITEM_COLUMNS} FROM FIN_ITEM WHERE ITEM_ID = :item_id"),
            {"item_id": item_id},
        ).mappings().first()
        return _row_to_dict(row) or None

    def get_view_by_manual_id(self, manual_id: int) -> Optional[Dict[str, Any]]:
        try:
            row = self.db.execute(
                text(
                    f"""
                    SELECT TOP 1 {_VIEW_ITEM_COLUMNS}
                    FROM v_fin_item
                    WHERE manualid = :manual_id
                    """
                ),
                {"manual_id": manual_id},
            ).mappings().first()
            return _row_to_dict(row) or None
        except ProgrammingError:
            self.db.rollback()
            return None

    def get_item_rates(self, item_id: float) -> Dict[str, Any]:
        row = self.db.execute(
            text(
                """
                SELECT SALES_RATE, COST_RATE, OAMT1, CAMT1, CQTY1, DISC_P1, DISC_P4
                FROM FIN_ITEM WHERE ITEM_ID = :item_id
                """
            ),
            {"item_id": item_id},
        ).mappings().first()
        return _row_to_dict(row)

    def get_fin_item_store_row(self, item_id: float) -> Optional[Dict[str, Any]]:
        row = self.db.execute(
            text(
                """
                SELECT MIN_LEVEL1, MAX_LEVEL1, RO_QTY1, CRITICAL_LEVEL1
                FROM FIN_ITEM WHERE ITEM_ID = :item_id
                """
            ),
            {"item_id": item_id},
        ).mappings().first()
        return _row_to_dict(row) or None

    def get_view_item_row(self, item_id: float) -> Optional[Dict[str, Any]]:
        """VB6 TxtID_Validate reads v_fin_item."""
        item_id_str = str(int(item_id)) if item_id == int(item_id) else str(item_id)
        try:
            row = self.db.execute(
                text(
                    f"""
                    SELECT TOP 1 {_VIEW_ITEM_COLUMNS}
                    FROM v_fin_item
                    WHERE CAST(item_id AS VARCHAR(20)) = :item_id_str
                       OR item_id = :item_id
                    """
                ),
                {"item_id": item_id, "item_id_str": item_id_str},
            ).mappings().first()
            return _row_to_dict(row) or None
        except ProgrammingError:
            self.db.rollback()
            return None

    def get_by_manual_id(self, manual_id: int) -> Optional[Dict[str, Any]]:
        return self.get_view_by_manual_id(manual_id) or self._get_fin_item_by_manual_id(manual_id)

    def _get_fin_item_by_manual_id(self, manual_id: int) -> Optional[Dict[str, Any]]:
        row = self.db.execute(
            text(f"SELECT {_ITEM_COLUMNS} FROM FIN_ITEM WHERE manualid = :manual_id"),
            {"manual_id": manual_id},
        ).mappings().first()
        return _row_to_dict(row) or None

    def get_by_barcode(self, barcode: str) -> Optional[Dict[str, Any]]:
        view = self.db.execute(
            text("SELECT TOP 1 * FROM v_fin_item WHERE barcodeid = :barcode"),
            {"barcode": barcode},
        ).mappings().first()
        if view:
            return _row_to_dict(view)
        row = self.db.execute(
            text(f"SELECT {_ITEM_COLUMNS} FROM FIN_ITEM WHERE barcodeid = :barcode"),
            {"barcode": barcode},
        ).mappings().first()
        return _row_to_dict(row) or None

    def get_by_ws_barcode(self, barcode: str) -> Optional[Dict[str, Any]]:
        view = self.db.execute(
            text("SELECT TOP 1 * FROM v_fin_item WHERE barcodeid_ws = :barcode"),
            {"barcode": barcode},
        ).mappings().first()
        if view:
            return _row_to_dict(view)
        row = self.db.execute(
            text(f"SELECT {_ITEM_COLUMNS} FROM FIN_ITEM WHERE BARCODEID_WS = :barcode"),
            {"barcode": barcode},
        ).mappings().first()
        return _row_to_dict(row) or None

    def get_fin_item_row(self, item_id: float) -> Optional[FinItem]:
        return self.db.get(FinItem, item_id)

    def lookup_uom(self, uom_id: int) -> Optional[str]:
        row = self.db.execute(
            text("SELECT uom_abbr FROM fin_c002 WHERE uom_id = :uom_id"),
            {"uom_id": uom_id},
        ).mappings().first()
        return _row_to_dict(row).get("uom_abbr")

    def lookup_country(self, country_id: int) -> Optional[str]:
        row = self.db.execute(
            text("SELECT country_title FROM Country WHERE Country_id = :country_id"),
            {"country_id": country_id},
        ).mappings().first()
        return _row_to_dict(row).get("country_title")

    def lookup_company(self, co_id: int) -> Optional[str]:
        row = self.db.execute(
            text("SELECT co_title FROM Co WHERE Co_id = :co_id"),
            {"co_id": co_id},
        ).mappings().first()
        return _row_to_dict(row).get("co_title")

    def lookup_gl(self, gl_id: int) -> Optional[str]:
        row = self.db.execute(
            text("SELECT ac_title FROM gl0001 WHERE ac_id = :gl_id AND ac_level = 4"),
            {"gl_id": gl_id},
        ).mappings().first()
        return _row_to_dict(row).get("ac_title")

    def lookup_gl_titles(self, gl_ids: List[int]) -> Dict[int, str]:
        unique_ids = sorted({int(i) for i in gl_ids if i})
        if not unique_ids:
            return {}
        stmt = (
            text("SELECT ac_id, ac_title FROM gl0001 WHERE ac_level = 4 AND ac_id IN :ids")
            .bindparams(bindparam("ids", expanding=True))
        )
        rows = self.db.execute(stmt, {"ids": unique_ids}).mappings().all()
        return {int(r["ac_id"]): r["ac_title"] for r in rows}

    def ledger_count(self, item_id: float) -> int:
        row = self.db.execute(
            text("SELECT COUNT(*) AS cnt FROM fin_ldgr WHERE ITEM_ID = :item_id"),
            {"item_id": item_id},
        ).mappings().first()
        return int(_row_to_dict(row).get("cnt") or 0)

    def last_purchases(self, item_id: float, limit: int = 5) -> List[Dict[str, Any]]:
        rows = self.db.execute(
            text(
                """
                SELECT TOP (:limit)
                    PROD_ID, doc_date, supplier_title, QTY,
                    RATE AS rate, EXP_DATE AS Exp_Date
                FROM v_fin_pur_exp_date
                WHERE ITEM_ID = :item_id
                ORDER BY doc_date DESC
                """
            ),
            {"item_id": float(item_id), "limit": limit},
        ).mappings().all()
        return [_row_to_dict(r) for r in rows]

    def last_sales(self, item_id: float, limit: int = 5) -> List[Dict[str, Any]]:
        rows = self.db.execute(
            text(
                """
                SELECT TOP (:limit)
                    INV_ID, DOC_DATE AS doc_date, CUSTOMER_TITLE AS customer_title, QTY,
                    CASE WHEN QTY > 0 THEN TOTAL_AMT / QTY ELSE TOTAL_AMT END AS rate
                FROM v_inv1
                WHERE ITEM_ID = :item_id
                ORDER BY DOC_DATE DESC
                """
            ),
            {"item_id": float(item_id), "limit": limit},
        ).mappings().all()
        return [_row_to_dict(r) for r in rows]

    def search_items(self, q: str, limit: int = 50) -> List[Dict[str, Any]]:
        q = (q or "").strip()
        if not q:
            return []
        pattern = f"%{q}%"
        exact = q
        rows = self.db.execute(
            text(
                f"""
                SELECT TOP (:limit)
                    ITEM_ID AS item_id, ITEM_TITLE AS Item_Title, manualid,
                    ITEM_SHORT AS item_short, barcodeid, BARCODEID_WS AS barcodeid_ws
                FROM FIN_ITEM
                WHERE CAST(ITEM_ID AS VARCHAR(20)) LIKE :pattern
                   OR CAST(ITEM_ID AS VARCHAR(20)) = :exact
                   OR ITEM_TITLE LIKE :pattern
                   OR ITEM_SHORT LIKE :pattern
                   OR CAST(manualid AS VARCHAR(20)) LIKE :pattern
                   OR CAST(manualid AS VARCHAR(20)) = :exact
                   OR barcodeid LIKE :pattern
                   OR barcodeid = :exact
                   OR BARCODEID_WS LIKE :pattern
                   OR BARCODEID_WS = :exact
                ORDER BY manualid DESC
                """
            ),
            {"pattern": pattern, "exact": exact, "limit": limit},
        ).mappings().all()
        return [_row_to_dict(r) for r in rows]

    def search_items_all_tokens(
        self, tokens: List[str], limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Require every token to appear in title/short/barcode fields."""
        clean = [t.strip() for t in tokens if t and t.strip()]
        if not clean:
            return []
        if len(clean) > 6:
            clean = clean[:6]
        clauses = []
        params: Dict[str, Any] = {"limit": limit}
        for idx, token in enumerate(clean):
            key = f"t{idx}"
            params[key] = f"%{token}%"
            clauses.append(
                f"""(
                    ITEM_TITLE LIKE :{key}
                    OR ITEM_SHORT LIKE :{key}
                    OR barcodeid LIKE :{key}
                    OR BARCODEID_WS LIKE :{key}
                )"""
            )
        where_sql = " AND ".join(clauses)
        rows = self.db.execute(
            text(
                f"""
                SELECT TOP (:limit)
                    ITEM_ID AS item_id, ITEM_TITLE AS Item_Title, manualid,
                    ITEM_SHORT AS item_short, barcodeid, BARCODEID_WS AS barcodeid_ws
                FROM FIN_ITEM
                WHERE {where_sql}
                ORDER BY manualid DESC
                """
            ),
            params,
        ).mappings().all()
        return [_row_to_dict(r) for r in rows]

    def delete_item(self, item_id: float) -> None:
        self.db.execute(text("DELETE FROM FIN_CAT WHERE ITEM_ID = :item_id"), {"item_id": item_id})
        item = self.get_fin_item_row(item_id)
        if item:
            self.db.delete(item)
        self.db.flush()

    def save_item(self, item: FinItem) -> FinItem:
        self.db.add(item)
        self.db.flush()
        return item
