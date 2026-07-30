"""Keep the ERP app running — auto-start and auto-restart on failure."""

from __future__ import annotations

import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYTHON = ROOT / "venv" / "Scripts" / "python.exe"
RUN_SCRIPT = ROOT / "run.py"
CHECK_SECONDS = 60
STARTUP_WAIT_SECONDS = 8


def is_healthy(port: int = 8000) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=5) as response:
            return response.status == 200
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def start_app() -> None:
    if not PYTHON.exists():
        raise FileNotFoundError(f"Python not found: {PYTHON}")
    subprocess.Popen(
        [str(PYTHON), str(RUN_SCRIPT)],
        cwd=str(ROOT),
        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0,
    )


def main() -> None:
    print("ERP watchdog started — checking every 60 seconds.")
    print("Press Ctrl+C to stop the watchdog (the site keeps running until STOP-APP.bat).")
    print("URL: https://erp.ahsteellab.com")
    print()

    if not is_healthy():
        print("App is down — starting now...")
        start_app()
        time.sleep(STARTUP_WAIT_SECONDS)

    while True:
        if is_healthy():
            print(f"[{time.strftime('%H:%M:%S')}] OK — app is running")
        else:
            print(f"[{time.strftime('%H:%M:%S')}] App not responding — restarting...")
            start_app()
            time.sleep(STARTUP_WAIT_SECONDS)
        time.sleep(CHECK_SECONDS)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nWatchdog stopped.")
