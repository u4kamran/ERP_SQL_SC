"""Inspect FIN_INV_M date columns on ERP vs ARP."""

from __future__ import annotations

import sys
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus


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


def inspect(env_path: str) -> None:
    class _Cfg(Probe):
        model_config = SettingsConfigDict(
            env_file=env_path,
            case_sensitive=False,
            extra="ignore",
        )

    cfg = _Cfg()
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
                SELECT c.name, t.name AS type_name
                FROM sys.columns c
                JOIN sys.tables tb ON c.object_id = tb.object_id
                JOIN sys.types t ON c.user_type_id = t.user_type_id
                WHERE tb.name = 'FIN_INV_M'
                  AND c.name LIKE 'DOC_DATE%'
                ORDER BY c.column_id
                """
            )
        ).fetchall()
        print("FIN_INV_M date columns:", cols)

        for col in [r[0] for r in cols]:
            rows = conn.execute(
                text(
                    f"""
                    SELECT TOP 3 {col}, COUNT(*) OVER() AS total
                    FROM dbo.FIN_INV_M
                    WHERE DOC_DATE IS NOT NULL OR DOC_DATE_T IS NOT NULL
                    ORDER BY {col} DESC
                    """
                )
            ).fetchall()
            print(f"Sample {col}:", [r[0] for r in rows], "total:", rows[0][1] if rows else 0)

        # compare DOC_DATE vs DOC_DATE_T if both exist
        names = {r[0] for r in cols}
        if {"DOC_DATE", "DOC_DATE_T"}.issubset(names):
            diff = conn.execute(
                text(
                    """
                    SELECT COUNT(*) FROM dbo.FIN_INV_M
                    WHERE DOC_DATE IS NOT NULL AND DOC_DATE_T IS NOT NULL
                      AND CAST(DOC_DATE AS DATE) <> CAST(DOC_DATE_T AS DATE)
                    """
                )
            ).scalar()
            null_t = conn.execute(text("SELECT COUNT(*) FROM dbo.FIN_INV_M WHERE DOC_DATE_T IS NULL")).scalar()
            print("Rows where date part differs:", diff)
            print("Rows where DOC_DATE_T is NULL:", null_t)

        # single-day counts with date-only logic
        for label, sql in [
            ("yesterday date equality", "SELECT COUNT(*) FROM dbo.V_FIN_SALE_DISC_NEW2 WHERE INV_ID BETWEEN 1 AND 999999999 AND CAST(DOC_DATE AS DATE) = CAST(DATEADD(day,-1,GETDATE()) AS DATE)"),
            ("july 20 date equality", "SELECT COUNT(*) FROM dbo.V_FIN_SALE_DISC_NEW2 WHERE INV_ID BETWEEN 1 AND 999999999 AND CAST(DOC_DATE AS DATE) = '2026-07-20'"),
            (
                "yesterday business window via FIN_INV_M.DOC_DATE_T",
                """
                SELECT COUNT(*)
                FROM dbo.FIN_INV_M m
                JOIN dbo.FIN_INV_D d ON d.SERIAL_NO = m.SERIAL_NO
                WHERE d.INV_ID BETWEEN 1 AND 999999999
                  AND m.DOC_DATE_T BETWEEN DATEADD(hour, 8, CAST(CAST(DATEADD(day,-1,GETDATE()) AS DATE) AS DATETIME))
                                       AND DATEADD(hour, 5, CAST(CAST(GETDATE() AS DATE) AS DATETIME))
                """,
            ),
        ]:
            try:
                cnt = conn.execute(text(sql)).scalar()
                print(label + ":", cnt)
            except Exception as exc:
                print(label + " error:", str(exc).split("\n")[0][:120])


if __name__ == "__main__":
    inspect(sys.argv[1])
