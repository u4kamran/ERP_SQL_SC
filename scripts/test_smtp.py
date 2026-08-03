"""Send a test email using SMTP settings from .env."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Send SMTP test email")
    parser.add_argument("--site", choices=["erp", "arp"], default="erp")
    parser.add_argument("--to", help="Recipient email (default: SMTP_USER)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    site_root = ROOT if args.site == "erp" else Path(r"D:\CursorProject\ahsteellab-arp")
    sys.path.insert(0, str(site_root))

    from app.config.settings import get_settings
    from app.services.email_service import EmailDeliveryError, EmailNotConfiguredError, EmailService

    get_settings.cache_clear()
    settings = get_settings()
    service = EmailService()

    print(f"Site: {settings.app_name}")
    print(f"SMTP: {service.configuration_hint()}")

    if not service.is_configured():
        return 1

    recipient = (args.to or settings.smtp_user).strip()
    try:
        service.send_email(
            [recipient],
            subject=f"Test email - {settings.app_name}",
            body_text=f"SMTP is working for {settings.app_name}.\n\nSent from {settings.base_url}",
        )
    except (EmailNotConfiguredError, EmailDeliveryError) as exc:
        print(f"FAILED: {exc}")
        return 1

    print(f"Test email sent to {recipient}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
