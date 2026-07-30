"""One-way SQL Server sync: local (source) -> online (target) via backup/restore."""

from __future__ import annotations

import shutil
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from app.config.settings import Settings, settings
from app.logging.logger import logger
from app.services.db_sync_store import record_run


@dataclass
class DatabaseTarget:
    name: str
    server: str
    enabled: bool = True


class DatabaseSyncError(Exception):
    pass


class DatabaseSyncService:
    """
    Sync local SQL Server databases to an online SQL Server.

    For ~10 GB ERP databases, full backup + copy + restore is the practical approach.
    Run on a schedule (e.g. nightly) — not every few minutes.
    """

    def __init__(self, cfg: Settings | None = None) -> None:
        self.cfg = cfg or settings
        self.backup_dir = Path(self.cfg.sync_backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def is_configured(self) -> bool:
        return bool(
            self.cfg.sync_enabled
            and self.cfg.sync_remote_server.strip()
            and self.cfg.sync_remote_user.strip()
            and self.cfg.sync_remote_password.strip()
            and self.cfg.sync_remote_backup_share.strip()
        )

    def configuration_hint(self) -> str:
        if not self.cfg.sync_enabled:
            return "Set SYNC_ENABLED=true in .env to enable database sync."
        if not self.cfg.sync_remote_server.strip():
            return "Set SYNC_REMOTE_SERVER to your online SQL Server host/IP."
        if not self.cfg.sync_remote_user.strip() or not self.cfg.sync_remote_password.strip():
            return "Set SYNC_REMOTE_USER and SYNC_REMOTE_PASSWORD for the online SQL Server."
        if not self.cfg.sync_remote_backup_share.strip():
            return (
                "Set SYNC_REMOTE_BACKUP_SHARE to a LAN folder on the backup PC "
                r"(e.g. \\192.168.1.20\SQLBackup). Uses local network only — no internet."
            )
        return "Ready — LAN sync: backup on main PC, copy to backup PC, restore there."

    def list_databases(self) -> list[DatabaseTarget]:
        targets: list[DatabaseTarget] = []
        if self.cfg.sync_auth_db:
            targets.append(
                DatabaseTarget(
                    name=self.cfg.db_name,
                    server=self.cfg.db_server,
                )
            )
        if self.cfg.sync_business_db:
            targets.append(
                DatabaseTarget(
                    name=self.cfg.business_db_name,
                    server=self.cfg.business_db_server or self.cfg.db_server,
                )
            )
        return targets

    def run(self, *, dry_run: bool = False) -> dict[str, Any]:
        if not self.cfg.sync_enabled and not dry_run:
            raise DatabaseSyncError("Sync is disabled. Set SYNC_ENABLED=true in .env.")
        if not dry_run and not self.is_configured():
            raise DatabaseSyncError(self.configuration_hint())

        started = time.time()
        results: dict[str, Any] = {
            "started_at": datetime.now().isoformat(timespec="seconds"),
            "dry_run": dry_run,
            "databases": {},
        }

        for target in self.list_databases():
            logger.info("DB sync: processing %s", target.name)
            if dry_run:
                results["databases"][target.name] = {
                    "status": "dry_run",
                    "source_server": target.server,
                    "target_server": self.cfg.sync_remote_server or "(not set)",
                }
                continue

            source_engine = self._engine(
                target.server,
                "master",
                self.cfg.db_user,
                self.cfg.db_password,
            )
            backup_path = self._backup_database(source_engine, target.name)
            copied_path = self._copy_to_remote_share(backup_path)
            self._restore_on_remote(target.name, copied_path)
            size_mb = round(backup_path.stat().st_size / (1024 * 1024), 1)
            results["databases"][target.name] = {
                "status": "success",
                "backup_file": str(backup_path),
                "remote_file": str(copied_path),
                "size_mb": size_mb,
            }
            logger.info("DB sync: %s completed (%s MB)", target.name, size_mb)

        duration = round(time.time() - started, 1)
        results["duration_sec"] = duration
        results["status"] = "success"
        results["message"] = f"Synced {len(results['databases'])} database(s) in {duration}s."

        if not dry_run:
            record_run(
                status="success",
                message=results["message"],
                details=results,
            )
        return results

    def _engine(self, server: str, database: str, user: str, password: str) -> Engine:
        odbc = (
            f"DRIVER={{{self.cfg.db_driver}}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"UID={user};"
            f"PWD={password};"
            f"TrustServerCertificate={self.cfg.db_trust_server_certificate};"
            f"Encrypt={self.cfg.db_encrypt};"
        )
        url = f"mssql+pyodbc:///?odbc_connect={quote_plus(odbc)}"
        return create_engine(url, pool_pre_ping=True)

    def _backup_database(self, engine: Engine, database: str) -> Path:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = (self.backup_dir / f"{database}_{stamp}.bak").resolve()
        # SQL Server 2008: CHECKSUM + STATS supported; no compression flag (Express).
        sql = """
            BACKUP DATABASE [{db}]
            TO DISK = :path
            WITH INIT, CHECKSUM, STATS = 10
        """.format(db=database)
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            conn.execute(text(sql), {"path": str(backup_path)})

        if not backup_path.exists() or backup_path.stat().st_size == 0:
            raise DatabaseSyncError(f"Backup failed for {database}.")
        return backup_path

    def _copy_to_remote_share(self, backup_path: Path) -> Path:
        share = self.cfg.sync_remote_backup_share.strip().rstrip("\\")
        if not share:
            raise DatabaseSyncError(self.configuration_hint())

        remote_dir = Path(share)
        remote_dir.mkdir(parents=True, exist_ok=True)
        remote_path = remote_dir / backup_path.name

        logger.info("DB sync: copying %s -> %s", backup_path, remote_path)
        if self._is_unc_path(share):
            self._robocopy(backup_path, remote_path)
        else:
            shutil.copy2(backup_path, remote_path)

        if not remote_path.exists():
            raise DatabaseSyncError(f"Copy failed — file not found at {remote_path}")
        return remote_path

    @staticmethod
    def _is_unc_path(path: str) -> bool:
        return path.startswith("\\\\")

    @staticmethod
    def _robocopy(source: Path, dest: Path) -> None:
        dest.parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            "robocopy",
            str(source.parent),
            str(dest.parent),
            source.name,
            "/Z",
            "/J",
            "/R:2",
            "/W:5",
            "/NFL",
            "/NDL",
            "/NJH",
            "/NJS",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode >= 8:
            raise DatabaseSyncError(
                f"robocopy failed ({proc.returncode}): {proc.stderr or proc.stdout}"
            )

    def _restore_file_moves(self, conn, restore_path: str) -> list[tuple[str, str]]:
        """Map logical files to backup-PC paths (required for SQL Server 2008 cross-machine restore)."""
        restore_base = self.cfg.sync_remote_restore_dir.strip()
        if not restore_base:
            return []

        data_dir = Path(restore_base) / "data"
        rows = conn.execute(
            text("RESTORE FILELISTONLY FROM DISK = :path"),
            {"path": restore_path},
        ).fetchall()

        moves: list[tuple[str, str]] = []
        for row in rows:
            logical = str(row[0])
            file_type = str(row[2]) if len(row) > 2 else "D"
            ext = ".ldf" if file_type.upper() == "L" else ".mdf"
            moves.append((logical, str(data_dir / f"{logical}{ext}")))
        return moves

    def _restore_on_remote(self, database: str, backup_path: Path) -> None:
        target_engine = self._engine(
            self.cfg.sync_remote_server.strip(),
            "master",
            self.cfg.sync_remote_user.strip(),
            self.cfg.sync_remote_password.strip(),
        )
        restore_dir = self.cfg.sync_remote_restore_dir.strip()
        if restore_dir:
            restore_path = str(Path(restore_dir) / backup_path.name)
        else:
            restore_path = str(backup_path)

        with target_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            exists = conn.execute(
                text("SELECT 1 FROM sys.databases WHERE name = :name"),
                {"name": database},
            ).first()

            if exists:
                conn.execute(
                    text(f"ALTER DATABASE [{database}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE")
                )

            moves = self._restore_file_moves(conn, restore_path)
            move_sql = ""
            if moves:
                move_sql = ", " + ", ".join(
                    f"MOVE N'{logical}' TO N'{dest}'" for logical, dest in moves
                )

            if exists:
                sql = f"""
                    RESTORE DATABASE [{database}]
                    FROM DISK = :path
                    WITH REPLACE, RECOVERY, STATS = 10{move_sql}
                """
            else:
                sql = f"""
                    RESTORE DATABASE [{database}]
                    FROM DISK = :path
                    WITH RECOVERY, STATS = 10{move_sql}
                """

            conn.execute(text(sql), {"path": restore_path})

            if exists:
                conn.execute(text(f"ALTER DATABASE [{database}] SET MULTI_USER"))

    def cleanup_old_backups(self, keep: int | None = None) -> int:
        keep = keep if keep is not None else self.cfg.sync_keep_local_backups
        if keep <= 0:
            return 0
        removed = 0
        files = sorted(self.backup_dir.glob("*.bak"), key=lambda p: p.stat().st_mtime, reverse=True)
        for old in files[keep:]:
            old.unlink(missing_ok=True)
            removed += 1
        return removed
