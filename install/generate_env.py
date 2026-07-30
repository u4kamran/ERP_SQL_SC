"""Create .env from install/env.shahenhp with random secrets."""

import base64
import os
import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = Path(__file__).resolve().parent / "env.shahenhp"
TARGET = ROOT / ".env"


def main() -> int:
    force = "--force" in sys.argv
    if not TEMPLATE.exists():
        print(f"Template not found: {TEMPLATE}")
        return 1
    if TARGET.exists() and not force:
        print(".env already exists - keeping your current file.")
        return 0

    secret_key = base64.b64encode(secrets.token_bytes(48)).decode("ascii")
    csrf_key = base64.b64encode(secrets.token_bytes(32)).decode("ascii")
    content = TEMPLATE.read_text(encoding="utf-8")
    content = content.replace("__GENERATE_SECRET_KEY__", secret_key)
    content = content.replace("__GENERATE_CSRF_KEY__", csrf_key)
    TARGET.write_text(content, encoding="utf-8", newline="\n")
    print("Created .env from install\\env.shahenhp")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
