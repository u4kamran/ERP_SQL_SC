"""Copy application source from ERP folder to ARP clone (same reports on both sites)."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ERP_ROOT = Path(__file__).resolve().parent.parent
ARP_ROOT = Path(r"D:\CursorProject\ahsteellab-arp")

# Directories copied wholesale (relative to repo root).
COPY_DIRS = (
    "app",
    "sql",
    "scripts",
    "deploy",
    "install",
    "docs",
    "vb6",
)

# Single files at repo root.
COPY_FILES = (
    "requirements.txt",
    "run.py",
    "README.md",
    "README-NSDS2626.md",
)

# Root batch helpers shared by both sites.
COPY_BAT_GLOB = "*.bat"

SKIP_DIR_NAMES = {
    "__pycache__",
    ".git",
    "venv",
    "logs",
    "data",
    "node_modules",
    ".cursor",
}

SKIP_FILE_NAMES = {
    ".env",
    "app_pass.txt",
}

# Per-site tunnel credentials — never overwrite ARP config from ERP.
# Note: when copying deploy/, paths are relative to deploy/ (not repo root).
SKIP_REL_PATHS = {
    Path("deploy/cloudflared/config.yml"),
    Path("cloudflared/config.yml"),
}

SKIP_REL_PREFIXES = ("cloudflared/bin",)


def _should_skip_dir(name: str) -> bool:
    return name in SKIP_DIR_NAMES


def _copy_tree(src: Path, dst: Path) -> tuple[int, int]:
    copied = 0
    skipped = 0
    if not src.exists():
        return copied, skipped

    for item in src.rglob("*"):
        rel = item.relative_to(src)
        if any(part in SKIP_DIR_NAMES for part in rel.parts):
            skipped += 1
            continue
        if rel in SKIP_REL_PATHS:
            skipped += 1
            continue
        rel_posix = rel.as_posix()
        if any(rel_posix == skip or rel_posix.startswith(skip + "/") for skip in SKIP_REL_PREFIXES):
            skipped += 1
            continue

        target = dst / rel
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue

        if item.name in SKIP_FILE_NAMES or item.suffix == ".pyc":
            skipped += 1
            continue

        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, target)
        copied += 1

    return copied, skipped


def sync_to_arp() -> int:
    if not ARP_ROOT.is_dir():
        print(f"ERROR: ARP folder not found: {ARP_ROOT}")
        print("Run CLONE-ARP-SITE.bat first.")
        return 1

    total_copied = 0
    total_skipped = 0

    print(f"Source (ERP): {ERP_ROOT}")
    print(f"Target (ARP): {ARP_ROOT}")
    print()

    for dirname in COPY_DIRS:
        src = ERP_ROOT / dirname
        dst = ARP_ROOT / dirname
        c, s = _copy_tree(src, dst)
        print(f"  {dirname}/  -> {c} files copied, {s} skipped")
        total_copied += c
        total_skipped += s

    for filename in COPY_FILES:
        src = ERP_ROOT / filename
        if src.is_file():
            shutil.copy2(src, ARP_ROOT / filename)
            total_copied += 1
            print(f"  {filename}")

    for bat in ERP_ROOT.glob(COPY_BAT_GLOB):
        if bat.name.upper().startswith("SYNC-CODE"):
            continue
        shutil.copy2(bat, ARP_ROOT / bat.name)
        total_copied += 1

    print()
    print(f"Done: {total_copied} files copied ({total_skipped} skipped).")
    print("ARP keeps its own .env, venv, logs, and cloudflared config.yml.")
    print("Restart ARP: START-ARP.bat or START-ALL.bat")
    return 0


if __name__ == "__main__":
    sys.exit(sync_to_arp())
