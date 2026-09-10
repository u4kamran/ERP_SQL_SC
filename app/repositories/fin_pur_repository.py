"""Data access for Purchase Receipt — Fin_Pur_M / Fin_Pur_D + GL/inventory (VB6 parity)."""

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


class FinPurRepository:
    DOC_TYPE_ID = 2

    def __init__(self, db: Session):
        self.db = db

    # ----- setup -----

    def get_gsetup(self) -> Dict[str, Any]:
        row = self.db.execute(text("SELECT TOP 1 * FROM gsetup")).mappings().first()
        return _row_to_dict(row)

    def get_doc_type(self, doc_id: int = DOC_TYPE_ID) -> Optional[Dict[str, Any]]:
        row = self.db.execute(
            text("SELECT * FROM fin_c001 WHERE doc_id = :doc_id"),
            {"doc_id": doc_id},
        ).mappings().first()
        return _row_to_dict(row) or None

    def get_doc_gl_setup(self, doc_id: int = DOC_TYPE_ID) -> Optional[Dict[str, Any]]:
        row = self.db.execute(
            text("SELECT * FROM fin_c003 WHERE doc_id = :doc_id"),
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

    # ----- master / detail -----

    def get_header(self, prod_id: int, fiscal: int = 0, doc_type_id: int = DOC_TYPE_ID) -> Optional[Dict[str, Any]]:
        row = self.db.execute(
            text(
                """
                SELECT * FROM Fin_Pur_M
                WHERE prod_id = :prod_id AND doc_type_id = :doc_type_id AND fiscal = :fiscal
                """
            ),
            {"prod_id": prod_id, "doc_type_id": doc_type_id, "fiscal": fiscal},
        ).mappings().first()
        return _row_to_dict(row) or None

    def get_header_by_serial(self, serial_no: int) -> Optional[Dict[str, Any]]:
        row = self.db.execute(
            text("SELECT * FROM Fin_Pur_M WHERE serial_no = :serial_no"),
            {"serial_no": serial_no},
        ).mappings().first()
        return _row_to_dict(row) or None

    def get_lines(self, serial_no: int) -> List[Dict[str, Any]]:
        rows = self.db.execute(
            text(
                """
                SELECT * FROM Fin_Pur_D
                WHERE Serial_No = :serial_no
                ORDER BY serial_order
                """
            ),
            {"serial_no": serial_no},
        ).mappings().all()
        return [_row_to_dict(r) for r in rows]

    def next_prod_id(self, fiscal: int = 0) -> int:
        row = self.db.execute(
            text("SELECT MAX(prod_id) AS Max_NO FROM Fin_Pur_M WHERE fiscal = :fiscal"),
            {"fiscal": fiscal},
        ).mappings().first()
        max_no = _vget(_row_to_dict(row), "Max_NO", "max_no")
        if max_no is None:
            return 1
        return int(max_no) + 1

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

    # ----- supplier / item -----

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

    def get_item_view(self, *, item_id: Optional[float] = None, manual_id: Optional[float] = None,
                      barcode: Optional[str] = None, barcode_ws: Optional[str] = None) -> Optional[Dict[str, Any]]:
        if item_id is not None:
            sql = "SELECT TOP 1 * FROM v_fin_item WHERE item_id = :v"
            params = {"v": item_id}
        elif manual_id is not None:
            sql = "SELECT TOP 1 * FROM v_fin_item WHERE manualid = :v"
            params = {"v": manual_id}
        elif barcode is not None:
            sql = "SELECT TOP 1 * FROM v_fin_item WHERE barcodeid = :v"
            params = {"v": barcode}
        elif barcode_ws is not None:
            sql = "SELECT TOP 1 * FROM v_fin_item WHERE barcodeid_ws = :v"
            params = {"v": barcode_ws}
        else:
            return None
        row = self.db.execute(text(sql), params).mappings().first()
        return _row_to_dict(row) or None

    def get_uom(self, uom_id: int) -> Optional[Dict[str, Any]]:
        row = self.db.execute(
            text("SELECT * FROM fin_c002 WHERE uom_id = :uom_id"),
            {"uom_id": uom_id},
        ).mappings().first()
        return _row_to_dict(row) or None

    def get_company(self, co_id: int) -> Optional[Dict[str, Any]]:
        row = self.db.execute(
            text("SELECT * FROM co WHERE co_id = :co_id"),
            {"co_id": co_id},
        ).mappings().first()
        return _row_to_dict(row) or None

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
                FROM FIN_ITEM
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

    # ----- reverse / delete -----

    def reverse_inventory_for_serial(self, serial_no: int) -> None:
        """VB6 CmdSave/CmdDelete: reverse using pur_Amt only."""
        lines = self.get_lines(serial_no)
        for line in lines:
            item_id = float(_vget(line, "item_id", "ITEM_ID", default=0) or 0)
            qty = float(_vget(line, "qty", "QTY", default=0) or 0)
            pur_amt = float(_vget(line, "pur_amt", "PUR_AMT", default=0) or 0)
            if not item_id:
                continue
            self.db.execute(
                text(
                    """
                    UPDATE fin_item
                    SET Cqty = Cqty - :qty,
                        CAMT = CAMT - :pur_amt,
                        Tnot = Tnot - 1,
                        Tnot1 = 0
                    WHERE item_id = :item_id
                    """
                ),
                {"qty": qty, "pur_amt": pur_amt, "item_id": item_id},
            )

    def reverse_gl_balances_for_serial(self, serial_no: int) -> None:
        rows = self.db.execute(
            text("SELECT Ac_id, debit, credit FROM gl0003 WHERE Serial_No = :serial_no"),
            {"serial_no": serial_no},
        ).mappings().all()
        for row in rows:
            data = _row_to_dict(row)
            ac_id = int(_vget(data, "Ac_id", "ac_id"))
            debit = float(_vget(data, "debit", default=0) or 0)
            credit = float(_vget(data, "credit", default=0) or 0)
            self.db.execute(
                text(
                    """
                    UPDATE gl0001
                    SET cbal = cbal - :debit + :credit,
                        Tnot = Tnot - 1
                    WHERE ac_id = :ac_id
                    """
                ),
                {"debit": debit, "credit": credit, "ac_id": ac_id},
            )

    def apply_gl_balances_for_serial(self, serial_no: int) -> tuple[float, float]:
        rows = self.db.execute(
            text("SELECT Ac_id, debit, credit FROM gl0003 WHERE Serial_No = :serial_no"),
            {"serial_no": serial_no},
        ).mappings().all()
        total_dr = 0.0
        total_cr = 0.0
        for row in rows:
            data = _row_to_dict(row)
            ac_id = int(_vget(data, "Ac_id", "ac_id"))
            debit = float(_vget(data, "debit", default=0) or 0)
            credit = float(_vget(data, "credit", default=0) or 0)
            total_dr += debit
            total_cr += credit
            self.db.execute(
                text(
                    """
                    UPDATE gl0001
                    SET cbal = cbal + :debit - :credit,
                        Tnot = Tnot + 1
                    WHERE ac_id = :ac_id
                    """
                ),
                {"debit": debit, "credit": credit, "ac_id": ac_id},
            )
        return total_dr, total_cr

    def delete_detail(self, serial_no: int) -> None:
        self.db.execute(text("DELETE FROM Fin_Pur_D WHERE Serial_No = :serial_no"), {"serial_no": serial_no})

    def delete_header(self, prod_id: int, serial_no: int) -> None:
        self.db.execute(
            text("DELETE FROM Fin_Pur_M WHERE prod_id = :prod_id AND Serial_No = :serial_no"),
            {"prod_id": prod_id, "serial_no": serial_no},
        )

    def delete_fin_ldgr(self, prod_id: int, serial_no: int, doc_type_id: int = DOC_TYPE_ID) -> None:
        self.db.execute(
            text(
                """
                DELETE FROM fin_ldgr
                WHERE doc_id = :prod_id AND Serial_No = :serial_no AND doc_type_id = :doc_type_id
                """
            ),
            {"prod_id": prod_id, "serial_no": serial_no, "doc_type_id": doc_type_id},
        )

    def delete_fin_ldgr_by_serial(self, serial_no: int) -> None:
        self.db.execute(text("DELETE FROM fin_ldgr WHERE Serial_No = :serial_no"), {"serial_no": serial_no})

    def delete_gl_lines(self, serial_no: int) -> None:
        self.db.execute(text("DELETE FROM gl0003 WHERE Serial_No = :serial_no"), {"serial_no": serial_no})

    def delete_gl_header(self, serial_no: int) -> None:
        self.db.execute(text("DELETE FROM gl0002 WHERE serial_no = :serial_no"), {"serial_no": serial_no})

    def delete_gl_for_document(self, serial_no: int, book_id: int, voucher_id: int) -> None:
        self.db.execute(
            text(
                """
                DELETE FROM gl0003
                WHERE Serial_No = :serial_no AND book_id = :book_id AND voucher_id = :voucher_id
                """
            ),
            {"serial_no": serial_no, "book_id": book_id, "voucher_id": voucher_id},
        )
        self.db.execute(
            text(
                """
                DELETE FROM gl0002
                WHERE Serial_No = :serial_no AND book_id = :book_id AND voucher_id = :voucher_id
                """
            ),
            {"serial_no": serial_no, "book_id": book_id, "voucher_id": voucher_id},
        )

    def check_detail_data(self, prod_id: int, book_id: int = 102) -> bool:
        """VB6 checkDetailData — gl0002 without gl0003 lines."""
        row = self.db.execute(
            text(
                """
                SELECT TOP 1 1 AS ok
                FROM Gl0002
                WHERE SERIAL_NO NOT IN (SELECT SERIAL_NO FROM Gl0003)
                  AND book_id = :book_id
                  AND VOUCHER_ID = :prod_id
                """
            ),
            {"book_id": book_id, "prod_id": prod_id},
        ).first()
        return row is not None

    def delete_zero_item_lines(self) -> None:
        self.db.execute(text("DELETE FROM FIN_PUR_D WHERE ITEM_ID = 0"))

    # ----- writes -----

    def upsert_header(
        self,
        *,
        is_new: bool,
        serial_no: int,
        prod_id: int,
        fiscal: int,
        doc_type_id: int,
        doc_date: date,
        supplier_id: int,
        remarks: str,
        payment_type: int,
        stax_type: int,
        gp_id: str,
        gp_time: str,
        vendor_title: str,
        address: str,
        stax_id: str,
        city_id: int,
        discount_amt: float,
        claim_amt: float,
        other_ded_amt: float,
        loading_amt: float,
        carriage_amt: float,
        other_charges_amt: float,
    ) -> None:
        if is_new:
            self.db.execute(
                text(
                    """
                    INSERT INTO Fin_Pur_M (
                        serial_no, prod_id, fiscal, Doc_Type_ID, sys_status, sys_use, sys_print,
                        doc_date, supplier_id, remarks, payment_type, stax_type, gp_id, gp_time,
                        Vendor_Title, Address, stax_id, city_id,
                        discount_amt, claim_amt, other_ded_amt, loading_amt, carriage_amt, other_charges_amt
                    ) VALUES (
                        :serial_no, :prod_id, :fiscal, :doc_type_id, 0, 0, 0,
                        :doc_date, :supplier_id, :remarks, :payment_type, :stax_type, :gp_id, :gp_time,
                        :vendor_title, :address, :stax_id, :city_id,
                        :discount_amt, :claim_amt, :other_ded_amt, :loading_amt, :carriage_amt, :other_charges_amt
                    )
                    """
                ),
                {
                    "serial_no": serial_no,
                    "prod_id": prod_id,
                    "fiscal": fiscal,
                    "doc_type_id": doc_type_id,
                    "doc_date": doc_date,
                    "supplier_id": supplier_id,
                    "remarks": remarks,
                    "payment_type": payment_type,
                    "stax_type": stax_type,
                    "gp_id": gp_id or " ",
                    "gp_time": gp_time or " ",
                    "vendor_title": vendor_title,
                    "address": address,
                    "stax_id": stax_id,
                    "city_id": city_id,
                    "discount_amt": discount_amt,
                    "claim_amt": claim_amt,
                    "other_ded_amt": other_ded_amt,
                    "loading_amt": loading_amt,
                    "carriage_amt": carriage_amt,
                    "other_charges_amt": other_charges_amt,
                },
            )
        else:
            self.db.execute(
                text(
                    """
                    UPDATE Fin_Pur_M SET
                        sys_status = 0, sys_use = 0, sys_print = 0,
                        doc_date = :doc_date, supplier_id = :supplier_id, remarks = :remarks,
                        payment_type = :payment_type, stax_type = :stax_type,
                        gp_id = :gp_id, gp_time = :gp_time,
                        Vendor_Title = :vendor_title, Address = :address,
                        stax_id = :stax_id, city_id = :city_id,
                        discount_amt = :discount_amt, claim_amt = :claim_amt,
                        other_ded_amt = :other_ded_amt, loading_amt = :loading_amt,
                        carriage_amt = :carriage_amt, other_charges_amt = :other_charges_amt
                    WHERE prod_id = :prod_id AND Doc_Type_ID = :doc_type_id AND fiscal = :fiscal
                    """
                ),
                {
                    "prod_id": prod_id,
                    "doc_type_id": doc_type_id,
                    "fiscal": fiscal,
                    "doc_date": doc_date,
                    "supplier_id": supplier_id,
                    "remarks": remarks,
                    "payment_type": payment_type,
                    "stax_type": stax_type,
                    "gp_id": gp_id or " ",
                    "gp_time": gp_time or " ",
                    "vendor_title": vendor_title,
                    "address": address,
                    "stax_id": stax_id,
                    "city_id": city_id,
                    "discount_amt": discount_amt,
                    "claim_amt": claim_amt,
                    "other_ded_amt": other_ded_amt,
                    "loading_amt": loading_amt,
                    "carriage_amt": carriage_amt,
                    "other_charges_amt": other_charges_amt,
                },
            )

    def upsert_gl_header(
        self,
        *,
        is_new: bool,
        serial_no: int,
        voucher_id: int,
        book_id: int,
        v_mode: int,
        fiscal: int,
        book_type: int,
        voucher_date: date,
        amount: float,
        tnot: int,
        username: str,
    ) -> None:
        existing = self.db.execute(
            text("SELECT serial_no FROM gl0002 WHERE serial_no = :serial_no"),
            {"serial_no": serial_no},
        ).first()
        if existing is None:
            self.db.execute(
                text(
                    """
                    INSERT INTO gl0002 (
                        Voucher_ID, book_id, v_mode, fiscal, book_type, eby, remarks,
                        sys_status, sys_use, sys_print, voucher_date, serial_no, Amount, Tnot, edit_by
                    ) VALUES (
                        :voucher_id, :book_id, :v_mode, :fiscal, :book_type, :eby, 'Nil',
                        0, 0, 0, :voucher_date, :serial_no, :amount, :tnot, :edit_by
                    )
                    """
                ),
                {
                    "voucher_id": voucher_id,
                    "book_id": book_id,
                    "v_mode": v_mode,
                    "fiscal": fiscal,
                    "book_type": book_type,
                    "eby": username,
                    "voucher_date": voucher_date,
                    "serial_no": serial_no,
                    "amount": amount,
                    "tnot": tnot,
                    "edit_by": username,
                },
            )
        else:
            self.db.execute(
                text(
                    """
                    UPDATE gl0002 SET
                        voucher_date = :voucher_date, serial_no = :serial_no,
                        Amount = :amount, Tnot = :tnot, edit_by = :edit_by
                    WHERE serial_no = :serial_no
                    """
                ),
                {
                    "voucher_date": voucher_date,
                    "serial_no": serial_no,
                    "amount": amount,
                    "tnot": tnot,
                    "edit_by": username,
                },
            )

    def insert_detail_line(self, params: Dict[str, Any]) -> None:
        self.db.execute(
            text(
                """
                INSERT INTO fin_pur_d (
                    prod_id, serial_order, Serial_No, doc_Date, item_ID, qty, rate, PUR_amt,
                    stax_rate, stax_amt, disc_Per, disc_amt, disc_Per_oi, disc_amt_oi,
                    total_amt, remarks, exp_date
                ) VALUES (
                    :prod_id, :serial_order, :serial_no, :doc_date, :item_id, :qty, :rate, :pur_amt,
                    :stax_rate, :stax_amt, :disc_per, :disc_amt, :disc_per_oi, :disc_amt_oi,
                    :total_amt, :remarks, :exp_date
                )
                """
            ),
            params,
        )

    def ensure_supp_item(self, supplier_id: int, item_id: float) -> None:
        row = self.db.execute(
            text(
                """
                SELECT 1 AS ok FROM FIN_SUPP_ITEMS
                WHERE item_id = :item_id AND supplier_id = :supplier_id
                """
            ),
            {"item_id": item_id, "supplier_id": supplier_id},
        ).first()
        if row is None:
            self.db.execute(
                text(
                    """
                    INSERT INTO fin_supp_items (supplier_id, item_id, stock_bal)
                    VALUES (:supplier_id, :item_id, 0)
                    """
                ),
                {"supplier_id": supplier_id, "item_id": item_id},
            )

    def update_item_on_purchase(
        self,
        *,
        item_id: float,
        qty: float,
        stock_amt: float,
        cost_rate: float,
    ) -> None:
        self.db.execute(
            text(
                """
                UPDATE fin_item SET
                    Cqty = Cqty + :qty,
                    CAMT = CAMT + :stock_amt,
                    cost_Rate = :cost_rate,
                    Tnot = Tnot + 1,
                    Tnot1 = 0
                WHERE item_id = :item_id
                """
            ),
            {"item_id": item_id, "qty": qty, "stock_amt": stock_amt, "cost_rate": cost_rate},
        )

    def update_item_from_line_entry(
        self,
        *,
        item_id: float,
        mrp: float,
        stax_reg: float,
        oamt1: float,
        camt1: float,
        cqty1: float,
        co_id: int,
    ) -> None:
        """Fin_PurD CmdSave — update item last-purchase fields."""
        self.db.execute(
            text(
                """
                UPDATE fin_item SET
                    disc_p1 = :mrp,
                    STAX_REG = :stax_reg,
                    oamt1 = :oamt1,
                    camt1 = :camt1,
                    cqty1 = :cqty1,
                    co_id = :co_id
                WHERE item_ID = :item_id
                """
            ),
            {
                "mrp": mrp,
                "stax_reg": stax_reg,
                "oamt1": oamt1,
                "camt1": camt1,
                "cqty1": cqty1,
                "co_id": co_id,
                "item_id": item_id,
            },
        )

    def insert_fin_ldgr(self, params: Dict[str, Any]) -> None:
        self.db.execute(
            text(
                """
                INSERT INTO fin_ldgr (
                    Item_ID, doc_id, doc_date, fiscal, Doc_Type_ID, serial_no,
                    Qtydr, Qtycr, Rate, amtdr, amtcr, [desc]
                ) VALUES (
                    :item_id, :doc_id, :doc_date, :fiscal, :doc_type_id, :serial_no,
                    :qtydr, 0, :rate, :amtdr, 0, :desc
                )
                """
            ),
            params,
        )

    def insert_gl_line(self, params: Dict[str, Any]) -> None:
        self.db.execute(
            text(
                """
                INSERT INTO gl0003 (
                    Voucher_ID, book_id, vdate, serial_no, Serial_order, Ac_id,
                    adcn, Narration, debit, credit, external_id, ref_id
                ) VALUES (
                    :voucher_id, :book_id, :vdate, :serial_no, :serial_order, :ac_id,
                    :adcn, :narration, :debit, :credit, 0, 0
                )
                """
            ),
            params,
        )

    def assign_co_to_items(self, co_id: int, item_ids: List[float]) -> int:
        if not item_ids:
            return 0
        count = 0
        for item_id in item_ids:
            self.db.execute(
                text("UPDATE fin_item SET co_id = :co_id WHERE item_id = :item_id"),
                {"co_id": co_id, "item_id": item_id},
            )
            count += 1
        return count
