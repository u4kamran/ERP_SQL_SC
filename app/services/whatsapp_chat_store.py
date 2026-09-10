"""JSON-backed WhatsApp / offline chatbot conversations and config."""

from __future__ import annotations

import json
import re
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from app.schemas.whatsapp_bot import WhatsAppBotConfig
from app.config.settings import settings

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_DATA_DIR = _PROJECT_ROOT / "data"
_CONFIG_FILE = _DATA_DIR / "whatsapp_bot_config.json"
_CHATS_FILE = _DATA_DIR / "whatsapp_bot_chats.json"
_LOCK = threading.Lock()
_MAX_MESSAGES = 200
_MAX_CONVERSATIONS = 500


def _now() -> datetime:
    return datetime.utcnow()


def _ensure_data_dir() -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)


def _default_config() -> dict[str, Any]:
    data = WhatsAppBotConfig().model_dump()
    data["store_address"] = (settings.company_name or settings.app_name or "").strip()
    return data


def _ensure_order_status_menu(text: str) -> str:
    """Keep option 6 in saved welcome text even if an older admin save omitted it."""
    value = (text or "").strip()
    if not value:
        return value
    lower = value.lower()
    if "6 my order" in lower or "my order status" in lower:
        return value
    if "5 talk to staff" in lower:
        return re.sub(
            r"(?im)^(5\s+Talk to staff)\s*$",
            r"\1\n6 My order status",
            value,
            count=1,
        )
    if re.search(r"(?im)^5\s+", value):
        return value.rstrip() + "\n6 My order status"
    return value


def load_config() -> WhatsAppBotConfig:
    with _LOCK:
        _ensure_data_dir()
        if not _CONFIG_FILE.exists():
            data = _default_config()
            _CONFIG_FILE.write_text(
                json.dumps(data, indent=2), encoding="utf-8"
            )
            return WhatsAppBotConfig(**data)
        try:
            raw = json.loads(_CONFIG_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            raw = _default_config()
        merged = {**_default_config(), **(raw if isinstance(raw, dict) else {})}
        welcome = _ensure_order_status_menu(str(merged.get("welcome_message") or ""))
        returning = _ensure_order_status_menu(
            str(merged.get("returning_welcome_message") or "")
        )
        if welcome != merged.get("welcome_message") or returning != merged.get(
            "returning_welcome_message"
        ):
            merged["welcome_message"] = welcome
            merged["returning_welcome_message"] = returning
            try:
                _CONFIG_FILE.write_text(
                    json.dumps(merged, indent=2), encoding="utf-8"
                )
            except OSError:
                pass
        return WhatsAppBotConfig(**merged)


def save_config(config: WhatsAppBotConfig) -> WhatsAppBotConfig:
    with _LOCK:
        _ensure_data_dir()
        payload = config.model_dump()
        payload["welcome_message"] = _ensure_order_status_menu(
            str(payload.get("welcome_message") or "")
        )
        payload["returning_welcome_message"] = _ensure_order_status_menu(
            str(payload.get("returning_welcome_message") or "")
        )
        _CONFIG_FILE.write_text(
            json.dumps(payload, indent=2), encoding="utf-8"
        )
        return WhatsAppBotConfig(**payload)


def _load_chats_unlocked() -> dict[str, Any]:
    _ensure_data_dir()
    if not _CHATS_FILE.exists():
        return {"conversations": {}}
    try:
        raw = json.loads(_CHATS_FILE.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return {"conversations": {}}
        conversations = raw.get("conversations") or {}
        if not isinstance(conversations, dict):
            conversations = {}
        return {"conversations": conversations}
    except (json.JSONDecodeError, OSError):
        return {"conversations": {}}


def _save_chats_unlocked(data: dict[str, Any]) -> None:
    _ensure_data_dir()
    conversations = data.get("conversations") or {}
    if len(conversations) > _MAX_CONVERSATIONS:
        ordered = sorted(
            conversations.items(),
            key=lambda item: item[1].get("updated_at") or "",
            reverse=True,
        )
        conversations = dict(ordered[:_MAX_CONVERSATIONS])
        data["conversations"] = conversations
    _CHATS_FILE.write_text(
        json.dumps(data, indent=2, default=str), encoding="utf-8"
    )


def list_conversations() -> list[dict[str, Any]]:
    with _LOCK:
        data = _load_chats_unlocked()
        items = list(data["conversations"].values())
    items.sort(key=lambda item: item.get("updated_at") or "", reverse=True)
    return items


def get_conversation(conversation_id: str) -> dict[str, Any] | None:
    with _LOCK:
        data = _load_chats_unlocked()
        item = data["conversations"].get(conversation_id)
        return dict(item) if item else None


def find_by_phone(phone: str) -> dict[str, Any] | None:
    digits = "".join(ch for ch in (phone or "") if ch.isdigit())
    if not digits:
        return None
    with _LOCK:
        data = _load_chats_unlocked()
        for item in data["conversations"].values():
            existing = "".join(
                ch for ch in str(item.get("phone") or "") if ch.isdigit()
            )
            if existing and existing[-10:] == digits[-10:]:
                return dict(item)
    return None


def upsert_conversation(
    *,
    conversation_id: str | None = None,
    phone: str = "",
    display_name: str = "",
    channel: str = "offline",
    status: str | None = None,
) -> dict[str, Any]:
    with _LOCK:
        data = _load_chats_unlocked()
        conversations = data["conversations"]
        found_id = conversation_id
        if not found_id and phone:
            for key, item in conversations.items():
                existing = "".join(
                    ch for ch in str(item.get("phone") or "") if ch.isdigit()
                )
                digits = "".join(ch for ch in phone if ch.isdigit())
                if existing and digits and existing[-10:] == digits[-10:]:
                    found_id = key
                    break
        if not found_id:
            found_id = str(uuid.uuid4())
        current = conversations.get(found_id) or {
            "conversation_id": found_id,
            "phone": phone,
            "display_name": display_name or phone or "Guest",
            "channel": channel,
            "status": "bot",
            "unread": 0,
            "updated_at": _now().isoformat(),
            "last_message": "",
            "messages": [],
        }
        if phone:
            current["phone"] = phone
        if display_name:
            current["display_name"] = display_name
        current["channel"] = channel or current.get("channel") or "offline"
        if status:
            current["status"] = status
        current["updated_at"] = _now().isoformat()
        conversations[found_id] = current
        data["conversations"] = conversations
        _save_chats_unlocked(data)
        return dict(current)


def append_message(
    conversation_id: str,
    *,
    direction: str,
    text: str,
    channel: str = "offline",
    sender: str = "",
    increase_unread: bool = False,
) -> dict[str, Any]:
    with _LOCK:
        data = _load_chats_unlocked()
        conversation = data["conversations"].get(conversation_id)
        if not conversation:
            raise KeyError(conversation_id)
        message = {
            "id": str(uuid.uuid4()),
            "direction": direction,
            "text": text,
            "created_at": _now().isoformat(),
            "channel": channel,
            "sender": sender,
        }
        messages = list(conversation.get("messages") or [])
        messages.append(message)
        conversation["messages"] = messages[-_MAX_MESSAGES:]
        conversation["last_message"] = text[:240]
        conversation["updated_at"] = message["created_at"]
        conversation["channel"] = channel or conversation.get("channel")
        if increase_unread:
            conversation["unread"] = int(conversation.get("unread") or 0) + 1
        data["conversations"][conversation_id] = conversation
        _save_chats_unlocked(data)
        return dict(conversation)


def set_status(conversation_id: str, status: str) -> dict[str, Any]:
    with _LOCK:
        data = _load_chats_unlocked()
        conversation = data["conversations"].get(conversation_id)
        if not conversation:
            raise KeyError(conversation_id)
        conversation["status"] = status
        conversation["updated_at"] = _now().isoformat()
        data["conversations"][conversation_id] = conversation
        _save_chats_unlocked(data)
        return dict(conversation)


def mark_read(conversation_id: str) -> dict[str, Any]:
    with _LOCK:
        data = _load_chats_unlocked()
        conversation = data["conversations"].get(conversation_id)
        if not conversation:
            raise KeyError(conversation_id)
        conversation["unread"] = 0
        data["conversations"][conversation_id] = conversation
        _save_chats_unlocked(data)
        return dict(conversation)


def update_context(
    conversation_id: str,
    context: dict[str, Any] | None,
) -> dict[str, Any]:
    with _LOCK:
        data = _load_chats_unlocked()
        conversation = data["conversations"].get(conversation_id)
        if not conversation:
            raise KeyError(conversation_id)
        if context is None:
            conversation.pop("context", None)
        else:
            conversation["context"] = context
        conversation["updated_at"] = _now().isoformat()
        data["conversations"][conversation_id] = conversation
        _save_chats_unlocked(data)
        return dict(conversation)


def unread_total() -> int:
    with _LOCK:
        data = _load_chats_unlocked()
        return sum(int(item.get("unread") or 0) for item in data["conversations"].values())
