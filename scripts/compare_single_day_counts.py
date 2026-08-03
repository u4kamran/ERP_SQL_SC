"""Compare single-day counts for ARP using DOC_DATE vs DOC_DATE_T."""

from __future__ import annotations

import sys
from datetime import datetime

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


def main() -> None:
    cfg = Probe()
    server = cfg.business_db_server or cfg.db_server
    odbc = (
        f"DRIVER={{{cfg.db_driver}}};SERVER={server};DATABASE={cfg.business_db_name};"
        f"UID={cfg.db_user};PWD={cfg.db_password};"
        f"TrustServerCertificate={cfg.db_trust_server_certificate};Encrypt={cfg.db_encrypt};"
    )
    engine = create_engine(f"mssql+pyodbc:///?odbc_connect={quote_plus(odbc)}")
    day = datetime(2026, 7, 20)
    start = datetime(2026, 7, 20, 8, 0, 0)
    end = datetime(2026, 7, 21, 5, 0, 0)
    tests = {
        "DOC_DATE between business window": """
            SELECT COUNT(*) FROM dbo.V_FIN_SALE_DISC_NEW2
            WHERE INV_ID BETWEEN 1 AND 999999999 AND DOC_DATE BETWEEN :s AND :e
        """,
        "CAST(DOC_DATE AS DATE) = 2026-07-20": """
            SELECT COUNT(*) FROM dbo.V_FIN_SALE_DISC_NEW2
            WHERE INV_ID BETWEEN 1 AND 999999999 AND CAST(DOC_DATE AS DATE) = '2026-07-20'
        """,
        "FIN_INV_M.DOC_DATE_T between business window": """
            SELECT COUNT(*)
            FROM dbo.FIN_INV_M m
            JOIN dbo.FIN_INV_D d ON d.SERIAL_NO = m.SERIAL_NO
            WHERE d.INV_ID BETWEEN 1 AND 999999999
              AND m.DOC_DATE_T BETWEEN :s AND :e
        """,
        "CAST(FIN_INV_M.DOC_DATE AS DATE) = 2026-07-20": """
            SELECT COUNT(*)
            FROM dbo.FIN_INV_M m
            JOIN dbo.FIN_INV_D d ON d.SERIAL_NO = m.SERIAL_NO
            WHERE d.INV_ID BETWEEN 1 AND 999999999
              AND CAST(m.DOC_DATE AS DATE) = '2026-07-20'
        """,
    }
    with engine.connect() as conn:
        print(cfg.business_db_name, "single day 20-Jul-2026")
        for label, sql in tests.items():
            try:
                params = {"s": start, "e": end} if ":s" in sql else {}
                print(f"  {label}: {conn.execute(text(sql), params).scalar()}")
            except Exception as exc:
                print(f"  {label}: ERROR {exc}")


if __name__ == "__main__":
    main()
