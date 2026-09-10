"""Create delivery tables in the configured business DB and seed auth permissions."""

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
    """Point USE [...] at the active business DB (ERP nsds2626 or ARP NAHSL2627)."""
    rewritten = re.sub(
        r"(?im)^\s*USE\s+\[[^\]]+\]\s*;\s*$",
        f"USE [{database}];",
        sql,
        count=1,
    )
    if f"USE [{database}];" not in rewritten:
        rewritten = f"USE [{database}];\nGO\n\n{sql}"
    return rewritten


def create_business_tables() -> None:
    import pyodbc

    server = settings.business_db_server or settings.db_server
    database = settings.business_db_name
    connection_string = (
        f"DRIVER={{{settings.db_driver}}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={settings.db_user};"
        f"PWD={settings.db_password};"
        f"TrustServerCertificate={settings.db_trust_server_certificate};"
        f"Encrypt={settings.db_encrypt};"
    )
    sql_path = ROOT / "sql" / "15_create_delivery_tables.sql"
    sql = prepare_sql_for_database(sql_path.read_text(encoding="utf-8"), database)
    batches = split_batches(sql)

    with pyodbc.connect(connection_string, autocommit=True) as connection:
        cursor = connection.cursor()
        for batch in batches:
            cursor.execute(batch)
        cursor.execute(
            """
            SELECT name
            FROM sys.tables
            WHERE name IN (
                N'delivery_riders',
                N'delivery_orders',
                N'delivery_status_history',
                N'delivery_customer_locations',
                N'delivery_rider_locations'
            )
            ORDER BY name
            """
        )
        found = [row[0] for row in cursor.fetchall()]

    print(f"Delivery tables are ready in {database} on {server}: {', '.join(found)}")
    missing = {
        "delivery_riders",
        "delivery_orders",
        "delivery_status_history",
        "delivery_customer_locations",
        "delivery_rider_locations",
    } - set(found)
    if missing:
        raise RuntimeError(f"Tables still missing in {database}: {', '.join(sorted(missing))}")


def main() -> int:
    try:
        create_business_tables()
        from scripts.seed_delivery_permissions import seed

        seed()
    except Exception as exc:
        print(f"Delivery setup failed: {exc}")
        return 1
    print("Delivery module setup completed. Existing users must sign in again.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
