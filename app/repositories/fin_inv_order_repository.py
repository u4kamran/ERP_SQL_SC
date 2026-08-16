"""Data access for Purchase Order — fin_inv_m_order / fin_inv_d_order (VB6 Fin_InvM_Order parity)."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session


def _row_to_dict(row) -> Dict[str, Any]:
    if row is None:
        return {}
    data = dict(row._mapping) if hasattr(row, "_mapping") else dict(row)
    for key, value in list(data.items()):
        if value is None:
            continue
        if hasattr(value, "__float__") and not isinstance(value, (bool, int, float, str, datetime, date)):
            try:
                data[key] = float(value)
            except (TypeError, ValueError):
                pass
    return data


def _parse_optional_date(value: Any) -> Optional[date]:
    """Parse UI date text; empty/" " → None (NULL) for datetime columns."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text_val = str(value).strip()
    if not text_val or text_val in {".", "-", "/"}:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(text_val[:10], fmt).date()
        except ValueError:
            continue
    return None


def _vget(data: Optional[dict], *keys, default=None):
    if not data:
        return default
    lowered = {str(k).lower(): v for k, v in data.items()}
    for key in keys:
        if key in data and data[key] is not None:
            return data[key]
        val = lowered.get(str(key).lower())
        if val is not None:
            return val
    return default


class FinInvOrderRepository:
    DOC_TYPE_ID = 33

    def __init__(self, db: Session):
        self.db = db

    def get_gsetup(self) -> Dict[str, Any]:
        row = self.db.execute(text("SELECT TOP 1 * FROM gsetup")).mappings().first()
        return _row_to_dict(row)

    def get_doc_type(self, doc_id: int = DOC_TYPE_ID) -> Optional[Dict[str, Any]]:
        row = self.db.execute(
            text("SELECT * FROM fin_c001 WHERE doc_id = :doc_id"),
            {"doc_id": doc_id},
        ).mappings().first()
        return _row_to_dict(row) or None

    def get_book(self, book_id: int) -> Optional[Dict[str, Any]]:
        row = self.db.execute(
            text("SELECT * FROM GL0004 WHERE sys_type = 1 AND book_id = :book_id"),
            {"book_id": book_id},
        ).mappings().first()
        return _row_to_dict(row) or None

    def user_has_book(self, legacy_uid: int, book_id: int) -> bool:
        row = self.db.execute(
            text("SELECT 1 AS ok FROM Gc0003 WHERE l_uid = :uid AND book_id = :book_id"),
            {"uid": legacy_uid, "book_id": book_id},
        ).first()
        return row is not None

    def get_header(self, inv_id: int, fiscal: int = 0, doc_type_id: int = DOC_TYPE_ID) -> Optional[Dict[str, Any]]:
        row = self.db.execute(
            text(
                """
                SELECT * FROM fin_inv_m_order
                WHERE inv_id = :inv_id AND doc_type_id = :doc_type_id AND fiscal = :fiscal
                """
            ),
            {"inv_id": inv_id, "doc_type_id": doc_type_id, "fiscal": fiscal},
        ).mappings().first()
        return _row_to_dict(row) or None

    def get_lines(self, serial_no: int) -> List[Dict[str, Any]]:
        rows = self.db.execute(
            text(
                """
                SELECT * FROM fin_inv_d_order
                WHERE Serial_No = :serial_no
                ORDER BY serial_order
                """
            ),
            {"serial_no": serial_no},
        ).mappings().all()
        return [_row_to_dict(r) for r in rows]

    def allocate_serial_no(self, legacy_uid: int) -> int:
        self.db.execute(
            text("INSERT INTO gc0002 (l_uid, dt_lasta) VALUES (:uid, :dt)"),
            {"uid": legacy_uid, "dt": datetime.now()},
        )
        row = self.db.execute(
            text("SELECT MAX(serial_no) AS serial_no FROM gc0002 WHERE l_uid = :uid"),
            {"uid": legacy_uid},
        ).mappings().first()
        return int(float(_vget(_row_to_dict(row), "serial_no", default=0) or 0))

    def preview_next_inv_id(self) -> int:
        row = self.db.execute(
            text("SELECT MAX(inv_id) AS max_no FROM fin_inv_no_order"),
        ).mappings().first()
        max_no = int(float(_vget(_row_to_dict(row), "max_no", "Max_NO", default=0) or 0))
        return max_no + 1

    def next_inv_id(self, legacy_uid: int) -> int:
        next_id = self.preview_next_inv_id()
        self.db.execute(
            text("INSERT INTO fin_inv_no_order (inv_id, l_uid) VALUES (:inv_id, :uid)"),
            {"inv_id": next_id, "uid": legacy_uid},
        )
        row2 = self.db.execute(
            text("SELECT MAX(inv_id) AS nextid FROM fin_inv_no_order WHERE l_uid = :uid"),
            {"uid": legacy_uid},
        ).mappings().first()
        return int(float(_vget(_row_to_dict(row2), "nextid", default=next_id) or next_id))

    def get_supplier(self, vendor_id: int) -> Optional[Dict[str, Any]]:
        row = self.db.execute(
            text("SELECT * FROM gl0006 WHERE vendor_id = :vendor_id"),
            {"vendor_id": vendor_id},
        ).mappings().first()
        return _row_to_dict(row) or None

    def get_city(self, city_id: int) -> Optional[Dict[str, Any]]:
        row = self.db.execute(
            text("SELECT * FROM City WHERE City_id = :city_id"),
            {"city_id": city_id},
        ).mappings().first()
        return _row_to_dict(row) or None

    def get_item(self, item_id: float) -> Optional[Dict[str, Any]]:
        row = self.db.execute(
            text("SELECT * FROM FIN_ITEM WHERE item_id = :item_id"),
            {"item_id": item_id},
        ).mappings().first()
        return _row_to_dict(row) or None

    def get_item_view_t(
        self,
        *,
        item_id: Optional[float] = None,
        manual_id: Optional[float] = None,
        barcode: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        if item_id is not None:
            sql = "SELECT TOP 1 * FROM V_fin_item_T WHERE item_id = :v"
            params = {"v": item_id}
        elif manual_id is not None:
            sql = "SELECT TOP 1 * FROM V_fin_item_T WHERE manualid = :v"
            params = {"v": manual_id}
        elif barcode is not None:
            sql = "SELECT TOP 1 * FROM V_fin_item_T WHERE barcodeid = :v"
            params = {"v": barcode}
        else:
            return None
        row = self.db.execute(text(sql), params).mappings().first()
        return _row_to_dict(row) or None

    def get_item_view_ws(self, barcode_ws: str) -> Optional[Dict[str, Any]]:
        row = self.db.execute(
            text("SELECT TOP 1 * FROM v_fin_item WHERE barcodeid_ws = :v"),
            {"v": barcode_ws},
        ).mappings().first()
        return _row_to_dict(row) or None

    def check_supplier_item(self, supplier_id: int, item_id: float) -> bool:
        row = self.db.execute(
            text(
                """
                SELECT TOP 1 1 AS ok
                FROM V_FIN_STOCK_SUPPLIER
                WHERE supplier_id = :supplier_id AND item_id = :item_id
                """
            ),
            {"supplier_id": supplier_id, "item_id": item_id},
        ).first()
        return row is not None

    def get_supplier_items(self, supplier_id: int) -> List[Dict[str, Any]]:
        rows = self.db.execute(
            text(
                """
                SELECT ac_title, manualid, ITEM_TITLE, TNOT, CQTY, COST_RATE, SALES_RATE, item_id
                FROM V_FIN_STOCK_SUPPLIER
                WHERE supplier_id = :supplier_id
                ORDER BY item_title
                """
            ),
            {"supplier_id": supplier_id},
        ).mappings().all()
        return [_row_to_dict(r) for r in rows]

    def supplier_has_item(self, supplier_id: int, manual_id: float) -> bool:
        row = self.db.execute(
            text(
                """
                SELECT TOP 1 1 AS ok
                FROM v_FinSuppItems
                WHERE manualid = :manual_id AND supplier_id = :supplier_id
                """
            ),
            {"manual_id": manual_id, "supplier_id": supplier_id},
        ).first()
        return row is not None

    def add_supplier_item(self, supplier_id: int, item_id: float) -> None:
        self.db.execute(
            text(
                """
                INSERT INTO fin_supp_items (supplier_id, item_id, stock_bal)
                VALUES (:supplier_id, :item_id, 0)
                """
            ),
            {"supplier_id": supplier_id, "item_id": item_id},
        )

    def remove_supplier_item(self, supplier_id: int, item_id: float) -> None:
        self.db.execute(
            text("DELETE FROM fin_supp_items WHERE item_id = :item_id AND supplier_id = :supplier_id"),
            {"item_id": item_id, "supplier_id": supplier_id},
        )

    def search_suppliers(self, q: str, limit: int = 40) -> List[Dict[str, Any]]:
        pattern = f"%{q.strip()}%"
        rows = self.db.execute(
            text(
                """
                SELECT TOP (:limit) vendor_id, vendor_title, stax_id, tag_1
                FROM gl0006
                WHERE CAST(vendor_id AS VARCHAR(20)) LIKE :pattern
                   OR vendor_title LIKE :pattern
                ORDER BY vendor_id
                """
            ),
            {"pattern": pattern, "limit": limit},
        ).mappings().all()
        return [_row_to_dict(r) for r in rows]

    def search_items(self, q: str, limit: int = 40) -> List[Dict[str, Any]]:
        pattern = f"%{q.strip()}%"
        rows = self.db.execute(
            text(
                """
                SELECT TOP (:limit) item_id, item_title, manualid, barcodeid
                FROM V_fin_item_T
                WHERE CAST(item_id AS VARCHAR(30)) LIKE :pattern
                   OR item_title LIKE :pattern
                   OR CAST(manualid AS VARCHAR(30)) LIKE :pattern
                   OR barcodeid LIKE :pattern
                ORDER BY item_id
                """
            ),
            {"pattern": pattern, "limit": limit},
        ).mappings().all()
        return [_row_to_dict(r) for r in rows]

    def purchase_history(self, item_id: float, limit: int = 5) -> List[Dict[str, Any]]:
        rows = self.db.execute(
            text(
                """
                SELECT TOP (:limit) PROD_ID, doc_date, supplier_title, QTY,
                       (TOTAL_AMT / NULLIF(QTY, 0)) AS rate, Exp_Date
                FROM v_fin_pur_exp_date
                WHERE ITEM_ID = :item_id
                ORDER BY doc_date DESC
                """
            ),
            {"item_id": str(item_id), "limit": limit},
        ).mappings().all()
        return [_row_to_dict(r) for r in rows]

    def sales_history(self, item_id: float, limit: int = 5) -> List[Dict[str, Any]]:
        rows = self.db.execute(
            text(
                """
                SELECT TOP (:limit) Inv_ID, doc_date, customer_title, QTY,
                       (TOTAL_AMT / NULLIF(QTY, 0)) AS rate
                FROM v_inv1
                WHERE ITEM_ID = :item_id
                ORDER BY doc_date DESC
                """
            ),
            {"item_id": str(item_id), "limit": limit},
        ).mappings().all()
        return [_row_to_dict(r) for r in rows]

    def po_history(self, supplier_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        rows = self.db.execute(
            text(
                """
                SELECT TOP (:limit) INV_ID, DOC_DATE, CUST_ID, CUSTOMER_TITLE,
                       SUM(SALE_AMT) AS TOTAL_AMT
                FROM V_Inv1Order
                WHERE CUST_ID = :supplier_id
                GROUP BY INV_ID, DOC_DATE, CUST_ID, CUSTOMER_TITLE
                ORDER BY DOC_DATE DESC, INV_ID DESC
                """
            ),
            {"supplier_id": supplier_id, "limit": limit},
        ).mappings().all()
        return [_row_to_dict(r) for r in rows]

    def get_print_rows(self, inv_id: int) -> List[Dict[str, Any]]:
        rows = self.db.execute(
            text(
                """
                SELECT * FROM v_inv1Order
                WHERE inv_id = :inv_id
                ORDER BY INV_ID, SERIAL_ORDER
                """
            ),
            {"inv_id": inv_id},
        ).mappings().all()
        return [_row_to_dict(r) for r in rows]

    def delete_detail(self, serial_no: int) -> None:
        self.db.execute(
            text("DELETE FROM fin_inv_d_order WHERE Serial_No = :serial_no"),
            {"serial_no": serial_no},
        )

    def delete_fin_ldgr(self, inv_id: int, serial_no: int, doc_type_id: int = DOC_TYPE_ID) -> None:
        self.db.execute(
            text(
                """
                DELETE FROM fin_ldgr
                WHERE doc_id = :inv_id AND Serial_No = :serial_no AND doc_type_id = :doc_type_id
                """
            ),
            {"inv_id": inv_id, "serial_no": serial_no, "doc_type_id": doc_type_id},
        )

    def delete_fin_ldgr_by_serial(self, serial_no: int) -> None:
        self.db.execute(text("DELETE FROM fin_ldgr WHERE Serial_No = :serial_no"), {"serial_no": serial_no})

    def delete_gl_lines(self, serial_no: int) -> None:
        self.db.execute(text("DELETE FROM gl0003 WHERE Serial_No = :serial_no"), {"serial_no": serial_no})

    def delete_gl_header(self, serial_no: int) -> None:
        self.db.execute(text("DELETE FROM gl0002 WHERE Serial_No = :serial_no"), {"serial_no": serial_no})

    def delete_header(self, inv_id: int, serial_no: int) -> None:
        self.db.execute(
            text("DELETE FROM fin_inv_m_order WHERE inv_id = :inv_id AND Serial_No = :serial_no"),
            {"inv_id": inv_id, "serial_no": serial_no},
        )

    def upsert_header(
        self,
        *,
        is_new: bool,
        serial_no: int,
        inv_id: int,
        gl_voucher_id: int,
        fiscal: int,
        doc_type_id: int,
        doc_date: date,
        supplier_id: int,
        payment_type: int,
        stax_type: int,
        gp_id: str,
        gp_time: str,
        cust_order: str,
        cust_order_date: str,
        sale_amt: float,
        amount_rec: float,
        bal_amt: float,
        customer_title: str,
        address: str,
        stax_id: str,
        city_id: int,
        remarks: str,
        discount_amt: float,
        claim_amt: float,
        other_ded_amt: float,
        loading_amt: float,
        carriage_amt: float,
        other_charges_amt: float,
    ) -> None:
        # Bind native date/datetime — DD/MM/YYYY strings fail under US/ODBC locale
        # (e.g. '15/08/2026' → month 15 → error 242).
        doc_date_t = datetime.now().replace(microsecond=0)
        params = {
            "serial_no": serial_no,
            "inv_id": inv_id,
            "gl_voucher_id": gl_voucher_id,
            "fiscal": fiscal,
            "doc_type_id": doc_type_id,
            "doc_date": doc_date,
            "doc_date_t": doc_date_t,
            "cust_id": supplier_id,
            "payment_type": payment_type,
            "stax_type": stax_type,
            "gp_id": gp_id or " ",
            "gp_time": gp_time or " ",
            "cust_order": cust_order or " ",
            "cust_order_date": _parse_optional_date(cust_order_date),
            "sale_amt": sale_amt,
            "amount_rec": amount_rec,
            "bal_amt": bal_amt,
            "customer_title": customer_title,
            "address": address,
            "stax_id": stax_id,
            "city_id": city_id,
            "country_id": 0,
            "remarks": remarks,
            "discount_amt": discount_amt,
            "claim_amt": claim_amt,
            "other_ded_amt": other_ded_amt,
            "loading_amt": loading_amt,
            "carriage_amt": carriage_amt,
            "other_charges_amt": other_charges_amt,
        }
        if is_new:
            self.db.execute(
                text(
                    """
                    INSERT INTO fin_inv_m_order (
                        serial_no, inv_id, gl_voucher_id, fiscal, doc_type_id,
                        sys_status, sys_use, sys_print,
                        doc_date, doc_date_T, cust_id, payment_type, stax_type,
                        gp_id, gp_time, cust_order, cust_order_date,
                        sale_amt, amount_rec, bal_amt,
                        customer_title, address, stax_id, city_id, country_id, remarks,
                        discount_amt, claim_amt, other_ded_amt,
                        loading_amt, carriage_amt, other_charges_amt
                    ) VALUES (
                        :serial_no, :inv_id, :gl_voucher_id, :fiscal, :doc_type_id,
                        0, 0, 0,
                        :doc_date, :doc_date_t, :cust_id, :payment_type, :stax_type,
                        :gp_id, :gp_time, :cust_order, :cust_order_date,
                        :sale_amt, :amount_rec, :bal_amt,
                        :customer_title, :address, :stax_id, :city_id, :country_id, :remarks,
                        :discount_amt, :claim_amt, :other_ded_amt,
                        :loading_amt, :carriage_amt, :other_charges_amt
                    )
                    """
                ),
                params,
            )
        else:
            self.db.execute(
                text(
                    """
                    UPDATE fin_inv_m_order SET
                        doc_date = :doc_date,
                        doc_date_T = :doc_date_t,
                        cust_id = :cust_id,
                        payment_type = :payment_type,
                        stax_type = :stax_type,
                        gp_id = :gp_id,
                        gp_time = :gp_time,
                        cust_order = :cust_order,
                        cust_order_date = :cust_order_date,
                        sale_amt = :sale_amt,
                        amount_rec = :amount_rec,
                        bal_amt = :bal_amt,
                        customer_title = :customer_title,
                        address = :address,
                        stax_id = :stax_id,
                        city_id = :city_id,
                        remarks = :remarks,
                        discount_amt = :discount_amt,
                        claim_amt = :claim_amt,
                        other_ded_amt = :other_ded_amt,
                        loading_amt = :loading_amt,
                        carriage_amt = :carriage_amt,
                        other_charges_amt = :other_charges_amt,
                        gl_voucher_id = :gl_voucher_id
                    WHERE inv_id = :inv_id AND serial_no = :serial_no
                    """
                ),
                params,
            )

    def insert_detail_line(self, data: dict) -> None:
        self.db.execute(
            text(
                """
                INSERT INTO fin_inv_d_order (
                    inv_id, serial_order, Serial_No, doc_date,
                    item_id, qty, rate, sale_amt, stax_rate, stax_amt, total_amt
                ) VALUES (
                    :inv_id, :serial_order, :serial_no, :doc_date,
                    :item_id, :qty, :rate, :sale_amt, :stax_rate, :stax_amt, :total_amt
                )
                """
            ),
            data,
        )
