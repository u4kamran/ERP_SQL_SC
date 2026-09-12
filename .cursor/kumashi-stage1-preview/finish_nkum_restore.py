"""Finish or diagnose NKUM2627 restore. Does not touch NAHSL2627."""
from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text

sys.path.insert(0, r"D:\CursorProject\ahsteellab-arp")
from app.config.settings import get_settings

TARGET_DB = "NKUM2627"
BAK = (
    r"C:\Program Files\Microsoft SQL Server\MSSQL10.MSSQLSERVER\MSSQL\Backup"
    r"\NAHSL2627_backup_2026_09_10_161158_0686549.bak"
)


def main() -> int:
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
    bak = BAK.replace("'", "''")

    with eng.connect() as conn:
        row = conn.execute(
            text(
                "SELECT name, state_desc FROM sys.databases WHERE name IN "
                "('NAHSL2627','NKUM2627','NAHSL2627_AUTH','NKUM2627_AUTH')"
            )
        ).fetchall()
        print("DBS:", row)

        state = conn.execute(
            text("SELECT state_desc FROM sys.databases WHERE name = :n"),
            {"n": TARGET_DB},
        ).scalar()
        print("NKUM state:", state)

        if state == "RESTORING":
            rows = conn.execute(text(f"RESTORE FILELISTONLY FROM DISK = N'{bak}'")).fetchall()
            moves = []
            for r in rows:
                logical = r[0]
                physical = r[1]
                ftype = str(r[2]).upper()
                parent = str(Path(physical).parent)
                if ftype == "D":
                    new_physical = str(Path(parent) / f"{TARGET_DB}.mdf")
                else:
                    new_physical = str(Path(parent) / f"{TARGET_DB}_{Path(physical).name}")
                moves.append((logical, new_physical))
            move_sql = ", ".join(
                f"MOVE N'{a.replace(chr(39), chr(39)*2)}' TO N'{b.replace(chr(39), chr(39)*2)}'"
                for a, b in moves
            )
            # REPLACE + RECOVERY to finish stuck restore
            sql = (
                f"RESTORE DATABASE [{TARGET_DB}] FROM DISK = N'{bak}' "
                f"WITH REPLACE, RECOVERY, STATS = 5, {move_sql}"
            )
            print("Re-running RESTORE WITH REPLACE, RECOVERY...")
            result = conn.execute(text(sql))
            cur = getattr(result, "cursor", None)
            if cur is not None:
                while cur.nextset():
                    pass

        state = conn.execute(
            text("SELECT state_desc FROM sys.databases WHERE name = :n"),
            {"n": TARGET_DB},
        ).scalar()
        src = conn.execute(
            text("SELECT state_desc FROM sys.databases WHERE name = :n"),
            {"n": "NAHSL2627"},
        ).scalar()
        print("Final NKUM2627:", state, "NAHSL2627:", src)
        if state == "ONLINE":
            st = conn.execute(text("SELECT COUNT(*) FROM [NAHSL2627].sys.tables")).scalar()
            dt = conn.execute(text("SELECT COUNT(*) FROM [NKUM2627].sys.tables")).scalar()
            print(f"tables source={st} target={dt}")
            return 0
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
