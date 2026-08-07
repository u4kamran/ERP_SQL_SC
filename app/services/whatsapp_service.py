"""WhatsApp Business Cloud API — automated PDF delivery."""

from __future__ import annotations

import re
from typing import Any

import httpx

from app.config.settings import settings


class WhatsAppNotConfiguredError(Exception):
    pass


class WhatsAppDeliveryError(Exception):
    pass


def normalize_pk_phone(raw: str) -> str:
    """Return digits only in international format 92XXXXXXXXXX."""
    digits = re.sub(r"\D", "", raw or "")
    if not digits:
        return ""
    if digits.startswith("00"):
        digits = digits[2:]
    if digits.startswith("0"):
        digits = f"92{digits[1:]}"
    elif not digits.startswith("92"):
        digits = f"92{digits}"
    if len(digits) < 12 or len(digits) > 13:
        return ""
    return digits


class WhatsAppService:
    def is_configured(self) -> bool:
        return bool(
            settings.whatsapp_enabled
            and settings.whatsapp_api_token.strip()
            and settings.whatsapp_phone_number_id.strip()
        )

    def configuration_hint(self) -> str:
        if not settings.whatsapp_enabled:
            return (
                "Set WHATSAPP_ENABLED=true in .env and add Meta Cloud API credentials, then restart."
            )
        if not settings.whatsapp_api_token.strip():
            return "Set WHATSAPP_API_TOKEN in .env (Meta Business → WhatsApp → API setup)."
        if not settings.whatsapp_phone_number_id.strip():
            return "Set WHATSAPP_PHONE_NUMBER_ID in .env (from Meta WhatsApp API setup)."
        return "Ready to send via WhatsApp Cloud API."

    def _api_url(self, path: str = "messages") -> str:
        phone_id = settings.whatsapp_phone_number_id.strip()
        version = settings.whatsapp_api_version.strip() or "v21.0"
        return f"https://graph.facebook.com/{version}/{phone_id}/{path}"

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {settings.whatsapp_api_token.strip()}",
            "Content-Type": "application/json",
        }

    def send_document(
        self,
        to_phone: str,
        document_url: str,
        *,
        filename: str,
        caption: str = "",
    ) -> dict[str, Any]:
        if not self.is_configured():
            raise WhatsAppNotConfiguredError(self.configuration_hint())

        recipient = normalize_pk_phone(to_phone)
        if not recipient:
            raise WhatsAppDeliveryError(
                "Invalid WhatsApp number. Use Pakistan mobile e.g. 03001234567 or 3001234567."
            )

        if not document_url.startswith("https://"):
            raise WhatsAppDeliveryError("PDF link must be a public HTTPS URL for WhatsApp delivery.")

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "document",
            "document": {
                "link": document_url,
                "filename": filename,
            },
        }
        if caption:
            payload["document"]["caption"] = caption[:1024]

        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(
                    self._api_url("messages"),
                    headers=self._headers(),
                    json=payload,
                )
        except httpx.HTTPError as exc:
            raise WhatsAppDeliveryError(f"Could not reach WhatsApp API: {exc}") from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise WhatsAppDeliveryError(
                f"WhatsApp API returned invalid response ({response.status_code})."
            ) from exc

        if response.status_code >= 400:
            err = data.get("error", {})
            message = err.get("message") or str(data)
            code = err.get("code", response.status_code)
            raise WhatsAppDeliveryError(f"WhatsApp API error ({code}): {message}")

        return data

    def send_text(self, to_phone: str, message: str) -> dict[str, Any]:
        if not self.is_configured():
            raise WhatsAppNotConfiguredError(self.configuration_hint())

        recipient = normalize_pk_phone(to_phone)
        if not recipient:
            raise WhatsAppDeliveryError("Invalid WhatsApp number.")

        payload = {
            "messaging_product": "whatsapp",
            "to": recipient,
            "type": "text",
            "text": {"preview_url": True, "body": message[:4096]},
        }

        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                self._api_url("messages"),
                headers=self._headers(),
                json=payload,
            )

        data = response.json()
        if response.status_code >= 400:
            err = data.get("error", {})
            raise WhatsAppDeliveryError(
                err.get("message") or f"WhatsApp API error {response.status_code}"
            )
        return data

    def download_media(self, media_id: str) -> tuple[bytes, str]:
        """Download inbound WhatsApp media bytes and mime type."""
        if not self.is_configured():
            raise WhatsAppNotConfiguredError(self.configuration_hint())
        media_id = (media_id or "").strip()
        if not media_id:
            raise WhatsAppDeliveryError("Missing WhatsApp media id.")

        version = settings.whatsapp_api_version.strip() or "v21.0"
        meta_url = f"https://graph.facebook.com/{version}/{media_id}"
        headers = {"Authorization": f"Bearer {settings.whatsapp_api_token.strip()}"}
        with httpx.Client(timeout=60.0, follow_redirects=True) as client:
            meta = client.get(meta_url, headers=headers)
            if meta.status_code >= 400:
                raise WhatsAppDeliveryError("Could not resolve WhatsApp media.")
            info = meta.json()
            download_url = info.get("url")
            mime_type = str(info.get("mime_type") or "audio/ogg")
            if not download_url:
                raise WhatsAppDeliveryError("WhatsApp media URL missing.")
            binary = client.get(download_url, headers=headers)
            if binary.status_code >= 400:
                raise WhatsAppDeliveryError("Could not download WhatsApp media.")
            return binary.content, mime_type
