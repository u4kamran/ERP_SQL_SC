"""Configure shared SMTP once for ERP + ARP (same Gmail account)."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARP_ROOT = Path(r"D:\CursorProject\ahsteellab-arp")
SHARED_SMTP = ROOT.parent / "shared-smtp.env"

SHARED_KEYS = (
    "SMTP_ENABLED",
    "SMTP_HOST",
    "SMTP_PORT",
    "SMTP_USE_SSL",
    "SMTP_USER",
    "SMTP_PASSWORD",
    "SMTP_FROM_EMAIL",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Configure shared SMTP for both sites")
    parser.add_argument("--host", default="smtp.gmail.com")
    parser.add_argument("--port", default="587")
    parser.add_argument("--user", help="Gmail address")
    parser.add_argument("--password", help="Gmail App Password")
    parser.add_argument("--from-email", help="From email (default: same as user)")
    parser.add_argument("--interactive", action="store_true")
    return parser.parse_args()


def update_env_file(path: Path, values: dict[str, str]) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    updated = set()
    new_lines: list[str] = []
    for line in lines:
        matched = False
        for key, val in values.items():
            if re.match(rf"^{re.escape(key)}=", line):
                new_lines.append(f"{key}={val}")
                updated.add(key)
                matched = True
                break
        if not matched:
            new_lines.append(line)
    for key, val in values.items():
        if key not in updated:
            new_lines.append(f"{key}={val}")
    path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()

    if args.interactive or not args.user or not args.password:
        print("Shared SMTP setup - same Gmail for ERP + ARP")
        print("App Password: https://myaccount.google.com/apppasswords")
        print()
        if not args.user:
            args.user = input("Gmail address: ").strip()
        if not args.password:
            import getpass

            args.password = getpass.getpass("Gmail App Password: ").strip()

    if not args.user or not args.password:
        print("Gmail address and App Password required.")
        return 1

    shared_values = {
        "SMTP_ENABLED": "true",
        "SMTP_HOST": args.host,
        "SMTP_PORT": str(args.port),
        "SMTP_USE_SSL": "false",
        "SMTP_USER": args.user,
        "SMTP_PASSWORD": args.password,
        "SMTP_FROM_EMAIL": args.from_email or args.user,
    }

    lines = ["# Shared SMTP - used by ERP and ARP", ""]
    lines.extend(f"{k}={v}" for k, v in shared_values.items())
    SHARED_SMTP.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Created: {SHARED_SMTP}")

    for label, folder, from_name in (
        ("ERP", ROOT, "Shafique Departmental Store"),
        ("ARP", ARP_ROOT, "Al Haram Steel Lab"),
    ):
        env_path = folder / ".env"
        if not env_path.exists():
            continue
        update_env_file(env_path, {"SMTP_ENABLED": "true", "SMTP_FROM_NAME": from_name})
        print(f"Enabled SMTP in {label}: {env_path}")

    print()
    print("Same Gmail is now used for both sites.")
    print("Restart: START-ERP.bat and START-ARP.bat")
    print("Test:   TEST-SMTP.bat")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
