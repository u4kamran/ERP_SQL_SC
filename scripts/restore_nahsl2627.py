"""One-off restore NAHSL2627 from .bak on SQL Server."""
from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config.settings import get_settings  # noqa: E402

get_settings.cache_clear()
settings = get_settings()

SERVER = settings.business_db_server or settings.db_server
USER = settings.db_user
PASSWORD = settings.db_password
DATABASE = "NAHSL2627"
BACKUP_PATH = r"E:\NAHSL2627_backup_2026_08_01_162816_1976055.bak"


def main() -> None:
    url = (
        f"mssql+pyodbc://{quote_plus(USER)}:{quote_plus(PASSWORD)}"
        f"@{SERVER}/master?driver=ODBC+Driver+18+for+SQL+Server"
        f"&TrustServerCertificate=yes&Encrypt=no"
    )
    engine = create_engine(url, isolation_level="AUTOCOMMIT")

    with engine.connect() as conn:
        exists = conn.execute(
            text("SELECT name, state_desc FROM sys.databases WHERE name = :name"),
            {"name": DATABASE},
        ).first()
        print("Before:", exists)

        conn.execute(
            text("RESTORE FILELISTONLY FROM DISK = :path"),
            {"path": BACKUP_PATH},
        ).fetchall()
        print("Backup file OK:", BACKUP_PATH)

        state = exists[1] if exists else None
        if exists and state == "RESTORING":
            print("Database stuck in RESTORING — dropping for clean restore...")
            conn.execute(text(f"DROP DATABASE [{DATABASE}]"))
            exists = None
        elif exists:
            print("Setting SINGLE_USER (disconnecting active sessions)...")
            conn.execute(
                text(f"ALTER DATABASE [{DATABASE}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE")
            )

        if exists:
            restore_sql = (
                f"RESTORE DATABASE [{DATABASE}] FROM DISK = :path "
                "WITH REPLACE, RECOVERY, STATS = 10"
            )
        else:
            restore_sql = (
                f"RESTORE DATABASE [{DATABASE}] FROM DISK = :path "
                "WITH RECOVERY, STATS = 10"
            )

        print("Restoring...")
        result = conn.execute(text(restore_sql), {"path": BACKUP_PATH})
        cursor = getattr(result, "cursor", None)
        if cursor is not None:
            while cursor.nextset():
                pass

        state = conn.execute(
            text("SELECT state_desc FROM sys.databases WHERE name = :name"),
            {"name": DATABASE},
        ).scalar()
        if state == "RESTORING":
            raise RuntimeError("Database still in RESTORING state after restore.")

        if exists:
            conn.execute(text(f"ALTER DATABASE [{DATABASE}] SET MULTI_USER"))

        after = conn.execute(
            text(
                "SELECT name, state_desc, recovery_model_desc "
                "FROM sys.databases WHERE name = :name"
            ),
            {"name": DATABASE},
        ).first()
        print("After:", after)

        rows = conn.execute(text(f"SELECT COUNT(*) FROM [{DATABASE}].dbo.GL0002")).scalar()
        print("GL0002 rows:", rows)

    print("Restore completed successfully.")


if __name__ == "__main__":
    main()
