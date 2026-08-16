"""Create customer_app_otp table (SMS_DB_ OTP queue support)."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.config.settings import settings


def split_batches(sql: str) -> list[str]:
    return [
        batch.strip()
        for batch in re.split(r"^\s*GO\s*$", sql, flags=re.MULTILINE | re.IGNORECASE)
        if batch.strip()
    ]


def prepare_sql_for_database(sql: str, database: str) -> str:
    rewritten = re.sub(
        r"(?im)^\s*USE\s+\[[^\]]+\]\s*;\s*$",
        f"USE [{database}];",
        sql,
        count=1,
    )
    if f"USE [{database}];" not in rewritten:
        rewritten = f"USE [{database}];\nGO\n\n{sql}"
    return rewritten


def _odbc_connect(database: str):
    import pyodbc

    server = settings.business_db_server or settings.db_server
    return pyodbc.connect(
        f"DRIVER={{{settings.db_driver}}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={settings.db_user};"
        f"PWD={settings.db_password};"
        f"TrustServerCertificate={settings.db_trust_server_certificate};"
        f"Encrypt={settings.db_encrypt};",
        autocommit=True,
    )


def create_otp_table() -> None:
    database = settings.business_db_name
    server = settings.business_db_server or settings.db_server
    sql_path = ROOT / "sql" / "27_create_customer_app_otp_tables.sql"
    sql = prepare_sql_for_database(sql_path.read_text(encoding="utf-8"), database)
    batches = split_batches(sql)

    with _odbc_connect(database) as connection:
        cursor = connection.cursor()
        for batch in batches:
            cursor.execute(batch)
        cursor.execute(
            """
            SELECT name FROM sys.tables
            WHERE name = N'customer_app_otp'
            """
        )
        found = [row[0] for row in cursor.fetchall()]

    print(f"customer_app_otp ready in {database} on {server}: {', '.join(found)}")
    if "customer_app_otp" not in found:
        raise SystemExit("customer_app_otp table missing")


if __name__ == "__main__":
    create_otp_table()
    print("Customer App OTP setup complete.")
