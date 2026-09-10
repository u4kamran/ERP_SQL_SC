"""
PHASE 2 — WhatsApp VCF → CUST_SMS synchronization (APPROVED WRITES).

Safety order:
  1) Backup dbo.CUST_SMS (SQL table copy + CSV dump of full table)
  2) Revalidate Phase 1 plan against live DB
  3) BEGIN TRANSACTION → INSERT new + UPDATE names only → COMMIT/ROLLBACK
  4) Verification + audit log reports

Usage:
  python scripts/whatsapp_vcf_sync_phase2.py --mode ALL --report <phase1.json>
  Modes: ALL | NEW_ONLY | NAME_UPDATES_ONLY
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from sqlalchemy import text

from app.database.business_session import business_engine

# Reuse Phase-1 helpers without requiring scripts/ as a package.
import importlib.util

_phase1_path = Path(__file__).resolve().parent / "whatsapp_vcf_sync_phase1.py"
_spec = importlib.util.spec_from_file_location("whatsapp_vcf_sync_phase1", _phase1_path)
_phase1 = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
sys.modules["whatsapp_vcf_sync_phase1"] = _phase1
_spec.loader.exec_module(_phase1)

REPORT_DIR = _phase1.REPORT_DIR
is_valid_pk_mobile_key = _phase1.is_valid_pk_mobile_key
mobile_for_storage = _phase1.mobile_for_storage
mobile_key = _phase1.mobile_key
names_effectively_same = _phase1.names_effectively_same

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REPORT = (
    REPORT_DIR / "WhatsApp_Customer_Sync_Report_20260815_150150.json"
)
AUDIT_SOURCE = "VCF"
AUDIT_USER = "cursor-agent"


def normalize_name_for_db(value: str) -> str:
    return (value or "").strip()[:150]


def backup_cust_sms(stamp: str) -> dict[str, Any]:
    """
    Create:
      - SQL Server backup table dbo.CUST_SMS_BAK_<stamp>
      - CSV dump of full CUST_SMS under reports/
    """
    bak_table = f"CUST_SMS_BAK_{stamp}"
    # SQL identifiers: only allow safe chars
    if not re.fullmatch(r"CUST_SMS_BAK_\d{8}_\d{6}", bak_table):
        raise RuntimeError(f"Unsafe backup table name: {bak_table}")

    csv_path = REPORT_DIR / f"CUST_SMS_FULL_BACKUP_{stamp}.csv"
    info: dict[str, Any] = {
        "backup_table": f"dbo.{bak_table}",
        "backup_csv": str(csv_path),
        "row_count": 0,
    }

    create_sql = text(
        f"""
        IF OBJECT_ID(N'dbo.{bak_table}', N'U') IS NOT NULL
            RAISERROR(N'Backup table already exists: dbo.{bak_table}', 16, 1);

        SELECT *
        INTO dbo.{bak_table}
        FROM dbo.CUST_SMS;
        """
    )
    count_sql = text(f"SELECT COUNT(1) AS cnt FROM dbo.{bak_table}")
    dump_sql = text(
        """
        SELECT
            CUST_ID,
            RTRIM(ISNULL(CUST_NAME, '')) AS CUST_NAME,
            RTRIM(ISNULL(MOBILE_NO, '')) AS MOBILE_NO,
            STATUS,
            ADDED_DATETIME,
            RTRIM(ISNULL(MOBILE_NO_TMP, '')) AS MOBILE_NO_TMP,
            RTRIM(ISNULL(CUST_ADDRESS, '')) AS CUST_ADDRESS,
            STAR_RATING,
            STAR_RATING_VALUE,
            STAR_RATING_VISIT,
            STAR_RATING_VISIT_VALUE,
            STAR_RATING_TSALES,
            STAR_RATING_TSALES_VALUE
        FROM dbo.CUST_SMS
        ORDER BY CUST_ID
        """
    )

    with business_engine.begin() as conn:
        conn.execute(create_sql)
        info["row_count"] = int(conn.execute(count_sql).scalar() or 0)
        rows = [dict(r) for r in conn.execute(dump_sql).mappings().all()]

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    cols = list(rows[0].keys()) if rows else [
        "CUST_ID",
        "CUST_NAME",
        "MOBILE_NO",
        "STATUS",
        "ADDED_DATETIME",
        "MOBILE_NO_TMP",
        "CUST_ADDRESS",
        "STAR_RATING",
        "STAR_RATING_VALUE",
        "STAR_RATING_VISIT",
        "STAR_RATING_VISIT_VALUE",
        "STAR_RATING_TSALES",
        "STAR_RATING_TSALES_VALUE",
    ]
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for row in rows:
            w.writerow(row)

    info["csv_rows"] = len(rows)
    return info


def load_plan(report_path: Path) -> list[dict[str, Any]]:
    data = json.loads(report_path.read_text(encoding="utf-8"))
    return list(data.get("results") or [])


def fetch_by_cust_id(conn, cust_id: int) -> dict[str, Any] | None:
    row = conn.execute(
        text(
            """
            SELECT
                CUST_ID AS cust_id,
                RTRIM(ISNULL(CUST_NAME, '')) AS cust_name,
                RTRIM(ISNULL(MOBILE_NO, '')) AS mobile_no,
                RTRIM(ISNULL(MOBILE_NO_TMP, '')) AS mobile_no_tmp
            FROM dbo.CUST_SMS
            WHERE CUST_ID = :cust_id
            """
        ),
        {"cust_id": cust_id},
    ).mappings().first()
    return dict(row) if row else None


def fetch_by_mobile_key(conn, key: str) -> list[dict[str, Any]]:
    rows = conn.execute(
        text(
            """
            SELECT
                CUST_ID AS cust_id,
                RTRIM(ISNULL(CUST_NAME, '')) AS cust_name,
                RTRIM(ISNULL(MOBILE_NO, '')) AS mobile_no,
                RTRIM(ISNULL(MOBILE_NO_TMP, '')) AS mobile_no_tmp
            FROM dbo.CUST_SMS
            WHERE LEN(LTRIM(RTRIM(ISNULL(MOBILE_NO, '')))) >= 10
              AND RIGHT(
                  REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
                      LTRIM(RTRIM(MOBILE_NO)),
                      ' ', ''), '-', ''), '(', ''), ')', ''), '+', ''),
                  10
              ) = :mobile_key
            ORDER BY CUST_ID
            """
        ),
        {"mobile_key": key},
    ).mappings().all()
    # Also check MOBILE_NO_TMP for completeness
    rows2 = conn.execute(
        text(
            """
            SELECT
                CUST_ID AS cust_id,
                RTRIM(ISNULL(CUST_NAME, '')) AS cust_name,
                RTRIM(ISNULL(MOBILE_NO, '')) AS mobile_no,
                RTRIM(ISNULL(MOBILE_NO_TMP, '')) AS mobile_no_tmp
            FROM dbo.CUST_SMS
            WHERE LEN(LTRIM(RTRIM(ISNULL(MOBILE_NO_TMP, '')))) >= 10
              AND RIGHT(
                  REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
                      LTRIM(RTRIM(MOBILE_NO_TMP)),
                      ' ', ''), '-', ''), '(', ''), ')', ''), '+', ''),
                  10
              ) = :mobile_key
            ORDER BY CUST_ID
            """
        ),
        {"mobile_key": key},
    ).mappings().all()
    by_id: dict[int, dict[str, Any]] = {}
    for r in list(rows) + list(rows2):
        by_id[int(r["cust_id"])] = dict(r)
    return list(by_id.values())


def revalidate(
    conn,
    plan: list[dict[str, Any]],
    mode: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Returns (updates, inserts, skipped).
    Re-checks live DB; never trusts Phase 1 blindly.
    """
    do_updates = mode in {"ALL", "NAME_UPDATES_ONLY"}
    do_inserts = mode in {"ALL", "NEW_ONLY"}

    updates: list[dict[str, Any]] = []
    inserts: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []

    for row in plan:
        cat = row.get("category")
        key = (row.get("normalized_phone") or "").strip()
        vcf_name = normalize_name_for_db(row.get("vcf_name") or "")

        if cat == "B" and do_updates:
            cust_id = row.get("db_cust_id")
            if not cust_id or not key or not vcf_name:
                skipped.append({**row, "skip_reason": "Invalid update plan row"})
                continue
            current = fetch_by_cust_id(conn, int(cust_id))
            if not current:
                skipped.append({**row, "skip_reason": f"CUST_ID {cust_id} no longer exists"})
                continue
            matches = fetch_by_mobile_key(conn, key)
            if len(matches) != 1:
                skipped.append(
                    {
                        **row,
                        "skip_reason": (
                            f"Phone key {key} now matches {len(matches)} rows "
                            f"(expected 1). Manual review."
                        ),
                    }
                )
                continue
            if int(matches[0]["cust_id"]) != int(cust_id):
                skipped.append(
                    {
                        **row,
                        "skip_reason": (
                            f"Phone key {key} now points to CUST_ID "
                            f"{matches[0]['cust_id']} (expected {cust_id})."
                        ),
                    }
                )
                continue
            # Confirm phone on this customer still matches key
            cur_keys = {
                k
                for k in (
                    mobile_key(current["mobile_no"]),
                    mobile_key(current["mobile_no_tmp"]),
                )
                if is_valid_pk_mobile_key(k)
            }
            if key not in cur_keys:
                skipped.append(
                    {
                        **row,
                        "skip_reason": (
                            f"CUST_ID {cust_id} phone changed since analysis "
                            f"(no longer key {key})."
                        ),
                    }
                )
                continue
            if names_effectively_same(current["cust_name"], vcf_name):
                skipped.append(
                    {
                        **row,
                        "skip_reason": "Name already effectively same at sync time",
                        "result": "ALREADY_SAME",
                    }
                )
                continue
            updates.append(
                {
                    **row,
                    "old_name": current["cust_name"],
                    "new_name": vcf_name,
                    "live_mobile": current["mobile_no"],
                }
            )
            continue

        if cat == "C" and do_inserts:
            if not key or not vcf_name:
                skipped.append({**row, "skip_reason": "Invalid insert plan row"})
                continue
            if not is_valid_pk_mobile_key(key):
                skipped.append({**row, "skip_reason": "Invalid mobile key"})
                continue
            existing = fetch_by_mobile_key(conn, key)
            if existing:
                skipped.append(
                    {
                        **row,
                        "skip_reason": (
                            f"ALREADY EXISTS as CUST_ID(s) "
                            f"{', '.join(str(x['cust_id']) for x in existing)}"
                        ),
                        "result": "ALREADY_EXISTS",
                    }
                )
                continue
            storage = (row.get("storage_phone") or "").strip() or mobile_for_storage(
                row.get("vcf_phone") or key
            )
            if mobile_key(storage) != key:
                storage = "0" + key
            inserts.append(
                {
                    **row,
                    "new_name": vcf_name,
                    "storage_phone": storage[:20],
                }
            )
            continue

        # Not in selected mode / not approved category
        if cat in {"B", "C"}:
            skipped.append(
                {
                    **row,
                    "skip_reason": f"Category {cat} excluded by mode={mode}",
                }
            )

    return updates, inserts, skipped


def apply_sync(
    updates: list[dict[str, Any]],
    inserts: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Atomic transaction: all updates + inserts, or ROLLBACK everything.
    Returns (update_audit, insert_audit).
    """
    update_audit: list[dict[str, Any]] = []
    insert_audit: list[dict[str, Any]] = []
    now = datetime.now().isoformat(timespec="seconds")

    with business_engine.begin() as conn:
        # Re-check inside the same connection/transaction
        for u in updates:
            key = u["normalized_phone"]
            cust_id = int(u["db_cust_id"])
            live = fetch_by_cust_id(conn, cust_id)
            matches = fetch_by_mobile_key(conn, key)
            if (
                not live
                or len(matches) != 1
                or int(matches[0]["cust_id"]) != cust_id
            ):
                raise RuntimeError(
                    f"Revalidation failed for UPDATE CUST_ID={cust_id} key={key}"
                )
            old_name = live["cust_name"]
            new_name = u["new_name"]
            result = conn.execute(
                text(
                    """
                    UPDATE dbo.CUST_SMS
                    SET CUST_NAME = :cust_name
                    WHERE CUST_ID = :cust_id
                    """
                ),
                {"cust_name": new_name, "cust_id": cust_id},
            )
            if result.rowcount != 1:
                raise RuntimeError(
                    f"UPDATE affected {result.rowcount} rows for CUST_ID={cust_id}"
                )
            update_audit.append(
                {
                    "datetime": now,
                    "source": AUDIT_SOURCE,
                    "user": AUDIT_USER,
                    "action": "UPDATE_NAME",
                    "customer_id": cust_id,
                    "phone": live["mobile_no"],
                    "normalized_phone": key,
                    "old_name": old_name,
                    "new_name": new_name,
                    "result": "SUCCESS",
                    "error": "",
                    "vcf_row": u.get("row_num"),
                }
            )

        for ins in inserts:
            key = ins["normalized_phone"]
            existing = fetch_by_mobile_key(conn, key)
            if existing:
                raise RuntimeError(
                    f"Insert aborted: key {key} already exists as "
                    f"{[x['cust_id'] for x in existing]}"
                )
            name = ins["new_name"]
            phone = ins["storage_phone"]
            row = conn.execute(
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
                        :name, :mobile, NULL, NULL,
                        1, GETDATE(),
                        NULL, NULL, NULL, NULL, NULL, NULL
                    )
                    """
                ),
                {"name": name, "mobile": phone},
            ).first()
            if not row:
                raise RuntimeError(f"INSERT failed for phone {phone}")
            new_id = int(row[0])
            insert_audit.append(
                {
                    "datetime": now,
                    "source": AUDIT_SOURCE,
                    "user": AUDIT_USER,
                    "action": "INSERT",
                    "customer_id": new_id,
                    "phone": phone,
                    "normalized_phone": key,
                    "old_name": "",
                    "new_name": name,
                    "result": "SUCCESS",
                    "error": "",
                    "vcf_row": ins.get("row_num"),
                }
            )

    return update_audit, insert_audit


def verify(
    conn,
    update_audit: list[dict[str, Any]],
    insert_audit: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for a in update_audit:
        live = fetch_by_cust_id(conn, int(a["customer_id"]))
        ok = bool(live) and names_effectively_same(
            live.get("cust_name") or "", a["new_name"]
        )
        rows.append(
            {
                **a,
                "verify_db_name": (live or {}).get("cust_name", ""),
                "verify_db_phone": (live or {}).get("mobile_no", ""),
                "verify_ok": ok,
            }
        )
    for a in insert_audit:
        live = fetch_by_cust_id(conn, int(a["customer_id"]))
        key_ok = False
        if live:
            keys = {
                k
                for k in (
                    mobile_key(live.get("mobile_no") or ""),
                    mobile_key(live.get("mobile_no_tmp") or ""),
                )
                if is_valid_pk_mobile_key(k)
            }
            key_ok = a["normalized_phone"] in keys
        ok = bool(live) and key_ok and names_effectively_same(
            live.get("cust_name") or "", a["new_name"]
        )
        rows.append(
            {
                **a,
                "verify_db_name": (live or {}).get("cust_name", ""),
                "verify_db_phone": (live or {}).get("mobile_no", ""),
                "verify_ok": ok,
            }
        )
    return rows


def write_reports(
    stamp: str,
    mode: str,
    backup_info: dict[str, Any],
    update_audit: list[dict[str, Any]],
    insert_audit: list[dict[str, Any]],
    skipped: list[dict[str, Any]],
    verify_rows: list[dict[str, Any]],
    error: str | None,
) -> dict[str, str]:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    base = f"WhatsApp_Customer_Sync_RESULT_{stamp}"
    paths = {
        "json": str(REPORT_DIR / f"{base}.json"),
        "csv": str(REPORT_DIR / f"{base}_AUDIT.csv"),
        "xlsx": str(REPORT_DIR / f"{base}.xlsx"),
        "summary": str(REPORT_DIR / f"{base}_SUMMARY.txt"),
    }

    summary = {
        "mode": mode,
        "backup_table": backup_info.get("backup_table"),
        "backup_csv": backup_info.get("backup_csv"),
        "backup_row_count": backup_info.get("row_count"),
        "successfully_updated": len(update_audit),
        "successfully_inserted": len(insert_audit),
        "skipped": len(skipped),
        "verify_ok": sum(1 for r in verify_rows if r.get("verify_ok")),
        "verify_failed": sum(1 for r in verify_rows if not r.get("verify_ok")),
        "failed": 1 if error else 0,
        "error": error or "",
        "committed": error is None,
    }

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "summary": summary,
        "backup": backup_info,
        "updates": update_audit,
        "inserts": insert_audit,
        "skipped": [
            {
                "row_num": s.get("row_num"),
                "category": s.get("category"),
                "vcf_name": s.get("vcf_name"),
                "normalized_phone": s.get("normalized_phone"),
                "db_cust_id": s.get("db_cust_id"),
                "skip_reason": s.get("skip_reason"),
                "result": s.get("result"),
            }
            for s in skipped
        ],
        "verification": verify_rows,
    }
    Path(paths["json"]).write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )

    audit_rows = update_audit + insert_audit
    cols = [
        "datetime",
        "source",
        "user",
        "action",
        "customer_id",
        "phone",
        "normalized_phone",
        "old_name",
        "new_name",
        "result",
        "error",
        "vcf_row",
    ]
    with open(paths["csv"], "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in audit_rows:
            w.writerow(r)

    wb = Workbook()
    ws = wb.active
    ws.title = "Summary"
    header_fill = PatternFill("solid", fgColor="1F4E79")
    header_font = Font(color="FFFFFF", bold=True)
    ws.append(["WhatsApp Customer Sync — Phase 2 Result"])
    ws["A1"].font = Font(bold=True, size=14)
    ws.append([])
    ws.append(["Metric", "Value"])
    ws["A3"].fill = header_fill
    ws["B3"].fill = header_fill
    ws["A3"].font = header_font
    ws["B3"].font = header_font
    for k, v in summary.items():
        ws.append([k, v])

    for title, rows, fields in [
        ("Audit Updates", update_audit, cols),
        ("Audit Inserts", insert_audit, cols),
        (
            "Skipped",
            payload["skipped"],
            [
                "row_num",
                "category",
                "vcf_name",
                "normalized_phone",
                "db_cust_id",
                "skip_reason",
                "result",
            ],
        ),
        (
            "Verification",
            verify_rows,
            cols
            + ["verify_db_name", "verify_db_phone", "verify_ok"],
        ),
    ]:
        sheet = wb.create_sheet(title)
        sheet.append(fields)
        for cell in sheet[1]:
            cell.fill = header_fill
            cell.font = header_font
        for r in rows:
            sheet.append([r.get(c) for c in fields])

    wb.save(paths["xlsx"])

    lines = [
        "Synchronization Result",
        f"Mode: {mode}",
        f"Committed: {summary['committed']}",
        f"Backup table: {summary['backup_table']}",
        f"Backup CSV: {summary['backup_csv']}",
        f"Successfully Updated: {summary['successfully_updated']}",
        f"Successfully Inserted: {summary['successfully_inserted']}",
        f"Skipped: {summary['skipped']}",
        f"Verify OK: {summary['verify_ok']}",
        f"Verify Failed: {summary['verify_failed']}",
    ]
    if error:
        lines.append(f"ERROR: {error}")
        lines.append("Transaction was ROLLED BACK. No sync changes applied.")
    Path(paths["summary"]).write_text("\n".join(lines), encoding="utf-8")
    return paths


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=["ALL", "NEW_ONLY", "NAME_UPDATES_ONLY"],
        default="ALL",
    )
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    if not args.report.exists():
        print(f"ERROR: Phase 1 report not found: {args.report}")
        return 1

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 72)
    print("PHASE 2 — BACKUP + SYNCHRONIZATION")
    print("=" * 72)
    print(f"Mode: {args.mode}")
    print(f"Plan: {args.report}")

    print("\n[1/4] Creating CUST_SMS backup...")
    backup_info = backup_cust_sms(stamp)
    print(f"  SQL table: {backup_info['backup_table']} ({backup_info['row_count']} rows)")
    print(f"  CSV dump:  {backup_info['backup_csv']} ({backup_info['csv_rows']} rows)")

    plan = load_plan(args.report)
    print(f"\n[2/4] Revalidating plan ({len(plan)} Phase-1 rows)...")

    update_audit: list[dict[str, Any]] = []
    insert_audit: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    verify_rows: list[dict[str, Any]] = []
    error: str | None = None

    try:
        with business_engine.connect() as conn:
            updates, inserts, skipped = revalidate(conn, plan, args.mode)
            print(f"  Approved updates after revalidation: {len(updates)}")
            print(f"  Approved inserts after revalidation: {len(inserts)}")
            print(f"  Skipped: {len(skipped)}")

        print("\n[3/4] Applying synchronization in ONE transaction...")
        update_audit, insert_audit = apply_sync(updates, inserts)
        print(f"  Updated: {len(update_audit)}")
        print(f"  Inserted: {len(insert_audit)}")

        print("\n[4/4] Post-sync verification...")
        with business_engine.connect() as conn:
            verify_rows = verify(conn, update_audit, insert_audit)
        ok = sum(1 for r in verify_rows if r.get("verify_ok"))
        bad = sum(1 for r in verify_rows if not r.get("verify_ok"))
        print(f"  Verify OK: {ok}")
        print(f"  Verify FAILED: {bad}")
        if bad:
            error = f"{bad} verification mismatch(es) after commit"
    except Exception as exc:
        error = str(exc)
        print(f"\nCRITICAL ERROR — transaction rolled back: {error}")

    paths = write_reports(
        stamp=stamp,
        mode=args.mode,
        backup_info=backup_info,
        update_audit=update_audit,
        insert_audit=insert_audit,
        skipped=skipped,
        verify_rows=verify_rows,
        error=error,
    )

    print("\n" + Path(paths["summary"]).read_text(encoding="utf-8"))
    print(f"\nResult Excel: {paths['xlsx']}")
    print(f"Audit CSV:    {paths['csv']}")
    print(f"Result JSON:  {paths['json']}")
    return 1 if error else 0


if __name__ == "__main__":
    raise SystemExit(main())
