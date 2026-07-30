"""SMTP email delivery."""

from __future__ import annotations

import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Iterable

from app.config.settings import settings


class EmailNotConfiguredError(Exception):
    pass


class EmailDeliveryError(Exception):
    pass


class EmailService:
    def is_configured(self) -> bool:
        return bool(
            settings.smtp_enabled
            and settings.smtp_host.strip()
            and settings.smtp_user.strip()
            and settings.smtp_password.strip()
        )

    def configuration_hint(self) -> str:
        if not settings.smtp_enabled:
            return "Set SMTP_ENABLED=true in .env and restart the app."
        if not settings.smtp_host.strip():
            return "Set SMTP_HOST in .env (Gmail: smtp.gmail.com)."
        if not settings.smtp_user.strip():
            return "Set SMTP_USER in .env to your Gmail address."
        if not settings.smtp_password.strip():
            return "Set SMTP_PASSWORD in .env to your Gmail App Password."
        return "Ready to send from " + settings.smtp_user.strip()

    def send_email(
        self,
        to_addrs: Iterable[str],
        subject: str,
        body_text: str,
        *,
        attachment: tuple[str, bytes, str] | None = None,
    ) -> None:
        if not self.is_configured():
            raise EmailNotConfiguredError(self.configuration_hint())

        recipients = [addr.strip() for addr in to_addrs if addr and addr.strip()]
        if not recipients:
            raise EmailDeliveryError("No recipient email addresses provided.")

        msg = MIMEMultipart()
        from_email = settings.smtp_from_email.strip() or settings.smtp_user.strip()
        msg["From"] = f"{settings.smtp_from_name} <{from_email}>"
        msg["To"] = ", ".join(recipients)
        msg["Subject"] = subject
        msg.attach(MIMEText(body_text, "plain", "utf-8"))

        if attachment:
            filename, content, mime_type = attachment
            part = MIMEApplication(content, _subtype=mime_type.split("/")[-1])
            part.add_header("Content-Disposition", "attachment", filename=filename)
            msg.attach(part)

        try:
            if settings.smtp_use_ssl or settings.smtp_port == 465:
                with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=30) as server:
                    server.login(settings.smtp_user, settings.smtp_password)
                    server.sendmail(from_email, recipients, msg.as_string())
            else:
                with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as server:
                    server.ehlo()
                    if settings.smtp_port == 587:
                        server.starttls()
                        server.ehlo()
                    server.login(settings.smtp_user, settings.smtp_password)
                    server.sendmail(from_email, recipients, msg.as_string())
        except smtplib.SMTPAuthenticationError as exc:
            raise EmailDeliveryError(
                "Gmail login failed. Use a Gmail App Password in SMTP_PASSWORD "
                "(not your normal Gmail password). "
                "Create one at https://myaccount.google.com/apppasswords"
            ) from exc
        except smtplib.SMTPException as exc:
            raise EmailDeliveryError(f"Could not send email: {exc}") from exc
        except OSError as exc:
            raise EmailDeliveryError(f"Could not connect to mail server: {exc}") from exc
