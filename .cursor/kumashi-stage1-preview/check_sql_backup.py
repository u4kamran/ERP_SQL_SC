"""Check backup artifacts on the SQL Server host (not local disk)."""
from __future__ import annotations

import sys
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text

sys.path.insert(0, r"D:\CursorProject\ahsteellab-arp")
from app.config.settings import get_settings

s = get_settings()
pwd = s.db_password
if hasattr(pwd, "get_secret_value"):
    pwd = pwd.get_secret_value()
server = s.business_db_server or s.db_server
url = (
    f"mssql+pyodbc://{quote_plus(s.db_user)}:{quote_plus(pwd)}"
    f"@{server}/master?driver=ODBC+Driver+18+for+SQL+Server"
    f"&TrustServerCertificate=yes&Encrypt=no"
)
eng = create_engine(url, isolation_level="AUTOCOMMIT")
bak = (
    r"C:\Program Files\Microsoft SQL Server\MSSQL10.MSSQLSERVER\MSSQL\Backup"
    r"\NAHSL2627_copy_for_NKUM2627.bak"
)
with eng.connect() as c:
    print("SERVER", server)
    # @@SERVERNAME / hostname
    print("SERVERNAME", c.execute(text("SELECT @@SERVERNAME")).scalar())
    print("MACHINE", c.execute(text("SELECT SERVERPROPERTY('MachineName')")).scalar())
    rows = c.execute(
        text("EXEC master.dbo.xp_dirtree :p, 1, 1"),
        {
            "p": r"C:\Program Files\Microsoft SQL Server\MSSQL10.MSSQLSERVER\MSSQL\Backup"
        },
    ).fetchall()
    print("BACKUP_FOLDER_ENTRIES", len(rows))
    for r in rows[:30]:
        print(" ", r)
    exists = c.execute(
        text("EXEC master.dbo.xp_fileexist :p"),
        {"p": bak},
    ).fetchone()
    print("FILEEXIST", exists)
