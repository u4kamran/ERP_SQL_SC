"""LAN database sync helpers — main PC -> backup PC, no internet."""

from __future__ import annotations

import ipaddress
import re
import subprocess
from typing import Any

from app.config.settings import Settings, settings
from app.services.db_sync_service import DatabaseSyncError, DatabaseSyncService


def _is_private_host(host: str) -> bool:
    host = (host or "").strip()
    if not host:
        return False
    if host.lower() in {"localhost", "(local)", "."}:
        return True
    if host.startswith("\\\\"):
        parts = host.strip("\\").split("\\")
        return _is_private_host(parts[0]) if parts else False
    bare = host.split(",")[0].split("\\")[0]
    if "." not in bare:
        # Single-label Windows hostname on LAN (e.g. shaheenac, shaheenhp).
        return True
    try:
        return ipaddress.ip_address(bare).is_private
    except ValueError:
        return bool(re.match(r"^192\.168\.|^10\.|^172\.(1[6-9]|2\d|3[0-1])\.", bare))


class LanDatabaseSyncService(DatabaseSyncService):
    """
    Two-machine LAN sync (zero internet bandwidth).

    Machine 1 (main): ERP + source SQL Server — run sync from here.
    Machine 2 (backup): SQL Server + shared folder — receives .bak and restore.
    """

    def __init__(self, cfg: Settings | None = None) -> None:
        super().__init__(cfg)
        self._validate_lan_hosts()

    def _validate_lan_hosts(self) -> None:
        if not self.cfg.sync_lan_only:
            return
        hosts = [
            self.cfg.db_server,
            self.cfg.business_db_server or self.cfg.db_server,
            self.cfg.sync_remote_server,
            self.cfg.sync_remote_backup_share,
        ]
        for host in hosts:
            if not host:
                continue
            if not _is_private_host(host):
                raise DatabaseSyncError(
                    f"SYNC_LAN_ONLY=true but host looks public/non-LAN: {host}. "
                    "Use 192.168.x.x or PC name on local network."
                )

    def ping_backup_pc(self) -> bool:
        host = self.cfg.sync_remote_server.strip().split("\\")[0].split(",")[0]
        if not host or host.lower() in {"localhost", "(local)"}:
            return True
        proc = subprocess.run(
            ["ping", "-n", "1", "-w", "1000", host],
            capture_output=True,
            text=True,
        )
        return proc.returncode == 0

    def status_report(self) -> dict[str, Any]:
        return {
            "enabled": self.cfg.sync_enabled,
            "configured": self.is_configured(),
            "hint": self.configuration_hint(),
            "lan_only": self.cfg.sync_lan_only,
            "main_sql_server": self.cfg.db_server,
            "backup_sql_server": self.cfg.sync_remote_server,
            "backup_share": self.cfg.sync_remote_backup_share,
            "backup_restore_dir": self.cfg.sync_remote_restore_dir,
            "business_db": self.cfg.business_db_name,
            "auth_db": self.cfg.db_name,
            "interval_minutes": self.cfg.sync_interval_minutes,
            "backup_pc_ping": self.ping_backup_pc() if self.cfg.sync_remote_server else None,
        }

    def run(self, *, dry_run: bool = False) -> dict[str, Any]:
        if not dry_run and self.cfg.sync_remote_server and not self.ping_backup_pc():
            raise DatabaseSyncError(
                f"Cannot reach backup PC at {self.cfg.sync_remote_server}. "
                "Check LAN cable/Wi-Fi and that both PCs are on."
            )
        result = super().run(dry_run=dry_run)
        result["mode"] = "lan"
        result["message"] = (
            f"LAN sync OK — {result.get('message', '')} (no internet used)."
        )
        return result
