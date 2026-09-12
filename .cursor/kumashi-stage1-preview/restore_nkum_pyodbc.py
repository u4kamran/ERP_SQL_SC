"""Drop stuck NKUM2627 (RESTORING only) and restore cleanly with pyodbc long timeout.
Never touches NAHSL2627.
"""
from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import quote_plus

import pyodbc

sys.path.insert(0, r"D:\CursorProject\ahsteellab-arp")
from app.config.settings import get_settings

TARGET = "NKUM2627"
SOURCE = "NAHSL2627"
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
    conn_str = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={server};"
        f"DATABASE=master;"
        f"UID={s.db_user};"
        f"PWD={pwd};"
        f"TrustServerCertificate=yes;"
        f"Encrypt=no;"
    )
    conn = pyodbc.connect(conn_str, autocommit=True, timeout=0)
    conn.timeout = 0
    cur = conn.cursor()

    cur.execute(
        "SELECT name, state_desc FROM sys.databases WHERE name IN (?, ?, ?, ?)",
        SOURCE,
        TARGET,
        "NAHSL2627_AUTH",
        "NKUM2627_AUTH",
    )
    print("Before:", cur.fetchall())

    cur.execute("SELECT state_desc FROM sys.databases WHERE name = ?", TARGET)
    row = cur.fetchone()
    if row and row[0] == "RESTORING":
        print("Dropping stuck RESTORING database", TARGET)
        cur.execute(f"DROP DATABASE [{TARGET}]")

    cur.execute("SELECT name FROM sys.databases WHERE name = ?", TARGET)
    if cur.fetchone():
        print("FATAL: target still exists")
        return 1

    print("HEADERONLY...")
    cur.execute(f"RESTORE HEADERONLY FROM DISK = N'{BAK.replace(chr(39), chr(39)*2)}'")
    cols = [c[0] for c in cur.description]
    header = cur.fetchone()
    info = dict(zip(cols, header)) if header else {}
    print(
        "BackupType=",
        info.get("BackupType"),
        "DatabaseName=",
        info.get("DatabaseName"),
        "Position=",
        info.get("Position"),
        "Compressed=",
        info.get("Compressed"),
    )

    cur.execute(f"RESTORE FILELISTONLY FROM DISK = N'{BAK.replace(chr(39), chr(39)*2)}'")
    files = cur.fetchall()
    moves = []
    for f in files:
        logical, physical, ftype = f[0], f[1], str(f[2]).upper()
        parent = str(Path(physical).parent)
        if ftype == "D":
            new_p = str(Path(parent) / f"{TARGET}.mdf")
        else:
            new_p = str(Path(parent) / f"{TARGET}_{Path(physical).name}")
        print(" MOVE", logical, "->", new_p)
        moves.append((logical, new_p))

    move_sql = ", ".join(f"MOVE N'{a}' TO N'{b}'" for a, b in moves)
    sql = (
        f"RESTORE DATABASE [{TARGET}] FROM DISK = N'{BAK.replace(chr(39), chr(39)*2)}' "
        f"WITH RECOVERY, STATS = 5, {move_sql}"
    )
    print("RESTORE begin (may take several minutes)...")
    cur.execute(sql)
    while True:
        try:
            if not cur.nextset():
                break
        except pyodbc.ProgrammingError:
            break
    # drain messages
    while cur.messages:
        print("MSG", cur.messages.pop(0))

    cur.execute("SELECT state_desc FROM sys.databases WHERE name = ?", TARGET)
    tstate = cur.fetchone()[0]
    cur.execute("SELECT state_desc FROM sys.databases WHERE name = ?", SOURCE)
    sstate = cur.fetchone()[0]
    print("After NKUM2627=", tstate, "NAHSL2627=", sstate)

    if tstate != "ONLINE":
        return 1

    cur.execute(f"SELECT COUNT(*) FROM [{SOURCE}].sys.tables")
    st = cur.fetchone()[0]
    cur.execute(f"SELECT COUNT(*) FROM [{TARGET}].sys.tables")
    dt = cur.fetchone()[0]
    print(f"tables source={st} target={dt}")
    cur.close()
    conn.close()
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
