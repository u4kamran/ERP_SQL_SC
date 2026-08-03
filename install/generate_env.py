"""Create .env from a site template with random secrets."""

import base64
import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INSTALL_DIR = Path(__file__).resolve().parent
TARGET = ROOT / ".env"

SITE_TEMPLATES = {
    "shahenhp": "env.shahenhp",
    "erp": "env.erp",
    "arp": "env.arp",
}


def parse_site(argv: list[str]) -> str:
    for i, arg in enumerate(argv):
        if arg == "--site" and i + 1 < len(argv):
            return argv[i + 1].lower()
        if arg.startswith("--site="):
            return arg.split("=", 1)[1].lower()
    return "shahenhp"


def main() -> int:
    site = parse_site(sys.argv[1:])
    force = "--force" in sys.argv

    template_name = SITE_TEMPLATES.get(site)
    if not template_name:
        print(f"Unknown site '{site}'. Choose: {', '.join(SITE_TEMPLATES)}")
        return 1

    template = INSTALL_DIR / template_name
    if not template.exists():
        print(f"Template not found: {template}")
        return 1

    if TARGET.exists() and not force:
        print(".env already exists - keeping your current file.")
        print(f"To regenerate: python install\\generate_env.py --site {site} --force")
        return 0

    secret_key = base64.b64encode(secrets.token_bytes(48)).decode("ascii")
    csrf_key = base64.b64encode(secrets.token_bytes(32)).decode("ascii")
    content = template.read_text(encoding="utf-8")
    content = content.replace("__GENERATE_SECRET_KEY__", secret_key)
    content = content.replace("__GENERATE_CSRF_KEY__", csrf_key)
    TARGET.write_text(content, encoding="utf-8", newline="\n")
    print(f"Created .env from install\\{template_name} (site: {site})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
