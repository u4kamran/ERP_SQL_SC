"""Stage 1 read-only catalog inspect. SELECT only. Does not create or alter databases."""
from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text

ROOT = Path(r"D:\CursorProject\ahsteellab-arp")
sys.path.insert(0, str(ROOT))

from app.config.settings import get_settings  # noqa: E402

settings = get_settings()
password = settings.db_password
if hasattr(password, "get_secret_value"):
    password = password.get_secret_value()

url = (
    f"mssql+pyodbc://{quote_plus(settings.db_user)}:{quote_plus(password)}"
    f"@{settings.db_server}/master?driver=ODBC+Driver+18+for+SQL+Server"
    f"&TrustServerCertificate=yes&Encrypt=no"
)
engine = create_engine(url)

with engine.connect() as conn:
    rows = conn.execute(
        text(
            "SELECT name FROM sys.databases WHERE name IN "
            "('NAHSL2627','NAHSL2627_AUTH','NKUM2627','NKUM2627_AUTH',"
            "'nsds2626','NSDS2626_AUTH') ORDER BY name"
        )
    ).fetchall()
    print("DATABASES_PRESENT:", [r[0] for r in rows])
    for db in ("NAHSL2627", "NAHSL2627_AUTH"):
        tables = conn.execute(text(f"SELECT COUNT(*) FROM [{db}].sys.tables")).scalar()
        views = conn.execute(text(f"SELECT COUNT(*) FROM [{db}].sys.views")).scalar()
        procs = conn.execute(text(f"SELECT COUNT(*) FROM [{db}].sys.procedures")).scalar()
        funcs = conn.execute(
            text(
                f"SELECT COUNT(*) FROM [{db}].sys.objects "
                "WHERE type IN ('FN','IF','TF')"
            )
        ).scalar()
        trig = conn.execute(text(f"SELECT COUNT(*) FROM [{db}].sys.triggers")).scalar()
        print(
            f"{db}: tables={tables} views={views} procedures={procs} "
            f"functions={funcs} triggers={trig}"
        )
    top_tables = conn.execute(
        text(
            "SELECT TOP 25 t.name FROM [NAHSL2627].sys.tables t "
            "ORDER BY t.name"
        )
    ).fetchall()
    print("NAHSL2627_SAMPLE_TABLES:", [r[0] for r in top_tables])
    auth_tables = conn.execute(
        text(
            "SELECT s.name + '.' + t.name FROM [NAHSL2627_AUTH].sys.tables t "
            "JOIN [NAHSL2627_AUTH].sys.schemas s ON s.schema_id = t.schema_id "
            "ORDER BY s.name, t.name"
        )
    ).fetchall()
    print("NAHSL2627_AUTH_TABLES:", [r[0] for r in auth_tables])
