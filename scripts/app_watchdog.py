"""Keep the ERP app running — auto-start and auto-restart on failure."""

from __future__ import annotations

import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYTHON = ROOT / "venv" / "Scripts" / "python.exe"
RUN_SCRIPT = ROOT / "run.py"
LOCK_FILE = ROOT / "data" / "app_watchdog.lock"
CHECK_SECONDS = 20
STARTUP_WAIT_SECONDS = 10
HEALTH_TIMEOUT_SECONDS = 5

_lock_fh = None


def _settings():
    sys.path.insert(0, str(ROOT))
    from app.config.settings import settings

    return settings


def _acquire_single_watchdog_lock() -> bool:
    """Only one watchdog per project folder. Keep the file handle open."""
    global _lock_fh
    LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    _lock_fh = open(LOCK_FILE, "a+b")
    try:
        if sys.platform == "win32":
            import msvcrt

            _lock_fh.seek(0)
            msvcrt.locking(_lock_fh.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(_lock_fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        _lock_fh.close()
        _lock_fh = None
        return False
    _lock_fh.seek(0)
    _lock_fh.truncate()
    _lock_fh.write(str(os.getpid()).encode("ascii"))
    _lock_fh.flush()
    return True


def is_healthy(port: int | None = None) -> bool:
    if port is None:
        port = _settings().port
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}/health", timeout=HEALTH_TIMEOUT_SECONDS
        ) as response:
            return response.status == 200
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def _python_pids_matching(needle: str) -> list[int]:
    """Return PIDs of python.exe whose command line contains needle (this project)."""
    me = os.getpid()
    script = (
        "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" "
        "| Where-Object { $_.CommandLine -and ($_.CommandLine -like '*"
        + needle.replace("'", "''")
        + "*') } "
        "| Select-Object -ExpandProperty ProcessId"
    )
    try:
        out = subprocess.check_output(
            ["powershell", "-NoProfile", "-Command", script],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, OSError):
        return []
    pids: list[int] = []
    for line in out.splitlines():
        line = line.strip()
        if line.isdigit():
            pid = int(line)
            if pid != me:
                pids.append(pid)
    return pids


def _listener_pid(port: int) -> int | None:
    try:
        out = subprocess.check_output(["netstat", "-ano"], text=True, stderr=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, OSError):
        return None
    needle = f":{port}"
    for line in out.splitlines():
        if "LISTENING" not in line or needle not in line:
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        local = parts[1]
        if local.endswith(needle) or local.endswith(f":{port}"):
            try:
                return int(parts[-1])
            except ValueError:
                return None
    return None


def _taskkill(pid: int) -> None:
    subprocess.run(
        ["taskkill", "/PID", str(pid), "/F"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )


def stop_hung_app(port: int) -> None:
    """Kill leftover run.py copies and anything still holding the app port."""
    pids = set(_python_pids_matching("ahsteellab-nsds2626*run.py"))
    listener = _listener_pid(port)
    if listener:
        pids.add(listener)
    for pid in sorted(pids):
        print(f"Stopping hung process PID {pid}...")
        _taskkill(pid)
    if pids:
        time.sleep(2)


def start_app() -> None:
    if not PYTHON.exists():
        raise FileNotFoundError(f"Python not found: {PYTHON}")
    subprocess.Popen(
        [str(PYTHON), str(RUN_SCRIPT)],
        cwd=str(ROOT),
        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0,
    )


def restart_app(port: int) -> None:
    stop_hung_app(port)
    start_app()
    time.sleep(STARTUP_WAIT_SECONDS)


def main() -> None:
    if not _acquire_single_watchdog_lock():
        print("Another ERP watchdog is already running in this folder.")
        print("Leave that window open. To restart, run STOP-ERP.bat then START-ERP.bat")
        sys.exit(0)

    settings = _settings()
    print(f"{settings.app_name} watchdog started — checking every {CHECK_SECONDS} seconds.")
    print("Press Ctrl+C to stop the watchdog (the site keeps running until STOP-APP.bat).")
    print(f"URL: {settings.base_url}")
    print(f"Port: {settings.port}")
    print()

    if not is_healthy(settings.port):
        print("App is down — starting now...")
        restart_app(settings.port)

    while True:
        if is_healthy(settings.port):
            print(f"[{time.strftime('%H:%M:%S')}] OK — app is running")
        else:
            print(f"[{time.strftime('%H:%M:%S')}] App not responding — restarting...")
            restart_app(settings.port)
        time.sleep(CHECK_SECONDS)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nWatchdog stopped.")
