"""Utility functions."""

import hashlib
import secrets
from typing import Optional

from fastapi import Request
from user_agents import parse

from app.config.settings import settings


def hash_token(token: str) -> str:
    """SHA-256 hash for storing tokens securely."""
    return hashlib.sha256(token.encode()).hexdigest()


def generate_secure_token(length: int = 32) -> str:
    return secrets.token_urlsafe(length)


def get_client_ip(request: Request) -> str:
    """Extract real client IP, supporting Cloudflare and reverse proxies."""
    if settings.trust_proxy_headers:
        cf_ip = request.headers.get(settings.cloudflare_ip_header)
        if cf_ip:
            return cf_ip.strip()

        x_forwarded_for = request.headers.get("X-Forwarded-For")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()

        x_real_ip = request.headers.get("X-Real-IP")
        if x_real_ip:
            return x_real_ip.strip()

    if request.client:
        return request.client.host
    return "unknown"


def get_request_scheme(request: Request) -> str:
    """Detect HTTPS behind reverse proxy / Cloudflare."""
    if settings.trust_proxy_headers:
        forwarded_proto = request.headers.get("X-Forwarded-Proto")
        if forwarded_proto:
            return forwarded_proto.lower()
        cf_visitor = request.headers.get("CF-Visitor")
        if cf_visitor and '"https"' in cf_visitor:
            return "https"
    return request.url.scheme


def parse_user_agent(user_agent: Optional[str]) -> dict:
    """Parse User-Agent string into browser, device, and OS."""
    if not user_agent:
        return {"browser": "Unknown", "device": "Unknown", "os": "Unknown"}

    ua = parse(user_agent)
    browser = f"{ua.browser.family} {ua.browser.version_string}".strip()
    device = ua.device.family or ("Mobile" if ua.is_mobile else "Desktop")
    os_name = f"{ua.os.family} {ua.os.version_string}".strip()

    return {
        "browser": browser or "Unknown",
        "device": device,
        "os": os_name or "Unknown",
    }
