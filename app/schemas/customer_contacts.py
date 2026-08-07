"""Customer marketing contact directory schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.platform_cards import PlatformCard


class CustomerMarketingLinks(BaseModel):
    email: str = ""
    facebook: str = ""
    instagram: str = ""
    whatsapp: str = ""
    tiktok: str = ""
    youtube: str = ""
    website: str = ""
    notes: str = ""


class CustomerMarketingLinksUpdate(CustomerMarketingLinks):
    pass


class CustomerContactRow(BaseModel):
    contact_key: str
    cust_sms_id: int
    ac_id: int | None = None
    ac_id_display: str = ""
    name: str
    party_type: str = "customer"
    phone_display: str = ""
    phone_raw: str = ""
    phone_alt_display: str = ""
    contact_person: str = ""
    address: str = ""
    added_at: str = ""
    erp_email: str = ""
    marketing_email: str = ""
    email_display: str = ""
    facebook: str = ""
    instagram: str = ""
    whatsapp: str = ""
    tiktok: str = ""
    youtube: str = ""
    website: str = ""
    notes: str = ""
    current_balance: float | None = None
    has_phone: bool = False
    has_email: bool = False
    has_social: bool = False
    gl_linked: bool = False


class CustomerContactListResponse(BaseModel):
    items: list[CustomerContactRow] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 50
    with_phone: int = 0
    with_email: int = 0
    with_social: int = 0


class CustomerContactStats(BaseModel):
    total_accounts: int = 0
    with_phone: int = 0
    with_email: int = 0
    with_social: int = 0
    missing_all: int = 0
    gl_linked: int = 0


class SocialDiscoveryLink(BaseModel):
    category: str
    label: str
    url: str
    description: str = ""


class DiscoveredProfile(BaseModel):
    platform: str
    label: str
    url: str
    confidence: str = "likely"
    source: str = ""


class ContactLookupResponse(BaseModel):
    found: bool = False
    lookup_type: str = ""
    query: str = ""
    match_count: int = 0
    contacts: list[CustomerContactRow] = Field(default_factory=list)
    social_links: list[SocialDiscoveryLink] = Field(default_factory=list)
    discovered_profiles: list[DiscoveredProfile] = Field(default_factory=list)
    platform_cards: list[PlatformCard] = Field(default_factory=list)
    message: str = ""
    help_note: str = ""
