"""Apply cheque printing SQL scripts carefully with per-step verification.

Runs against business DB (tables + sample layout) and auth DB (permissions).
SQL Server 2008 compatible. Idempotent where scripts use IF NOT EXISTS.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.config.settings import settings

EXPECTED_TABLES = [
    "BANK_MASTER",
    "CHEQUE_LAYOUT_MASTER",
    "CHEQUE_LAYOUT_DETAIL",
    "CHEQUE_BOOK",
    "CHEQUE_PRINT_REGISTER",
    "CHEQUE_PRINT_AUDIT",
    "CHEQUE_PRINTER_CALIBRATION",
    "CHEQUE_USER_PREFERENCE",
    "CHEQUE_PERMISSION",
    "CHEQUE_POSITIVE_PAY_QUEUE",
]

EXPECTED_PERMS = [
    "cheque.print",
    "cheque.reprint",
    "cheque.preview",
    "cheque.layout.create",
    "cheque.layout.edit",
    "cheque.layout.delete",
    "cheque.cancel",
    "cheque.export_pdf",
    "cheque.calibrate",
    "cheque.batch",
    "cheque.history",
]


def split_batches(sql: str) -> list[str]:
    return [
        batch.strip()
        for batch in re.split(r"^\s*GO\s*$", sql, flags=re.MULTILINE | re.IGNORECASE)
        if batch.strip()
    ]


def conn_str(database: str) -> str:
    server = settings.business_db_server or settings.db_server
    return (
        f"DRIVER={{{settings.db_driver}}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={settings.db_user};"
        f"PWD={settings.db_password};"
        f"TrustServerCertificate={settings.db_trust_server_certificate};"
        f"Encrypt={settings.db_encrypt};"
    )


def run_script(database: str, sql_path: Path, label: str) -> None:
    import pyodbc

    if not sql_path.exists():
        raise FileNotFoundError(sql_path)

    sql = sql_path.read_text(encoding="utf-8")
    # Auth seed hard-codes USE [NSDS2626_AUTH]; rewrite to active auth DB if needed
    if database.upper() != "NSDS2626_AUTH":
        sql = re.sub(
            r"(?im)^\s*USE\s+\[NSDS2626_AUTH\]\s*;\s*$",
            f"USE [{database}];",
            sql,
        )

    batches = split_batches(sql)
    print(f"\n=== {label} ===")
    print(f"Database : {database}")
    print(f"Script   : {sql_path.name}")
    print(f"Batches  : {len(batches)}")

    with pyodbc.connect(conn_str(database), autocommit=True, timeout=30) as connection:
        cursor = connection.cursor()
        for i, batch in enumerate(batches, start=1):
            preview = " ".join(batch.split())[:100]
            try:
                cursor.execute(batch)
                # Consume any result sets / PRINT messages
                while True:
                    try:
                        if cursor.description is not None:
                            cursor.fetchall()
                    except Exception:
                        pass
                    if not cursor.nextset():
                        break
                print(f"  OK  batch {i}/{len(batches)}: {preview}...")
            except Exception as exc:
                print(f"  FAIL batch {i}/{len(batches)}: {preview}...")
                raise RuntimeError(f"{label} failed on batch {i}: {exc}") from exc

    print(f"=== {label} completed ===")


def verify_business(database: str) -> None:
    import pyodbc

    print(f"\n=== Verify business objects in {database} ===")
    with pyodbc.connect(conn_str(database), timeout=30) as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT name FROM sys.tables
            WHERE name IN ({})
            ORDER BY name
            """.format(",".join("?" for _ in EXPECTED_TABLES)),
            EXPECTED_TABLES,
        )
        found = [r[0] for r in cursor.fetchall()]
        missing = set(EXPECTED_TABLES) - set(found)
        print(f"Tables found ({len(found)}/{len(EXPECTED_TABLES)}): {', '.join(found)}")
        if missing:
            raise RuntimeError(f"Missing tables: {', '.join(sorted(missing))}")

        cursor.execute(
            """
            SELECT
                (SELECT COUNT(*) FROM BANK_MASTER) AS banks,
                (SELECT COUNT(*) FROM CHEQUE_LAYOUT_MASTER) AS layouts,
                (SELECT COUNT(*) FROM CHEQUE_LAYOUT_DETAIL) AS details,
                (SELECT COUNT(*) FROM CHEQUE_PERMISSION) AS perms
            """
        )
        banks, layouts, details, perms = cursor.fetchone()
        print(f"Counts: BANK_MASTER={banks}, LAYOUT_MASTER={layouts}, LAYOUT_DETAIL={details}, PERMISSION={perms}")

        cursor.execute(
            """
            SELECT i.name
            FROM sys.indexes i
            INNER JOIN sys.tables t ON t.object_id = i.object_id
            WHERE t.name IN ('CHEQUE_LAYOUT_DETAIL','CHEQUE_PRINT_REGISTER','CHEQUE_PRINT_AUDIT','BANK_MASTER')
              AND i.name LIKE 'IX_CHQ%' OR (t.name = 'BANK_MASTER' AND i.name = 'IX_BANK_MASTER_Active')
            ORDER BY i.name
            """
        )
        # Fix the OR precedence with a cleaner query
        cursor.execute(
            """
            SELECT t.name AS table_name, i.name AS index_name
            FROM sys.indexes i
            INNER JOIN sys.tables t ON t.object_id = i.object_id
            WHERE i.name IN (
                'IX_CHQ_LAY_D_Layout',
                'IX_CHQ_REG_Voucher',
                'IX_CHQ_REG_PayeeDate',
                'IX_CHQ_REG_Status',
                'IX_CHQ_AUD_Register',
                'IX_CHQ_AUD_Action',
                'IX_BANK_MASTER_Active'
            )
            ORDER BY i.name
            """
        )
        indexes = cursor.fetchall()
        print(f"Indexes found ({len(indexes)}/7):")
        for tname, iname in indexes:
            print(f"  - {iname} on {tname}")
        if len(indexes) < 7:
            raise RuntimeError("Not all expected indexes were created")

        cursor.execute(
            """
            SELECT m.LayoutName, COUNT(d.DetailID) AS obj_count
            FROM CHEQUE_LAYOUT_MASTER m
            LEFT JOIN CHEQUE_LAYOUT_DETAIL d ON d.LayoutID = m.LayoutID
            WHERE m.LayoutName = 'Standard Laser'
            GROUP BY m.LayoutName
            """
        )
        row = cursor.fetchone()
        if not row:
            raise RuntimeError("Sample layout 'Standard Laser' not found")
        print(f"Sample layout '{row[0]}' has {row[1]} detail objects")
        if row[1] < 10:
            raise RuntimeError(f"Expected >= 10 layout objects, found {row[1]}")


def verify_auth(database: str) -> None:
    import pyodbc

    print(f"\n=== Verify auth permissions in {database} ===")
    with pyodbc.connect(conn_str(database), timeout=30) as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT ModuleId, ModuleCode, ModuleName FROM auth.Modules WHERE ModuleCode = 'CHEQUE'")
        mod = cursor.fetchone()
        if not mod:
            raise RuntimeError("CHEQUE module not found in auth.Modules")
        print(f"Module: {mod[1]} ({mod[2]}) id={mod[0]}")

        cursor.execute(
            """
            SELECT PermissionCode
            FROM auth.Permissions
            WHERE PermissionCode LIKE 'cheque.%'
            ORDER BY PermissionCode
            """
        )
        found = [r[0] for r in cursor.fetchall()]
        print(f"Permissions ({len(found)}/{len(EXPECTED_PERMS)}):")
        for code in found:
            print(f"  - {code}")
        missing = set(EXPECTED_PERMS) - set(found)
        if missing:
            raise RuntimeError(f"Missing permissions: {', '.join(sorted(missing))}")

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM auth.RolePermissions rp
            INNER JOIN auth.Permissions p ON p.PermissionId = rp.PermissionId
            INNER JOIN auth.Roles r ON r.RoleId = rp.RoleId
            WHERE p.PermissionCode LIKE 'cheque.%'
              AND r.RoleCode IN ('SUPER_ADMIN', 'ADMIN')
            """
        )
        rp_count = cursor.fetchone()[0]
        print(f"RolePermissions for ADMIN/SUPER_ADMIN: {rp_count}")
        if rp_count < len(EXPECTED_PERMS):
            raise RuntimeError(f"Expected at least {len(EXPECTED_PERMS)} role-permission links, found {rp_count}")


def verify_vb6_files() -> None:
    print("\n=== Verify VB6 module files ===")
    base = ROOT / "vb6" / "ChequePrinting"
    required = [
        "modChequeEnums.bas",
        "modChequeWinAPI.bas",
        "modChequeUtils.bas",
        "clsAmountToWords.cls",
        "clsPrinterManager.cls",
        "clsLayoutObject.cls",
        "clsLayoutManager.cls",
        "clsChequeData.cls",
        "clsChequeAudit.cls",
        "clsChequePrinter.cls",
        "frmChequePrint.frm",
        "frmChequeLayoutDesigner.frm",
        "frmChequeCalibration.frm",
        "frmChequeHistory.frm",
        "frmChequeSearch.frm",
        "frmChequeBatch.frm",
        "integration/VoucherM_PrintCheque.bas.txt",
        "integration/GlMenu_ChequeHooks.bas.txt",
        "README.md",
    ]
    missing = []
    for rel in required:
        path = base / rel
        if not path.exists() or path.stat().st_size < 50:
            missing.append(rel)
        else:
            print(f"  OK  {rel} ({path.stat().st_size} bytes)")
    if missing:
        raise RuntimeError(f"Missing/empty VB6 files: {', '.join(missing)}")

    # Attribute VB_Name sanity
    for path in base.glob("*.bas"):
        text = path.read_text(encoding="utf-8", errors="replace")
        if "Attribute VB_Name" not in text:
            raise RuntimeError(f"{path.name} missing Attribute VB_Name")
    for path in base.glob("*.cls"):
        text = path.read_text(encoding="utf-8", errors="replace")
        if "Attribute VB_Name" not in text:
            raise RuntimeError(f"{path.name} missing Attribute VB_Name")
    for path in base.glob("*.frm"):
        text = path.read_text(encoding="utf-8", errors="replace")
        if "Attribute VB_Name" not in text or "Begin VB.Form" not in text:
            raise RuntimeError(f"{path.name} missing form header / VB_Name")
    print("VB6 Attribute / form headers OK")


def main() -> int:
    business_db = settings.business_db_name
    auth_db = settings.db_name
    server = settings.business_db_server or settings.db_server

    print("Cheque Printing setup")
    print(f"Server      : {server}")
    print(f"Business DB : {business_db}")
    print(f"Auth DB     : {auth_db}")

    try:
        # Probe
        import pyodbc

        for db in (business_db, auth_db):
            with pyodbc.connect(conn_str(db), timeout=15) as c:
                cur = c.cursor()
                cur.execute("SELECT DB_NAME(), @@SERVERNAME")
                name, srv = cur.fetchone()
                print(f"Connected   : {name} @ {srv}")

        run_script(business_db, ROOT / "sql" / "22_create_cheque_printing_tables.sql", "STEP 1 — Schema")
        run_script(auth_db, ROOT / "sql" / "23_seed_cheque_printing_permissions.sql", "STEP 2 — Auth permissions")
        run_script(business_db, ROOT / "sql" / "24_seed_cheque_sample_layout.sql", "STEP 3 — Sample layout")

        verify_business(business_db)
        verify_auth(auth_db)
        verify_vb6_files()

        print("\nALL CHECKS PASSED")
        return 0
    except Exception as exc:
        print(f"\nFAILED: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
