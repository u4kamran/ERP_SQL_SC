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


def create_business_tables() -> None:
    import pyodbc

    server = settings.business_db_server or settings.db_server
    connection_string = (
        f"DRIVER={{{settings.db_driver}}};"
        f"SERVER={server};"
        f"DATABASE={settings.business_db_name};"
        f"UID={settings.db_user};"
        f"PWD={settings.db_password};"
        f"TrustServerCertificate={settings.db_trust_server_certificate};"
        f"Encrypt={settings.db_encrypt};"
    )
    sql_path = ROOT / "sql" / "15_create_delivery_tables.sql"
    batches = split_batches(sql_path.read_text(encoding="utf-8"))

    with pyodbc.connect(connection_string, autocommit=True) as connection:
        cursor = connection.cursor()
        for batch in batches:
            cursor.execute(batch)

    print(f"Delivery tables are ready in {settings.business_db_name} on {server}.")


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
