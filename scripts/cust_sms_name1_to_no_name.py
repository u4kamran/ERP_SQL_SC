"""
Option A: Update CUST_SMS rows where CUST_NAME is exactly '1' → 'No Name'.
Does NOT touch the 76 already updated from VCF.
"""

from __future__ import annotations

import csv
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from app.database.business_session import business_engine

ROOT = Path(__file__).resolve().parent.parent
REPORT_DIR = ROOT / "data" / "SC_WhatsappNo_Import" / "reports"
NEW_NAME = "No Name"


def main() -> int:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    bak_table = f"CUST_SMS_NAME1_BAK_{stamp}"
    if not bak_table.replace("_", "").isalnum():
        raise RuntimeError("unsafe backup table name")

    print("=" * 72)
    print("OPTION A — Replace remaining CUST_NAME = '1' with 'No Name'")
    print("=" * 72)

    select_sql = text(
        """
        SELECT
            CUST_ID,
            RTRIM(ISNULL(CUST_NAME, '')) AS CUST_NAME,
            RTRIM(ISNULL(MOBILE_NO, '')) AS MOBILE_NO,
            RTRIM(ISNULL(MOBILE_NO_TMP, '')) AS MOBILE_NO_TMP,
            RTRIM(ISNULL(CUST_ADDRESS, '')) AS CUST_ADDRESS,
            STATUS,
            ADDED_DATETIME
        FROM dbo.CUST_SMS
        WHERE RTRIM(ISNULL(CUST_NAME, '')) = '1'
        ORDER BY CUST_ID
        """
    )

    with business_engine.connect() as conn:
        before_rows = [dict(r) for r in conn.execute(select_sql).mappings().all()]
        before_count = len(before_rows)
        print(f"Rows currently named '1': {before_count}")
        if before_count == 0:
            print("Nothing to update.")
            return 0

    # Backup affected rows to SQL table + CSV
    create_bak = text(
        f"""
        IF OBJECT_ID(N'dbo.{bak_table}', N'U') IS NOT NULL
            RAISERROR(N'Backup table already exists', 16, 1);

        SELECT *
        INTO dbo.{bak_table}
        FROM dbo.CUST_SMS
        WHERE RTRIM(ISNULL(CUST_NAME, '')) = '1';
        """
    )
    with business_engine.begin() as conn:
        conn.execute(create_bak)
        bak_count = int(
            conn.execute(text(f"SELECT COUNT(1) FROM dbo.{bak_table}")).scalar() or 0
        )
    print(f"Backup table: dbo.{bak_table} ({bak_count} rows)")

    csv_path = REPORT_DIR / f"Name1_Before_NoName_{stamp}.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        cols = list(before_rows[0].keys())
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(before_rows)
    print(f"Backup CSV: {csv_path}")

    # Atomic update
    with business_engine.begin() as conn:
        result = conn.execute(
            text(
                """
                UPDATE dbo.CUST_SMS
                SET CUST_NAME = :new_name
                WHERE RTRIM(ISNULL(CUST_NAME, '')) = '1'
                """
            ),
            {"new_name": NEW_NAME},
        )
        updated = int(result.rowcount or 0)
        still_one = int(
            conn.execute(
                text(
                    """
                    SELECT COUNT(1)
                    FROM dbo.CUST_SMS
                    WHERE RTRIM(ISNULL(CUST_NAME, '')) = '1'
                    """
                )
            ).scalar()
            or 0
        )
        now_noname = int(
            conn.execute(
                text(
                    """
                    SELECT COUNT(1)
                    FROM dbo.CUST_SMS
                    WHERE RTRIM(ISNULL(CUST_NAME, '')) = :new_name
                    """
                ),
                {"new_name": NEW_NAME},
            ).scalar()
            or 0
        )

    summary = {
        "option": "A",
        "action": "Replace CUST_NAME '1' with 'No Name'",
        "backup_table": f"dbo.{bak_table}",
        "backup_csv": str(csv_path),
        "before_named_1": before_count,
        "rows_updated": updated,
        "still_named_1_after": still_one,
        "named_no_name_after": now_noname,
        "timestamp": stamp,
        "committed": True,
    }
    out_json = REPORT_DIR / f"Name1_To_NoName_RESULT_{stamp}.json"
    out_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print()
    print("RESULT")
    print(f"  Updated: {updated}")
    print(f"  Still named '1': {still_one}")
    print(f"  Now named 'No Name': {now_noname}")
    print(f"  Result JSON: {out_json}")
    if still_one != 0 or updated != before_count:
        print("WARNING: counts did not match expectations.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
