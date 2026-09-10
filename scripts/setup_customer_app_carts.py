"""Create customer_app_cart tables and seed auth permissions."""

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


def create_business_tables() -> None:
    database = settings.business_db_name
    server = settings.business_db_server or settings.db_server
    sql_path = ROOT / "sql" / "25_create_customer_app_cart_tables.sql"
    sql = prepare_sql_for_database(sql_path.read_text(encoding="utf-8"), database)
    batches = split_batches(sql)

    with _odbc_connect(database) as connection:
        cursor = connection.cursor()
        for batch in batches:
            cursor.execute(batch)
        cursor.execute(
            """
            SELECT name
            FROM sys.tables
            WHERE name IN (
                N'customer_app_cart_seq',
                N'customer_app_carts',
                N'customer_app_cart_lines',
                N'customer_app_cart_status_history'
            )
            ORDER BY name
            """
        )
        found = [row[0] for row in cursor.fetchall()]

    print(f"Customer app cart tables ready in {database} on {server}: {', '.join(found)}")
    missing = {
        "customer_app_cart_seq",
        "customer_app_carts",
        "customer_app_cart_lines",
        "customer_app_cart_status_history",
    } - set(found)
    if missing:
        raise SystemExit(f"Missing tables: {', '.join(sorted(missing))}")


def seed_permissions() -> None:
    auth_db = settings.db_name
    sql_path = ROOT / "sql" / "26_seed_customer_app_cart_permissions.sql"
    sql = prepare_sql_for_database(sql_path.read_text(encoding="utf-8"), auth_db)
    batches = split_batches(sql)

    with _odbc_connect(auth_db) as connection:
        cursor = connection.cursor()
        for batch in batches:
            cursor.execute(batch)
        cursor.execute(
            """
            SELECT PermissionCode
            FROM auth.Permissions
            WHERE PermissionCode LIKE 'marketing.customer_app_carts.%'
            ORDER BY PermissionCode
            """
        )
        found = [row[0] for row in cursor.fetchall()]

    print(f"Permissions seeded in {auth_db}: {', '.join(found)}")


if __name__ == "__main__":
    create_business_tables()
    seed_permissions()
    print("Customer App Carts module setup complete.")
