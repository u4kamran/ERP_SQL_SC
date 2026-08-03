"""Quick check: business DB + V_FIN_SALE_DISC_NEW2 for sales dashboard."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sqlalchemy import create_engine, text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--env-file",
        type=Path,
        help="Optional .env path (default: project .env)",
    )
    args = parser.parse_args()

    if args.env_file:
        from pydantic_settings import BaseSettings, SettingsConfigDict

        class _ProbeSettings(BaseSettings):
            model_config = SettingsConfigDict(
                env_file=str(args.env_file),
                env_file_encoding="utf-8",
                case_sensitive=False,
                extra="ignore",
            )
            db_server: str
            db_user: str
            db_password: str
            db_driver: str = "ODBC Driver 18 for SQL Server"
            db_trust_server_certificate: str = "yes"
            db_encrypt: str = "no"
            business_db_server: str = ""
            business_db_name: str = "nsds2626"

            @property
            def business_database_url(self) -> str:
                from urllib.parse import quote_plus

                server = self.business_db_server or self.db_server
                odbc_connect = (
                    f"DRIVER={{{self.db_driver}}};"
                    f"SERVER={server};"
                    f"DATABASE={self.business_db_name};"
                    f"UID={self.db_user};"
                    f"PWD={self.db_password};"
                    f"TrustServerCertificate={self.db_trust_server_certificate};"
                    f"Encrypt={self.db_encrypt};"
                )
                return f"mssql+pyodbc:///?odbc_connect={quote_plus(odbc_connect)}"

        cfg = _ProbeSettings()
        business_db_name = cfg.business_db_name
        business_db_server = cfg.business_db_server or cfg.db_server
        database_url = cfg.business_database_url
    else:
        from app.config.settings import get_settings

        get_settings.cache_clear()
        from app.config import settings as settings_mod

        settings_mod.settings = get_settings()
        settings = settings_mod.settings
        business_db_name = settings.business_db_name
        business_db_server = settings.business_db_server or settings.db_server
        database_url = settings.business_database_url

    print(f"Business DB: {business_db_name} @ {business_db_server}")
    engine = create_engine(database_url)
    with engine.connect() as conn:
        oid = conn.execute(text("SELECT OBJECT_ID('dbo.V_FIN_SALE_DISC_NEW2')")).scalar()
        print(f"V_FIN_SALE_DISC_NEW2 exists: {bool(oid)} (oid={oid})")
        if not oid:
            rows = conn.execute(
                text("SELECT name FROM sys.views WHERE name LIKE '%SALE%' ORDER BY name")
            ).fetchall()
            print("Sale-related views:", [r[0] for r in rows[:30]])
            return 1

    if args.env_file:
        from app.repositories.sales_dashboard_repository import SalesDashboardRepository
        from app.utils.business_day import default_report_range
        from sqlalchemy.orm import sessionmaker

        Session = sessionmaker(bind=engine)
        db = Session()
        try:
            start, end = default_report_range()
            print(f"Default range: {start} -> {end}")
            repo = SalesDashboardRepository(db)
            summary = repo.get_summary(start, end, total_days=1)
            print("Summary OK:", summary)
            print(f"Daily rows: {len(repo.get_daily_sales(start, end))}")
            print(f"Top invoices: {len(repo.get_top_invoices(start, end, limit=3))}")
            print(f"Day-wise rows: {len(repo.get_day_wise_sales(start, end))}")
        except Exception as exc:
            print("QUERY ERROR:", type(exc).__name__, exc)
            return 1
        finally:
            db.close()
    else:
        from app.database.business_session import BusinessSessionLocal
        from app.repositories.sales_dashboard_repository import SalesDashboardRepository
        from app.utils.business_day import default_report_range

        start, end = default_report_range()
        print(f"Default range: {start} -> {end}")
        db = BusinessSessionLocal()
        try:
            repo = SalesDashboardRepository(db)
            summary = repo.get_summary(start, end, total_days=1)
            print("Summary OK:", summary)
            print(f"Daily rows: {len(repo.get_daily_sales(start, end))}")
            print(f"Top invoices: {len(repo.get_top_invoices(start, end, limit=3))}")
            print(f"Day-wise rows: {len(repo.get_day_wise_sales(start, end))}")
        except Exception as exc:
            print("QUERY ERROR:", type(exc).__name__, exc)
            return 1
        finally:
            db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
