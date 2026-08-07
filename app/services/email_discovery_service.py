"""Automatic public profile checks for an email address."""

from __future__ import annotations

import hashlib
import re

import httpx

from app.schemas.customer_contacts import DiscoveredProfile

_EMAIL_RE = re.compile(r"^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$", re.IGNORECASE)


def is_valid_email(email: str) -> bool:
    return bool(_EMAIL_RE.match((email or "").strip()))


def email_username(email: str) -> str:
    return (email or "").strip().lower().split("@", 1)[0]


def discover_profiles_by_email(email: str) -> list[DiscoveredProfile]:
    """Check public sources that may reveal profiles for an email."""
    email = (email or "").strip().lower()
    if not is_valid_email(email):
        return []

    results: list[DiscoveredProfile] = []
    results.extend(_check_gravatar(email))
    results.extend(_guess_username_profiles(email))
    return results


def _check_gravatar(email: str) -> list[DiscoveredProfile]:
    digest = hashlib.md5(email.encode("utf-8")).hexdigest()
    profile_url = f"https://gravatar.com/{digest}"
    api_url = f"https://en.gravatar.com/{digest}.json"

    try:
        with httpx.Client(timeout=8.0, follow_redirects=True) as client:
            response = client.get(api_url)
        if response.status_code != 200:
            return []

        data = response.json()
        entry = (data.get("entry") or [{}])[0]
        display_name = str(entry.get("displayName") or "").strip()
        accounts = entry.get("accounts") or []

        profiles: list[DiscoveredProfile] = []
        if display_name:
            profiles.append(
                DiscoveredProfile(
                    platform="Gravatar",
                    label=display_name,
                    url=profile_url,
                    confidence="verified",
                    source="Gravatar public profile",
                )
            )

        for account in accounts:
            domain = str(account.get("domain") or "").strip()
            username = str(account.get("username") or "").strip()
            shortname = str(account.get("shortname") or domain).strip()
            if not domain or not username:
                continue
            url = f"https://{domain}/{username}"
            profiles.append(
                DiscoveredProfile(
                    platform=shortname.title(),
                    label=f"@{username}",
                    url=url,
                    confidence="strong",
                    source="Linked from Gravatar profile",
                )
            )
        return profiles
    except (httpx.HTTPError, ValueError, KeyError):
        return []


def _guess_username_profiles(email: str) -> list[DiscoveredProfile]:
    """Public profile page guesses from email username — verify manually."""
    user = re.sub(r"[^a-z0-9._-]", "", email_username(email))
    if len(user) < 3:
        return []

    candidates = [
        ("Facebook", f"https://www.facebook.com/{user}", "Possible Facebook username"),
        ("Instagram", f"https://www.instagram.com/{user}/", "Possible Instagram username"),
        ("TikTok", f"https://www.tiktok.com/@{user}", "Possible TikTok username"),
        ("X (Twitter)", f"https://x.com/{user}", "Possible X/Twitter username"),
        ("GitHub", f"https://github.com/{user}", "Possible GitHub username"),
        ("YouTube", f"https://www.youtube.com/@{user}", "Possible YouTube channel"),
        ("LinkedIn", f"https://www.linkedin.com/in/{user}/", "Possible LinkedIn username"),
        ("Telegram", f"https://t.me/{user}", "Possible Telegram username"),
        ("Pinterest", f"https://www.pinterest.com/{user}/", "Possible Pinterest profile"),
    ]

    return [
        DiscoveredProfile(
            platform=platform,
            label=f"Try @{user}",
            url=url,
            confidence="likely",
            source=note,
        )
        for platform, url, note in candidates
    ]
