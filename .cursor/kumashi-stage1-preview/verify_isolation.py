"""Verify isolation: AL HARAM DBs online; KUMASHI DBs online and distinct."""
from __future__ import annotations

import sys
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text

sys.path.insert(0, r"D:\CursorProject\ahsteellab-kumashi")
from app.config.settings import get_settings

s = get_settings()
pwd = s.db_password
if hasattr(pwd, "get_secret_value"):
    pwd = pwd.get_secret_value()
url = (
    f"mssql+pyodbc://{quote_plus(s.db_user)}:{quote_plus(pwd)}"
    f"@{s.db_server}/master?driver=ODBC+Driver+18+for+SQL+Server"
    f"&TrustServerCertificate=yes&Encrypt=no"
)
eng = create_engine(url)
with eng.connect() as c:
    rows = c.execute(
        text(
            "SELECT name, state_desc FROM sys.databases WHERE name IN "
            "('NAHSL2627','NAHSL2627_AUTH','NKUM2627','NKUM2627_AUTH') ORDER BY name"
        )
    ).fetchall()
    for r in rows:
        print(f"{r[0]}={r[1]}")
    print("ENV_AUTH", s.db_name)
    print("ENV_BIZ", s.business_db_name)
    print("ENV_APP", s.app_name)
    print("ENV_SITE", s.site_code)
    print("ENV_PORT", s.port)
