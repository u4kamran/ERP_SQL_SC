"""Generate public social media discovery search links for a contact."""

from __future__ import annotations

import re
from urllib.parse import quote_plus

from app.schemas.customer_contacts import SocialDiscoveryLink
from app.services.email_discovery_service import email_username, is_valid_email
from app.utils.phone_extract import extract_pk_mobiles, format_pk_phone_display, pk_phone_for_input


def build_social_discovery_links(
    *,
    name: str = "",
    phone_display: str = "",
    phone_raw: str = "",
    email: str = "",
) -> list[SocialDiscoveryLink]:
    """Build one-click public search links to find social profiles."""
    local_phone = phone_display or (f"0{phone_raw}" if phone_raw else "")
    intl_phone = f"92{phone_raw}" if phone_raw else ""
    clean_name = (name or "").strip()
    clean_email = (email or "").strip().lower()
    user = email_username(clean_email) if clean_email else ""

    queries: list[tuple[str, str, str, str]] = []

    if local_phone:
        queries.extend(
            [
                ("Messaging", "WhatsApp", f"https://wa.me/92{phone_raw}", "Open WhatsApp chat"),
                ("General", "Google — mobile number", _google(f'"{local_phone}" OR "+{intl_phone}"'), "Search web by phone"),
                ("Social Media", "Facebook", _google(f'site:facebook.com "{local_phone}"'), "Find Facebook profiles"),
                ("Social Media", "Instagram", _google(f'site:instagram.com "{local_phone}"'), "Find Instagram profiles"),
                ("Social Media", "LinkedIn", _google(f'site:linkedin.com "{local_phone}"'), "Find LinkedIn profiles"),
                ("Social Media", "TikTok", _google(f'site:tiktok.com "{local_phone}"'), "Find TikTok profiles"),
                ("Social Media", "X (Twitter)", _google(f'site:twitter.com OR site:x.com "{local_phone}"'), "Find X/Twitter profiles"),
            ]
        )

    if clean_email and is_valid_email(clean_email):
        queries.extend(
            [
                ("General", "Google — full email", _google(f'"{clean_email}"'), "Search entire web for this email"),
                ("General", "Google — email + social", _google(
                    f'"{clean_email}" (site:facebook.com OR site:instagram.com OR site:linkedin.com OR site:tiktok.com)'
                ), "Find social accounts mentioning this email"),
                ("Social Media", "Facebook search", f"https://www.facebook.com/search/top?q={quote_plus(clean_email)}", "Facebook public search"),
                ("Social Media", "Facebook (email)", _google(f'site:facebook.com "{clean_email}"'), "Google search on Facebook"),
                ("Social Media", "Instagram (email)", _google(f'site:instagram.com "{clean_email}"'), "Google search on Instagram"),
                ("Social Media", "LinkedIn (email)", _google(f'site:linkedin.com "{clean_email}"'), "Google search on LinkedIn"),
                ("Social Media", "TikTok (email)", _google(f'site:tiktok.com "{clean_email}"'), "Google search on TikTok"),
                ("Social Media", "X / Twitter (email)", _google(f'site:twitter.com OR site:x.com "{clean_email}"'), "Google search on X"),
                ("Social Media", "Pinterest (email)", _google(f'site:pinterest.com "{clean_email}"'), "Google search on Pinterest"),
                ("Social Media", "YouTube (email)", _google(f'site:youtube.com "{clean_email}"'), "Google search on YouTube"),
            ]
        )
        if user and len(user) >= 3:
            queries.extend(
                [
                    ("Username", "Google — email username", _google(
                        f'"{user}" (site:facebook.com OR site:instagram.com OR site:tiktok.com OR site:linkedin.com)'
                    ), f"Search social sites for username '{user}' from email"),
                    ("Username", "Instagram @username", _google(f'site:instagram.com "{user}"'), f"Instagram posts/profiles for {user}"),
                    ("Username", "Facebook @username", _google(f'site:facebook.com "{user}"'), f"Facebook pages/profiles for {user}"),
                ]
            )

    if clean_name and (local_phone or clean_email):
        combo = f'"{clean_name}"'
        if local_phone:
            combo += f' "{local_phone}"'
        if clean_email:
            combo += f' "{clean_email}"'
        queries.append(("General", "Google — name + contact", _google(combo), "Combined name and contact search"))

    if clean_name:
        queries.extend(
            [
                ("Social Media", "Facebook (name)", _google(f'site:facebook.com "{clean_name}" Pakistan'), "Search by customer name"),
                ("Social Media", "Instagram (name)", _google(f'site:instagram.com "{clean_name}"'), "Search Instagram by name"),
            ]
        )

    seen: set[str] = set()
    links: list[SocialDiscoveryLink] = []
    for category, label, url, description in queries:
        if url in seen:
            continue
        seen.add(url)
        links.append(
            SocialDiscoveryLink(
                category=category,
                label=label,
                url=url,
                description=description,
            )
        )
    return links


def normalize_lookup_phone(raw: str) -> tuple[str, str, str]:
    """Return (normalized 92..., display 03..., raw for wa.me)."""
    phones = extract_pk_mobiles(raw)
    if not phones:
        digits = re.sub(r"\D", "", raw or "")
        if len(digits) >= 10:
            return "", digits, digits[-10:]
        return "", "", ""
    normalized = phones[0]
    return normalized, format_pk_phone_display(normalized), pk_phone_for_input(normalized)


def _google(query: str) -> str:
    return f"https://www.google.com/search?q={quote_plus(query)}"
