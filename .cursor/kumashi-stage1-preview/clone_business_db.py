"""Stage 2: CREATE NKUM2627 as full clone of NAHSL2627 via COPY_ONLY backup + restore.
Does NOT modify NAHSL2627. Aborts if NKUM2627 already exists.
"""
from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text

# Read credentials from AL HARAM .env (source of truth for SQL access) without loading KUMASHI yet.
ARP_ROOT = Path(r"D:\CursorProject\ahsteellab-arp")
sys.path.insert(0, str(ARP_ROOT))

from app.config.settings import get_settings  # noqa: E402

SOURCE_DB = "NAHSL2627"
TARGET_DB = "NKUM2627"
# Path must be on the SQL Server host (shaheenhp), not necessarily this PC's D: drive.
BACKUP_PATH = Path(
    r"C:\Program Files\Microsoft SQL Server\MSSQL10.MSSQLSERVER\MSSQL\Backup"
    r"\NAHSL2627_copy_for_NKUM2627.bak"
)


def pwd(settings) -> str:
    p = settings.db_password
    return p.get_secret_value() if hasattr(p, "get_secret_value") else str(p)


def main() -> int:
    settings = get_settings()
    server = settings.business_db_server or settings.db_server
    user = settings.db_user
    password = pwd(settings)

    BACKUP_DIR = BACKUP_PATH.parent
    # Backup folder already exists on SQL Server; do not create Program Files dirs from here.
    bak = str(BACKUP_PATH)

    url = (
        f"mssql+pyodbc://{quote_plus(user)}:{quote_plus(password)}"
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
                    "(:s, :t, 'NAHSL2627_AUTH', 'NKUM2627_AUTH')"
                ),
                {"s": SOURCE_DB, "t": TARGET_DB},
            ).fetchall()
        }
        print("Present:", sorted(existing))
        if SOURCE_DB not in existing:
            print(f"FATAL: source {SOURCE_DB} missing")
            return 1
        if TARGET_DB in existing:
            print(f"FATAL: {TARGET_DB} already exists — abort (will not overwrite)")
            return 1

        print(f"BACKUP {SOURCE_DB} COPY_ONLY -> {bak}")
        conn.execute(
            text(
                f"BACKUP DATABASE [{SOURCE_DB}] TO DISK = :path "
                "WITH COPY_ONLY, INIT, STATS = 10"
            ),
            {"path": bak},
        )
        print("Backup complete")

        rows = conn.execute(
            text("RESTORE FILELISTONLY FROM DISK = :path"),
            {"path": bak},
        ).fetchall()
        # columns: LogicalName, PhysicalName, Type, ...
        moves = []
        for row in rows:
            logical = row[0]
            physical = row[1]
            ftype = row[2]  # D or L
            ext = ".mdf" if str(ftype).upper() == "D" else ".ldf"
            # Keep files next to original folder when possible
            parent = str(Path(physical).parent)
            new_name = f"{TARGET_DB}{'' if str(ftype).upper() == 'D' else '_log'}{ext}"
            if str(ftype).upper() == "D":
                new_physical = str(Path(parent) / f"{TARGET_DB}.mdf")
            else:
                new_physical = str(Path(parent) / f"{TARGET_DB}_log.ldf")
            moves.append((logical, new_physical))
            print(f"  MOVE [{logical}] -> {new_physical}")

        move_sql = ", ".join(
            f"MOVE N'{logical}' TO N'{physical}'" for logical, physical in moves
        )
        restore_sql = (
            f"RESTORE DATABASE [{TARGET_DB}] FROM DISK = :path "
            f"WITH RECOVERY, STATS = 10, {move_sql}"
        )
        print(f"RESTORE as {TARGET_DB} ...")
        result = conn.execute(text(restore_sql), {"path": bak})
        cursor = getattr(result, "cursor", None)
        if cursor is not None:
            while cursor.nextset():
                pass

        state = conn.execute(
            text("SELECT state_desc FROM sys.databases WHERE name = :n"),
            {"n": TARGET_DB},
        ).scalar()
        print(f"Target state: {state}")
        if state != "ONLINE":
            print("FATAL: target not ONLINE")
            return 1

        # Verify AL HARAM still present and online
        src_state = conn.execute(
            text("SELECT state_desc FROM sys.databases WHERE name = :n"),
            {"n": SOURCE_DB},
        ).scalar()
        print(f"Source {SOURCE_DB} state: {src_state}")
        if src_state != "ONLINE":
            print("WARNING: source not ONLINE after clone")
            return 1

        src_tables = conn.execute(
            text(f"SELECT COUNT(*) FROM [{SOURCE_DB}].sys.tables")
        ).scalar()
        dst_tables = conn.execute(
            text(f"SELECT COUNT(*) FROM [{TARGET_DB}].sys.tables")
        ).scalar()
        print(f"Table count source={src_tables} target={dst_tables}")

    print("OK: NKUM2627 created. NAHSL2627 untouched.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
