"""Preview / apply: copy mobile numbers into Gl0001.CREATED_BY from GL0005/GL0006."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text

from app.database.business_session import BusinessSessionLocal
from app.utils.phone_extract import extract_pk_mobiles, format_pk_phone_display


def _pick_mobile(*values: str) -> str:
    phones = extract_pk_mobiles(*values)
    if not phones:
        return ""
    return format_pk_phone_display(phones[0])


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync Gl0001.CREATED_BY from vendor/customer phones")
    parser.add_argument("--apply", action="store_true", help="Write updates to database")
    parser.add_argument("--limit", type=int, default=20, help="Preview rows to print")
    args = parser.parse_args()

    with BusinessSessionLocal() as db:
        rows = db.execute(
            text(
                """
                SELECT
                    g1.ac_id,
                    RTRIM(g1.ac_title) AS ac_title,
                    RTRIM(g1.CREATED_BY) AS created_by,
                    RTRIM(g5.PHONE) AS cust_phone,
                    RTRIM(g5.CONTACT_PERSON) AS cust_contact,
                    RTRIM(g6.PHONE) AS vend_phone,
                    RTRIM(g6.CONTACT_PERSON) AS vend_contact
                FROM Gl0001 g1
                LEFT JOIN GL0005 g5 ON g5.CUSTOMER_ID = g1.ac_id
                LEFT JOIN GL0006 g6 ON g6.VENDOR_ID = g1.ac_id
                WHERE g1.ac_level = 4
                """
            )
        ).mappings().all()

        updates: list[dict] = []
        for row in rows:
            current = str(row["created_by"] or "").strip()
            if current and current != "." and extract_pk_mobiles(current):
                continue

            mobile = _pick_mobile(
                row["vend_phone"],
                row["vend_contact"],
                row["cust_phone"],
                row["cust_contact"],
            )
            if not mobile:
                continue

            updates.append(
                {
                    "ac_id": int(row["ac_id"]),
                    "ac_title": row["ac_title"],
                    "old": current or ".",
                    "new": mobile,
                }
            )

        print(f"Accounts with mobile available to sync: {len(updates)}")
        for item in updates[: args.limit]:
            print(f"  {item['ac_id']} | {item['ac_title'][:40]} | {item['old']} -> {item['new']}")
        if len(updates) > args.limit:
            print(f"  ... and {len(updates) - args.limit} more")

        if not args.apply:
            print("\nPreview only. Run with --apply to update Gl0001.CREATED_BY")
            return

        for item in updates:
            db.execute(
                text("UPDATE Gl0001 SET CREATED_BY = :mobile WHERE ac_id = :ac_id"),
                {"mobile": item["new"], "ac_id": item["ac_id"]},
            )
        db.commit()
        print(f"\nUpdated {len(updates)} account(s).")


if __name__ == "__main__":
    main()
