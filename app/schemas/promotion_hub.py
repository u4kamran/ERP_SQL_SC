"""Promotion hub schemas."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.customer_contacts import CustomerContactRow, DiscoveredProfile, SocialDiscoveryLink
from app.schemas.platform_cards import PlatformCard


class PromotionTemplate(BaseModel):
    id: str
    name: str
    subject: str = ""
    message: str
    link: str = ""


class PromotionChannelStatus(BaseModel):
    whatsapp_configured: bool = False
    email_configured: bool = False
    whatsapp_hint: str = ""
    email_hint: str = ""
    guest_price_url: str = ""
    company_website: str = ""


class PromotionComposeResponse(BaseModel):
    contact: CustomerContactRow | None = None
    discovered_profiles: list[DiscoveredProfile] = Field(default_factory=list)
    social_links: list[SocialDiscoveryLink] = Field(default_factory=list)
    platform_cards: list[PlatformCard] = Field(default_factory=list)
    templates: list[PromotionTemplate] = Field(default_factory=list)
    channels: PromotionChannelStatus
    preview_message: str = ""


class SendPromotionRequest(BaseModel):
    cust_sms_id: int | None = None
    phone: str = ""
    email: str = ""
    subject: str = Field("", max_length=200)
    message: str = Field(..., min_length=1, max_length=4000)
    link: str = Field("", max_length=500)
    channel: Literal["whatsapp", "email", "whatsapp_manual"]


class SendPromotionResponse(BaseModel):
    success: bool
    channel: str
    message: str
    manual_url: str = ""
