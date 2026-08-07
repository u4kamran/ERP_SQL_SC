"""SQL Server 2008-compatible data access for delivery management."""

from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


_ORDER_COLUMNS = """
    o.id,
    o.source_serial_no,
    o.invoice_id,
    o.invoice_date,
    o.customer_id,
    o.cust_sms_id,
    RTRIM(ISNULL(o.customer_title, '')) AS customer_title,
    RTRIM(ISNULL(o.customer_mobile_no, '')) AS customer_mobile_no,
    RTRIM(ISNULL(o.customer_alternate_mobile, '')) AS customer_alternate_mobile,
    RTRIM(ISNULL(o.address, '')) AS address,
    o.city_id,
    o.sale_amount,
    o.balance_amount,
    o.total_amount,
    o.payment_type,
    o.rider_id,
    RTRIM(r.name) AS rider_name,
    o.status,
    o.created_at,
    o.updated_at,
    o.delivered_at,
    o.delivered_latitude,
    o.delivered_longitude,
    o.delivered_accuracy,
    cl.latitude AS customer_latitude,
    cl.longitude AS customer_longitude,
    cl.updated_at AS customer_location_updated_at,
    rl.latitude AS rider_latitude,
    rl.longitude AS rider_longitude,
    rl.recorded_at AS rider_location_updated_at,
    o.remarks
"""


class DeliveryRepository:
    def __init__(self, db: Session):
        self.db = db

    def summary(self) -> dict[str, Any]:
        totals = self.db.execute(
            text(
                """
                SELECT
                    COUNT(1) AS total_orders,
                    SUM(CASE WHEN rider_id IS NULL THEN 1 ELSE 0 END) AS unassigned_orders,
                    SUM(CASE
                        WHEN status = 'Delivered'
                         AND CAST(delivered_at AS DATE) = CAST(GETDATE() AS DATE)
                        THEN 1 ELSE 0
                    END) AS delivered_today
                FROM dbo.delivery_orders
                WHERE LEN(LTRIM(RTRIM(customer_mobile_no))) > 0
                  AND LTRIM(RTRIM(customer_mobile_no)) <> '.'
                """
            )
        ).mappings().first()
        rider_row = self.db.execute(
            text("SELECT COUNT(1) AS cnt FROM dbo.delivery_riders WHERE is_active = 1")
        ).mappings().first()
        statuses = self.db.execute(
            text(
                """
                SELECT status, COUNT(1) AS cnt
                FROM dbo.delivery_orders
                WHERE LEN(LTRIM(RTRIM(customer_mobile_no))) > 0
                  AND LTRIM(RTRIM(customer_mobile_no)) <> '.'
                GROUP BY status
                """
            )
        ).mappings().all()
        return {
            "total_orders": int((totals or {}).get("total_orders") or 0),
            "unassigned_orders": int((totals or {}).get("unassigned_orders") or 0),
            "delivered_today": int((totals or {}).get("delivered_today") or 0),
            "active_riders": int((rider_row or {}).get("cnt") or 0),
            "status_counts": {str(row["status"]): int(row["cnt"]) for row in statuses},
        }

    def count_orders(
        self,
        *,
        search: str = "",
        order_status: str | None = None,
        rider_id: int | None = None,
    ) -> int:
        where_sql, params = self._order_filters(
            search=search, order_status=order_status, rider_id=rider_id
        )
        row = self.db.execute(
            text(f"SELECT COUNT(1) AS cnt FROM dbo.delivery_orders o {where_sql}"),
            params,
        ).mappings().first()
        return int(row["cnt"] if row else 0)

    def list_orders(
        self,
        *,
        skip: int,
        limit: int,
        search: str = "",
        order_status: str | None = None,
        rider_id: int | None = None,
    ) -> list[dict[str, Any]]:
        where_sql, params = self._order_filters(
            search=search, order_status=order_status, rider_id=rider_id
        )
        params.update({"start_row": skip + 1, "end_row": skip + limit})
        rows = self.db.execute(
            text(
                f"""
                SELECT *
                FROM (
                    SELECT
                        {_ORDER_COLUMNS},
                        ROW_NUMBER() OVER (
                            ORDER BY o.created_at DESC, o.id DESC
                        ) AS rn
                    FROM dbo.delivery_orders o
                    LEFT JOIN dbo.delivery_riders r ON r.id = o.rider_id
                    LEFT JOIN dbo.delivery_customer_locations cl
                        ON cl.mobile_key = RIGHT(
                            REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
                                LTRIM(RTRIM(o.customer_mobile_no)),
                                ' ', ''), '-', ''), '(', ''), ')', ''), '+', ''),
                            10
                        )
                    LEFT JOIN dbo.delivery_rider_locations rl ON rl.rider_id = o.rider_id
                    {where_sql}
                ) AS ranked
                WHERE rn BETWEEN :start_row AND :end_row
                ORDER BY rn
                """
            ),
            params,
        ).mappings().all()
        return [dict(row) for row in rows]

    def get_order(self, order_id: int) -> dict[str, Any] | None:
        row = self.db.execute(
            text(
                f"""
                SELECT {_ORDER_COLUMNS}
                FROM dbo.delivery_orders o
                LEFT JOIN dbo.delivery_riders r ON r.id = o.rider_id
                LEFT JOIN dbo.delivery_customer_locations cl
                    ON cl.mobile_key = RIGHT(
                        REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
                            LTRIM(RTRIM(o.customer_mobile_no)),
                            ' ', ''), '-', ''), '(', ''), ')', ''), '+', ''),
                        10
                    )
                LEFT JOIN dbo.delivery_rider_locations rl ON rl.rider_id = o.rider_id
                WHERE o.id = :order_id
                  AND LEN(LTRIM(RTRIM(o.customer_mobile_no))) > 0
                  AND LTRIM(RTRIM(o.customer_mobile_no)) <> '.'
                """
            ),
            {"order_id": order_id},
        ).mappings().first()
        return dict(row) if row else None

    def search_registration_invoices(
        self,
        *,
        gp_time: str,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        rows = self.db.execute(
            text(
                """
                SELECT TOP (:limit)
                    m.SERIAL_NO AS source_serial_no,
                    m.INV_ID AS invoice_id,
                    ISNULL(m.DOC_DATE_T, m.DOC_DATE) AS invoice_date,
                    LTRIM(RTRIM(ISNULL(CONVERT(VARCHAR(200), m.GP_TIME, 121), '')))
                        AS gp_time,
                    RTRIM(ISNULL(m.CUSTOMER_TITLE, '')) AS customer_title,
                    RTRIM(ISNULL(m.CUSTOMER_MOBILENO, '')) AS current_mobile,
                    RTRIM(ISNULL(m.ADDRESS, '')) AS address,
                    ISNULL(totals.total_amount, m.SALE_AMT) AS total_amount,
                    m.PAYMENT_TYPE AS payment_type
                FROM dbo.FIN_INV_M m
                OUTER APPLY (
                    SELECT SUM(d.TOTAL_AMT) AS total_amount
                    FROM dbo.FIN_INV_D d
                    WHERE d.SERIAL_NO = m.SERIAL_NO
                ) totals
                WHERE LTRIM(RTRIM(ISNULL(
                    CONVERT(VARCHAR(200), m.GP_TIME, 121), ''
                ))) = :gp_time
                  AND m.SERIAL_NO IS NOT NULL
                ORDER BY ISNULL(m.DOC_DATE_T, m.DOC_DATE) DESC, m.SERIAL_NO DESC
                """
            ),
            {"gp_time": gp_time.strip(), "limit": limit},
        ).mappings().all()
        return [dict(row) for row in rows]

    def get_registration_invoice(self, source_serial_no: int) -> dict[str, Any] | None:
        row = self.db.execute(
            text(
                """
                SELECT
                    m.SERIAL_NO AS source_serial_no,
                    m.INV_ID AS invoice_id,
                    ISNULL(m.DOC_DATE_T, m.DOC_DATE) AS invoice_date,
                    LTRIM(RTRIM(ISNULL(CONVERT(VARCHAR(200), m.GP_TIME, 121), '')))
                        AS gp_time,
                    RTRIM(ISNULL(m.CUSTOMER_TITLE, '')) AS customer_title,
                    RTRIM(ISNULL(m.CUSTOMER_MOBILENO, '')) AS current_mobile,
                    RTRIM(ISNULL(m.ADDRESS, '')) AS address,
                    ISNULL(totals.total_amount, m.SALE_AMT) AS total_amount,
                    m.PAYMENT_TYPE AS payment_type
                FROM dbo.FIN_INV_M m
                OUTER APPLY (
                    SELECT SUM(d.TOTAL_AMT) AS total_amount
                    FROM dbo.FIN_INV_D d
                    WHERE d.SERIAL_NO = m.SERIAL_NO
                ) totals
                WHERE m.SERIAL_NO = :source_serial_no
                """
            ),
            {"source_serial_no": source_serial_no},
        ).mappings().first()
        return dict(row) if row else None

    def find_delivery_customer(self, mobile_key: str) -> dict[str, Any] | None:
        row = self.db.execute(
            text(
                """
                SELECT TOP 1
                    c.CUST_ID AS cust_sms_id,
                    RTRIM(ISNULL(c.CUST_NAME, '')) AS name,
                    RTRIM(ISNULL(c.MOBILE_NO, '')) AS mobile,
                    RTRIM(ISNULL(c.MOBILE_NO_TMP, '')) AS alternate_mobile,
                    RTRIM(ISNULL(c.CUST_ADDRESS, '')) AS address
                FROM dbo.CUST_SMS c
                WHERE LEN(LTRIM(RTRIM(c.MOBILE_NO))) >= 10
                  AND RIGHT(
                      REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
                          LTRIM(RTRIM(c.MOBILE_NO)),
                          ' ', ''), '-', ''), '(', ''), ')', ''), '+', ''),
                      10
                  ) = :mobile_key
                ORDER BY c.CUST_ID DESC
                """
            ),
            {"mobile_key": mobile_key},
        ).mappings().first()
        return dict(row) if row else None

    def create_delivery_customer(
        self,
        *,
        name: str,
        mobile: str,
        address: str,
    ) -> int:
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
            {"name": name, "mobile": mobile, "address": address},
        ).first()
        return int(row[0])

    def update_customer_address(self, cust_sms_id: int, address: str) -> bool:
        result = self.db.execute(
            text(
                """
                UPDATE dbo.CUST_SMS
                SET CUST_ADDRESS = :address
                WHERE CUST_ID = :cust_sms_id
                """
            ),
            {"cust_sms_id": int(cust_sms_id), "address": (address or "").strip()[:2000]},
        )
        return result.rowcount > 0

    def get_customer_location(self, mobile_key: str) -> dict[str, Any] | None:
        if not mobile_key:
            return None
        row = self.db.execute(
            text(
                """
                SELECT TOP 1
                    mobile_key,
                    RTRIM(ISNULL(customer_mobile_no, '')) AS customer_mobile_no,
                    cust_sms_id,
                    latitude,
                    longitude,
                    accuracy,
                    updated_at
                FROM dbo.delivery_customer_locations
                WHERE mobile_key = :mobile_key
                """
            ),
            {"mobile_key": mobile_key},
        ).mappings().first()
        return dict(row) if row else None

    def update_invoice_delivery_mobile(
        self,
        *,
        source_serial_no: int,
        mobile: str,
    ) -> bool:
        result = self.db.execute(
            text(
                """
                UPDATE dbo.FIN_INV_M
                SET CUSTOMER_MOBILENO = :mobile
                WHERE SERIAL_NO = :source_serial_no
                """
            ),
            {"source_serial_no": source_serial_no, "mobile": mobile},
        )
        return result.rowcount > 0

    def get_order_id_by_source(self, source_serial_no: int) -> int | None:
        value = self.db.execute(
            text(
                """
                SELECT id
                FROM dbo.delivery_orders
                WHERE source_serial_no = :source_serial_no
                """
            ),
            {"source_serial_no": source_serial_no},
        ).scalar()
        return int(value) if value is not None else None

    def source_invoice_by_serial(self, source_serial_no: int) -> dict[str, Any] | None:
        row = self.db.execute(
            text(
                """
                SELECT
                    m.SERIAL_NO AS source_serial_no,
                    m.INV_ID AS invoice_id,
                    ISNULL(m.DOC_DATE_T, m.DOC_DATE) AS invoice_date,
                    m.CUST_ID AS customer_id,
                    contact.CUST_ID AS cust_sms_id,
                    COALESCE(
                        NULLIF(RTRIM(contact.CUST_NAME), ''),
                        RTRIM(ISNULL(m.CUSTOMER_TITLE, ''))
                    ) AS customer_title,
                    RTRIM(ISNULL(m.CUSTOMER_MOBILENO, '')) AS customer_mobile_no,
                    RTRIM(ISNULL(contact.MOBILE_NO_TMP, '')) AS customer_alternate_mobile,
                    COALESCE(
                        NULLIF(RTRIM(contact.CUST_ADDRESS), ''),
                        RTRIM(ISNULL(m.ADDRESS, ''))
                    ) AS address,
                    m.CITY_ID AS city_id,
                    m.SALE_AMT AS sale_amount,
                    m.BAL_AMT AS balance_amount,
                    ISNULL(totals.total_amount, m.SALE_AMT) AS total_amount,
                    m.PAYMENT_TYPE AS payment_type
                FROM dbo.FIN_INV_M m
                OUTER APPLY (
                    SELECT SUM(d.TOTAL_AMT) AS total_amount
                    FROM dbo.FIN_INV_D d
                    WHERE d.SERIAL_NO = m.SERIAL_NO
                ) totals
                OUTER APPLY (
                    SELECT TOP 1
                        c.CUST_ID, c.CUST_NAME, c.MOBILE_NO_TMP, c.CUST_ADDRESS
                    FROM dbo.CUST_SMS c
                    WHERE LEN(LTRIM(RTRIM(c.MOBILE_NO))) >= 10
                      AND RIGHT(
                          REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
                              LTRIM(RTRIM(c.MOBILE_NO)),
                              ' ', ''), '-', ''), '(', ''), ')', ''), '+', ''),
                          10
                      ) = RIGHT(
                          REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
                              LTRIM(RTRIM(m.CUSTOMER_MOBILENO)),
                              ' ', ''), '-', ''), '(', ''), ')', ''), '+', ''),
                          10
                      )
                    ORDER BY c.CUST_ID DESC
                ) contact
                WHERE m.SERIAL_NO = :source_serial_no
                  AND LEN(LTRIM(RTRIM(ISNULL(m.CUSTOMER_MOBILENO, '')))) > 0
                  AND LTRIM(RTRIM(m.CUSTOMER_MOBILENO)) <> '.'
                """
            ),
            {"source_serial_no": source_serial_no},
        ).mappings().first()
        return dict(row) if row else None

    def source_invoices(self, *, lookback_hours: int, limit: int) -> list[dict[str, Any]]:
        rows = self.db.execute(
            text(
                """
                SELECT TOP (:limit)
                    m.SERIAL_NO AS source_serial_no,
                    m.INV_ID AS invoice_id,
                    ISNULL(m.DOC_DATE_T, m.DOC_DATE) AS invoice_date,
                    m.CUST_ID AS customer_id,
                    contact.CUST_ID AS cust_sms_id,
                    COALESCE(
                        NULLIF(RTRIM(contact.CUST_NAME), ''),
                        RTRIM(ISNULL(m.CUSTOMER_TITLE, ''))
                    ) AS customer_title,
                    RTRIM(ISNULL(m.CUSTOMER_MOBILENO, '')) AS customer_mobile_no,
                    RTRIM(ISNULL(contact.MOBILE_NO_TMP, '')) AS customer_alternate_mobile,
                    COALESCE(
                        NULLIF(RTRIM(contact.CUST_ADDRESS), ''),
                        RTRIM(ISNULL(m.ADDRESS, ''))
                    ) AS address,
                    m.CITY_ID AS city_id,
                    m.SALE_AMT AS sale_amount,
                    m.BAL_AMT AS balance_amount,
                    ISNULL(totals.total_amount, m.SALE_AMT) AS total_amount,
                    m.PAYMENT_TYPE AS payment_type
                FROM dbo.FIN_INV_M m
                OUTER APPLY (
                    SELECT SUM(d.TOTAL_AMT) AS total_amount
                    FROM dbo.FIN_INV_D d
                    WHERE d.SERIAL_NO = m.SERIAL_NO
                ) totals
                OUTER APPLY (
                    SELECT TOP 1
                        c.CUST_ID,
                        c.CUST_NAME,
                        c.MOBILE_NO_TMP,
                        c.CUST_ADDRESS
                    FROM dbo.CUST_SMS c
                    WHERE LEN(LTRIM(RTRIM(c.MOBILE_NO))) >= 10
                      AND RIGHT(
                          REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
                              LTRIM(RTRIM(c.MOBILE_NO)),
                              ' ', ''), '-', ''), '(', ''), ')', ''), '+', ''),
                          10
                      ) = RIGHT(
                          REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
                              LTRIM(RTRIM(m.CUSTOMER_MOBILENO)),
                              ' ', ''), '-', ''), '(', ''), ')', ''), '+', ''),
                          10
                      )
                    ORDER BY c.CUST_ID DESC
                ) contact
                WHERE LEN(LTRIM(RTRIM(ISNULL(m.CUSTOMER_MOBILENO, '')))) > 0
                  AND LTRIM(RTRIM(m.CUSTOMER_MOBILENO)) <> '.'
                  AND m.SERIAL_NO IS NOT NULL
                  AND ISNULL(m.DOC_DATE_T, m.DOC_DATE) >= DATEADD(
                      HOUR, :lookback_offset, GETDATE()
                  )
                  AND NOT EXISTS (
                      SELECT 1
                      FROM dbo.delivery_orders existing
                      WHERE existing.source_serial_no = m.SERIAL_NO
                  )
                ORDER BY ISNULL(m.DOC_DATE_T, m.DOC_DATE) DESC, m.SERIAL_NO DESC
                """
            ),
            {"limit": limit, "lookback_offset": -lookback_hours},
        ).mappings().all()
        return [dict(row) for row in rows]

    def refresh_source_orders(self) -> int:
        result = self.db.execute(
            text(
                """
                UPDATE o
                SET
                    invoice_id = m.INV_ID,
                    invoice_date = ISNULL(m.DOC_DATE_T, m.DOC_DATE),
                    customer_id = m.CUST_ID,
                    cust_sms_id = contact.CUST_ID,
                    customer_title = COALESCE(
                        NULLIF(RTRIM(contact.CUST_NAME), ''),
                        RTRIM(ISNULL(m.CUSTOMER_TITLE, ''))
                    ),
                    customer_mobile_no = RTRIM(m.CUSTOMER_MOBILENO),
                    customer_alternate_mobile = NULLIF(
                        RTRIM(contact.MOBILE_NO_TMP), ''
                    ),
                    address = COALESCE(
                        NULLIF(RTRIM(contact.CUST_ADDRESS), ''),
                        RTRIM(ISNULL(m.ADDRESS, ''))
                    ),
                    city_id = m.CITY_ID,
                    sale_amount = m.SALE_AMT,
                    balance_amount = m.BAL_AMT,
                    total_amount = ISNULL(totals.total_amount, m.SALE_AMT),
                    payment_type = m.PAYMENT_TYPE,
                    updated_at = GETDATE()
                FROM dbo.delivery_orders o
                INNER JOIN dbo.FIN_INV_M m
                    ON m.SERIAL_NO = o.source_serial_no
                OUTER APPLY (
                    SELECT SUM(d.TOTAL_AMT) AS total_amount
                    FROM dbo.FIN_INV_D d
                    WHERE d.SERIAL_NO = m.SERIAL_NO
                ) totals
                OUTER APPLY (
                    SELECT TOP 1
                        c.CUST_ID,
                        c.CUST_NAME,
                        c.MOBILE_NO_TMP,
                        c.CUST_ADDRESS
                    FROM dbo.CUST_SMS c
                    WHERE LEN(LTRIM(RTRIM(c.MOBILE_NO))) >= 10
                      AND RIGHT(
                          REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
                              LTRIM(RTRIM(c.MOBILE_NO)),
                              ' ', ''), '-', ''), '(', ''), ')', ''), '+', ''),
                          10
                      ) = RIGHT(
                          REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
                              LTRIM(RTRIM(m.CUSTOMER_MOBILENO)),
                              ' ', ''), '-', ''), '(', ''), ')', ''), '+', ''),
                          10
                      )
                    ORDER BY c.CUST_ID DESC
                ) contact
                WHERE o.status IN ('Pending', 'Assigned')
                  AND LEN(LTRIM(RTRIM(ISNULL(m.CUSTOMER_MOBILENO, '')))) > 0
                  AND LTRIM(RTRIM(m.CUSTOMER_MOBILENO)) <> '.'
                  AND (
                      ISNULL(o.invoice_id, -1) <> ISNULL(m.INV_ID, -1)
                      OR ISNULL(o.invoice_date, CONVERT(DATETIME, '19000101', 112))
                         <> ISNULL(ISNULL(m.DOC_DATE_T, m.DOC_DATE), CONVERT(DATETIME, '19000101', 112))
                      OR ISNULL(o.customer_id, -1) <> ISNULL(m.CUST_ID, -1)
                      OR ISNULL(o.cust_sms_id, -1) <> ISNULL(contact.CUST_ID, -1)
                      OR ISNULL(o.customer_title, '') <> COALESCE(
                          NULLIF(RTRIM(contact.CUST_NAME), ''),
                          RTRIM(ISNULL(m.CUSTOMER_TITLE, ''))
                      )
                      OR ISNULL(o.customer_mobile_no, '')
                         <> RTRIM(ISNULL(m.CUSTOMER_MOBILENO, ''))
                      OR ISNULL(o.customer_alternate_mobile, '')
                         <> ISNULL(RTRIM(contact.MOBILE_NO_TMP), '')
                      OR ISNULL(o.address, '') <> COALESCE(
                          NULLIF(RTRIM(contact.CUST_ADDRESS), ''),
                          RTRIM(ISNULL(m.ADDRESS, ''))
                      )
                      OR ISNULL(o.city_id, -1) <> ISNULL(m.CITY_ID, -1)
                      OR ISNULL(o.sale_amount, 0) <> ISNULL(m.SALE_AMT, 0)
                      OR ISNULL(o.balance_amount, 0) <> ISNULL(m.BAL_AMT, 0)
                      OR ISNULL(o.total_amount, 0)
                         <> ISNULL(ISNULL(totals.total_amount, m.SALE_AMT), 0)
                      OR ISNULL(o.payment_type, -1) <> ISNULL(m.PAYMENT_TYPE, -1)
                  )
                """
            )
        )
        return max(result.rowcount, 0)

    def enrich_customer_contacts(self) -> int:
        result = self.db.execute(
            text(
                """
                UPDATE o
                SET
                    cust_sms_id = contact.CUST_ID,
                    customer_title = COALESCE(
                        NULLIF(RTRIM(contact.CUST_NAME), ''),
                        o.customer_title
                    ),
                    customer_alternate_mobile = NULLIF(
                        RTRIM(contact.MOBILE_NO_TMP), ''
                    ),
                    address = COALESCE(
                        NULLIF(RTRIM(contact.CUST_ADDRESS), ''),
                        o.address
                    )
                FROM dbo.delivery_orders o
                CROSS APPLY (
                    SELECT TOP 1
                        c.CUST_ID,
                        c.CUST_NAME,
                        c.MOBILE_NO_TMP,
                        c.CUST_ADDRESS
                    FROM dbo.CUST_SMS c
                    WHERE LEN(LTRIM(RTRIM(c.MOBILE_NO))) >= 10
                      AND RIGHT(
                          REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
                              LTRIM(RTRIM(c.MOBILE_NO)),
                              ' ', ''), '-', ''), '(', ''), ')', ''), '+', ''),
                          10
                      ) = RIGHT(
                          REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
                              LTRIM(RTRIM(o.customer_mobile_no)),
                              ' ', ''), '-', ''), '(', ''), ')', ''), '+', ''),
                          10
                      )
                    ORDER BY c.CUST_ID DESC
                ) contact
                WHERE o.cust_sms_id IS NULL
                  AND LEN(LTRIM(RTRIM(o.customer_mobile_no))) > 0
                  AND LTRIM(RTRIM(o.customer_mobile_no)) <> '.'
                """
            )
        )
        return max(result.rowcount, 0)

    def insert_source_order(self, source: dict[str, Any]) -> int | None:
        row = self.db.execute(
            text(
                """
                INSERT INTO dbo.delivery_orders (
                    source_serial_no, invoice_id, invoice_date, customer_id, cust_sms_id,
                    customer_title, customer_mobile_no, customer_alternate_mobile,
                    address, city_id,
                    sale_amount, balance_amount, total_amount, payment_type,
                    status, created_at, updated_at
                )
                OUTPUT INSERTED.id
                SELECT
                    :source_serial_no, :invoice_id, :invoice_date, :customer_id, :cust_sms_id,
                    :customer_title, :customer_mobile_no, :customer_alternate_mobile,
                    :address, :city_id,
                    :sale_amount, :balance_amount, :total_amount, :payment_type,
                    'Pending', GETDATE(), GETDATE()
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM dbo.delivery_orders WITH (UPDLOCK, HOLDLOCK)
                    WHERE source_serial_no = :source_serial_no
                )
                """
            ),
            source,
        ).first()
        return int(row[0]) if row else None

    def list_riders(self) -> list[dict[str, Any]]:
        rows = self.db.execute(
            text(
                """
                SELECT r.id, RTRIM(r.name) AS name, RTRIM(r.phone) AS phone,
                       r.is_active, r.created_at, r.updated_at,
                       location.latitude, location.longitude,
                       location.accuracy AS location_accuracy,
                       location.recorded_at AS location_updated_at
                FROM dbo.delivery_riders r
                LEFT JOIN dbo.delivery_rider_locations location
                    ON location.rider_id = r.id
                ORDER BY r.is_active DESC, r.name, r.id
                """
            )
        ).mappings().all()
        return [dict(row) for row in rows]

    def get_rider(self, rider_id: int) -> dict[str, Any] | None:
        row = self.db.execute(
            text(
                """
                SELECT r.id, RTRIM(r.name) AS name, RTRIM(r.phone) AS phone,
                       r.is_active, r.created_at, r.updated_at,
                       location.latitude, location.longitude,
                       location.accuracy AS location_accuracy,
                       location.recorded_at AS location_updated_at
                FROM dbo.delivery_riders r
                LEFT JOIN dbo.delivery_rider_locations location
                    ON location.rider_id = r.id
                WHERE r.id = :rider_id
                """
            ),
            {"rider_id": rider_id},
        ).mappings().first()
        return dict(row) if row else None

    def create_rider(self, *, name: str, phone: str | None) -> int:
        row = self.db.execute(
            text(
                """
                INSERT INTO dbo.delivery_riders (
                    name, phone, is_active, created_at, updated_at
                )
                OUTPUT INSERTED.id
                VALUES (:name, :phone, 1, GETDATE(), GETDATE())
                """
            ),
            {"name": name, "phone": phone},
        ).first()
        return int(row[0])

    def update_rider(
        self,
        *,
        rider_id: int,
        name: str,
        phone: str | None,
        is_active: bool,
    ) -> bool:
        result = self.db.execute(
            text(
                """
                UPDATE dbo.delivery_riders
                SET name = :name,
                    phone = :phone,
                    is_active = :is_active,
                    updated_at = GETDATE()
                WHERE id = :rider_id
                """
            ),
            {
                "rider_id": rider_id,
                "name": name,
                "phone": phone,
                "is_active": 1 if is_active else 0,
            },
        )
        return result.rowcount > 0

    def set_rider_active(self, *, rider_id: int, is_active: bool) -> bool:
        result = self.db.execute(
            text(
                """
                UPDATE dbo.delivery_riders
                SET is_active = :is_active, updated_at = GETDATE()
                WHERE id = :rider_id
                """
            ),
            {"rider_id": rider_id, "is_active": 1 if is_active else 0},
        )
        return result.rowcount > 0

    def assign_order(self, *, order_id: int, rider_id: int) -> bool:
        result = self.db.execute(
            text(
                """
                UPDATE dbo.delivery_orders
                SET rider_id = :rider_id, status = 'Assigned', updated_at = GETDATE()
                WHERE id = :order_id
                """
            ),
            {"order_id": order_id, "rider_id": rider_id},
        )
        return result.rowcount > 0

    def bulk_assign_orders(
        self,
        *,
        rider_id: int,
    ) -> list[dict[str, Any]]:
        rows = self.db.execute(
            text(
                """
                UPDATE dbo.delivery_orders
                SET rider_id = :rider_id,
                    status = N'Assigned',
                    updated_at = GETDATE()
                OUTPUT INSERTED.id AS order_id, DELETED.status AS old_status
                WHERE status IN (N'Pending', N'Assigned', N'Failed Delivery')
                  AND (
                      rider_id IS NULL
                      OR rider_id <> :rider_id
                      OR status <> N'Assigned'
                  )
                """
            ),
            {"rider_id": rider_id},
        ).mappings().all()
        return [dict(row) for row in rows]

    def bulk_deliver_assigned_orders(
        self,
        *,
        rider_id: int | None,
    ) -> list[dict[str, Any]]:
        rows = self.db.execute(
            text(
                """
                UPDATE dbo.delivery_orders
                SET status = N'Delivered',
                    delivered_at = GETDATE(),
                    updated_at = GETDATE(),
                    remarks = LEFT(
                        CASE
                            WHEN NULLIF(LTRIM(RTRIM(ISNULL(remarks, N''))), N'')
                                IS NULL
                                THEN N'Admin bulk delivered without GPS.'
                            ELSE remarks
                                + CHAR(13) + CHAR(10)
                                + N'Admin bulk delivered without GPS.'
                        END,
                        1000
                    )
                OUTPUT INSERTED.id AS order_id, DELETED.status AS old_status
                WHERE status = N'Assigned'
                  AND (:rider_id IS NULL OR rider_id = :rider_id)
                """
            ),
            {"rider_id": rider_id},
        ).mappings().all()
        return [dict(row) for row in rows]

    def update_order_status(
        self,
        *,
        order_id: int,
        new_status: str,
        latitude,
        longitude,
        accuracy,
        remarks: str | None,
    ) -> bool:
        result = self.db.execute(
            text(
                """
                UPDATE dbo.delivery_orders
                SET
                    status = :new_status,
                    updated_at = GETDATE(),
                    delivered_at = CASE
                        WHEN :new_status = 'Delivered' THEN GETDATE()
                        ELSE delivered_at
                    END,
                    delivered_latitude = CASE
                        WHEN :new_status = 'Delivered' THEN :latitude
                        ELSE delivered_latitude
                    END,
                    delivered_longitude = CASE
                        WHEN :new_status = 'Delivered' THEN :longitude
                        ELSE delivered_longitude
                    END,
                    delivered_accuracy = CASE
                        WHEN :new_status = 'Delivered' THEN :accuracy
                        ELSE delivered_accuracy
                    END,
                    remarks = CASE
                        WHEN :remarks IS NOT NULL THEN :remarks
                        ELSE remarks
                    END
                WHERE id = :order_id
                """
            ),
            {
                "order_id": order_id,
                "new_status": new_status,
                "latitude": latitude,
                "longitude": longitude,
                "accuracy": accuracy,
                "remarks": remarks,
            },
        )
        return result.rowcount > 0

    def upsert_customer_location(
        self,
        *,
        mobile_key: str,
        customer_mobile_no: str,
        cust_sms_id: int | None,
        latitude,
        longitude,
        accuracy,
        actor_username: str,
    ) -> None:
        params = {
            "mobile_key": mobile_key,
            "customer_mobile_no": customer_mobile_no,
            "cust_sms_id": cust_sms_id,
            "latitude": latitude,
            "longitude": longitude,
            "accuracy": accuracy,
            "actor_username": actor_username[:100],
        }
        result = self.db.execute(
            text(
                """
                UPDATE dbo.delivery_customer_locations
                SET customer_mobile_no = :customer_mobile_no,
                    cust_sms_id = :cust_sms_id,
                    latitude = :latitude,
                    longitude = :longitude,
                    accuracy = :accuracy,
                    updated_at = GETDATE(),
                    updated_by = :actor_username
                WHERE mobile_key = :mobile_key
                """
            ),
            params,
        )
        if result.rowcount == 0:
            self.db.execute(
                text(
                    """
                    INSERT INTO dbo.delivery_customer_locations (
                        mobile_key, customer_mobile_no, cust_sms_id,
                        latitude, longitude, accuracy, updated_at, updated_by
                    )
                    VALUES (
                        :mobile_key, :customer_mobile_no, :cust_sms_id,
                        :latitude, :longitude, :accuracy, GETDATE(), :actor_username
                    )
                    """
                ),
                params,
            )

    def upsert_rider_location(
        self,
        *,
        rider_id: int,
        order_id: int,
        latitude,
        longitude,
        accuracy,
        actor_username: str,
    ) -> None:
        params = {
            "rider_id": rider_id,
            "order_id": order_id,
            "latitude": latitude,
            "longitude": longitude,
            "accuracy": accuracy,
            "actor_username": actor_username[:100],
        }
        result = self.db.execute(
            text(
                """
                UPDATE dbo.delivery_rider_locations
                SET latitude = :latitude,
                    longitude = :longitude,
                    accuracy = :accuracy,
                    source_order_id = :order_id,
                    recorded_at = GETDATE(),
                    updated_by = :actor_username
                WHERE rider_id = :rider_id
                """
            ),
            params,
        )
        if result.rowcount == 0:
            self.db.execute(
                text(
                    """
                    INSERT INTO dbo.delivery_rider_locations (
                        rider_id, latitude, longitude, accuracy,
                        source_order_id, recorded_at, updated_by
                    )
                    VALUES (
                        :rider_id, :latitude, :longitude, :accuracy,
                        :order_id, GETDATE(), :actor_username
                    )
                    """
                ),
                params,
            )

    def add_history(
        self,
        *,
        order_id: int,
        old_status: str | None,
        new_status: str,
        actor_username: str,
        remarks: str | None = None,
    ) -> None:
        self.db.execute(
            text(
                """
                INSERT INTO dbo.delivery_status_history (
                    order_id, old_status, new_status, actor_username,
                    remarks, created_at
                )
                VALUES (
                    :order_id, :old_status, :new_status, :actor_username,
                    :remarks, GETDATE()
                )
                """
            ),
            {
                "order_id": order_id,
                "old_status": old_status,
                "new_status": new_status,
                "actor_username": actor_username[:100],
                "remarks": remarks,
            },
        )

    @staticmethod
    def _order_filters(
        *,
        search: str,
        order_status: str | None,
        rider_id: int | None,
    ) -> tuple[str, dict[str, Any]]:
        clauses: list[str] = [
            "LEN(LTRIM(RTRIM(o.customer_mobile_no))) > 0",
            "LTRIM(RTRIM(o.customer_mobile_no)) <> '.'",
        ]
        params: dict[str, Any] = {}
        search = (search or "").strip()
        if search:
            clauses.append(
                """
                (
                    o.customer_title LIKE :pattern
                    OR o.customer_mobile_no LIKE :pattern
                    OR o.address LIKE :pattern
                    OR CAST(o.source_serial_no AS VARCHAR(20)) LIKE :pattern
                    OR CAST(o.invoice_id AS VARCHAR(20)) LIKE :pattern
                )
                """
            )
            params["pattern"] = f"%{search}%"
        if order_status:
            clauses.append("o.status = :order_status")
            params["order_status"] = order_status
        if rider_id is not None:
            clauses.append("o.rider_id = :rider_id")
            params["rider_id"] = rider_id
        return (("WHERE " + " AND ".join(clauses)) if clauses else "", params)
