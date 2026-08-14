"""SMTP email delivery."""

from __future__ import annotations

import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Iterable

from app.config.settings import settings


def _branded_html(body_html: str) -> str:
    if "ahs-mail-header" in (body_html or ""):
        return body_html
    logo = f"{settings.base_url.rstrip('/')}{settings.brand_logo_url}"
    name = settings.app_name
    slogan = settings.brand_slogan or ""
    header = (
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        'style="font-family:Arial,Helvetica,sans-serif">'
        '<tr><td class="ahs-mail-header" style="padding:16px 0 18px;border-bottom:1px solid #e6ebf1">'
        f'<img src="{logo}" alt="{name}" width="160" style="display:block;border:0;max-width:160px;height:auto">'
        f'<div style="color:#5b6775;font-size:12px;margin-top:8px">{slogan}</div>'
        "</td></tr><tr><td style=\"padding-top:16px\">"
    )
    footer = (
        '</td></tr><tr><td style="padding-top:20px;border-top:1px solid #e6ebf1;'
        'color:#5b6775;font-size:11px">'
        f"{name} · {slogan}"
        "</td></tr></table>"
    )
    return header + body_html + footer


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
        body_html: str | None = None,
        attachment: tuple[str, bytes, str] | None = None,
    ) -> None:
        if not self.is_configured():
            raise EmailNotConfiguredError(self.configuration_hint())

        recipients = [addr.strip() for addr in to_addrs if addr and addr.strip()]
        if not recipients:
            raise EmailDeliveryError("No recipient email addresses provided.")

        msg = MIMEMultipart("mixed" if attachment else ("alternative" if body_html else "mixed"))
        from_email = settings.smtp_from_email.strip() or settings.smtp_user.strip()
        msg["From"] = f"{settings.smtp_from_name} <{from_email}>"
        msg["To"] = ", ".join(recipients)
        msg["Subject"] = subject

        html = _branded_html(body_html) if body_html else None
        if attachment and html:
            alt = MIMEMultipart("alternative")
            alt.attach(MIMEText(body_text, "plain", "utf-8"))
            alt.attach(MIMEText(html, "html", "utf-8"))
            msg.attach(alt)
        elif html:
            msg.attach(MIMEText(body_text, "plain", "utf-8"))
            msg.attach(MIMEText(html, "html", "utf-8"))
        else:
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
