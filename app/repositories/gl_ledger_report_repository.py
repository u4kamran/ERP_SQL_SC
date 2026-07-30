"""Data access for General Ledger report."""

from __future__ import annotations

import re
from datetime import date
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session


def _row_to_dict(row) -> Dict[str, Any]:
    return dict(row)


class GlLedgerReportRepository:
    def __init__(self, db: Session):
        self.db = db

    def lookup_account(self, ac_id: int) -> Optional[Dict[str, Any]]:
        row = self.db.execute(
            text(
                """
                SELECT ac_id, ac_title
                FROM Gl0001
                WHERE ac_level = 4 AND ac_id = :ac_id
                """
            ),
            {"ac_id": ac_id},
        ).mappings().first()
        return _row_to_dict(row) if row else None

    def search_whatsapp_contact_rows(self, q: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Temporary: mobile numbers from Gl0001.CREATED_BY."""
        q = (q or "").strip()
        if not q:
            return []
        pattern = f"%{q}%"
        id_digits = re.sub(r"\D", "", q)
        ac_id_match = int(id_digits) if id_digits.isdigit() and len(id_digits) >= 5 else None

        rows = self.db.execute(
            text(
                """
                SELECT TOP (:limit)
                    g1.ac_id,
                    RTRIM(g1.ac_title) AS name,
                    RTRIM(g1.CREATED_BY) AS created_by,
                    'gl0001' AS source
                FROM Gl0001 g1
                WHERE g1.ac_level = 4
                  AND (
                    g1.ac_title LIKE :pattern
                    OR g1.CREATED_BY LIKE :pattern
                    OR (:ac_id IS NOT NULL AND g1.ac_id = :ac_id)
                  )
                ORDER BY g1.ac_title
                """
            ),
            {"pattern": pattern, "limit": limit, "ac_id": ac_id_match},
        ).mappings().all()

        results: List[Dict[str, Any]] = []
        for row in rows:
            item = _row_to_dict(row)
            item["phone"] = item.get("created_by") or ""
            item["contact_person"] = ""
            results.append(item)
        return results

    def search_accounts(self, q: str, limit: int = 50) -> List[Dict[str, Any]]:
        q = (q or "").strip()
        if not q:
            return []
        pattern = f"%{q}%"
        rows = self.db.execute(
            text(
                """
                SELECT TOP (:limit) ac_id, ac_title
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

    def fetch_accounts(
        self,
        start_ac_id: int,
        end_ac_id: int,
        suppress_zero_bal: bool,
    ) -> List[Dict[str, Any]]:
        sql = """
            SELECT ac_id, ac_title, obal, cbal, tnot
            FROM Gl0001
            WHERE ac_level = 4
              AND ac_id >= :start_ac_id
              AND ac_id <= :end_ac_id
        """
        if suppress_zero_bal:
            sql += " AND cbal <> 0"
        sql += " ORDER BY ac_id"
        rows = self.db.execute(
            text(sql),
            {"start_ac_id": start_ac_id, "end_ac_id": end_ac_id},
        ).mappings().all()
        return [_row_to_dict(r) for r in rows]

    def fetch_opening_totals(
        self,
        start_ac_id: int,
        end_ac_id: int,
        date_from: date,
    ) -> Dict[int, Dict[str, float]]:
        rows = self.db.execute(
            text(
                """
                SELECT ac_id,
                       SUM(ISNULL(DEBIT, 0)) AS tdebit,
                       SUM(ISNULL(CREDIT, 0)) AS tcredit
                FROM Gl0003
                WHERE vdate < :date_from
                  AND ac_id >= :start_ac_id
                  AND ac_id <= :end_ac_id
                GROUP BY ac_id
                """
            ),
            {
                "date_from": date_from,
                "start_ac_id": start_ac_id,
                "end_ac_id": end_ac_id,
            },
        ).mappings().all()
        return {
            int(r["ac_id"]): {
                "tdebit": float(r["tdebit"] or 0),
                "tcredit": float(r["tcredit"] or 0),
            }
            for r in rows
        }

    def fetch_transactions(
        self,
        start_ac_id: int,
        end_ac_id: int,
        date_from: date,
        date_to: date,
    ) -> List[Dict[str, Any]]:
        rows = self.db.execute(
            text(
                """
                SELECT g3.ac_id,
                       g2.VOUCHER_ID,
                       g2.book_id,
                       g2.v_mode,
                       g2.VOUCHER_DATE,
                       g2.FISCAL,
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
