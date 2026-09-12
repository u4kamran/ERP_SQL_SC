"""Probe SQL paths for NKUM2627 clone."""
from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text

sys.path.insert(0, r"D:\CursorProject\ahsteellab-arp")
from app.config.settings import get_settings

s = get_settings()
p = s.db_password
pwd = p.get_secret_value() if hasattr(p, "get_secret_value") else p
server = s.business_db_server or s.db_server
url = (
    f"mssql+pyodbc://{quote_plus(s.db_user)}:{quote_plus(pwd)}"
    f"@{server}/master?driver=ODBC+Driver+18+for+SQL+Server"
    f"&TrustServerCertificate=yes&Encrypt=no"
)
eng = create_engine(url)
with eng.connect() as c:
    print("SERVER", server)
    rows = c.execute(
        text(
            "SELECT physical_name FROM sys.master_files "
            "WHERE database_id = DB_ID('NAHSL2627')"
        )
    ).fetchall()
    for r in rows:
        print("FILE", r[0])
    try:
        r = c.execute(
            text(
                "EXEC master.dbo.xp_instance_regread "
                "N'HKEY_LOCAL_MACHINE', "
                "N'Software\\Microsoft\\MSSQLServer\\MSSQLServer', "
                "N'BackupDirectory'"
            )
        ).fetchone()
        print("BACKUP_DIR", r)
    except Exception as e:
        print("BACKUP_DIR_ERR", e)
    # size
    size = c.execute(
        text(
            "SELECT CAST(SUM(size) * 8.0 / 1024 AS INT) "
            "FROM sys.master_files WHERE database_id = DB_ID('NAHSL2627')"
        )
    ).scalar()
    print("SIZE_MB", size)
