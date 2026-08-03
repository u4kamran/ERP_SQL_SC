"""Helpers for legacy sales dashboard view column names."""

from __future__ import annotations

from functools import lru_cache

from sqlalchemy import text

from app.database.business_session import business_engine

_DATE_COLUMNS = ("DOC_DATE_T", "DOC_DATE")


@lru_cache(maxsize=1)
def sales_doc_date_column() -> str:
    """
    Date/time column on V_FIN_SALE_DISC_NEW2 for filtering and business-day grouping.

    ERP (nsds2626) uses DOC_DATE_T; ARP (NAHSL2627) uses DOC_DATE.
    """
    with business_engine.connect() as conn:
        name = conn.execute(
            text(
                """
                SELECT TOP 1 c.name
                FROM sys.columns c
                INNER JOIN sys.views v ON c.object_id = v.object_id
                WHERE v.name = 'V_FIN_SALE_DISC_NEW2'
                  AND c.name IN ('DOC_DATE_T', 'DOC_DATE')
                ORDER BY CASE c.name WHEN 'DOC_DATE_T' THEN 0 ELSE 1 END
                """
            )
        ).scalar()
    return name or _DATE_COLUMNS[0]
