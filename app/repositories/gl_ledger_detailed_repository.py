"""Data access for Detailed Customer Ledger (extends GL ledger reads; no schema changes)."""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, List

from sqlalchemy import bindparam, text
from sqlalchemy.orm import Session

from app.repositories.gl_ledger_report_repository import GlLedgerReportRepository, _row_to_dict


class GlLedgerDetailedReportRepository(GlLedgerReportRepository):
    """Reuse GL ledger queries; add SERIAL_NO + detail lookups for INV/PUR/SRT/PURR."""

    def __init__(self, db: Session):
        super().__init__(db)

    def fetch_transactions(
        self,
        start_ac_id: int,
        end_ac_id: int,
        date_from: date,
        date_to: date,
    ) -> List[Dict[str, Any]]:
        """Same as GL ledger fetch, plus SERIAL_NO for detail joins."""
        rows = self.db.execute(
            text(
                """
                SELECT g3.ac_id,
                       g2.VOUCHER_ID,
                       g2.book_id,
                       g2.v_mode,
                       g2.VOUCHER_DATE,
                       g2.FISCAL,
                       g2.SERIAL_NO,
                       g3.serial_order,
                       g3.NARRATION,
                       g3.DEBIT,
                       g3.CREDIT,
                       g3.ADCN,
                       g3.EXTERNAL_ID,
                       g3.REF_ID,
                       g4.VOUCHER_ABBR
                FROM Gl0002 g2
                RIGHT JOIN Gl0003 g3 ON g2.SERIAL_NO = g3.SERIAL_NO
                LEFT JOIN Gl0004 g4 ON g2.book_id = g4.BOOK_ID
                WHERE g2.VOUCHER_DATE >= :date_from
                  AND g2.VOUCHER_DATE <= :date_to
                  AND g3.ac_id >= :start_ac_id
                  AND g3.ac_id <= :end_ac_id
                ORDER BY g3.ac_id, g2.VOUCHER_DATE, g2.VOUCHER_ID, g2.book_id
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

    # ── Sales Invoice (INV, book_id=121) ──────────────────────────

    def fetch_invoice_headers_by_serials(self, serials: List[int]) -> Dict[int, Dict[str, Any]]:
        if not serials:
            return {}
        unique = sorted({int(s) for s in serials})
        rows = self.db.execute(
            text(
                """
                SELECT
                    m.SERIAL_NO,
                    m.INV_ID,
                    RTRIM(ISNULL(CONVERT(VARCHAR(50), m.GP_ID), '')) AS GP_ID
                FROM fin_inv_m m
                WHERE m.SERIAL_NO IN :serials
                """
            ).bindparams(bindparam("serials", expanding=True)),
            {"serials": unique},
        ).mappings().all()
        return {int(r["SERIAL_NO"]): _row_to_dict(r) for r in rows}

    def fetch_invoice_lines_by_serials(self, serials: List[int]) -> Dict[int, List[Dict[str, Any]]]:
        if not serials:
            return {}
        unique = sorted({int(s) for s in serials})
        rows = self.db.execute(
            text(
                """
                SELECT
                    d.SERIAL_NO,
                    d.INV_ID,
                    d.SERIAL_ORDER,
                    d.QTY,
                    d.RATE,
                    d.SALE_AMT,
                    d.STAX_RATE,
                    d.STAX_AMT,
                    d.TOTAL_AMT,
                    RTRIM(ISNULL(i.ITEM_TITLE, '')) AS ITEM_TITLE
                FROM fin_inv_d d
                LEFT JOIN fin_item i ON i.ITEM_ID = d.ITEM_ID
                WHERE d.SERIAL_NO IN :serials
                ORDER BY d.SERIAL_NO, d.SERIAL_ORDER
                """
            ).bindparams(bindparam("serials", expanding=True)),
            {"serials": unique},
        ).mappings().all()
        by_serial: Dict[int, List[Dict[str, Any]]] = {}
        for row in rows:
            sn = int(row["SERIAL_NO"])
            by_serial.setdefault(sn, []).append(_row_to_dict(row))
        return by_serial

    # ── Sale Return (SRT, book_id=105) ────────────────────────────

    def fetch_sale_return_headers_by_serials(self, serials: List[int]) -> Dict[int, Dict[str, Any]]:
        if not serials:
            return {}
        unique = sorted({int(s) for s in serials})
        rows = self.db.execute(
            text(
                """
                SELECT
                    m.SERIAL_NO,
                    m.INV_ID,
                    RTRIM(ISNULL(CONVERT(VARCHAR(50), m.GP_ID), '')) AS GP_ID
                FROM Fin_InvR_M m
                WHERE m.SERIAL_NO IN :serials
                """
            ).bindparams(bindparam("serials", expanding=True)),
            {"serials": unique},
        ).mappings().all()
        return {int(r["SERIAL_NO"]): _row_to_dict(r) for r in rows}

    def fetch_sale_return_lines_by_serials(self, serials: List[int]) -> Dict[int, List[Dict[str, Any]]]:
        if not serials:
            return {}
        unique = sorted({int(s) for s in serials})
        rows = self.db.execute(
            text(
                """
                SELECT
                    d.SERIAL_NO,
                    d.SERIAL_ORDER,
                    d.QTY,
                    d.RATE,
                    d.SALE_AMT,
                    d.STAX_RATE,
                    d.STAX_AMT,
                    d.TOTAL_AMT,
                    RTRIM(ISNULL(i.ITEM_TITLE, '')) AS ITEM_TITLE
                FROM fin_invR_D d
                LEFT JOIN fin_item i ON i.ITEM_ID = d.ITEM_ID
                WHERE d.SERIAL_NO IN :serials
                ORDER BY d.SERIAL_NO, d.SERIAL_ORDER
                """
            ).bindparams(bindparam("serials", expanding=True)),
            {"serials": unique},
        ).mappings().all()
        by_serial: Dict[int, List[Dict[str, Any]]] = {}
        for row in rows:
            sn = int(row["SERIAL_NO"])
            by_serial.setdefault(sn, []).append(_row_to_dict(row))
        return by_serial

    # ── GRN / Purchase (PUR, book_id=102) ─────────────────────────

    def fetch_purchase_headers_by_serials(self, serials: List[int]) -> Dict[int, Dict[str, Any]]:
        if not serials:
            return {}
        unique = sorted({int(s) for s in serials})
        rows = self.db.execute(
            text(
                """
                SELECT
                    m.SERIAL_NO,
                    m.PROD_ID,
                    RTRIM(ISNULL(CONVERT(VARCHAR(50), m.GP_ID), '')) AS GP_ID
                FROM Fin_Pur_M m
                WHERE m.SERIAL_NO IN :serials
                """
            ).bindparams(bindparam("serials", expanding=True)),
            {"serials": unique},
        ).mappings().all()
        return {int(r["SERIAL_NO"]): _row_to_dict(r) for r in rows}

    def fetch_purchase_lines_by_serials(self, serials: List[int]) -> Dict[int, List[Dict[str, Any]]]:
        if not serials:
            return {}
        unique = sorted({int(s) for s in serials})
        rows = self.db.execute(
            text(
                """
                SELECT
                    d.SERIAL_NO,
                    d.SERIAL_ORDER,
                    d.QTY,
                    d.RATE,
                    d.PUR_AMT,
                    d.STAX_RATE,
                    d.STAX_AMT,
                    d.TOTAL_AMT,
                    RTRIM(ISNULL(i.ITEM_TITLE, '')) AS ITEM_TITLE
                FROM Fin_Pur_D d
                LEFT JOIN fin_item i ON i.ITEM_ID = d.ITEM_ID
                WHERE d.SERIAL_NO IN :serials
                ORDER BY d.SERIAL_NO, d.SERIAL_ORDER
                """
            ).bindparams(bindparam("serials", expanding=True)),
            {"serials": unique},
        ).mappings().all()
        by_serial: Dict[int, List[Dict[str, Any]]] = {}
        for row in rows:
            sn = int(row["SERIAL_NO"])
            by_serial.setdefault(sn, []).append(_row_to_dict(row))
        return by_serial

    # ── Purchase Return (PURR, book_id=125) ───────────────────────

    def fetch_purchase_return_headers_by_serials(self, serials: List[int]) -> Dict[int, Dict[str, Any]]:
        if not serials:
            return {}
        unique = sorted({int(s) for s in serials})
        rows = self.db.execute(
            text(
                """
                SELECT
                    m.SERIAL_NO,
                    m.PROD_ID,
                    RTRIM(ISNULL(CONVERT(VARCHAR(50), m.GP_ID), '')) AS GP_ID
                FROM Fin_Pur_Return_M m
                WHERE m.SERIAL_NO IN :serials
                """
            ).bindparams(bindparam("serials", expanding=True)),
            {"serials": unique},
        ).mappings().all()
        return {int(r["SERIAL_NO"]): _row_to_dict(r) for r in rows}

    def fetch_purchase_return_lines_by_serials(self, serials: List[int]) -> Dict[int, List[Dict[str, Any]]]:
        if not serials:
            return {}
        unique = sorted({int(s) for s in serials})
        rows = self.db.execute(
            text(
                """
                SELECT
                    d.SERIAL_NO,
                    d.SERIAL_ORDER,
                    d.QTY,
                    d.RATE,
                    d.PUR_AMT,
                    d.STAX_RATE,
                    d.STAX_AMT,
                    d.TOTAL_AMT,
                    RTRIM(ISNULL(i.ITEM_TITLE, '')) AS ITEM_TITLE
                FROM Fin_Pur_Return_D d
                LEFT JOIN fin_item i ON i.ITEM_ID = d.ITEM_ID
                WHERE d.SERIAL_NO IN :serials
                ORDER BY d.SERIAL_NO, d.SERIAL_ORDER
                """
            ).bindparams(bindparam("serials", expanding=True)),
            {"serials": unique},
        ).mappings().all()
        by_serial: Dict[int, List[Dict[str, Any]]] = {}
        for row in rows:
            sn = int(row["SERIAL_NO"])
            by_serial.setdefault(sn, []).append(_row_to_dict(row))
        return by_serial
