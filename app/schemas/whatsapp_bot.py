"""Schemas for WhatsApp / offline chatbot inbox."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class WhatsAppBotConfig(BaseModel):
    online_mode: bool = False
    auto_reply: bool = True
    welcome_message: str = (
        "Assalam-o-Alaikum{name_part}!\n"
        "Welcome to {company}.\n"
        "We are pleased to assist you.\n\n"
        "How may we help you today?\n"
        "1 Delivery status\n"
        "2 Store info\n"
        "3 Price list (text / voice)\n"
        "4 Place order\n"
        "5 Talk to staff\n"
        "6 My order status"
    )
    returning_welcome_message: str = (
        "Assalam-o-Alaikum, *{name}*!\n"
        "Welcome back to {company}.\n"
        "It is our pleasure to serve you again.\n\n"
        "How may we assist you today?\n"
        "1 Delivery status\n"
        "2 Store info\n"
        "3 Price list (text / voice)\n"
        "4 Place order\n"
        "5 Talk to staff\n"
        "6 My order status"
    )
    store_phone: str = ""
    store_address: str = "Shafique Departmental Store"
    store_hours: str = "Daily 8:00 AM – 10:00 PM"
    human_handoff_message: str = (
        "A staff member will contact you shortly. "
        "You can also call the store."
    )


class WhatsAppBotConfigUpdate(WhatsAppBotConfig):
    pass


class ChatMessage(BaseModel):
    id: str
    direction: Literal["in", "out", "system"]
    text: str
    created_at: datetime
    channel: Literal["whatsapp", "offline"] = "offline"
    sender: str = ""


class ChatConversation(BaseModel):
    conversation_id: str
    phone: str = ""
    display_name: str = ""
    channel: Literal["whatsapp", "offline"] = "offline"
    status: Literal["bot", "human", "closed"] = "bot"
    unread: int = 0
    updated_at: datetime
    last_message: str = ""
    messages: list[ChatMessage] = Field(default_factory=list)


class ChatConversationSummary(BaseModel):
    conversation_id: str
    phone: str = ""
    display_name: str = ""
    channel: Literal["whatsapp", "offline"]
    status: Literal["bot", "human", "closed"]
    unread: int = 0
    updated_at: datetime
    last_message: str = ""


class OfflineChatRequest(BaseModel):
    conversation_id: str | None = None
    message: str = Field(..., min_length=1, max_length=2000)
    display_name: str = Field("", max_length=100)
    phone: str = Field("", max_length=30)
    latitude: float | None = None
    longitude: float | None = None
    accuracy: float | None = None

    @field_validator("message", "display_name", "phone", mode="before")
    @classmethod
    def strip_text(cls, value):
        return value.strip() if isinstance(value, str) else value


class ChatQuickReply(BaseModel):
    """Tap control shown under a bot reply (web chat)."""

    title: str = Field(..., min_length=1, max_length=120)
    payload: str = Field(..., min_length=1, max_length=200)
    style: Literal["chip", "item", "action"] = "chip"
    subtitle: str = Field("", max_length=80)
    meta: str = Field("", max_length=40)


class OfflineChatResponse(BaseModel):
    conversation: ChatConversation
    reply: str
    quick_replies: list[ChatQuickReply] = Field(default_factory=list)
    phone_verified: bool = False


class MobileOtpSendRequest(BaseModel):
    phone: str = Field(..., min_length=7, max_length=30)

    @field_validator("phone", mode="before")
    @classmethod
    def strip_phone(cls, value):
        return value.strip() if isinstance(value, str) else value


class MobileOtpVerifyRequest(BaseModel):
    phone: str = Field(..., min_length=7, max_length=30)
    code: str = Field(..., min_length=4, max_length=10)

    @field_validator("phone", "code", mode="before")
    @classmethod
    def strip_fields(cls, value):
        return value.strip() if isinstance(value, str) else value


class MobileOtpResponse(BaseModel):
    ok: bool = True
    phone: str = ""
    message: str = ""
    expires_in: int | None = None
    sent_via: str | None = None
    verified: bool = False
    dev_code: str | None = None


class StaffReplyRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)

    @field_validator("message", mode="before")
    @classmethod
    def strip_message(cls, value):
        return value.strip() if isinstance(value, str) else value


class ConversationStatusUpdate(BaseModel):
    status: Literal["bot", "human", "closed"]


class WhatsAppBotStatus(BaseModel):
    bot_enabled: bool
    online_mode: bool
    auto_reply: bool
    whatsapp_configured: bool
    webhook_url: str
    verify_token_configured: bool
    configuration_hint: str
    conversation_count: int = 0
    unread_total: int = 0
    pending_orders: int = 0
