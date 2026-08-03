"""List columns on V_FIN_SALE_DISC_NEW2 for a site .env."""

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
        rows = conn.execute(
            text(
                """
                SELECT c.name
                FROM sys.columns c
                JOIN sys.views v ON c.object_id = v.object_id
                WHERE v.name = 'V_FIN_SALE_DISC_NEW2'
                ORDER BY c.column_id
                """
            )
        ).fetchall()
        print(cfg.business_db_name, ":", [r[0] for r in rows])


if __name__ == "__main__":
    main()
