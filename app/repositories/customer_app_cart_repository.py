"""Repository for Customer App Cart tables (business DB)."""

from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


_CART_COLS = """
    id,
    cart_ref,
    cust_sms_id,
    RTRIM(customer_name) AS customer_name,
    RTRIM(customer_mobile_no) AS customer_mobile_no,
    mobile_key,
    RTRIM(ISNULL(customer_address, '')) AS customer_address,
    status,
    source,
    total_items,
    CAST(estimated_subtotal AS FLOAT) AS estimated_subtotal,
    CAST(estimated_discount AS FLOAT) AS estimated_discount,
    CAST(estimated_tax AS FLOAT) AS estimated_tax,
    CAST(estimated_total AS FLOAT) AS estimated_total,
    converted_doc_ref,
    created_at,
    updated_at,
    idempotency_key
"""


class CustomerAppCartRepository:
    def __init__(self, db: Session):
        self.db = db

    def find_customer_by_mobile_key(self, mobile_key: str) -> dict[str, Any] | None:
        row = self.db.execute(
            text(
                """
                SELECT TOP 1
                    CUST_ID AS cust_id,
                    RTRIM(ISNULL(CUST_NAME, '')) AS cust_name,
                    RTRIM(ISNULL(MOBILE_NO, '')) AS mobile_no,
                    RTRIM(ISNULL(CUST_ADDRESS, '')) AS cust_address,
                    STATUS AS status,
                    ADDED_DATETIME AS added_datetime
                FROM dbo.CUST_SMS
                WHERE LEN(LTRIM(RTRIM(ISNULL(MOBILE_NO, '')))) >= 10
                  AND RIGHT(
                      REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
                          LTRIM(RTRIM(MOBILE_NO)),
                          ' ', ''), '-', ''), '(', ''), ')', ''), '+', ''),
                      10
                  ) = :mobile_key
                ORDER BY CUST_ID DESC
                """
            ),
            {"mobile_key": mobile_key},
        ).mappings().first()
        return dict(row) if row else None

    def create_customer(self, *, name: str, mobile: str, address: str | None) -> int:
        row = self.db.execute(
            text(
                """
                INSERT INTO dbo.CUST_SMS (
                    CUST_NAME, MOBILE_NO, MOBILE_NO_TMP, CUST_ADDRESS,
                    STATUS, ADDED_DATETIME,
                    STAR_RATING, STAR_RATING_VALUE,
                    STAR_RATING_VISIT, STAR_RATING_VISIT_VALUE,
                    STAR_RATING_TSALES, STAR_RATING_TSALES_VALUE
                )
                OUTPUT INSERTED.CUST_ID
                VALUES (
                    :name, :mobile, NULL, :address,
                    1, GETDATE(),
                    NULL, NULL, NULL, NULL, NULL, NULL
                )
                """
            ),
            {"name": name, "mobile": mobile, "address": address or ""},
        ).first()
        return int(row[0])

    def get_by_idempotency(self, idempotency_key: str) -> dict[str, Any] | None:
        row = self.db.execute(
            text(
                f"""
                SELECT {_CART_COLS}
                FROM dbo.customer_app_carts
                WHERE idempotency_key = :idempotency_key
                """
            ),
            {"idempotency_key": idempotency_key},
        ).mappings().first()
        return dict(row) if row else None

    def get_by_id(self, cart_id: int) -> dict[str, Any] | None:
        row = self.db.execute(
            text(
                f"""
                SELECT {_CART_COLS}
                FROM dbo.customer_app_carts
                WHERE id = :cart_id
                """
            ),
            {"cart_id": cart_id},
        ).mappings().first()
        return dict(row) if row else None

    def get_by_ref(self, cart_ref: str) -> dict[str, Any] | None:
        row = self.db.execute(
            text(
                f"""
                SELECT {_CART_COLS}
                FROM dbo.customer_app_carts
                WHERE cart_ref = :cart_ref
                """
            ),
            {"cart_ref": cart_ref.strip().upper()},
        ).mappings().first()
        return dict(row) if row else None

    def next_cart_ref(self) -> str:
        """Allocate CART-YYYYMMDD-NNNN under row lock (safe for concurrent saves)."""
        day_key = self.db.execute(text("SELECT CONVERT(CHAR(8), GETDATE(), 112)")).scalar()
        day_key = str(day_key)
        self.db.execute(
            text(
                """
                IF NOT EXISTS (
                    SELECT 1 FROM dbo.customer_app_cart_seq WITH (UPDLOCK, HOLDLOCK)
                    WHERE day_key = :day_key
                )
                    INSERT INTO dbo.customer_app_cart_seq (day_key, last_n)
                    VALUES (:day_key, 0)
                """
            ),
            {"day_key": day_key},
        )
        row = self.db.execute(
            text(
                """
                UPDATE dbo.customer_app_cart_seq WITH (UPDLOCK, HOLDLOCK)
                SET last_n = last_n + 1
                OUTPUT INSERTED.last_n
                WHERE day_key = :day_key
                """
            ),
            {"day_key": day_key},
        ).first()
        seq = int(row[0])
        return f"CART-{day_key}-{seq:04d}"

    def insert_cart(
        self,
        *,
        cart_ref: str,
        cust_sms_id: int,
        customer_name: str,
        customer_mobile_no: str,
        mobile_key: str,
        customer_address: str | None,
        total_items: int,
        estimated_subtotal: float,
        estimated_discount: float,
        estimated_tax: float,
        estimated_total: float,
        idempotency_key: str,
    ) -> int:
        row = self.db.execute(
            text(
                """
                INSERT INTO dbo.customer_app_carts (
                    cart_ref, cust_sms_id, customer_name, customer_mobile_no,
                    mobile_key, customer_address, status, source,
                    total_items, estimated_subtotal, estimated_discount,
                    estimated_tax, estimated_total, idempotency_key,
                    created_at, updated_at
                )
                OUTPUT INSERTED.id
                VALUES (
                    :cart_ref, :cust_sms_id, :customer_name, :customer_mobile_no,
                    :mobile_key, :customer_address, N'SAVED', N'MOBILE_APP',
                    :total_items, :estimated_subtotal, :estimated_discount,
                    :estimated_tax, :estimated_total, :idempotency_key,
                    GETDATE(), GETDATE()
                )
                """
            ),
            {
                "cart_ref": cart_ref,
                "cust_sms_id": cust_sms_id,
                "customer_name": customer_name,
                "customer_mobile_no": customer_mobile_no,
                "mobile_key": mobile_key,
                "customer_address": customer_address,
                "total_items": total_items,
                "estimated_subtotal": estimated_subtotal,
                "estimated_discount": estimated_discount,
                "estimated_tax": estimated_tax,
                "estimated_total": estimated_total,
                "idempotency_key": idempotency_key,
            },
        ).first()
        return int(row[0])

    def insert_line(self, *, cart_id: int, line_no: int, line: dict[str, Any]) -> None:
        self.db.execute(
            text(
                """
                INSERT INTO dbo.customer_app_cart_lines (
                    cart_id, line_no, manual_id, item_title, barcode, uom_title,
                    qty, unit_price, discount_amount, tax_amount, line_total
                )
                VALUES (
                    :cart_id, :line_no, :manual_id, :item_title, :barcode, :uom_title,
                    :qty, :unit_price, :discount_amount, :tax_amount, :line_total
                )
                """
            ),
            {
                "cart_id": cart_id,
                "line_no": line_no,
                "manual_id": line["manual_id"],
                "item_title": line["item_title"],
                "barcode": line.get("barcode"),
                "uom_title": line.get("uom_title"),
                "qty": line["qty"],
                "unit_price": line["unit_price"],
                "discount_amount": line.get("discount_amount") or 0,
                "tax_amount": line.get("tax_amount") or 0,
                "line_total": line["line_total"],
            },
        )

    def insert_history(
        self,
        *,
        cart_id: int,
        old_status: str | None,
        new_status: str,
        action_code: str,
        actor_username: str,
        remarks: str | None = None,
    ) -> None:
        self.db.execute(
            text(
                """
                INSERT INTO dbo.customer_app_cart_status_history (
                    cart_id, old_status, new_status, action_code,
                    actor_username, remarks, created_at
                )
                VALUES (
                    :cart_id, :old_status, :new_status, :action_code,
                    :actor_username, :remarks, GETDATE()
                )
                """
            ),
            {
                "cart_id": cart_id,
                "old_status": old_status,
                "new_status": new_status,
                "action_code": action_code,
                "actor_username": actor_username,
                "remarks": remarks,
            },
        )

    def list_lines(self, cart_id: int) -> list[dict[str, Any]]:
        rows = self.db.execute(
            text(
                """
                SELECT
                    line_no,
                    manual_id,
                    RTRIM(item_title) AS item_title,
                    RTRIM(ISNULL(barcode, '')) AS barcode,
                    RTRIM(ISNULL(uom_title, '')) AS uom_title,
                    CAST(qty AS FLOAT) AS qty,
                    CAST(unit_price AS FLOAT) AS unit_price,
                    CAST(discount_amount AS FLOAT) AS discount_amount,
                    CAST(tax_amount AS FLOAT) AS tax_amount,
                    CAST(line_total AS FLOAT) AS line_total
                FROM dbo.customer_app_cart_lines
                WHERE cart_id = :cart_id
                ORDER BY line_no
                """
            ),
            {"cart_id": cart_id},
        ).mappings().all()
        return [dict(r) for r in rows]

    def list_history(self, cart_id: int) -> list[dict[str, Any]]:
        rows = self.db.execute(
            text(
                """
                SELECT
                    id,
                    old_status,
                    new_status,
                    action_code,
                    actor_username,
                    remarks,
                    created_at
                FROM dbo.customer_app_cart_status_history
                WHERE cart_id = :cart_id
                ORDER BY id
                """
            ),
            {"cart_id": cart_id},
        ).mappings().all()
        return [dict(r) for r in rows]

    def count_carts(
        self,
        *,
        mobile_key: str | None = None,
        status: str | None = None,
        source: str | None = None,
        search: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> int:
        where_sql, params = self._filter_clause(
            mobile_key=mobile_key,
            status=status,
            source=source,
            search=search,
            date_from=date_from,
            date_to=date_to,
        )
        row = self.db.execute(
            text(f"SELECT COUNT(1) AS cnt FROM dbo.customer_app_carts {where_sql}"),
            params,
        ).mappings().first()
        return int(row["cnt"] if row else 0)

    def list_carts(
        self,
        *,
        skip: int = 0,
        limit: int = 20,
        mobile_key: str | None = None,
        status: str | None = None,
        source: str | None = None,
        search: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[dict[str, Any]]:
        where_sql, params = self._filter_clause(
            mobile_key=mobile_key,
            status=status,
            source=source,
            search=search,
            date_from=date_from,
            date_to=date_to,
        )
        params["start_row"] = skip + 1
        params["end_row"] = skip + limit
        rows = self.db.execute(
            text(
                f"""
                SELECT *
                FROM (
                    SELECT
                        {_CART_COLS},
                        ROW_NUMBER() OVER (ORDER BY created_at DESC, id DESC) AS rn
                    FROM dbo.customer_app_carts
                    {where_sql}
                ) AS ranked
                WHERE rn BETWEEN :start_row AND :end_row
                ORDER BY rn
                """
            ),
            params,
        ).mappings().all()
        return [dict(r) for r in rows]

    def update_status(self, cart_id: int, status: str) -> None:
        self.db.execute(
            text(
                """
                UPDATE dbo.customer_app_carts
                SET status = :status, updated_at = GETDATE()
                WHERE id = :cart_id
                """
            ),
            {"cart_id": cart_id, "status": status},
        )

    def _filter_clause(
        self,
        *,
        mobile_key: str | None,
        status: str | None,
        source: str | None,
        search: str | None,
        date_from: str | None,
        date_to: str | None,
    ) -> tuple[str, dict[str, Any]]:
        clauses: list[str] = []
        params: dict[str, Any] = {}
        if mobile_key:
            clauses.append("mobile_key = :mobile_key")
            params["mobile_key"] = mobile_key
        if status:
            clauses.append("status = :status")
            params["status"] = status
        if source:
            clauses.append("source = :source")
            params["source"] = source
        if date_from:
            clauses.append("created_at >= :date_from")
            params["date_from"] = date_from
        if date_to:
            clauses.append("created_at < DATEADD(day, 1, CAST(:date_to AS DATETIME))")
            params["date_to"] = date_to
        if search and search.strip():
            clauses.append(
                """(
                    cart_ref LIKE :q
                    OR customer_name LIKE :q
                    OR customer_mobile_no LIKE :q
                    OR mobile_key LIKE :q_digits
                )"""
            )
            q = f"%{search.strip()}%"
            params["q"] = q
            digits = "".join(ch for ch in search if ch.isdigit())
            params["q_digits"] = f"%{digits[-10:] if len(digits) >= 10 else digits}%"
        where_sql = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        return where_sql, params
