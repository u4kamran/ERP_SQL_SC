"""Inspect V_FIN_SALE_DISC_NEW2 definition and date column types."""

from __future__ import annotations

import sys
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


class Probe(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(sys.argv[1]),
        case_sensitive=False,
        extra="ignore",
    )
    db_server: str
    db_user: str
    db_password: str
    business_db_server: str = ""
    business_db_name: str = "nsds2626"
    db_driver: str = "ODBC Driver 18 for SQL Server"
    db_trust_server_certificate: str = "yes"
    db_encrypt: str = "no"


def main() -> None:
    cfg = Probe()
    server = cfg.business_db_server or cfg.db_server
    odbc = (
        f"DRIVER={{{cfg.db_driver}}};SERVER={server};DATABASE={cfg.business_db_name};"
        f"UID={cfg.db_user};PWD={cfg.db_password};"
        f"TrustServerCertificate={cfg.db_trust_server_certificate};Encrypt={cfg.db_encrypt};"
    )
    engine = create_engine(f"mssql+pyodbc:///?odbc_connect={quote_plus(odbc)}")
    with engine.connect() as conn:
        print("===", cfg.business_db_name, "===")
        cols = conn.execute(
            text(
                """
                SELECT c.name, t.name AS type_name, c.max_length, c.precision, c.scale
                FROM sys.columns c
                JOIN sys.views v ON c.object_id = v.object_id
                JOIN sys.types t ON c.user_type_id = t.user_type_id
                WHERE v.name = 'V_FIN_SALE_DISC_NEW2'
                ORDER BY c.column_id
                """
            )
        ).fetchall()
        for row in cols:
            print("column:", tuple(row))

        view_sql = conn.execute(
            text(
                """
                SELECT m.definition
                FROM sys.sql_modules m
                JOIN sys.views v ON m.object_id = v.object_id
                WHERE v.name = 'V_FIN_SALE_DISC_NEW2'
                """
            )
        ).scalar()
        if view_sql:
            print("\nVIEW DEFINITION (first 2500 chars):")
            print(view_sql[:2500])

        # sample date values
        for col in ("DOC_DATE_T", "DOC_DATE"):
            try:
                rows = conn.execute(
                    text(
                        f"""
                        SELECT TOP 5 {col}, COUNT(*) OVER() AS total
                        FROM dbo.V_FIN_SALE_DISC_NEW2
                        WHERE INV_ID BETWEEN 1 AND 999999999
                        ORDER BY {col} DESC
                        """
                    )
                ).fetchall()
                print(f"\nSample {col}:")
                for r in rows:
                    print(" ", r[0], "total rows sample from:", r[1] if len(r) > 1 else "")
            except Exception as exc:
                print(f"\n{col} sample error:", exc)

        # yesterday single-day test
        from datetime import datetime, timedelta

        now = datetime.now()
        start_h = 8
        bd = now.date() - timedelta(days=1)
        y_start = datetime.combine(bd, datetime.min.time().replace(hour=start_h))
        y_end = datetime.combine(now.date(), datetime.min.time().replace(hour=5))

        for col in ("DOC_DATE_T", "DOC_DATE"):
            try:
                cnt = conn.execute(
                    text(
                        f"""
                        SELECT COUNT(*) FROM dbo.V_FIN_SALE_DISC_NEW2
                        WHERE INV_ID BETWEEN 1 AND 999999999
                          AND {col} BETWEEN :s AND :e
                        """
                    ),
                    {"s": y_start, "e": y_end},
                ).scalar()
                print(f"\nYesterday business window via {col}: {cnt} rows ({y_start} -> {y_end})")
            except Exception as exc:
                print(f"\nYesterday test {col} error:", exc)


if __name__ == "__main__":
    main()
