"""Inspect dbo.CUST_SMS table structure and sample rows."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from app.database.business_session import business_engine

with business_engine.connect() as conn:
    cols = conn.execute(
        text(
            """
            SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'CUST_SMS'
            ORDER BY ORDINAL_POSITION
            """
        )
    ).fetchall()
    print("COLUMNS:")
    for c in cols:
        print(f"  {c[0]:30} {c[1]:15} {c[2]}")
    cnt = conn.execute(text("SELECT COUNT(*) FROM dbo.CUST_SMS")).scalar()
    print(f"ROW_COUNT: {cnt}")
    sample = conn.execute(text("SELECT TOP 5 * FROM dbo.CUST_SMS")).mappings().all()
    print("SAMPLE:")
    for row in sample:
        print(dict(row))
