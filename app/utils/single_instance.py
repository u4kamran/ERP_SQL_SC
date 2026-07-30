"""Ensure only one ERP instance listens on the app port."""

from __future__ import annotations

import socket
import sys
import urllib.error
import urllib.request


def _health_ok(host: str, port: int) -> bool:
    url = f"http://{host}:{port}/health"
    try:
        with urllib.request.urlopen(url, timeout=3) as response:
            return response.status == 200
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def _port_is_free(bind_host: str, port: int) -> bool:
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        probe.bind((bind_host, port))
        return True
    except OSError:
        return False
    finally:
        probe.close()


def ensure_single_instance(host: str, port: int) -> None:
    """Exit cleanly when the app is already running; fail fast on a stuck port."""
    check_host = "127.0.0.1"
    bind_host = "127.0.0.1" if host in ("0.0.0.0", "::") else host

    if _health_ok(check_host, port):
        print(f"ERP is already running on http://{check_host}:{port}")
        print("Open https://erp.ahsteellab.com — no need to start again.")
        print("To restart, run STOP-APP.bat then START-APP.bat")
        sys.exit(0)

    if not _port_is_free(bind_host, port):
        print(f"Port {port} is in use but the app is not responding.")
        print("Run RESTART-APP.bat or STOP-APP.bat to clear the old process.")
        sys.exit(1)
