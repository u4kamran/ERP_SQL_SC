"""Clone NAHSL2627 -> NKUM2627 using literal SQL paths (SQL 2008 safe)."""
from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text

sys.path.insert(0, r"D:\CursorProject\ahsteellab-arp")
from app.config.settings import get_settings

SOURCE_DB = "NAHSL2627"
TARGET_DB = "NKUM2627"
# Local writable path on this SQL host
BACKUP_DIR = Path(r"D:\CursorProject\backups\kumashi-stage2")
BACKUP_PATH = BACKUP_DIR / "NAHSL2627_copy_for_NKUM2627.bak"


def main() -> int:
    settings = get_settings()
    password = settings.db_password
    if hasattr(password, "get_secret_value"):
        password = password.get_secret_value()
    server = settings.business_db_server or settings.db_server
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    bak = str(BACKUP_PATH).replace("'", "''")

    url = (
        f"mssql+pyodbc://{quote_plus(settings.db_user)}:{quote_plus(password)}"
        f"@{server}/master?driver=ODBC+Driver+18+for+SQL+Server"
        f"&TrustServerCertificate=yes&Encrypt=no"
    )
    engine = create_engine(url, isolation_level="AUTOCOMMIT")

    with engine.connect() as conn:
        existing = {
            r[0]
            for r in conn.execute(
                text(
                    "SELECT name FROM sys.databases WHERE name IN "
                    "('NAHSL2627','NKUM2627','NAHSL2627_AUTH','NKUM2627_AUTH')"
                )
            )
        }
        print("Present:", sorted(existing))
        if SOURCE_DB not in existing:
            print("FATAL: source missing")
            return 1
        if TARGET_DB in existing:
            print("FATAL: target already exists")
            return 1

        # Remove stale bak if any
        if BACKUP_PATH.exists():
            BACKUP_PATH.unlink()

        print(f"BACKUP {SOURCE_DB} -> {bak}")
        # Literal path — bind params unreliable for BACKUP/RESTORE on this driver
        conn.execute(
            text(
                f"BACKUP DATABASE [{SOURCE_DB}] TO DISK = N'{bak}' "
                "WITH COPY_ONLY, INIT, STATS = 5"
            )
        )
        print("Backup SQL finished; file exists:", BACKUP_PATH.exists(), "size:", BACKUP_PATH.stat().st_size if BACKUP_PATH.exists() else 0)

        if not BACKUP_PATH.exists():
            print("FATAL: bak file missing after BACKUP")
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
                new_physical = str(Path(parent) / f"{TARGET_DB}_log.ldf")
            moves.append((logical, new_physical))
            print(f"  MOVE [{logical}] -> {new_physical}")

        move_sql = ", ".join(
            f"MOVE N'{logical.replace(chr(39), chr(39)+chr(39))}' TO N'{phys.replace(chr(39), chr(39)+chr(39))}'"
            for logical, phys in moves
        )
        restore_sql = (
            f"RESTORE DATABASE [{TARGET_DB}] FROM DISK = N'{bak}' "
            f"WITH RECOVERY, STATS = 5, {move_sql}"
        )
        print("RESTORE starting...")
        result = conn.execute(text(restore_sql))
        cursor = getattr(result, "cursor", None)
        if cursor is not None:
            while cursor.nextset():
                pass

        state = conn.execute(
            text("SELECT state_desc FROM sys.databases WHERE name = :n"),
            {"n": TARGET_DB},
        ).scalar()
        src_state = conn.execute(
            text("SELECT state_desc FROM sys.databases WHERE name = :n"),
            {"n": SOURCE_DB},
        ).scalar()
        print("Target:", state, "Source:", src_state)
        if state != "ONLINE" or src_state != "ONLINE":
            return 1
        src_n = conn.execute(text(f"SELECT COUNT(*) FROM [{SOURCE_DB}].sys.tables")).scalar()
        dst_n = conn.execute(text(f"SELECT COUNT(*) FROM [{TARGET_DB}].sys.tables")).scalar()
        print(f"tables source={src_n} target={dst_n}")
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
