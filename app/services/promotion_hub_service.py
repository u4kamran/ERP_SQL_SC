"""Promotion hub — compose and send marketing messages."""

from __future__ import annotations

from app.config.settings import settings
from app.schemas.customer_contacts import DiscoveredProfile
from app.schemas.promotion_hub import (
    PromotionChannelStatus,
    PromotionComposeResponse,
    PromotionTemplate,
    SendPromotionRequest,
    SendPromotionResponse,
)
from app.services.customer_contacts_service import CustomerContactsService
from app.services.email_discovery_service import discover_profiles_by_email
from app.services.email_service import EmailDeliveryError, EmailNotConfiguredError, EmailService
from app.services.platform_cards_service import build_platform_cards
from app.services.promotion_store import company_links, load_templates
from app.services.social_discovery_service import build_social_discovery_links
from app.services.whatsapp_service import (
    WhatsAppDeliveryError,
    WhatsAppNotConfiguredError,
    WhatsAppService,
    normalize_pk_phone,
)
from app.utils.phone_extract import pk_phone_for_input

class PromotionHubService:
    def __init__(self, db):
        self.db = db
        self.contacts = CustomerContactsService(db)

    def channel_status(self) -> PromotionChannelStatus:
        wa = WhatsAppService()
        em = EmailService()
        links = company_links()
        return PromotionChannelStatus(
            whatsapp_configured=wa.is_configured(),
            email_configured=em.is_configured(),
            whatsapp_hint=wa.configuration_hint(),
            email_hint=em.configuration_hint(),
            guest_price_url=links["guest_price"],
            company_website=links["company_website"],
        )

    def compose(
        self,
        *,
        phone: str = "",
        email: str = "",
        cust_sms_id: int | None = None,
        template_id: str = "sale",
    ) -> PromotionComposeResponse:
        contact = None
        discovered: list[DiscoveredProfile] = []
        social_links = []

        if cust_sms_id:
            contact = self.contacts.get_contact(cust_sms_id)
        elif phone.strip():
            lookup = self.contacts.lookup_contact(phone=phone.strip())
            contact = lookup.contacts[0] if lookup.contacts else None
            discovered = lookup.discovered_profiles
            social_links = lookup.social_links
        elif email.strip():
            lookup = self.contacts.lookup_contact(email=email.strip())
            contact = lookup.contacts[0] if lookup.contacts else None
            discovered = lookup.discovered_profiles
            social_links = lookup.social_links
            if not discovered and email.strip():
                discovered = discover_profiles_by_email(email.strip())

        if contact and not discovered and contact.email_display:
            discovered = discover_profiles_by_email(contact.email_display)

        if contact and not social_links:
            social_links = build_social_discovery_links(
                name=contact.name,
                phone_display=contact.phone_display,
                phone_raw=contact.phone_raw,
                email=contact.email_display,
            )

        templates = load_templates()
        template = next((t for t in templates if t.id == template_id), templates[0])
        links = company_links()
        preview = self._render_message(
            template,
            name=contact.name if contact else "Customer",
            link=template.link or links["guest_price"],
        )

        platform_cards = build_platform_cards(
            contact,
            discovered,
            social_links,
            include_company=True,
            include_search=False,
        )
        # Promotion hub: WhatsApp/Email cards use send action
        for card in platform_cards:
            if card.platform == "WhatsApp":
                card.action = "send"
            elif card.platform == "Email":
                card.action = "send"

        return PromotionComposeResponse(
            contact=contact,
            discovered_profiles=discovered,
            social_links=social_links,
            platform_cards=platform_cards,
            templates=templates,
            channels=self.channel_status(),
            preview_message=preview,
        )

    def send(self, body: SendPromotionRequest) -> SendPromotionResponse:
        contact = None
        if body.cust_sms_id:
            contact = self.contacts.get_contact(body.cust_sms_id)

        phone = body.phone.strip() or (contact.phone_raw if contact else "")
        email = body.email.strip() or (contact.email_display if contact else "")
        full_message = body.message.strip()
        if body.link.strip() and body.link.strip() not in full_message:
            full_message = f"{full_message}\n\n{body.link.strip()}"

        if body.channel == "email":
            if not email:
                return SendPromotionResponse(
                    success=False,
                    channel="email",
                    message="No email address. Save email on customer first or enter one.",
                )
            try:
                EmailService().send_email(
                    [email],
                    body.subject.strip() or f"Offers from {settings.app_name}",
                    full_message,
                )
                return SendPromotionResponse(
                    success=True,
                    channel="email",
                    message=f"Promotion email sent to {email}.",
                )
            except EmailNotConfiguredError as exc:
                return SendPromotionResponse(success=False, channel="email", message=str(exc))
            except EmailDeliveryError as exc:
                return SendPromotionResponse(success=False, channel="email", message=str(exc))

        # WhatsApp
        normalized = normalize_pk_phone(phone)
        if not normalized:
            return SendPromotionResponse(
                success=False,
                channel=body.channel,
                message="No valid mobile number for WhatsApp.",
            )

        wa_url = f"https://wa.me/{normalized}?text={self._wa_encode(full_message)}"

        if body.channel == "whatsapp_manual":
            return SendPromotionResponse(
                success=True,
                channel="whatsapp_manual",
                message="WhatsApp opened with pre-filled message.",
                manual_url=wa_url,
            )

        wa = WhatsAppService()
        if not wa.is_configured():
            return SendPromotionResponse(
                success=True,
                channel="whatsapp_manual",
                message="WhatsApp API not configured — use manual WhatsApp link.",
                manual_url=wa_url,
            )

        try:
            wa.send_text(phone, full_message)
            return SendPromotionResponse(
                success=True,
                channel="whatsapp",
                message=f"Promotion sent via WhatsApp to {contact.phone_display if contact else phone}.",
                manual_url=wa_url,
            )
        except (WhatsAppNotConfiguredError, WhatsAppDeliveryError):
            return SendPromotionResponse(
                success=True,
                channel="whatsapp_manual",
                message="API send failed — use manual WhatsApp link.",
                manual_url=wa_url,
            )

    @staticmethod
    def _render_message(template: PromotionTemplate, *, name: str, link: str) -> str:
        links = company_links()
        return (
            template.message.replace("{name}", name)
            .replace("{link}", link)
            .replace("{company}", links["company_name"])
        )

    @staticmethod
    def _wa_encode(text: str) -> str:
        from urllib.parse import quote

        return quote(text)
