"""
Create auth database for ERP or ARP site by running sql/*.sql with the correct DB name.

Usage:
    python scripts/setup_auth_database.py --site arp
    python scripts/setup_auth_database.py --site erp
    python scripts/setup_auth_database.py --auth-db NAHSL2627_AUTH --server shahenhp
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SQL_DIR = ROOT / "sql"

SQL_FILES = [
    "01_create_database.sql",
    "02_create_schema.sql",
    "03_create_tables.sql",
    "04_create_indexes.sql",
    "05_seed_data.sql",
    "06_seed_inventory_permissions.sql",
    "07_seed_gl_ledger_permissions.sql",
    "08_seed_sms_email_scheduler_permissions.sql",
    "09_seed_voucher_permissions.sql",
    "10_seed_reports_role.sql",
]

SITE_AUTH_DBS = {
    "erp": "NSDS2626_AUTH",
    "arp": "NAHSL2627_AUTH",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create auth database from sql/*.sql")
    parser.add_argument("--site", choices=sorted(SITE_AUTH_DBS), help="Site profile (erp or arp)")
    parser.add_argument("--auth-db", help="Auth database name (overrides --site)")
    parser.add_argument("--server", help="SQL Server host (default: from .env or shahenhp)")
    parser.add_argument("--user", default="sa", help="SQL login (default: sa)")
    parser.add_argument("--password", help="SQL password (default: from .env)")
    return parser.parse_args()


def load_settings():
    sys.path.insert(0, str(ROOT))
    from app.config.settings import settings

    return settings


def split_batches(sql: str) -> list[str]:
    parts = re.split(r"^\s*GO\s*$", sql, flags=re.MULTILINE | re.IGNORECASE)
    return [part.strip() for part in parts if part.strip()]


def run_sql_file(cursor, path: Path, source_db: str, target_db: str) -> None:
    sql = path.read_text(encoding="utf-8")
    sql = sql.replace(source_db, target_db)
    for batch in split_batches(sql):
        cursor.execute(batch)


def main() -> int:
    try:
        import pyodbc
    except ImportError:
        print("pyodbc not installed. Run: pip install pyodbc")
        return 1

    args = parse_args()
    settings = None
    try:
        settings = load_settings()
    except Exception:
        pass

    if args.auth_db:
        auth_db = args.auth_db
    elif args.site:
        auth_db = SITE_AUTH_DBS[args.site]
    else:
        print("Specify --site erp|arp or --auth-db NAME")
        return 1

    server = args.server or (settings.db_server if settings else "shaheenhp")
    password = args.password or (settings.db_password if settings else "")
    if not password:
        print("No DB password. Set DB_PASSWORD in .env or pass --password")
        return 1

    driver = "ODBC Driver 18 for SQL Server"
    conn_str = (
        f"DRIVER={{{driver}}};"
        f"SERVER={server};"
        f"DATABASE=master;"
        f"UID={args.user};"
        f"PWD={password};"
        f"TrustServerCertificate=yes;"
        f"Encrypt=no;"
    )

    print(f"Server:   {server}")
    print(f"Auth DB:  {auth_db}")
    print()

    try:
        conn = pyodbc.connect(conn_str, autocommit=True)
    except Exception as exc:
        print(f"Connection failed: {exc}")
        return 1

    cursor = conn.cursor()
    source_db = "NSDS2626_AUTH"

    for filename in SQL_FILES:
        path = SQL_DIR / filename
        if not path.exists():
            print(f"SKIP missing file: {filename}")
            continue
        print(f"--- {filename} ---")
        try:
            run_sql_file(cursor, path, source_db, auth_db)
            print("OK")
        except Exception as exc:
            print(f"FAILED: {exc}")
            cursor.close()
            conn.close()
            return 1
        print()

    cursor.close()
    conn.close()

    print(f"Auth database {auth_db} is ready on {server}.")
    print("Default login: admin / ChangeMe@2026!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
