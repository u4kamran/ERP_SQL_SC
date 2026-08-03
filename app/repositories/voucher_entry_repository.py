"""Data access for voucher entry — same tables as VB6 (GL0002, GL0003, GL0001, gc0002)."""

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
        if hasattr(value, "__float__") and not isinstance(value, (bool, int, float, str)):
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


class VoucherEntryRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_gsetup(self) -> Dict[str, Any]:
        row = self.db.execute(text("SELECT TOP 1 * FROM gsetup")).mappings().first()
        return _row_to_dict(row)

    def list_books(self, legacy_uid: int, admin_bypass: bool = False) -> List[Dict[str, Any]]:
        if admin_bypass:
            sql = """
                SELECT book_id, book_title, voucher_abbr, book_type, ac_id,
                       v_numbering, v_combination, bb_od, title_JV, ed_status
                FROM GL0004
                WHERE sys_type = 0
                ORDER BY book_id
            """
            rows = self.db.execute(text(sql)).mappings().all()
        else:
            sql = """
                SELECT b.book_id, b.book_title, b.voucher_abbr, b.book_type, b.ac_id,
                       b.v_numbering, b.v_combination, b.bb_od, b.title_JV, b.ed_status
                FROM GL0004 b
                INNER JOIN Gc0003 g ON g.book_id = b.book_id AND g.l_uid = :uid
                WHERE b.sys_type = 0
                ORDER BY b.book_id
            """
            rows = self.db.execute(text(sql), {"uid": legacy_uid}).mappings().all()
        return [_row_to_dict(r) for r in rows]

    def get_book(self, book_id: int) -> Optional[Dict[str, Any]]:
        row = self.db.execute(
            text(
                """
                SELECT book_id, book_title, voucher_abbr, book_type, ac_id,
                       v_numbering, v_combination, bb_od, title_JV, ed_status
                FROM GL0004
                WHERE sys_type = 0 AND book_id = :book_id
                """
            ),
            {"book_id": book_id},
        ).mappings().first()
        return _row_to_dict(row) or None

    def user_has_book(self, legacy_uid: int, book_id: int) -> bool:
        row = self.db.execute(
            text("SELECT 1 AS ok FROM Gc0003 WHERE l_uid = :uid AND book_id = :book_id"),
            {"uid": legacy_uid, "book_id": book_id},
        ).first()
        return row is not None

    def get_account(self, ac_id: int) -> Optional[Dict[str, Any]]:
        row = self.db.execute(
            text(
                """
                SELECT ac_id, ac_title, ac_level, ed_status, cbal, Tnot
                FROM Gl0001
                WHERE ac_id = :ac_id
                """
            ),
            {"ac_id": ac_id},
        ).mappings().first()
        return _row_to_dict(row) or None

    def search_accounts(self, q: str, limit: int = 40) -> List[Dict[str, Any]]:
        pattern = f"%{q.strip()}%"
        rows = self.db.execute(
            text(
                """
                SELECT TOP (:limit) ac_id, ac_title, cbal
                FROM Gl0001
                WHERE ac_level = 4
                  AND (
                    CAST(ac_id AS VARCHAR(20)) LIKE :pattern
                    OR ac_title LIKE :pattern
                  )
                ORDER BY ac_id
                """
            ),
            {"pattern": pattern, "limit": limit},
        ).mappings().all()
        return [_row_to_dict(r) for r in rows]

    def search_narration_templates(self, q: str, limit: int = 40) -> List[Dict[str, Any]]:
        pattern = f"%{q.strip()}%"
        rows = self.db.execute(
            text(
                """
                SELECT TOP (:limit) nar_id, nar_title, ref_title
                FROM gl_seq
                WHERE nar_title LIKE :pattern
                ORDER BY nar_title
                """
            ),
            {"pattern": pattern, "limit": limit},
        ).mappings().all()
        return [_row_to_dict(r) for r in rows]

    def search_narration_history(self, ac_id: int, q: str, limit: int = 40) -> List[Dict[str, Any]]:
        pattern = f"%{q.strip()}%"
        rows = self.db.execute(
            text(
                """
                SELECT TOP (:limit) narration, COUNT(*) AS use_count
                FROM Gl0003
                WHERE ac_id = :ac_id AND narration LIKE :pattern
                GROUP BY narration
                ORDER BY use_count DESC, narration
                """
            ),
            {"ac_id": ac_id, "pattern": pattern, "limit": limit},
        ).mappings().all()
        return [_row_to_dict(r) for r in rows]

    def last_narration_for_account(self, ac_id: int) -> Optional[str]:
        row = self.db.execute(
            text(
                """
                SELECT TOP 1 narration
                FROM Gl0003
                WHERE ac_id = :ac_id AND narration IS NOT NULL AND RTRIM(narration) <> ''
                ORDER BY serial_no DESC, serial_order DESC
                """
            ),
            {"ac_id": ac_id},
        ).mappings().first()
        if not row:
            return None
        return str(_vget(_row_to_dict(row), "narration", default="") or "").strip()

    def get_header_by_key(
        self, voucher_id: int, book_id: int, v_mode: int, fiscal: int
    ) -> Optional[Dict[str, Any]]:
        row = self.db.execute(
            text(
                """
                SELECT *
                FROM GL0002
                WHERE voucher_id = :voucher_id AND book_id = :book_id
                  AND v_mode = :v_mode AND fiscal = :fiscal
                """
            ),
            {
                "voucher_id": voucher_id,
                "book_id": book_id,
                "v_mode": v_mode,
                "fiscal": fiscal,
            },
        ).mappings().first()
        return _row_to_dict(row) or None

    def list_headers_by_book_voucher(
        self, voucher_id: int, book_id: int, v_mode: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        sql = """
            SELECT *
            FROM GL0002
            WHERE voucher_id = :voucher_id AND book_id = :book_id
        """
        params: Dict[str, Any] = {"voucher_id": voucher_id, "book_id": book_id}
        if v_mode is not None:
            sql += " AND v_mode = :v_mode"
            params["v_mode"] = v_mode
        sql += " ORDER BY fiscal DESC, serial_no DESC"
        rows = self.db.execute(text(sql), params).mappings().all()
        return [_row_to_dict(r) for r in rows]

    def get_header_by_serial(self, serial_no: float) -> Optional[Dict[str, Any]]:
        row = self.db.execute(
            text("SELECT * FROM GL0002 WHERE serial_no = :serial_no"),
            {"serial_no": serial_no},
        ).mappings().first()
        return _row_to_dict(row) or None

    def get_lines(self, serial_no: float) -> List[Dict[str, Any]]:
        rows = self.db.execute(
            text(
                """
                SELECT serial_order, Ac_ID AS ac_id, Narration AS narration,
                       debit, credit, adcn AS reference
                FROM Gl0003
                WHERE serial_no = :serial_no
                ORDER BY serial_order
                """
            ),
            {"serial_no": serial_no},
        ).mappings().all()
        return [_row_to_dict(r) for r in rows]

    def next_voucher_id(self, book_id: int, v_mode: int, fiscal: int) -> int:
        row = self.db.execute(
            text(
                """
                SELECT MAX(voucher_id) AS max_no
                FROM GL0002
                WHERE book_id = :book_id AND v_mode = :v_mode AND fiscal = :fiscal
                """
            ),
            {"book_id": book_id, "v_mode": v_mode, "fiscal": fiscal},
        ).mappings().first()
        data = _row_to_dict(row)
        max_no = _vget(data, "max_no", "Max_NO")
        if max_no is None:
            return 1
        return int(max_no) + 1

    def allocate_serial_no(self, legacy_uid: int) -> float:
        self.db.execute(
            text("INSERT INTO gc0002 (l_uid, dt_lasta) VALUES (:uid, :dt)"),
            {"uid": legacy_uid, "dt": datetime.now()},
        )
        row = self.db.execute(
            text("SELECT MAX(serial_no) AS serial_no FROM gc0002 WHERE l_uid = :uid"),
            {"uid": legacy_uid},
        ).mappings().first()
        return float(_vget(_row_to_dict(row), "serial_no", default=0))

    def reverse_balances_for_serial(self, serial_no: float) -> None:
        lines = self.get_lines(serial_no)
        for line in lines:
            ac_id = int(_vget(line, "ac_id", "Ac_ID"))
            debit = float(_vget(line, "debit", default=0) or 0)
            credit = float(_vget(line, "credit", default=0) or 0)
            self.db.execute(
                text(
                    """
                    UPDATE Gl0001
                    SET cbal = cbal - :debit + :credit,
                        Tnot = Tnot - 1
                    WHERE ac_id = :ac_id
                    """
                ),
                {"ac_id": ac_id, "debit": debit, "credit": credit},
            )

    def delete_lines(self, serial_no: float) -> None:
        self.db.execute(
            text("DELETE FROM Gl0003 WHERE serial_no = :serial_no"),
            {"serial_no": serial_no},
        )

    def delete_header(self, serial_no: float) -> None:
        self.db.execute(
            text("DELETE FROM GL0002 WHERE serial_no = :serial_no"),
            {"serial_no": serial_no},
        )

    def insert_header(
        self,
        *,
        serial_no: float,
        voucher_id: int,
        book_id: int,
        v_mode: int,
        fiscal: int,
        voucher_date: date,
        remarks: str,
        amount: float,
        book_type: int,
        line_count: int,
        username: str,
        is_new: bool,
    ) -> None:
        if is_new:
            self.db.execute(
                text(
                    """
                    INSERT INTO GL0002 (
                        serial_no, voucher_id, book_id, v_mode, fiscal,
                        voucher_date, remarks, Amount, book_type, Tnot,
                        sys_status, sys_use, sys_print, signed_by, eby, edit_by
                    ) VALUES (
                        :serial_no, :voucher_id, :book_id, :v_mode, :fiscal,
                        :voucher_date, :remarks, :amount, :book_type, :tnot,
                        0, 0, 0, ' ', :eby, :edit_by
                    )
                    """
                ),
                {
                    "serial_no": serial_no,
                    "voucher_id": voucher_id,
                    "book_id": book_id,
                    "v_mode": v_mode,
                    "fiscal": fiscal,
                    "voucher_date": voucher_date,
                    "remarks": remarks,
                    "amount": amount,
                    "book_type": book_type,
                    "tnot": line_count,
                    "eby": username,
                    "edit_by": username,
                },
            )
        else:
            self.db.execute(
                text(
                    """
                    UPDATE GL0002
                    SET voucher_date = :voucher_date,
                        remarks = :remarks,
                        Amount = :amount,
                        book_type = :book_type,
                        Tnot = :tnot,
                        sys_status = 0,
                        sys_use = 0,
                        sys_print = 0,
                        signed_by = ' ',
                        edit_by = :edit_by
                    WHERE serial_no = :serial_no
                    """
                ),
                {
                    "serial_no": serial_no,
                    "voucher_date": voucher_date,
                    "remarks": remarks,
                    "amount": amount,
                    "book_type": book_type,
                    "tnot": line_count,
                    "edit_by": username,
                },
            )

    def insert_line(
        self,
        *,
        serial_no: float,
        voucher_id: int,
        book_id: int,
        serial_order: int,
        voucher_date: date,
        ac_id: int,
        narration: str,
        debit: float,
        credit: float,
        reference: str,
    ) -> None:
        self.db.execute(
            text(
                """
                INSERT INTO Gl0003 (
                    voucher_id, book_id, serial_order, serial_no, VDate,
                    Ac_ID, Narration, debit, credit, adcn, REF_ID
                ) VALUES (
                    :voucher_id, :book_id, :serial_order, :serial_no, :vdate,
                    :ac_id, :narration, :debit, :credit, :reference, 0
                )
                """
            ),
            {
                "voucher_id": voucher_id,
                "book_id": book_id,
                "serial_order": serial_order,
                "serial_no": serial_no,
                "vdate": voucher_date,
                "ac_id": ac_id,
                "narration": narration,
                "debit": debit,
                "credit": credit,
                "reference": reference,
            },
        )

    def apply_balance(self, ac_id: int, debit: float, credit: float) -> None:
        self.db.execute(
            text(
                """
                UPDATE Gl0001
                SET cbal = cbal + :debit - :credit,
                    Tnot = Tnot + 1
                WHERE ac_id = :ac_id
                """
            ),
            {"ac_id": ac_id, "debit": debit, "credit": credit},
        )

    def get_last_voucher_lines(self, book_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        row = self.db.execute(
            text(
                """
                SELECT TOP 1 serial_no
                FROM GL0002
                WHERE book_id = :book_id
                ORDER BY serial_no DESC
                """
            ),
            {"book_id": book_id},
        ).mappings().first()
        if not row:
            return []
        serial_no = _vget(_row_to_dict(row), "serial_no")
        lines = self.get_lines(float(serial_no))
        return lines[:limit]
