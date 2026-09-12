"""Restore today's NAHSL2627 .bak as new database NKUM2627. Does not touch NAHSL2627."""
from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text

sys.path.insert(0, r"D:\CursorProject\ahsteellab-arp")
from app.config.settings import get_settings

SOURCE_DB = "NAHSL2627"
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
        existing = {
            r[0]
            for r in conn.execute(
                text(
                    "SELECT name FROM sys.databases WHERE name IN "
                    "('NAHSL2627','NKUM2627')"
                )
            )
        }
        print("Present:", sorted(existing))
        if TARGET_DB in existing:
            print("FATAL: NKUM2627 already exists")
            return 1
        if SOURCE_DB not in existing:
            print("FATAL: source missing")
            return 1

        exists = conn.execute(text(f"EXEC master.dbo.xp_fileexist N'{bak}'")).fetchone()
        print("BAK fileexist:", exists)
        if not exists or int(exists[0]) != 1:
            print("FATAL: bak missing on SQL host")
            return 1

        rows = conn.execute(text(f"RESTORE FILELISTONLY FROM DISK = N'{bak}'")).fetchall()
        moves = []
        for row in rows:
            logical = row[0]
            physical = row[1]
            ftype = str(row[2]).upper()
            parent = str(Path(physical).parent)
            if ftype == "D":
                new_physical = str(Path(parent) / f"{TARGET_DB}.mdf")
            else:
                # handle multiple log files uniquely
                stem = Path(physical).name
                new_physical = str(Path(parent) / f"{TARGET_DB}_{stem}")
            print(f"  {logical} ({ftype}) -> {new_physical}")
            moves.append((logical, new_physical))

        move_sql = ", ".join(
            f"MOVE N'{a.replace(chr(39), chr(39)*2)}' TO N'{b.replace(chr(39), chr(39)*2)}'"
            for a, b in moves
        )
        sql = (
            f"RESTORE DATABASE [{TARGET_DB}] FROM DISK = N'{bak}' "
            f"WITH RECOVERY, STATS = 5, {move_sql}"
        )
        print("RESTORE starting from today's AL HARAM bak...")
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
            {"n": SOURCE_DB},
        ).scalar()
        print("NKUM2627:", state, "NAHSL2627:", src)
        if state != "ONLINE" or src != "ONLINE":
            return 1
        st = conn.execute(text(f"SELECT COUNT(*) FROM [{SOURCE_DB}].sys.tables")).scalar()
        dt = conn.execute(text(f"SELECT COUNT(*) FROM [{TARGET_DB}].sys.tables")).scalar()
        print(f"tables source={st} target={dt}")
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
