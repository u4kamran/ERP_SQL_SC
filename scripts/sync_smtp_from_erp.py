"""Copy SMTP settings from ERP .env into shared-smtp.env for ERP + ARP."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARP_ROOT = Path(r"D:\CursorProject\ahsteellab-arp")
SHARED_SMTP = ROOT.parent / "shared-smtp.env"

SMTP_KEYS = (
    "SMTP_ENABLED",
    "SMTP_HOST",
    "SMTP_PORT",
    "SMTP_USE_SSL",
    "SMTP_USER",
    "SMTP_PASSWORD",
    "SMTP_FROM_EMAIL",
)


def read_env_values(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        for key in SMTP_KEYS:
            match = re.match(rf"^{re.escape(key)}=(.*)$", line)
            if match:
                values[key] = match.group(1).strip()
    return values


def write_shared(values: dict[str, str]) -> None:
    lines = [
        "# Shared SMTP - same Gmail for Shafique Center (ERP) + Al Haram Steel Lab (ARP)",
        "# Updated by scripts/sync_smtp_from_erp.py",
        "",
    ]
    for key in SMTP_KEYS:
        if key in values and values[key] != "":
            lines.append(f"{key}={values[key]}")
    SHARED_SMTP.write_text("\n".join(lines) + "\n", encoding="utf-8")


def patch_env(path: Path, updates: dict[str, str]) -> None:
    if not path.exists():
        return
    lines = path.read_text(encoding="utf-8").splitlines()
    seen = set()
    new_lines: list[str] = []
    for line in lines:
        matched = False
        for key, val in updates.items():
            if re.match(rf"^{re.escape(key)}=", line):
                new_lines.append(f"{key}={val}")
                seen.add(key)
                matched = True
                break
        if not matched:
            new_lines.append(line)
    for key, val in updates.items():
        if key not in seen:
            new_lines.append(f"{key}={val}")
    path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


def main() -> int:
    erp_env = ROOT / ".env"
    arp_env = ARP_ROOT / ".env"
    shared_existing = read_env_values(SHARED_SMTP)

    merged = dict(shared_existing)
    for source in (erp_env, arp_env):
        for key, val in read_env_values(source).items():
            if val:
                merged[key] = val

    merged["SMTP_ENABLED"] = "true"
    if not merged.get("SMTP_HOST"):
        merged["SMTP_HOST"] = "smtp.gmail.com"
    if not merged.get("SMTP_PORT"):
        merged["SMTP_PORT"] = "587"
    if not merged.get("SMTP_USE_SSL"):
        merged["SMTP_USE_SSL"] = "false"
    if merged.get("SMTP_USER") and not merged.get("SMTP_FROM_EMAIL"):
        merged["SMTP_FROM_EMAIL"] = merged["SMTP_USER"]

    if not merged.get("SMTP_USER") or not merged.get("SMTP_PASSWORD"):
        print("Missing SMTP_USER or SMTP_PASSWORD.")
        print("Copy the working SMTP lines from Shafique Center .env into:")
        print(f"  {erp_env}")
        print("Then run this script again.")
        print()
        print("Or run: CONFIGURE-SMTP.bat")
        return 1

    write_shared(merged)
    print(f"Created/updated: {SHARED_SMTP}")

    patch_env(erp_env, {
        "SMTP_ENABLED": "true",
        "SMTP_FROM_NAME": "Shafique Departmental Store",
    })
    print(f"Enabled SMTP in ERP: {erp_env}")

    if arp_env.exists():
        patch_env(arp_env, {
            "SMTP_ENABLED": "true",
            "SMTP_HOST": merged.get("SMTP_HOST", "smtp.gmail.com"),
            "SMTP_PORT": merged.get("SMTP_PORT", "587"),
            "SMTP_USE_SSL": merged.get("SMTP_USE_SSL", "false"),
            "SMTP_USER": merged.get("SMTP_USER", ""),
            "SMTP_PASSWORD": merged.get("SMTP_PASSWORD", ""),
            "SMTP_FROM_EMAIL": merged.get("SMTP_FROM_EMAIL", merged.get("SMTP_USER", "")),
            "SMTP_FROM_NAME": "Al Haram Steel Lab",
        })
        print(f"Enabled SMTP in ARP: {arp_env}")

    print()
    print("Same Gmail is now used for both sites via shared-smtp.env")
    print("Restart: START-ARP.bat (and START-ERP.bat if needed)")
    print("Test:   TEST-SMTP.bat")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
