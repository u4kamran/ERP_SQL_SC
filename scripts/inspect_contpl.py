"""Inspect dbo.CONTPL structure (schema only)."""
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
            FROM nsds2626.INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'CONTPL'
            ORDER BY ORDINAL_POSITION
            """
        )
    ).fetchall()
    print("COLUMNS:")
    for c in cols:
        print(f"  {c[0]:30} {c[1]:15} {c[2]}")
    count = conn.execute(text("SELECT COUNT(*) FROM dbo.CONTPL")).scalar()
    print(f"ROW_COUNT: {count}")
