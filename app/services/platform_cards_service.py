"""Build styled platform cards for marketing / promotion UIs."""

from __future__ import annotations

from app.schemas.customer_contacts import CustomerContactRow, DiscoveredProfile, SocialDiscoveryLink
from app.schemas.platform_cards import PlatformCard
from app.services.promotion_store import company_links

_PLATFORM_STYLES: dict[str, tuple[str, str]] = {
    "WhatsApp": ("bi-whatsapp", "#25D366"),
    "Facebook": ("bi-facebook", "#1877F2"),
    "Instagram": ("bi-instagram", "#E4405F"),
    "TikTok": ("bi-tiktok", "#000000"),
    "X (Twitter)": ("bi-twitter-x", "#000000"),
    "LinkedIn": ("bi-linkedin", "#0A66C2"),
    "YouTube": ("bi-youtube", "#FF0000"),
    "GitHub": ("bi-github", "#24292f"),
    "Gravatar": ("bi-person-circle", "#1e8cbe"),
    "Email": ("bi-envelope-fill", "#0d6efd"),
    "Price Scan": ("bi-upc-scan", "#198754"),
    "Website": ("bi-globe2", "#6f42c1"),
    "Google": ("bi-google", "#4285F4"),
    "Telegram": ("bi-telegram", "#0088cc"),
    "Pinterest": ("bi-pinterest", "#E60023"),
    "SMS": ("bi-chat-dots-fill", "#fd7e14"),
}


def _style_for_platform(platform: str) -> tuple[str, str]:
    return _PLATFORM_STYLES.get(platform, ("bi-search", "#6c757d"))


def _platform_from_label(label: str) -> str:
    lower = (label or "").lower()
    for name in _PLATFORM_STYLES:
        if name.lower() in lower:
            return name
    if "google" in lower:
        return "Google"
    if "twitter" in lower or "x.com" in lower:
        return "X (Twitter)"
    return "Google"


def build_platform_cards(
    contact: CustomerContactRow | None,
    discovered: list[DiscoveredProfile] | None = None,
    social_links: list[SocialDiscoveryLink] | None = None,
    *,
    include_company: bool = True,
    include_search: bool = True,
) -> list[PlatformCard]:
    """Assemble de-duplicated platform cards for contact lookup and promotion hub."""
    cards: list[PlatformCard] = []
    discovered = discovered or []
    social_links = social_links or []
    links = company_links()

    if contact and contact.phone_raw:
        cards.append(
            PlatformCard(
                platform="WhatsApp",
                icon="bi-whatsapp",
                color="#25D366",
                label="Send WhatsApp",
                url=contact.whatsapp or f"https://wa.me/92{contact.phone_raw}",
                action="open",
                description="Open WhatsApp chat",
            )
        )
        cards.append(
            PlatformCard(
                platform="SMS",
                icon="bi-chat-dots-fill",
                color="#fd7e14",
                label=contact.phone_display or f"0{contact.phone_raw}",
                url=f"sms:+92{contact.phone_raw}",
                action="open",
                description="Open SMS app",
            )
        )

    if contact and contact.email_display:
        cards.append(
            PlatformCard(
                platform="Email",
                icon="bi-envelope-fill",
                color="#0d6efd",
                label=contact.email_display,
                url=f"mailto:{contact.email_display}",
                action="open",
                description="Send email",
            )
        )

    if include_company:
        cards.append(
            PlatformCard(
                platform="Price Scan",
                icon="bi-upc-scan",
                color="#198754",
                label="Guest Price Scan",
                url=links["guest_price"],
                action="share",
                description="Share barcode price check link",
            )
        )
        cards.append(
            PlatformCard(
                platform="Website",
                icon="bi-globe2",
                color="#6f42c1",
                label="AH Steel Lab",
                url=links["company_website"],
                action="share",
                description="Company website",
            )
        )

    if contact:
        for platform, url, icon in [
            ("Facebook", contact.facebook, "bi-facebook"),
            ("Instagram", contact.instagram, "bi-instagram"),
            ("TikTok", contact.tiktok, "bi-tiktok"),
            ("YouTube", contact.youtube, "bi-youtube"),
            ("Website", contact.website, "bi-globe2"),
        ]:
            if url:
                icon_name, color = _style_for_platform(platform)
                cards.append(
                    PlatformCard(
                        platform=platform,
                        icon=icon,
                        color=color,
                        label=f"Saved {platform}",
                        url=url,
                        action="open",
                        confidence="verified",
                        description="Saved marketing profile",
                    )
                )

    for profile in discovered:
        icon, color = _style_for_platform(profile.platform)
        cards.append(
            PlatformCard(
                platform=profile.platform,
                icon=icon,
                color=color,
                label=profile.label,
                url=profile.url,
                action="open",
                confidence=profile.confidence,
                description=profile.source,
            )
        )

    if include_search:
        for link in social_links:
            platform = _platform_from_label(link.label)
            icon, color = _style_for_platform(platform)
            cards.append(
                PlatformCard(
                    platform=platform,
                    icon=icon,
                    color=color,
                    label=link.label,
                    url=link.url,
                    action="open",
                    confidence="search",
                    description=link.description or link.category,
                )
            )

    seen: set[str] = set()
    unique: list[PlatformCard] = []
    for card in cards:
        if card.url in seen:
            continue
        seen.add(card.url)
        unique.append(card)
    return unique
