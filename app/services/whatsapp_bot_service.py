"""Small rule-based chatbot for delivery / store questions (online + offline)."""

from __future__ import annotations

import logging
import re
from typing import Any

from sqlalchemy.orm import Session

from app.config.settings import settings
from app.repositories.delivery_repository import DeliveryRepository
from app.schemas.whatsapp_bot import (
    ChatConversation,
    ChatConversationSummary,
    ChatMessage,
    ChatQuickReply,
    OfflineChatRequest,
    OfflineChatResponse,
    StaffReplyRequest,
    WhatsAppBotConfig,
    WhatsAppBotConfigUpdate,
    WhatsAppBotStatus,
)
from app.services import whatsapp_chat_store as store
from app.services.guest_price_lookup_service import is_hidden_shop_title
from app.services.item_price_search_service import ItemPriceSearchService
from app.services.mobile_otp_service import MobileOtpService
from app.services.speech_to_text_service import SpeechToTextError, SpeechToTextService
from app.services import voice_search_control_store as voice_control
from app.services.whatsapp_order_service import WhatsAppOrderService
from app.services.whatsapp_shop_service import (
    WhatsAppShopService,
    is_shop_nav_message,
    parse_area_line,
    parse_fulfill,
    parse_hub_action,
    parse_open_category,
    parse_sub_index,
    shop_cart_hint,
)
from app.services.whatsapp_service import (
    WhatsAppDeliveryError,
    WhatsAppNotConfiguredError,
    WhatsAppService,
    normalize_pk_phone,
)

logger = logging.getLogger("ahsteellab")


class WhatsAppBotService:
    def __init__(self, db: Session | None = None):
        self.db = db
        self.whatsapp = WhatsAppService()

    def status(self) -> WhatsAppBotStatus:
        config = store.load_config()
        base = settings.base_url.rstrip("/")
        return WhatsAppBotStatus(
            bot_enabled=bool(settings.whatsapp_bot_enabled),
            online_mode=bool(config.online_mode and self.whatsapp.is_configured()),
            auto_reply=config.auto_reply,
            whatsapp_configured=self.whatsapp.is_configured(),
            webhook_url=f"{base}/api/v1/public/whatsapp/webhook",
            verify_token_configured=bool(settings.whatsapp_verify_token.strip()),
            configuration_hint=self._configuration_hint(config),
            conversation_count=len(store.list_conversations()),
            unread_total=store.unread_total(),
            pending_orders=WhatsAppOrderService.pending_count(),
        )

    def get_config(self) -> WhatsAppBotConfig:
        return store.load_config()

    def update_config(self, data: WhatsAppBotConfigUpdate) -> WhatsAppBotConfig:
        return store.save_config(WhatsAppBotConfig(**data.model_dump()))

    def list_conversations(self) -> list[ChatConversationSummary]:
        items = []
        for row in store.list_conversations():
            items.append(
                ChatConversationSummary(
                    conversation_id=row["conversation_id"],
                    phone=row.get("phone") or "",
                    display_name=row.get("display_name") or "",
                    channel=row.get("channel") or "offline",
                    status=row.get("status") or "bot",
                    unread=int(row.get("unread") or 0),
                    updated_at=row["updated_at"],
                    last_message=row.get("last_message") or "",
                )
            )
        return items

    def get_conversation(self, conversation_id: str) -> ChatConversation:
        row = store.get_conversation(conversation_id)
        if not row:
            raise KeyError(conversation_id)
        store.mark_read(conversation_id)
        return self._to_conversation(store.get_conversation(conversation_id) or row)

    def set_status(self, conversation_id: str, status: str) -> ChatConversation:
        return self._to_conversation(store.set_status(conversation_id, status))

    def offline_chat(self, body: OfflineChatRequest) -> OfflineChatResponse:
        phone = normalize_pk_phone(body.phone) or body.phone.strip()
        conversation = store.upsert_conversation(
            conversation_id=body.conversation_id,
            display_name=body.display_name or "Guest",
            phone=phone,
            channel="offline",
        )
        conversation = self._attach_known_customer(conversation)
        # Browser GPS pin for Google Maps (guest chat Share Location).
        if body.latitude is not None and body.longitude is not None:
            ctx = dict(conversation.get("context") or {})
            if ctx.get("mode") == "order" or not ctx:
                ctx["latitude"] = float(body.latitude)
                ctx["longitude"] = float(body.longitude)
                if body.accuracy is not None:
                    ctx["location_accuracy"] = float(body.accuracy)
                ctx["maps_url"] = (
                    f"https://www.google.com/maps?q="
                    f"{float(body.latitude)},{float(body.longitude)}"
                )
                if ctx.get("mode") == "order":
                    store.update_context(conversation["conversation_id"], ctx)
                    conversation = (
                        store.get_conversation(conversation["conversation_id"])
                        or conversation
                    )
        inbound_text = body.message
        if (
            body.latitude is not None
            and body.longitude is not None
            and inbound_text.strip().upper() in {"LOCATION", "LOC", "GPS", "MAP"}
        ):
            inbound_text = f"LOC {body.latitude},{body.longitude}"
        conversation = store.append_message(
            conversation["conversation_id"],
            direction="in",
            text=inbound_text,
            channel="offline",
            sender=conversation.get("display_name") or body.display_name or "Guest",
            increase_unread=True,
        )
        reply = self._build_reply(
            inbound_text,
            phone=conversation.get("phone") or phone or "",
            conversation=conversation,
        )
        if reply.get("handoff"):
            store.set_status(conversation["conversation_id"], "human")
        conversation = (
            store.get_conversation(conversation["conversation_id"]) or conversation
        )
        quick_replies = self._quick_replies_for(conversation)
        reply_text = reply["text"]
        ctx = conversation.get("context") or {}
        shop_view = str(ctx.get("shop_view") or "")
        item_replies = [q for q in quick_replies if q.style == "item"]
        # After add-to-cart while browsing: short confirmation + stay on shelf.
        if not reply.get("stay_in_shop"):
            # Web chat uses tap rows — keep a short hint, not a duplicate numbered list.
            if item_replies:
                all_categories = all(
                    str(q.payload or "").upper().startswith("CAT ") for q in item_replies
                )
                if shop_view == "categories" or all_categories:
                    reply_text = (
                        "Shop by category — tap a department below.\n"
                        "Tap *Categories* anytime to return to this list."
                    )
                else:
                    reply_text = (
                        "Products below — use − / + and tap *ADD*.\n"
                        "You stay on this list to buy more. "
                        "Use *Categories* or *Back* to move around."
                    )
            # Cart UI is button-based — keep only a short summary, not full receipt text.
            if any(item.style == "cart" for item in quick_replies):
                reply_text = reply.get("short_text") or self._cart_short_text(
                    (conversation.get("context") or {}).get("cart") or [],
                    note=reply.get("note") or "",
                )
        # Silent shelf add — refresh product list only, no chat bubble.
        skip_bubble = bool(reply.get("stay_in_shop")) or (
            bool(reply.get("silent_ui"))
            and any(item.style == "cart" for item in quick_replies)
        )
        if reply.get("stay_in_shop"):
            reply_text = ""
        if not skip_bubble:
            conversation = store.append_message(
                conversation["conversation_id"],
                direction="out",
                text=reply_text,
                channel="offline",
                sender="bot",
            )
        else:
            conversation = (
                store.get_conversation(conversation["conversation_id"]) or conversation
            )
        phone_verified = False
        if phone:
            phone_verified = MobileOtpService().is_verified(phone)
        placeholder, hint = self._input_prompt_for(conversation)
        ctx = conversation.get("context") or {}
        cart = list(ctx.get("cart") or [])
        orders = WhatsAppOrderService()
        totals = orders.totals(cart) if cart else {"item_count": 0, "order_total": 0.0}
        return OfflineChatResponse(
            conversation=self._to_conversation(conversation),
            reply="" if skip_bubble else reply_text,
            quick_replies=quick_replies,
            phone_verified=phone_verified,
            input_placeholder=placeholder,
            input_hint=hint,
            shop_category_id=ctx.get("shop_category_id"),
            shop_category_title=ctx.get("shop_category_title") or "",
            shop_view=ctx.get("shop_view") or "",
            cart_count=int(totals.get("item_count") or 0),
            cart_total=float(totals.get("order_total") or 0),
            stay_in_shop=bool(reply.get("stay_in_shop")),
            added_manual_id=reply.get("added_manual_id"),
        )

    def staff_reply(
        self,
        conversation_id: str,
        body: StaffReplyRequest,
        *,
        actor_username: str,
    ) -> ChatConversation:
        conversation = store.get_conversation(conversation_id)
        if not conversation:
            raise KeyError(conversation_id)
        config = store.load_config()
        channel = conversation.get("channel") or "offline"
        phone = (conversation.get("phone") or "").strip()

        # WhatsApp chats must actually deliver via Cloud API — never fake-send.
        if channel == "whatsapp":
            if not phone:
                raise RuntimeError(
                    "This WhatsApp chat has no customer phone number, "
                    "so the message cannot be delivered."
                )
            if not self.whatsapp.is_configured():
                raise RuntimeError(
                    "WhatsApp Cloud API is not configured. "
                    "In .env set WHATSAPP_ENABLED=true, WHATSAPP_API_TOKEN, "
                    "and WHATSAPP_PHONE_NUMBER_ID, then restart the app."
                )
            if not config.online_mode:
                raise RuntimeError(
                    "WhatsApp phone delivery is OFF. "
                    "In Bot Settings turn on “Deliver replies to WhatsApp phones”, "
                    "save, then send again. (This is not the guest web chat.)"
                )
            try:
                self.whatsapp.send_text(phone, body.message)
            except WhatsAppNotConfiguredError as exc:
                raise RuntimeError(str(exc)) from exc
            except WhatsAppDeliveryError as exc:
                raise RuntimeError(f"WhatsApp delivery failed: {exc}") from exc

        conversation = store.append_message(
            conversation_id,
            direction="out",
            text=body.message,
            channel=channel,
            sender=actor_username,
        )
        store.set_status(conversation_id, "human")
        return self._to_conversation(
            store.get_conversation(conversation_id) or conversation
        )

    def handle_inbound_whatsapp(
        self,
        *,
        phone: str,
        text: str,
        profile_name: str = "",
    ) -> str | None:
        if not settings.whatsapp_bot_enabled:
            return None
        config = store.load_config()
        conversation = store.upsert_conversation(
            phone=normalize_pk_phone(phone) or phone,
            display_name=profile_name or phone,
            channel="whatsapp",
        )
        conversation = self._attach_known_customer(conversation)
        conversation = store.append_message(
            conversation["conversation_id"],
            direction="in",
            text=text,
            channel="whatsapp",
            sender=conversation.get("display_name") or profile_name or phone,
            increase_unread=True,
        )
        if conversation.get("status") == "human" or not config.auto_reply:
            return None
        reply = self._build_reply(
            text,
            phone=conversation.get("phone") or phone,
            conversation=conversation,
        )
        if reply.get("handoff"):
            store.set_status(conversation["conversation_id"], "human")
        store.append_message(
            conversation["conversation_id"],
            direction="out",
            text=reply["text"],
            channel="whatsapp",
            sender="bot",
        )
        if config.online_mode and self.whatsapp.is_configured():
            try:
                self.whatsapp.send_text(conversation["phone"] or phone, reply["text"])
            except (WhatsAppNotConfiguredError, WhatsAppDeliveryError) as exc:
                logger.warning(
                    "WhatsApp bot reply not delivered to %s: %s",
                    conversation.get("phone") or phone,
                    exc,
                )
                return reply["text"]
        elif config.online_mode and not self.whatsapp.is_configured():
            logger.warning(
                "WhatsApp bot reply skipped — Cloud API not configured (%s)",
                self.whatsapp.configuration_hint(),
            )
        elif not config.online_mode:
            logger.warning(
                "WhatsApp bot reply skipped — Online mode is OFF in bot settings"
            )
        return reply["text"]

    def handle_inbound_whatsapp_audio(
        self,
        *,
        phone: str,
        media_id: str,
        profile_name: str = "",
        mime_type: str = "audio/ogg",
    ) -> str | None:
        """Download voice note, transcribe, then run the same chatbot pipeline."""
        if not settings.whatsapp_bot_enabled:
            return None
        config = store.load_config()
        conversation = store.upsert_conversation(
            phone=normalize_pk_phone(phone) or phone,
            display_name=profile_name or phone,
            channel="whatsapp",
        )
        mobile_key = normalize_pk_phone(phone) or phone
        allowed, reason = voice_control.check_allowed(
            channel="whatsapp",
            mobile=mobile_key,
            ip="",
        )
        if not allowed:
            voice_control.record_event(
                channel="whatsapp",
                mobile=mobile_key,
                status="blocked",
                block_reason=reason,
                detail="whatsapp voice blocked",
            )
            text = f"{reason}\nPlease type the item name, or reply 3 for price search help."
            store.append_message(
                conversation["conversation_id"],
                direction="in",
                text="[voice note]",
                channel="whatsapp",
                sender=profile_name or phone,
                increase_unread=True,
            )
            if conversation.get("status") == "human" or not config.auto_reply:
                return None
            store.append_message(
                conversation["conversation_id"],
                direction="out",
                text=text,
                channel="whatsapp",
                sender="bot",
            )
            if config.online_mode and self.whatsapp.is_configured():
                try:
                    self.whatsapp.send_text(conversation["phone"] or phone, text)
                except (WhatsAppNotConfiguredError, WhatsAppDeliveryError):
                    pass
            return text
        try:
            audio_bytes, detected_mime = self.whatsapp.download_media(media_id)
            transcript, model, body = SpeechToTextService().transcribe_audio_with_meta(
                audio_bytes,
                mime_type=detected_mime or mime_type,
            )
            voice_control.record_event(
                channel="whatsapp",
                mobile=mobile_key,
                search_text=transcript,
                status="ok",
                model=model,
                body=body,
                detail="whatsapp voice",
            )
        except (WhatsAppNotConfiguredError, WhatsAppDeliveryError, SpeechToTextError) as exc:
            voice_control.record_event(
                channel="whatsapp",
                mobile=mobile_key,
                status="failed",
                detail=str(exc)[:240],
            )
            text = (
                f"Voice note received, but I could not understand it yet.\n{exc}\n"
                "Please type the item name, or reply 3 for price search help."
            )
            store.append_message(
                conversation["conversation_id"],
                direction="in",
                text="[voice note]",
                channel="whatsapp",
                sender=profile_name or phone,
                increase_unread=True,
            )
            if conversation.get("status") == "human" or not config.auto_reply:
                return None
            store.append_message(
                conversation["conversation_id"],
                direction="out",
                text=text,
                channel="whatsapp",
                sender="bot",
            )
            if config.online_mode and self.whatsapp.is_configured():
                try:
                    self.whatsapp.send_text(conversation["phone"] or phone, text)
                except (WhatsAppNotConfiguredError, WhatsAppDeliveryError):
                    pass
            return text

        context = conversation.get("context") or {}
        lower_t = transcript.lower()
        voice_text = transcript
        if context.get("mode") == "order" or self._wants_order(lower_t):
            if self._wants_order(lower_t) and context.get("mode") != "order":
                voice_text = "4"
            else:
                voice_text = transcript
        elif context.get("mode") != "price" and not self._wants_price_menu(lower_t) and not self._looks_like_price_query(lower_t):
            voice_text = f"price {transcript}"
        display = f"[voice] {transcript}"
        store.append_message(
            conversation["conversation_id"],
            direction="in",
            text=display,
            channel="whatsapp",
            sender=profile_name or phone,
            increase_unread=True,
        )
        if conversation.get("status") == "human" or not config.auto_reply:
            return None
        if context.get("mode") not in {"price", "order"} and voice_text.startswith("price "):
            store.update_context(
                conversation["conversation_id"],
                {"mode": "price", "pending_options": [], "page": 0, "all_options": []},
            )
            conversation = store.get_conversation(conversation["conversation_id"]) or conversation
        reply = self._build_reply(
            voice_text,
            phone=conversation.get("phone") or phone,
            conversation=conversation,
        )
        if reply.get("handoff"):
            store.set_status(conversation["conversation_id"], "human")
        out = f"Heard: {transcript}\n\n{reply['text']}"
        store.append_message(
            conversation["conversation_id"],
            direction="out",
            text=out,
            channel="whatsapp",
            sender="bot",
        )
        if config.online_mode and self.whatsapp.is_configured():
            try:
                self.whatsapp.send_text(conversation["phone"] or phone, out)
            except (WhatsAppNotConfiguredError, WhatsAppDeliveryError) as exc:
                logger.warning(
                    "WhatsApp voice reply not delivered to %s: %s",
                    conversation.get("phone") or phone,
                    exc,
                )
                return out
        elif not config.online_mode or not self.whatsapp.is_configured():
            logger.warning(
                "WhatsApp voice reply skipped — online=%s configured=%s",
                config.online_mode,
                self.whatsapp.is_configured(),
            )
        return out

    def _build_reply(
        self,
        message: str,
        *,
        phone: str,
        conversation: dict[str, Any],
    ) -> dict[str, Any]:
        config = store.load_config()
        company = settings.company_name or settings.app_name
        text = (message or "").strip()
        lower = text.lower()
        digits = re.sub(r"\D", "", text)
        conversation_id = conversation["conversation_id"]
        context = conversation.get("context") or {}

        if self._is_menu(lower) or lower in {"hi", "hello", "salam", "assalam", "start"}:
            store.update_context(conversation_id, None)
            conversation = self._attach_known_customer(conversation)
            return {
                "text": self._format_welcome(
                    config,
                    company=company,
                    conversation=conversation,
                    phone=phone,
                ),
                "handoff": False,
            }

        # Direct add from live search suggestions (web WhatsApp autocomplete).
        additem = re.fullmatch(r"additem\s+(\d+)(?:\s+(\d+(?:\.\d+)?))?", lower)
        if additem:
            return self._order_reply(text, conversation=conversation, phone=phone)

        # Active order/price list picks (1,2,3…) must win over main-menu digits.
        if context.get("mode") == "order":
            return self._order_reply(text, conversation=conversation, phone=phone)

        if context.get("mode") == "price":
            return self._price_reply(text, conversation=conversation)

        if context.get("mode") == "order_status":
            return self._chat_order_status_reply(
                text, conversation=conversation, phone=phone
            )

        # Main menu digits / keywords (idle conversation only).
        menu_digit = self._main_menu_digit(lower)
        if (
            menu_digit == "6"
            or self._wants_chat_order_status(lower)
            or self._looks_like_chat_order_no(lower)
        ):
            return self._chat_order_status_reply(
                text, conversation=conversation, phone=phone
            )
        if menu_digit == "5" or self._wants_human(lower):
            store.update_context(conversation_id, None)
            return {"text": config.human_handoff_message, "handoff": True}
        if menu_digit == "2" or self._wants_store_info(lower):
            store.update_context(conversation_id, None)
            phone_line = config.store_phone or "Ask staff for store number"
            return {
                "text": (
                    f"{company}\n"
                    f"Address: {config.store_address}\n"
                    f"Hours: {config.store_hours}\n"
                    f"Phone: {phone_line}"
                ),
                "handoff": False,
            }
        if menu_digit == "4" or self._wants_order(lower):
            return self._order_reply(text, conversation=conversation, phone=phone)
        if (
            menu_digit == "3"
            or self._wants_price_menu(lower)
            or self._looks_like_price_query(lower)
        ):
            return self._price_reply(text, conversation=conversation)
        if menu_digit == "1" or self._wants_delivery(lower) or self._looks_like_invoice(
            digits, lower
        ):
            store.update_context(conversation_id, None)
            return {
                "text": self._delivery_status_reply(text, phone=phone),
                "handoff": False,
            }

        # Soft fallback: treat longer text as product search
        if self.db is not None and re.search(r"[A-Za-z\u0600-\u06FF]{3,}", text):
            result = self._price_reply(text, conversation=conversation, soft=True)
            if result.get("matched"):
                return result

        return {
            "text": (
                "I did not understand that.\n"
                "Reply 1 delivery, 2 store info, 3 price list, "
                "4 place order, 5 talk to staff, or 6 my order status."
            ),
            "handoff": False,
        }

    def _order_reply(
        self,
        message: str,
        *,
        conversation: dict[str, Any],
        phone: str,
    ) -> dict[str, Any]:
        if self.db is None:
            return {
                "text": "Ordering is temporarily unavailable. Please try again later.",
                "handoff": False,
            }

        orders = WhatsAppOrderService()
        searcher = ItemPriceSearchService(self.db)
        conversation_id = conversation["conversation_id"]
        prior = dict(conversation.get("context") or {})
        already_ordering = prior.get("mode") == "order"
        context = prior if already_ordering else orders.empty_order_context(
            customer_name=conversation.get("display_name") or "",
            customer_mobile=conversation.get("phone") or phone or "",
        )
        text = (message or "").strip()
        lower = text.lower().strip()

        additem = re.fullmatch(r"additem\s+(\d+)(?:\s+(\d+(?:\.\d+)?))?", lower)
        if additem and context.get("step") not in {
            "await_name",
            "await_mobile",
            "await_address",
            "await_location",
            "await_notes",
            "confirm_address",
        }:
            manual_id = int(additem.group(1))
            qty = float(additem.group(2) or 1)
            try:
                item = searcher.guest.lookup_manual_id(manual_id)
            except Exception:
                return {
                    "text": "That product is not available. Try another search.",
                    "handoff": False,
                }
            line = orders.item_from_lookup(item, qty)
            context["cart"] = orders.merge_into_cart(context.get("cart") or [], line)
            context["pending_item"] = None
            context["pending_options"] = []
            context["all_options"] = []
            context["page"] = 0
            context["step"] = "browse"
            try:
                searcher.support.log_search(
                    query_text=f"ADDITEM {manual_id}",
                    cleaned_query=str(manual_id),
                    result_count=1,
                    selected_manual_id=manual_id,
                    channel="web",
                )
            except Exception:
                pass
            self._save_shop_return(context)
            return self._after_add_to_cart(
                conversation_id,
                context,
                line_title=line.item_title,
                line_qty=line.qty,
                line_manual_id=manual_id,
            )
        if already_ordering and is_shop_nav_message(
            text, shop_view=str(context.get("shop_view") or "")
        ):
            shop_out = self._shop_reply(
                text,
                conversation=conversation,
                context=context,
                searcher=searcher,
            )
            if shop_out:
                return shop_out

        # Re-entering order menu while already ordering → show guidance, keep cart.
        # Never treat bare numbers (1-99) as menu here — they mean list pick / qty.
        if (
            already_ordering
            and self._wants_order(lower)
            and not re.fullmatch(r"\d{1,2}", lower)
        ):
            store.update_context(conversation_id, context)
            if context.get("cart"):
                return {
                    "text": orders.format_cart(
                        context.get("cart") or [],
                        customer_name=context.get("customer_name") or "",
                        customer_mobile=context.get("customer_mobile") or "",
                        title="ORDER DRAFT",
                        footer=(
                            "Send item name to add more.\n"
                            "CONFIRM to place · MENU to exit"
                        ),
                    ),
                    "handoff": False,
                }
            return {"text": self._order_browse_prompt(context), "handoff": False}

        if self._wants_order(lower) and not already_ordering:
            conversation = self._attach_known_customer(conversation)
            mobile = self._resolved_mobile(conversation, phone)
            # WhatsApp always carries the sender number — never ask to type it.
            if not mobile and conversation.get("channel") == "whatsapp" and phone:
                mobile = phone
            profile = self._lookup_cust_sms(mobile) if mobile else None
            name = ""
            address = ""
            if profile:
                name = profile.get("name") or ""
                mobile = profile.get("mobile") or mobile
                address = profile.get("address") or ""
            if not name:
                name = conversation.get("display_name") or ""
            # Keep conversation phone in sync so later steps never re-ask.
            if mobile:
                store.upsert_conversation(
                    conversation_id=conversation_id,
                    display_name=name or conversation.get("display_name") or "",
                    phone=normalize_pk_phone(mobile) or mobile,
                    channel=conversation.get("channel") or "offline",
                )
                conversation = (
                    store.get_conversation(conversation_id) or conversation
                )
            context = orders.empty_order_context(
                customer_name=name,
                customer_mobile=mobile,
                customer_address=address,
            )
            mobile_show = self._display_mobile(mobile)
            if profile:
                context["cust_sms_id"] = profile.get("cust_id")
                self._hydrate_saved_location(context)
                prefix = (
                    f"Welcome back, *{name}*!\n"
                    f"Mobile: *{mobile_show}*\n"
                    f"We found your profile at "
                    f"{settings.company_name or settings.app_name}.\n"
                )
                if address:
                    prefix += f"Address on file: {address}\n"
                elif context.get("maps_url"):
                    prefix += f"Saved Maps pin: {context['maps_url']}\n"
                return self._shopping_ready_reply(conversation, context, prefix)

            if not context["customer_name"] or context["customer_name"].lower() in {
                "guest",
                (phone or "").lower(),
                (mobile or "").lower(),
                mobile_show.lower(),
            }:
                context["step"] = "await_name"
                store.update_context(conversation_id, context)
                mobile_hint = (
                    f"\nYour mobile on this chat: *{mobile_show}*\n"
                    if mobile_show
                    else ""
                )
                return {
                    "text": (
                        "*Place Order*\n"
                        "──────────────────\n"
                        "Welcome to our ordering desk.\n"
                        f"{mobile_hint}"
                        "Please send your *full name* to continue.\n"
                        "Example: Ahmed Khan"
                    ),
                    "handoff": False,
                }
            # Only ask mobile when we truly do not have it (rare offline case).
            if not self._mobile_key(context["customer_mobile"]):
                context["step"] = "await_mobile"
                store.update_context(conversation_id, context)
                return {
                    "text": (
                        f"Thank you, *{context['customer_name']}*.\n"
                        "Please send your *mobile number* (03XXXXXXXXX)\n"
                        "so we can save your customer profile."
                    ),
                    "handoff": False,
                }
            ensure = self._ensure_cust_sms(
                name=context["customer_name"],
                mobile=context["customer_mobile"],
                address=context.get("customer_address") or "",
            )
            if ensure:
                context["cust_sms_id"] = ensure.get("cust_id")
                if ensure.get("name"):
                    context["customer_name"] = ensure["name"]
            intro = (
                f"Welcome, *{context['customer_name']}*!\n"
                f"Mobile: *{self._display_mobile(context['customer_mobile'])}*\n"
                "Your customer profile is ready.\n\n"
                if ensure and ensure.get("is_new")
                else (
                    f"Welcome, *{context['customer_name']}*!\n"
                    f"Mobile: *{self._display_mobile(context['customer_mobile'])}*\n\n"
                )
            )
            return self._shopping_ready_reply(conversation, context, intro)

        # Collect customer details
        if context.get("step") == "await_name":
            name = text.strip()[:100]
            if len(name) < 2:
                return {"text": "Please send a valid name.", "handoff": False}
            context["customer_name"] = name
            mobile = self._resolved_mobile(conversation, phone, context)
            store.upsert_conversation(
                conversation_id=conversation_id,
                display_name=name,
                phone=normalize_pk_phone(mobile) or mobile,
                channel=conversation.get("channel") or "offline",
            )
            if not self._mobile_key(mobile):
                # WhatsApp should never land here; offline guest without phone only.
                if conversation.get("channel") == "whatsapp" and phone:
                    mobile = phone
                else:
                    context["step"] = "await_mobile"
                    store.update_context(conversation_id, context)
                    return {
                        "text": (
                            f"Thank you, *{name}*.\n"
                            "Please send your *mobile number* (03XXXXXXXXX)\n"
                            "so we can create your customer profile."
                        ),
                        "handoff": False,
                    }
            context["customer_mobile"] = mobile
            ensure = self._ensure_cust_sms(
                name=name,
                mobile=mobile,
                address=context.get("customer_address") or "",
            )
            if ensure:
                context["cust_sms_id"] = ensure.get("cust_id")
            created = "created" if ensure and ensure.get("is_new") else "updated"
            return self._shopping_ready_reply(
                conversation,
                context,
                (
                    f"Thank you, *{name}*.\n"
                    f"Mobile: *{self._display_mobile(mobile)}*\n"
                    f"Your customer profile has been {created} successfully.\n\n"
                ),
            )

        if context.get("step") == "await_mobile":
            # If mobile arrived from WhatsApp / form meanwhile, skip typing.
            known = self._resolved_mobile(conversation, phone, context)
            if self._mobile_key(known) and not self._mobile_key(text):
                mobile = known
            else:
                mobile = normalize_pk_phone(text) or re.sub(r"\D", "", text)
            if len(re.sub(r"\D", "", mobile)) < 10:
                return {
                    "text": "Please send a valid Pakistan mobile, e.g. 03001234567.",
                    "handoff": False,
                }
            profile = self._lookup_cust_sms(mobile)
            if profile and profile.get("name"):
                context["customer_name"] = profile["name"]
                context["customer_mobile"] = profile.get("mobile") or mobile
                context["customer_address"] = profile.get("address") or context.get(
                    "customer_address"
                ) or ""
                context["cust_sms_id"] = profile.get("cust_id")
                store.upsert_conversation(
                    conversation_id=conversation_id,
                    display_name=profile["name"],
                    phone=mobile,
                    channel=conversation.get("channel") or "offline",
                )
                return self._shopping_ready_reply(
                    conversation,
                    context,
                    (
                        f"Assalam-o-Alaikum, *{profile['name']}*!\n"
                        "Welcome back — we recognized your number.\n\n"
                    ),
                )
            context["customer_mobile"] = mobile
            store.upsert_conversation(
                conversation_id=conversation_id,
                display_name=context.get("customer_name")
                or conversation.get("display_name")
                or "",
                phone=mobile,
                channel=conversation.get("channel") or "offline",
            )
            if not context.get("customer_name") or context["customer_name"].lower() in {
                "guest",
                mobile.lower(),
            }:
                context["step"] = "await_name"
                store.update_context(conversation_id, context)
                return {
                    "text": (
                        "Thank you. We do not have this number on file yet.\n"
                        "Please send your *full name* to create your profile."
                    ),
                    "handoff": False,
                }
            ensure = self._ensure_cust_sms(
                name=context["customer_name"],
                mobile=mobile,
                address=context.get("customer_address") or "",
            )
            if ensure:
                context["cust_sms_id"] = ensure.get("cust_id")
            return self._shopping_ready_reply(
                conversation,
                context,
                (
                    f"Welcome, *{context['customer_name']}*!\n"
                    "Your customer profile has been created successfully.\n\n"
                ),
            )

        if context.get("step") == "await_fulfill":
            return self._fulfill_reply(text, conversation=conversation, context=context)

        if context.get("step") == "await_area":
            return self._area_reply(text, conversation=conversation, context=context)

        if context.get("step") == "confirm_address":
            if lower in {"keep", "yes", "ok", "same"}:
                self._hydrate_saved_location(context)
                return self._continue_after_address(conversation, context)
            if lower in {"skip", "no", "none", "-"}:
                context["customer_address"] = ""
                return self._continue_after_address(conversation, context)
            if lower in {"update", "change", "edit", "new"}:
                context["step"] = "await_address"
                store.update_context(conversation_id, context)
                return {
                    "text": self._ask_address_prompt(existing=""),
                    "handoff": False,
                }
            # Treat free text as a new address / maps pin
            return self._apply_address_input(text, conversation=conversation, context=context)

        if context.get("step") == "await_address":
            if lower in {"skip", "no", "none", "-"}:
                context["customer_address"] = context.get("customer_address") or ""
                return self._continue_after_address(conversation, context)
            return self._apply_address_input(text, conversation=conversation, context=context)

        if context.get("step") == "await_location":
            if lower in {"skip", "no", "none", "-"}:
                return self._finalize_order(conversation, context)
            coords = self._parse_geo_coords(text)
            if not coords:
                return {
                    "text": (
                        "Please share a Google Maps pin, or send coordinates like:\n"
                        "*31.5204, 74.3587*\n"
                        "Or reply SKIP."
                    ),
                    "handoff": False,
                }
            context["latitude"] = coords[0]
            context["longitude"] = coords[1]
            context["maps_url"] = (
                f"https://www.google.com/maps?q={coords[0]},{coords[1]}"
            )
            self._persist_customer_location(context)
            store.update_context(conversation_id, context)
            return self._finalize_order(conversation, context)

        if context.get("step") == "await_notes":
            notes = text.strip()[:500]
            if lower in {"skip", "no", "none", "-"}:
                notes = ""
            context["notes"] = notes
            if (context.get("order_type") or "") == "pickup":
                context["customer_address"] = (
                    (context.get("customer_address") or "").strip()
                    or settings.company_address
                    or "Pickup from store"
                )
                store.update_context(conversation_id, context)
                return self._finalize_order(conversation, context)
            self._hydrate_profile_address(context)
            self._hydrate_saved_location(context)
            area_seed = ", ".join(
                part for part in [context.get("area") or "", context.get("city") or ""] if part
            )
            if area_seed and not (context.get("customer_address") or "").strip():
                context["customer_address"] = area_seed
            saved_addr = (context.get("customer_address") or "").strip()
            if saved_addr:
                context["step"] = "confirm_address"
                store.update_context(conversation_id, context)
                return {
                    "text": (
                        "*Delivery address on file*\n"
                        f"{saved_addr}\n\n"
                        "Reply *KEEP* to use this address.\n"
                        "Reply *UPDATE* to change it.\n"
                        "Or reply *SKIP* for pickup / no address."
                    ),
                    "handoff": False,
                }
            context["step"] = "await_address"
            store.update_context(conversation_id, context)
            return {
                "text": self._ask_address_prompt(existing=""),
                "handoff": False,
            }

        # Cart commands — view + professional qty / delete controls
        if lower in {"cart", "bill", "review", "total"}:
            return self._cart_view_reply(
                conversation_id,
                context,
                title="YOUR CART",
                note="Use − / + on each item, or Delete. Then CONFIRM when ready.",
            )

        if lower in {"clear", "empty"}:
            context["cart"] = []
            context["pending_item"] = None
            context["pending_options"] = []
            context["all_options"] = []
            context["step"] = "browse"
            context["shop_view"] = "hub"
            context["shop_list"] = []
            store.update_context(conversation_id, context)
            return {
                "text": "Cart cleared.\n" + self._order_browse_prompt(context),
                "handoff": False,
            }

        if lower in {"cancel"}:
            store.update_context(conversation_id, None)
            return {
                "text": "Order cancelled. Reply MENU for main options.",
                "handoff": False,
            }

        inc_match = re.fullmatch(r"(?:inc|plus|\+)\s*(\d{1,2})", lower)
        if inc_match:
            idx = int(inc_match.group(1))
            before = len(context.get("cart") or [])
            if not (1 <= idx <= before):
                return {
                    "text": f"No cart line {idx}. Open CART to see items.",
                    "handoff": False,
                }
            context["cart"] = orders.adjust_cart_qty(
                context.get("cart") or [], idx, 1
            )
            return self._cart_view_reply(
                conversation_id,
                context,
                title="QUANTITY UPDATED",
                note="",
                silent_ui=True,
            )

        dec_match = re.fullmatch(r"(?:dec|minus|\-)\s*(\d{1,2})", lower)
        if dec_match:
            idx = int(dec_match.group(1))
            before = len(context.get("cart") or [])
            if not (1 <= idx <= before):
                return {
                    "text": f"No cart line {idx}. Open CART to see items.",
                    "handoff": False,
                }
            context["cart"] = orders.adjust_cart_qty(
                context.get("cart") or [], idx, -1
            )
            return self._cart_view_reply(
                conversation_id,
                context,
                title="QUANTITY UPDATED",
                note="",
                silent_ui=True,
            )

        qty_set_match = re.fullmatch(
            r"(?:qty|quantity)\s+(\d{1,2})\s+(\d+(?:\.\d+)?)",
            lower,
        )
        if qty_set_match:
            idx = int(qty_set_match.group(1))
            qty = float(qty_set_match.group(2))
            before = len(context.get("cart") or [])
            if not (1 <= idx <= before):
                return {
                    "text": f"No cart line {idx}. Open CART to see items.",
                    "handoff": False,
                }
            if qty <= 0:
                context["cart"] = orders.remove_from_cart(
                    context.get("cart") or [], idx
                )
                return self._cart_view_reply(
                    conversation_id,
                    context,
                    title="ITEM REMOVED",
                    note="",
                    silent_ui=True,
                )
            context["cart"] = orders.set_cart_qty(
                context.get("cart") or [], idx, qty
            )
            return self._cart_view_reply(
                conversation_id,
                context,
                title="QUANTITY UPDATED",
                note="",
                silent_ui=True,
            )

        remove_match = re.fullmatch(r"(?:remove|del|delete)\s+(\d{1,2})", lower)
        if remove_match:
            idx = int(remove_match.group(1))
            before = len(context.get("cart") or [])
            if not (1 <= idx <= before):
                return {
                    "text": f"No cart line {idx}. Open CART to see items.",
                    "handoff": False,
                }
            context["cart"] = orders.remove_from_cart(context.get("cart") or [], idx)
            return self._cart_view_reply(
                conversation_id,
                context,
                title="ITEM REMOVED",
                note="",
                silent_ui=True,
            )

        if lower in {"confirm", "yes", "place", "checkout", "done"}:
            cart = list(context.get("cart") or [])
            if not cart:
                return {
                    "text": "Your cart is empty. Send an item name to add products first.",
                    "handoff": False,
                }
            # Always re-read latest cart qty from stored context before confirming.
            fresh = store.get_conversation(conversation_id) or {}
            fresh_ctx = dict(fresh.get("context") or context)
            cart = list(fresh_ctx.get("cart") or cart)
            if not cart:
                return {
                    "text": "Your cart is empty. Send an item name to add products first.",
                    "handoff": False,
                }
            context = fresh_ctx
            context["cart"] = cart
            shop = WhatsAppShopService(self.db)
            priced, notices, ready = shop.validate_cart_lines(cart, orders)
            context["cart"] = priced
            if not ready:
                store.update_context(conversation_id, context)
                extra = "\n".join(notices) if notices else "Please review your cart."
                if priced:
                    return self._cart_view_reply(
                        conversation_id,
                        context,
                        title="CART UPDATED",
                        note=(
                            extra
                            + "\nPrices and stock are from the store system. "
                            "Fix the cart, then CONFIRM again."
                        ),
                    )
                context["step"] = "browse"
                context["shop_view"] = "hub"
                store.update_context(conversation_id, context)
                return {
                    "text": extra + "\n" + self._order_browse_prompt(context),
                    "handoff": False,
                }
            context["step"] = "await_notes"
            store.update_context(conversation_id, context)
            totals = orders.totals(priced)
            notice = ("\n".join(notices) + "\n\n") if notices else ""
            fulfill = (context.get("order_type") or "delivery").title()
            return {
                "text": (
                    f"{notice}"
                    f"Ready to place your *{fulfill}* order.\n"
                    f"*{int(totals['item_count'])} item(s)* · "
                    f"Store total *Rs {orders._money(float(totals['order_total']))}*\n"
                    "Tax/delivery if any are confirmed by the store.\n\n"
                    "Optional note for shop (or reply SKIP):\n"
                    "Example: Call before delivery"
                ),
                "handoff": False,
            }

        # Quantity for pending item
        if context.get("step") == "await_qty" and context.get("pending_item"):
            qty = self._parse_qty(text)
            if qty is None:
                return {
                    "text": "Please send quantity as a number.\nExample: 2",
                    "handoff": False,
                }
            line = orders.item_from_lookup(context["pending_item"], qty)
            context["cart"] = orders.merge_into_cart(context.get("cart") or [], line)
            context["pending_item"] = None
            context["pending_options"] = []
            context["all_options"] = []
            return self._after_add_to_cart(
                conversation_id,
                context,
                line_title=line.item_title,
                line_qty=line.qty,
                line_manual_id=int(line.manual_id or 0) or None,
            )

        # Category shop (browse / search-in-category) — before global item search.
        shop_out = self._shop_reply(
            text,
            conversation=conversation,
            context=context,
            searcher=searcher,
        )
        if shop_out:
            return shop_out

        # Option pick from search results
        options = list(context.get("all_options") or context.get("pending_options") or [])
        if lower in {"new", "search", "again"}:
            context["pending_item"] = None
            context["pending_options"] = []
            context["all_options"] = []
            context["page"] = 0
            context["step"] = "browse"
            context["shop_view"] = "hub"
            context["shop_list"] = []
            context["all_options"] = []
            store.update_context(conversation_id, context)
            return {
                "text": "OK. " + self._order_browse_prompt(context),
                "handoff": False,
            }

        if options and lower in {"more", "next"}:
            page = int(context.get("page") or 0) + 1
            page_size = 8
            if page * page_size >= len(options):
                return {
                    "text": "No more items. Type a new name, or tap New search.",
                    "handoff": False,
                }
            context["page"] = page
            store.update_context(conversation_id, context)
            remaining = len(options) - page * page_size
            return {
                "text": (
                    f"More matches — page {page + 1}.\n"
                    f"{min(page_size, remaining)} more item(s). Tap below."
                ),
                "handoff": False,
            }

        if options and re.fullmatch(r"\d{1,2}", lower):
            choice = int(lower)
            if 1 <= choice <= len(options):
                selected = options[choice - 1]
                self._save_shop_return(context)
                context["pending_item"] = selected
                context["pending_options"] = []
                context["all_options"] = []
                context["step"] = "await_qty"
                store.update_context(conversation_id, context)
                card = searcher.format_price_card(
                    self._options_from_dicts([selected])[0]
                )
                return {
                    "text": (
                        f"{card}\n\n"
                        "How many units do you want?\n"
                        "Reply with quantity, e.g. *1* or *2*"
                    ),
                    "handoff": False,
                }
            return {
                "text": f"Please reply with a number from 1 to {len(options)}.",
                "handoff": False,
            }

        # Search item to add — name/brand typing always becomes tap options.
        is_code_query = bool(re.fullmatch(r"\d{1,20}", text.strip()))
        result = searcher.search(text, limit=24, force_list=not is_code_query)
        if result.match_type == "none":
            store.update_context(conversation_id, context)
            return {
                "text": (
                    f"{result.message}\n\n"
                    "Try brand + size, barcode, or item code.\n"
                    "CART to review · CONFIRM to place · MENU to exit"
                ),
                "handoff": False,
            }

        # Barcode / item code: jump straight to quantity.
        if is_code_query and result.match_type == "exact" and result.items:
            selected = result.items[0].model_dump(mode="json")
            self._save_shop_return(context)
            context["pending_item"] = selected
            context["pending_options"] = []
            context["all_options"] = []
            context["step"] = "await_qty"
            store.update_context(conversation_id, context)
            card = searcher.format_price_card(result.items[0])
            return {
                "text": (
                    f"{card}\n\n"
                    "How many units do you want?\n"
                    "Reply with quantity, e.g. *1* or *2*"
                ),
                "handoff": False,
            }

        option_dicts = [
            item.model_dump(mode="json")
            for item in result.items
            if not is_hidden_shop_title(item.item_title)
        ]
        if not option_dicts:
            store.update_context(conversation_id, context)
            return {
                "text": (
                    f"{result.message or 'No matching products found.'}\n\n"
                    "Try brand + size, barcode, or item code.\n"
                    "CART to review · CONFIRM to place · MENU to exit"
                ),
                "handoff": False,
            }
        context["pending_options"] = option_dicts
        context["all_options"] = option_dicts
        context["page"] = 0
        context["step"] = "browse"
        context["last_query"] = result.cleaned_query or text
        store.update_context(conversation_id, context)
        return {
            "text": (
                f"Found {len(option_dicts)} item(s) for "
                f"'{result.cleaned_query or text}'.\n"
                "Tap an item below to add it."
            ),
            "handoff": False,
        }

    def _finalize_order(
        self,
        conversation: dict[str, Any],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        orders = WhatsAppOrderService()
        conversation_id = conversation["conversation_id"]
        self._persist_customer_address(context)
        self._persist_customer_location(context)
        if context.get("latitude") is not None and context.get("longitude") is not None:
            context["maps_url"] = (
                context.get("maps_url")
                or (
                    "https://www.google.com/maps?q="
                    f"{context['latitude']},{context['longitude']}"
                )
            )
        try:
            order = orders.confirm_order(conversation=conversation, context=context)
        except ValueError as exc:
            return {"text": str(exc), "handoff": False}
        store.update_context(conversation_id, None)
        store.set_status(conversation_id, "human")
        return {
            "text": order.receipt_text,
            "handoff": True,
        }

    def _ask_address_prompt(self, *, existing: str) -> str:
        lines = [
            "*Delivery address*",
            "──────────────────",
        ]
        if existing:
            lines.append(f"Current: {existing}")
            lines.append("")
        lines.extend(
            [
                "Send your full delivery address.",
                "You may also paste a *Google Maps* link or GPS like:",
                "31.5204, 74.3587",
                "",
                "Reply SKIP for pickup / no address.",
            ]
        )
        return "\n".join(lines)

    def _continue_after_address(
        self,
        conversation: dict[str, Any],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        conversation_id = conversation["conversation_id"]
        self._persist_customer_address(context)
        if (context.get("order_type") or "") == "pickup":
            return self._finalize_order(conversation, context)
        if context.get("latitude") is not None and context.get("longitude") is not None:
            self._persist_customer_location(context)
            return self._finalize_order(conversation, context)
        context["step"] = "await_location"
        store.update_context(conversation_id, context)
        return {
            "text": (
                "Please share your *Google Maps location* for delivery:\n"
                "• Paste Maps link, or\n"
                "• Send GPS like *31.5204, 74.3587*, or\n"
                "• On web chat tap *Share location*\n\n"
                "Reply SKIP to place order without pin."
            ),
            "handoff": False,
        }

    def _apply_address_input(
        self,
        text: str,
        *,
        conversation: dict[str, Any],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        coords = self._parse_geo_coords(text)
        address = self._strip_geo_from_text(text).strip()[:500]
        if coords:
            context["latitude"] = coords[0]
            context["longitude"] = coords[1]
            context["maps_url"] = (
                f"https://www.google.com/maps?q={coords[0]},{coords[1]}"
            )
            if not address:
                address = f"GPS {coords[0]}, {coords[1]}"
        if not address and not coords:
            return {
                "text": (
                    "Please send a valid address, Google Maps link, "
                    "or GPS coordinates."
                ),
                "handoff": False,
            }
        if address:
            context["customer_address"] = address
        store.update_context(conversation["conversation_id"], context)
        return self._continue_after_address(conversation, context)

    def _hydrate_profile_address(self, context: dict[str, Any]) -> None:
        if (context.get("customer_address") or "").strip():
            return
        profile = self._lookup_cust_sms(context.get("customer_mobile") or "")
        if profile and profile.get("address"):
            context["customer_address"] = profile["address"]
            context["cust_sms_id"] = profile.get("cust_id") or context.get("cust_sms_id")

    def _hydrate_saved_location(self, context: dict[str, Any]) -> None:
        if context.get("latitude") is not None and context.get("longitude") is not None:
            return
        if self.db is None:
            return
        key = self._mobile_key(context.get("customer_mobile") or "")
        if not key:
            return
        try:
            row = DeliveryRepository(self.db).get_customer_location(key)
        except Exception:
            return
        if not row:
            return
        try:
            context["latitude"] = float(row["latitude"])
            context["longitude"] = float(row["longitude"])
            context["maps_url"] = (
                f"https://www.google.com/maps?q="
                f"{context['latitude']},{context['longitude']}"
            )
            if row.get("accuracy") is not None:
                context["location_accuracy"] = float(row["accuracy"])
        except (TypeError, ValueError, KeyError):
            return

    def _persist_customer_address(self, context: dict[str, Any]) -> None:
        if self.db is None:
            return
        address = (context.get("customer_address") or "").strip()
        if not address:
            return
        cust_id = context.get("cust_sms_id")
        mobile = context.get("customer_mobile") or ""
        if not cust_id:
            ensure = self._ensure_cust_sms(
                name=context.get("customer_name") or "Customer",
                mobile=mobile,
                address=address,
            )
            if ensure:
                context["cust_sms_id"] = ensure.get("cust_id")
                cust_id = ensure.get("cust_id")
        if not cust_id:
            return
        try:
            DeliveryRepository(self.db).update_customer_address(int(cust_id), address)
            self.db.commit()
        except Exception:
            try:
                self.db.rollback()
            except Exception:
                pass

    def _persist_customer_location(self, context: dict[str, Any]) -> None:
        if self.db is None:
            return
        lat = context.get("latitude")
        lng = context.get("longitude")
        if lat is None or lng is None:
            return
        mobile = context.get("customer_mobile") or ""
        key = self._mobile_key(mobile)
        if not key:
            return
        try:
            DeliveryRepository(self.db).upsert_customer_location(
                mobile_key=key,
                customer_mobile_no=self._mobile_for_storage(mobile) or mobile,
                cust_sms_id=int(context["cust_sms_id"])
                if context.get("cust_sms_id")
                else None,
                latitude=float(lat),
                longitude=float(lng),
                accuracy=float(context["location_accuracy"])
                if context.get("location_accuracy") is not None
                else None,
                actor_username="whatsapp-bot",
            )
            self.db.commit()
        except Exception:
            try:
                self.db.rollback()
            except Exception:
                pass

    @staticmethod
    def _parse_geo_coords(text: str) -> tuple[float, float] | None:
        raw = (text or "").strip()
        if not raw:
            return None
        patterns = [
            r"(?:loc|gps|location)\s*[:=]?\s*(-?\d{1,2}\.\d+)\s*[, ]\s*(-?\d{1,3}\.\d+)",
            r"[?&]q=(-?\d{1,2}\.\d+),(-?\d{1,3}\.\d+)",
            r"@(-?\d{1,2}\.\d+),(-?\d{1,3}\.\d+)",
            r"!3d(-?\d{1,2}\.\d+)!4d(-?\d{1,3}\.\d+)",
            r"(?:maps\.google\.|/maps/|google\.com/maps)[^\s]*[@=](-?\d{1,2}\.\d+),(-?\d{1,3}\.\d+)",
            r"^(-?\d{1,2}\.\d+)\s*[, ]\s*(-?\d{1,3}\.\d+)$",
        ]
        for pattern in patterns:
            match = re.search(pattern, raw, flags=re.I)
            if not match:
                continue
            try:
                lat = float(match.group(1))
                lng = float(match.group(2))
            except (TypeError, ValueError):
                continue
            if -90 <= lat <= 90 and -180 <= lng <= 180:
                return lat, lng
        return None

    @staticmethod
    def _strip_geo_from_text(text: str) -> str:
        cleaned = (text or "").strip()
        cleaned = re.sub(
            r"https?://\S*(?:google\.com/maps|maps\.google|maps\.app\.goo\.gl)\S*",
            " ",
            cleaned,
            flags=re.I,
        )
        cleaned = re.sub(
            r"(?:loc|gps|location)\s*[:=]?\s*-?\d{1,2}\.\d+\s*[, ]\s*-?\d{1,3}\.\d+",
            " ",
            cleaned,
            flags=re.I,
        )
        cleaned = re.sub(
            r"-?\d{1,2}\.\d+\s*[, ]\s*-?\d{1,3}\.\d+",
            " ",
            cleaned,
        )
        return re.sub(r"\s+", " ", cleaned).strip()

    _SHOP_RETURN_KEYS = (
        "shop_view",
        "shop_category_id",
        "shop_category_title",
        "shop_parent_id",
        "shop_parent_title",
        "shop_list",
        "shop_subs",
        "shop_q",
        "shop_page",
        "shop_has_more",
        "shop_promo",
    )

    def _save_shop_return(self, context: dict[str, Any]) -> None:
        view = str(context.get("shop_view") or "")
        if view not in {"products", "offers", "categories"}:
            return
        snap: dict[str, Any] = {}
        for key in self._SHOP_RETURN_KEYS:
            val = context.get(key)
            if key in {"shop_list", "shop_subs"}:
                snap[key] = list(val or [])
            else:
                snap[key] = val
        context["shop_return"] = snap

    def _restore_shop_return(self, context: dict[str, Any]) -> None:
        snap = context.pop("shop_return", None)
        if not snap:
            return
        for key, val in snap.items():
            context[key] = val

    def _view_cart_label(self, context: dict[str, Any]) -> str:
        cart = list(context.get("cart") or [])
        if not cart:
            return "View cart"
        orders = WhatsAppOrderService()
        totals = orders.totals(cart)
        total_s = orders._money(float(totals.get("order_total") or 0))
        return f"View cart · Rs {total_s}"

    def _after_add_to_cart(
        self,
        conversation_id: str,
        context: dict[str, Any],
        *,
        line_title: str,
        line_qty: float,
        line_manual_id: int | None = None,
    ) -> dict[str, Any]:
        """Add line then stay on the current shop shelf — full cart only on CART tap."""
        orders = WhatsAppOrderService()
        self._restore_shop_return(context)
        context["step"] = "browse"
        context["pending_item"] = None
        context["pending_options"] = []
        context["all_options"] = []
        store.update_context(conversation_id, context)

        cart = list(context.get("cart") or [])
        totals = orders.totals(cart)
        qty_s = orders._qty(line_qty)
        view = str(context.get("shop_view") or "")
        cat_title = str(context.get("shop_category_title") or "").strip()
        where = f" in *{cat_title}*" if view == "products" and cat_title else ""

        note = (
            f"Added *{line_title}* × {qty_s}\n"
            f"*{int(totals['item_count'])} item(s)* · "
            f"Total *Rs {orders._money(float(totals['order_total']))}*"
        )
        added_id = int(line_manual_id or 0) or None
        return {
            "text": f"{note}\nKeep shopping{where}, or tap *View cart*.",
            "handoff": False,
            "stay_in_shop": True,
            "added_manual_id": added_id,
        }

    def _cart_short_text(
        self,
        cart: list[dict[str, Any]],
        *,
        note: str = "",
    ) -> str:
        orders = WhatsAppOrderService()
        totals = orders.totals(cart or [])
        lines = []
        if note:
            lines.append(note)
        lines.append(
            f"*{int(totals['item_count'])} item(s)* · "
            f"Qty {orders._qty(float(totals['qty_total']))} · "
            f"Total *Rs {orders._money(float(totals['order_total']))}*"
        )
        lines.append("Use − / + / Delete on each item, then tap Confirm.")
        return "\n".join(lines)

    def _cart_view_reply(
        self,
        conversation_id: str,
        context: dict[str, Any],
        *,
        title: str = "YOUR CART",
        note: str = "",
        silent_ui: bool = False,
    ) -> dict[str, Any]:
        del title  # kept for call-site compatibility; UI is button-based now
        orders = WhatsAppOrderService()
        cart = orders.purge_hidden_titles(context.get("cart") or [])
        context["cart"] = cart
        if not cart:
            context["step"] = "browse"
            context["shop_view"] = context.get("shop_view") or "hub"
            context["pending_options"] = []
            context["all_options"] = []
            context["shop_list"] = []
            store.update_context(conversation_id, context)
            return {
                "text": (
                    "Your cart is empty.\n"
                    + self._order_browse_prompt(context)
                ),
                "handoff": False,
                "silent_ui": False,
            }
        context["step"] = "cart_view"
        context["pending_item"] = None
        context["pending_options"] = []
        context["all_options"] = []
        context["shop_list"] = []
        store.update_context(conversation_id, context)
        short = self._cart_short_text(cart, note=note)
        # Compact body only — full receipt is shown after final order place.
        whatsapp_lines = [short, "", "QTY 1 5 · REMOVE 1 · CONFIRM · CLEAR · MENU"]
        return {
            "text": "\n".join(whatsapp_lines),
            "short_text": short,
            "note": note,
            "silent_ui": silent_ui,
            "handoff": False,
        }

    def _cart_line_replies(self, cart: list[dict[str, Any]]) -> list[ChatQuickReply]:
        orders = WhatsAppOrderService()
        buttons: list[ChatQuickReply] = []
        for idx, raw in enumerate(cart or [], start=1):
            title = str(raw.get("item_title") or f"Item {idx}").strip()
            if title.lower().startswith("empty"):
                continue
            if len(title) > 80:
                title = title[:77] + "…"
            unit_price = float(raw.get("unit_price") or 0)
            unit = orders._money(unit_price)
            line_total = orders._money(float(raw.get("line_total") or 0))
            qty = float(raw.get("qty") or 1)
            code = raw.get("manual_id")
            subtitle = f"Code {code} · Rs {unit} each" if code else f"Rs {unit} each"
            buttons.append(
                ChatQuickReply(
                    title=title,
                    payload=str(idx),
                    style="cart",
                    subtitle=subtitle,
                    meta=f"Rs {line_total}",
                    qty=qty,
                    line_index=idx,
                    unit_price=unit_price,
                )
            )
        buttons.extend(
            [
                ChatQuickReply(title="Confirm order", payload="CONFIRM", style="action"),
                ChatQuickReply(title="Add more items", payload="NEW", style="action"),
                ChatQuickReply(title="Clear cart", payload="CLEAR", style="action"),
                ChatQuickReply(title="Menu", payload="MENU", style="action"),
            ]
        )
        return buttons

    def _order_browse_prompt(self, context: dict[str, Any]) -> str:
        name = context.get("customer_name") or "Customer"
        mobile = self._display_mobile(context.get("customer_mobile") or "")
        fulfill = context.get("order_type") or ""
        lines = [
            f"*Shop for {name}*",
            "──────────────────",
        ]
        if mobile:
            lines.append(f"Mobile: {mobile}")
        if fulfill:
            loc = ", ".join(
                p for p in [context.get("area") or "", context.get("city") or ""] if p
            )
            label = "Pick-up" if fulfill == "pickup" else "Delivery"
            lines.append(f"{label}" + (f" · {loc}" if loc else ""))
        hint = shop_cart_hint(context)
        if hint:
            lines.append(hint)
        lines.extend(
            [
                "",
                "1 Categories",
                "2 Search products",
                "3 Offers",
                "4 View cart",
                "",
                "Type a name to search all products.",
                "In a category, type to search *only that category*.",
                "Tap *Categories* anytime · *Back* for previous level.",
                "CART · CONFIRM · MENU",
                "",
                "Sales prices from the store. No invented fees.",
            ]
        )
        return "\n".join(lines)

    def _fulfill_prompt(self) -> str:
        return (
            "*Delivery or Pick-up?*\n"
            "──────────────────\n"
            "1 Delivery\n"
            "2 Pick-up (store collection)\n\n"
            "Delivery charges, if any, are confirmed by the store.\n"
            "This chat does not invent fees."
        )

    def _shopping_ready_reply(
        self,
        conversation: dict[str, Any],
        context: dict[str, Any],
        prefix: str = "",
    ) -> dict[str, Any]:
        conversation_id = conversation["conversation_id"]
        context["mode"] = "order"
        if not (context.get("order_type") or "").strip():
            context["step"] = "await_fulfill"
            context["shop_view"] = "hub"
            store.update_context(conversation_id, context)
            return {
                "text": f"{prefix}{self._fulfill_prompt()}".strip(),
                "handoff": False,
            }
        context["step"] = "browse"
        context["shop_view"] = "hub"
        context["shop_list"] = []
        store.update_context(conversation_id, context)
        return {
            "text": f"{prefix}{self._order_browse_prompt(context)}".strip(),
            "handoff": False,
        }

    def _open_shop_hub(self, conversation: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        context["step"] = "browse"
        context["shop_view"] = "hub"
        context["shop_list"] = []
        context["all_options"] = []
        context["pending_options"] = []
        context["shop_q"] = ""
        store.update_context(conversation["conversation_id"], context)
        return {"text": self._order_browse_prompt(context), "handoff": False}

    def _fulfill_reply(
        self,
        text: str,
        *,
        conversation: dict[str, Any],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        choice = parse_fulfill(text.lower().strip())
        if not choice:
            return {"text": self._fulfill_prompt(), "handoff": False}
        context["order_type"] = choice
        if choice == "pickup":
            context["city"] = "Lahore"
            context["area"] = "Shad Bagh"
            if not (context.get("customer_address") or "").strip():
                context["customer_address"] = settings.company_address or ""
            return self._shopping_ready_reply(
                conversation,
                context,
                "Pick-up at our Shad Bagh store.\nShare your area only if asked later.\n\n",
            )
        context["step"] = "await_area"
        store.update_context(conversation["conversation_id"], context)
        return {
            "text": (
                "*Delivery area*\n"
                "Send city and area, e.g. *Lahore, Shad Bagh*\n"
                "GPS is not required.\n"
                "Or reply *Shad Bagh* to use the store area."
            ),
            "handoff": False,
        }

    def _area_reply(
        self,
        text: str,
        *,
        conversation: dict[str, Any],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        lower = text.lower().strip()
        if lower in {"shad bagh", "store", "store area", "use store area"}:
            context["city"] = "Lahore"
            context["area"] = "Shad Bagh"
        else:
            parsed = parse_area_line(text)
            if not parsed:
                return {
                    "text": (
                        "Please send city and area, e.g. *Lahore, Shad Bagh*."
                    ),
                    "handoff": False,
                }
            context["city"], context["area"] = parsed
        if not (context.get("customer_address") or "").strip():
            context["customer_address"] = f"{context['area']}, {context['city']}"
        return self._shopping_ready_reply(
            conversation,
            context,
            f"Delivering to *{context['area']}, {context['city']}*.\n"
            "The store confirms any delivery charge.\n\n",
        )

    def _format_shop_list(
        self,
        *,
        heading: str,
        rows: list[dict[str, Any]],
        context: dict[str, Any],
        empty_query: str = "",
        subs: list[dict[str, Any]] | None = None,
        categories_only: bool = False,
    ) -> str:
        lines = [heading, "──────────────────"]
        hint = shop_cart_hint(context)
        if hint:
            lines.append(hint)
            lines.append("")
        sub_rows = list(subs or [])
        if sub_rows:
            lines.append("Shop by subcategory")
            for idx, row in enumerate(sub_rows, start=1):
                title = str(row.get("item_title") or "")
                lines.append(f"S{idx} {title}")
            lines.append("Tap a subcategory for more categories / products.")
            lines.append("")
        if not rows:
            if empty_query:
                title = context.get("shop_category_title") or "this category"
                lines.extend(
                    [
                        "No products found",
                        f'We couldn\'t find anything matching "{empty_query}" in {title}.',
                        "CLEAR SEARCH · BACK · MENU",
                    ]
                )
            elif categories_only:
                lines.append("No more categories.")
                lines.append("BACK · MENU")
            else:
                lines.append("No products in this category right now.")
                lines.append("BACK · MENU")
            return "\n".join(lines)
        if categories_only:
            lines.append("Tap a category to open it.")
        else:
            lines.append("Products")
        for idx, row in enumerate(rows, start=1):
            title = str(row.get("item_title") or "")
            if categories_only or row.get("kind") == "category":
                lines.append(f"{idx} {title}")
                continue
            price = row.get("sales_rate")
            try:
                price_s = f"Rs {int(float(price)):,}" if price else ""
            except (TypeError, ValueError):
                price_s = ""
            stock = "" if row.get("in_stock", True) else " (out of stock)"
            extra = f" — {price_s}" if price_s else ""
            lines.append(f"{idx} {title}{extra}{stock}")
        if context.get("shop_has_more"):
            lines.append("MORE for next page")
        lines.append("CART · BACK · MENU")
        return "\n".join(lines)

    def _show_categories(
        self,
        conversation: dict[str, Any],
        context: dict[str, Any],
        *,
        parent_id: int | None = None,
        page: int = 1,
    ) -> dict[str, Any]:
        shop = WhatsAppShopService(self.db)
        data = shop.list_categories(parent_id, page)
        if page > 1 and not data["items"]:
            return {"text": "No more categories. Reply BACK or MENU.", "handoff": False}
        context["step"] = "browse"
        context["shop_view"] = "categories"
        context["shop_parent_id"] = parent_id
        context["shop_page"] = data["page"]
        context["shop_has_more"] = data["has_more"]
        context["shop_list"] = data["items"]
        context["shop_category_id"] = parent_id
        context["shop_q"] = ""
        context["shop_subs"] = []
        context["all_options"] = []
        context["pending_options"] = []
        store.update_context(conversation["conversation_id"], context)
        heading = (
            "*Categories*\nTap a category to shop — like the store app."
            if not parent_id
            else "*More categories*\nTap a subcategory to open it."
        )
        return {
            "text": self._format_shop_list(
                heading=heading,
                rows=data["items"],
                context=context,
                categories_only=True,
            ),
            "handoff": False,
        }

    def _show_products(
        self,
        conversation: dict[str, Any],
        context: dict[str, Any],
        *,
        category_id: int | None,
        title: str,
        q: str = "",
        page: int = 1,
        promo_only: bool = False,
        parent_id: int | None = None,
    ) -> dict[str, Any]:
        shop = WhatsAppShopService(self.db)
        q_clean = (q or "").strip()
        data = shop.list_products(
            category_id=None if promo_only else category_id,
            q=q_clean or None,
            page=page,
            promo_only=promo_only,
        )
        if page > 1 and not data["items"] and not q_clean:
            return {"text": "No more products. Reply BACK or MENU.", "handoff": False}
        rows = [
            row
            for row in list(data["items"])
            if not is_hidden_shop_title(str(row.get("item_title") or ""))
        ]
        heading_title = title or ("Offers" if promo_only else "Products")
        prev_title = str(context.get("shop_category_title") or "")
        subs: list[dict[str, Any]] = []
        if page > 1 and not q_clean:
            subs = list(context.get("shop_subs") or [])
        elif (
            not q_clean
            and not promo_only
            and page <= 1
            and category_id
        ):
            sub_data = shop.list_categories(category_id, 1)
            subs = list(sub_data.get("items") or [])
        if q_clean:
            heading = f"*Search results in {heading_title}*"
        elif promo_only:
            heading = "*Offers*"
        elif subs:
            heading = (
                f"*{heading_title}*\n"
                f"Search in {heading_title} — type a name.\n"
                "Shop by subcategory below, then products."
            )
        else:
            heading = f"*{heading_title}*\nSearch in {heading_title} — type a name."
        context["step"] = "browse"
        context["shop_view"] = "offers" if promo_only else "products"
        context["shop_category_id"] = category_id
        context["shop_category_title"] = heading_title
        context["shop_parent_id"] = parent_id
        context["shop_parent_title"] = prev_title if parent_id else ""
        context["shop_q"] = q_clean
        context["shop_page"] = data["page"]
        context["shop_has_more"] = data["has_more"]
        context["shop_promo"] = promo_only
        context["shop_subs"] = [] if q_clean else subs
        context["shop_list"] = rows
        context["all_options"] = []
        context["pending_options"] = []
        store.update_context(conversation["conversation_id"], context)
        return {
            "text": self._format_shop_list(
                heading=heading,
                rows=rows,
                context=context,
                empty_query=q_clean,
                subs=context.get("shop_subs") or [],
            ),
            "handoff": False,
        }

    def _pick_shop_row(
        self,
        conversation: dict[str, Any],
        context: dict[str, Any],
        searcher: ItemPriceSearchService,
        index: int,
    ) -> dict[str, Any] | None:
        rows = list(context.get("shop_list") or [])
        if not (1 <= index <= len(rows)):
            return None
        row = rows[index - 1]
        if row.get("kind") == "category" or context.get("shop_view") == "categories":
            cid = int(row.get("category_id") or 0)
            parent = (
                context.get("shop_category_id")
                if context.get("shop_view") == "products"
                else context.get("shop_parent_id")
            )
            return self._show_products(
                conversation,
                context,
                category_id=cid,
                title=str(row.get("item_title") or ""),
                parent_id=int(parent) if parent else None,
            )
        shop = WhatsAppShopService(self.db)
        product = shop.lookup_product(int(row.get("manual_id") or 0))
        if product is None:
            return {
                "text": "That product is not available. Try another number.",
                "handoff": False,
            }
        pending = product.model_dump()
        self._save_shop_return(context)
        context["pending_item"] = pending
        context["pending_options"] = []
        context["all_options"] = []
        context["step"] = "await_qty"
        store.update_context(conversation["conversation_id"], context)
        rate = product.sales_rate
        try:
            price_s = f"Rs {int(float(rate)):,}" if rate else ""
        except (TypeError, ValueError):
            price_s = ""
        stock = "In stock" if product.in_stock else "Out of stock"
        card = (
            f"*{product.item_title}*\n"
            f"{price_s}\n"
            f"{stock}\n"
            "Prices from the store system."
        )
        return {
            "text": (
                f"{card}\n\n"
                "How many units do you want?\n"
                "Reply with quantity, e.g. *1* or *2*"
            ),
            "handoff": False,
        }

    def _shop_nav_extras(self, context: dict[str, Any]) -> list[ChatQuickReply]:
        """Categories + Back always visible while shopping — same idea as the mobile app."""
        extras: list[ChatQuickReply] = [
            ChatQuickReply(title="Categories", payload="CATEGORIES", style="action"),
        ]
        shop_view = context.get("shop_view") or ""
        if shop_view in {"products", "offers", "categories"}:
            extras.append(ChatQuickReply(title="Back", payload="BACK", style="action"))
        if context.get("shop_has_more"):
            extras.append(ChatQuickReply(title="More", payload="MORE", style="action"))
        if context.get("shop_q"):
            extras.append(
                ChatQuickReply(
                    title="Clear search", payload="CLEAR SEARCH", style="action"
                )
            )
        if context.get("cart"):
            extras.append(
                ChatQuickReply(
                    title=self._view_cart_label(context),
                    payload="CART",
                    style="action",
                )
            )
        return extras

    def _shop_reply(
        self,
        text: str,
        *,
        conversation: dict[str, Any],
        context: dict[str, Any],
        searcher: ItemPriceSearchService,
    ) -> dict[str, Any] | None:
        step = context.get("step") or ""
        lower = text.lower().strip()
        shop_view = context.get("shop_view") or "hub"
        is_nav = is_shop_nav_message(text, shop_view=shop_view)
        if not is_nav and step not in {"browse", "cart_view"}:
            return None
        opened = parse_open_category(text)
        if opened:
            cid, title = opened
            parent = (
                context.get("shop_category_id")
                if shop_view == "products"
                else context.get("shop_parent_id")
            )
            return self._show_products(
                conversation,
                context,
                category_id=cid,
                title=title or str(context.get("shop_category_title") or "Category"),
                parent_id=int(parent) if parent else None,
            )
        sub_idx = parse_sub_index(text)
        if sub_idx:
            subs = list(context.get("shop_subs") or [])
            if 1 <= sub_idx <= len(subs):
                row = subs[sub_idx - 1]
                return self._show_products(
                    conversation,
                    context,
                    category_id=int(row.get("category_id") or 0),
                    title=str(row.get("item_title") or ""),
                    parent_id=context.get("shop_category_id"),
                )
        action = parse_hub_action(lower, shop_view=shop_view)

        if action == "cart":
            return self._cart_view_reply(
                conversation["conversation_id"],
                context,
                title="YOUR CART",
                note="Use − / + on each item, then CONFIRM.",
            )
        if action == "hub":
            return self._open_shop_hub(conversation, context)
        if action == "categories":
            context["step"] = "browse"
            context["shop_q"] = ""
            context["shop_subs"] = []
            context["pending_item"] = None
            context["pending_options"] = []
            context["all_options"] = []
            return self._show_categories(conversation, context, page=1, parent_id=None)
        if action == "offers":
            return self._show_products(
                conversation,
                context,
                category_id=None,
                title="Offers",
                promo_only=True,
            )
        if action == "search":
            context["shop_view"] = "hub"
            context["shop_category_id"] = None
            context["shop_category_title"] = ""
            context["shop_q"] = ""
            context["shop_list"] = []
            context["all_options"] = []
            context["step"] = "browse"
            store.update_context(conversation["conversation_id"], context)
            return {
                "text": (
                    "Search all products.\n"
                    "Send item name, brand, barcode, or code."
                ),
                "handoff": False,
            }
        if action == "clear_search" and shop_view in {"products", "offers"}:
            return self._show_products(
                conversation,
                context,
                category_id=context.get("shop_category_id"),
                title=str(context.get("shop_category_title") or "Category"),
                q="",
                page=1,
                promo_only=bool(context.get("shop_promo")),
                parent_id=context.get("shop_parent_id"),
            )
        if action == "back":
            if shop_view in {"products", "offers"}:
                parent = context.get("shop_parent_id")
                if parent:
                    return self._show_products(
                        conversation,
                        context,
                        category_id=int(parent),
                        title=str(context.get("shop_parent_title") or "Category"),
                        page=1,
                    )
                return self._show_categories(conversation, context, page=1)
            if shop_view == "categories":
                return self._open_shop_hub(conversation, context)
            return self._open_shop_hub(conversation, context)

        if lower in {"more", "next"} and shop_view in {"categories", "products", "offers"}:
            page = int(context.get("shop_page") or 1) + 1
            if shop_view == "categories":
                return self._show_categories(
                    conversation,
                    context,
                    parent_id=context.get("shop_parent_id"),
                    page=page,
                )
            return self._show_products(
                conversation,
                context,
                category_id=context.get("shop_category_id"),
                title=str(context.get("shop_category_title") or "Category"),
                q=str(context.get("shop_q") or ""),
                page=page,
                promo_only=bool(context.get("shop_promo")),
                parent_id=context.get("shop_parent_id"),
            )

        if re.fullmatch(r"\d{1,2}", lower) and context.get("shop_list"):
            picked = self._pick_shop_row(
                conversation, context, searcher, int(lower)
            )
            if picked:
                return picked

        if shop_view in {"products", "offers"} and len(lower) >= 1:
            if lower in {"more", "next", "back", "menu", "cart", "confirm"}:
                return None
            if re.fullmatch(r"\d{1,2}", lower):
                return {
                    "text": f"Please reply with a number from 1 to {len(context.get('shop_list') or [])}.",
                    "handoff": False,
                }
            return self._show_products(
                conversation,
                context,
                category_id=context.get("shop_category_id"),
                title=str(context.get("shop_category_title") or "Category"),
                q=text.strip(),
                page=1,
                promo_only=bool(context.get("shop_promo")),
                parent_id=context.get("shop_parent_id"),
            )
        return None

    @staticmethod
    def _parse_qty(text: str) -> float | None:
        raw = (text or "").strip().lower()
        match = re.fullmatch(
            r"(?:qty|quantity|x)?\s*(\d+(?:\.\d+)?)\s*(?:pcs|pc|x|units?|qty)?",
            raw,
        )
        if not match:
            return None
        try:
            value = float(match.group(1))
        except ValueError:
            return None
        if value <= 0 or value > 9999:
            return None
        return value

    def _price_reply(
        self,
        message: str,
        *,
        conversation: dict[str, Any],
        soft: bool = False,
    ) -> dict[str, Any]:
        if self.db is None:
            return {
                "text": "Price search is temporarily unavailable. Please try again later.",
                "handoff": False,
                "matched": False,
            }

        conversation_id = conversation["conversation_id"]
        context = dict(conversation.get("context") or {})
        lower = message.strip().lower()
        searcher = ItemPriceSearchService(self.db)
        scan_link = f"{settings.base_url.rstrip('/')}/guest/scan"

        options = list(context.get("all_options") or context.get("pending_options") or [])
        page = int(context.get("page") or 0)

        # Menu "3" must not steal a listed option number while results are showing.
        if (
            self._wants_price_menu(lower)
            and not self._looks_like_price_query(lower)
            and not (options and re.fullmatch(r"\d{1,2}", lower.strip()))
        ):
            store.update_context(
                conversation_id,
                {"mode": "price", "pending_options": [], "all_options": [], "page": 0},
            )
            return {
                "text": (
                    "Price list search ready.\n"
                    "Send item name, brand, barcode, or item code.\n"
                    "You can also send a voice note with the product name.\n"
                    f"Barcode scanner: {scan_link}\n\n"
                    "Tips: try short names like 'Dalda 5L' or 'Surf Excel'.\n"
                    "Reply MENU anytime to go back."
                ),
                "handoff": False,
                "matched": True,
            }

        if options and lower in {"more", "next"}:
            page_size = 8
            next_page = page + 1
            if next_page * page_size >= len(options):
                return {
                    "text": "No more items. Type a new name, or tap New search.",
                    "handoff": False,
                    "matched": True,
                }
            page = next_page
            store.update_context(
                conversation_id,
                {
                    "mode": "price",
                    "pending_options": options,
                    "all_options": options,
                    "page": page,
                },
            )
            remaining = len(options) - page * page_size
            return {
                "text": (
                    f"More matches — page {page + 1}.\n"
                    f"{min(page_size, remaining)} more item(s). Tap below."
                ),
                "handoff": False,
                "matched": True,
            }

        if options and lower in {"new", "search", "again"}:
            store.update_context(
                conversation_id,
                {"mode": "price", "pending_options": [], "all_options": [], "page": 0},
            )
            return {
                "text": "OK. Send a new item name, barcode, or voice note.",
                "handoff": False,
                "matched": True,
            }

        if options and re.fullmatch(r"\d{1,2}", lower.strip()):
            choice = int(lower.strip())
            if 1 <= choice <= len(options):
                selected = options[choice - 1]
                from app.schemas.guest_price_lookup import GuestPriceSearchMatch

                item = GuestPriceSearchMatch(**selected)
                store.update_context(
                    conversation_id,
                    {"mode": "price", "pending_options": [], "all_options": [], "page": 0},
                )
                card = searcher.format_price_card(item)
                return {
                    "text": f"{card}\n\nSend another item name, or MENU for main menu.",
                    "handoff": False,
                    "matched": True,
                }
            return {
                "text": f"Please reply with a number from 1 to {len(options)}.",
                "handoff": False,
                "matched": True,
            }

        is_code_query = bool(re.fullmatch(r"\d{1,20}", message.strip()))
        result = searcher.search(message, limit=24, force_list=not is_code_query)
        if result.match_type == "none":
            if soft:
                return {"text": "", "handoff": False, "matched": False}
            store.update_context(
                conversation_id,
                {"mode": "price", "pending_options": [], "all_options": [], "page": 0},
            )
            return {
                "text": (
                    f"{result.message}\n\n"
                    "Try brand + size (example: Olper 1L), barcode, or item code.\n"
                    f"Or scan here: {scan_link}"
                ),
                "handoff": False,
                "matched": True,
            }

        # Barcode / item code: show card directly.
        if is_code_query and result.match_type == "exact" and result.items:
            item = result.items[0]
            store.update_context(
                conversation_id,
                {"mode": "price", "pending_options": [], "all_options": [], "page": 0},
            )
            return {
                "text": (
                    f"Exact match:\n{searcher.format_price_card(item)}\n\n"
                    "Send another item, or MENU for main menu."
                ),
                "handoff": False,
                "matched": True,
            }

        option_dicts = [item.model_dump(mode="json") for item in result.items]
        store.update_context(
            conversation_id,
            {
                "mode": "price",
                "pending_options": option_dicts,
                "all_options": option_dicts,
                "page": 0,
                "last_query": result.cleaned_query or message,
            },
        )
        return {
            "text": (
                f"Found {len(option_dicts)} item(s) for "
                f"'{result.cleaned_query or message}'.\n"
                "Tap an item below to see the rate."
            ),
            "handoff": False,
            "matched": True,
        }

    @staticmethod
    def _options_from_dicts(options: list[dict[str, Any]]):
        from app.schemas.guest_price_lookup import GuestPriceSearchMatch

        return [GuestPriceSearchMatch(**item) for item in options]

    def _chat_order_status_reply(
        self,
        message: str,
        *,
        conversation: dict[str, Any],
        phone: str,
    ) -> dict[str, Any]:
        from app.services import whatsapp_order_store as order_store

        conversation_id = conversation["conversation_id"]
        text = (message or "").strip()
        lower = text.lower().strip()
        mobile = self._resolved_mobile(conversation, phone)

        # Leave status mode for other main-menu actions.
        if self._is_menu(lower) or lower in {"hi", "hello", "salam", "assalam", "start"}:
            store.update_context(conversation_id, None)
            conversation = self._attach_known_customer(conversation)
            config = store.load_config()
            company = settings.company_name or settings.app_name
            return {
                "text": self._format_welcome(
                    config,
                    company=company,
                    conversation=conversation,
                    phone=phone,
                ),
                "handoff": False,
            }
        if self._wants_order(lower):
            store.update_context(conversation_id, None)
            return self._order_reply(text, conversation=conversation, phone=phone)
        if self._wants_human(lower):
            store.update_context(conversation_id, None)
            return {
                "text": store.load_config().human_handoff_message,
                "handoff": True,
            }
        if self._wants_delivery(lower):
            store.update_context(conversation_id, None)
            return {
                "text": self._delivery_status_reply(text, phone=phone),
                "handoff": False,
            }

        # Direct order number lookup (WO-...)
        order_no = self._extract_chat_order_no(text)
        if order_no:
            row = order_store.find_by_order_no(order_no)
            store.update_context(conversation_id, None)
            if not row:
                return {
                    "text": (
                        f"No chat order found for *{order_no}*.\n"
                        "Check the order number on your receipt, or reply *6* "
                        "to search by your mobile."
                    ),
                    "handoff": False,
                }
            return {
                "text": self._format_chat_order_status([row]),
                "handoff": False,
            }

        # Menu entry "6" / "my order" — try mobile first
        if self._wants_chat_order_status(lower) and not order_no:
            if mobile:
                rows = order_store.find_by_mobile(mobile, limit=5)
                if rows:
                    store.update_context(conversation_id, None)
                    return {
                        "text": self._format_chat_order_status(rows),
                        "handoff": False,
                    }
            store.update_context(
                conversation_id,
                {"mode": "order_status", "step": "await_ref"},
            )
            if mobile:
                hint = (
                    f"No recent chat orders found for *{self._display_mobile(mobile)}*.\n"
                    "Send your *order number* (example: WO-20260807-ABCD),\n"
                    "or another *mobile number* used on the order.\n"
                )
            else:
                hint = (
                    "Send your *order number* (example: WO-20260807-ABCD)\n"
                    "or the *mobile number* used on the order.\n"
                )
            return {
                "text": (
                    "*My order status*\n"
                    "──────────────────\n"
                    f"{hint}"
                    "Reply MENU to go back."
                ),
                "handoff": False,
            }

        # Awaiting order no / mobile inside order_status mode
        if re.fullmatch(r"\d{10,13}", re.sub(r"\D", "", text)) or len(
            re.sub(r"\D", "", text)
        ) >= 10:
            rows = order_store.find_by_mobile(text, limit=5)
            store.update_context(conversation_id, None)
            if not rows:
                return {
                    "text": (
                        "No chat orders found for that mobile.\n"
                        "Try your order number (WO-…), or reply *4* to place a new order."
                    ),
                    "handoff": False,
                }
            return {
                "text": self._format_chat_order_status(rows),
                "handoff": False,
            }

        store.update_context(
            conversation_id,
            {"mode": "order_status", "step": "await_ref"},
        )
        return {
            "text": (
                "Please send a valid *order number* (WO-…)\n"
                "or the *mobile number* used when ordering."
            ),
            "handoff": False,
        }

    def _format_chat_order_status(self, rows: list[dict[str, Any]]) -> str:
        if not rows:
            return "No orders found."
        lines = ["*Your chat order status*", "──────────────────"]
        for row in rows[:5]:
            order_no = row.get("order_no") or "—"
            status = str(row.get("status") or "pending").upper()
            total = self._money_label(row.get("order_total"))
            name = row.get("customer_name") or "Customer"
            mobile = self._display_mobile(
                row.get("customer_mobile") or row.get("phone") or ""
            )
            created = str(row.get("created_at") or "")[:16].replace("T", " ")
            items = int(row.get("item_count") or len(row.get("items") or []) or 0)
            address = (row.get("customer_address") or "").strip()
            lines.append(f"Order   *{order_no}*")
            lines.append(f"Status  *{status}*")
            lines.append(f"Customer {name}")
            if mobile:
                lines.append(f"Mobile   {mobile}")
            lines.append(f"Items    {items}")
            if total:
                lines.append(f"Total    {total}")
            if address:
                lines.append(f"Address  {address}")
            if created:
                lines.append(f"Placed   {created}")
            maps = (row.get("maps_url") or "").strip()
            if maps:
                lines.append(f"Maps     {maps}")
            lines.append("──────────────────")
        lines.append("Reply *4* for a new order, or MENU for main menu.")
        return "\n".join(lines)

    @staticmethod
    def _looks_like_chat_order_no(lower: str) -> bool:
        return bool(re.search(r"\bwo[-\s]?\d{8}[-\s]?[a-z0-9]{4}\b", lower, flags=re.I))

    @staticmethod
    def _extract_chat_order_no(text: str) -> str:
        match = re.search(
            r"\b(WO[-\s]?\d{8}[-\s]?[A-Za-z0-9]{4})\b",
            text or "",
            flags=re.I,
        )
        if not match:
            return ""
        raw = re.sub(r"\s+", "", match.group(1).upper())
        raw = raw.replace("WO", "WO-", 1) if raw.startswith("WO") and not raw.startswith("WO-") else raw
        # Normalize WO-YYYYMMDD-XXXX
        m2 = re.fullmatch(r"WO-?(\d{8})-?([A-Z0-9]{4})", raw)
        if not m2:
            return raw
        return f"WO-{m2.group(1)}-{m2.group(2)}"

    def _delivery_status_reply(self, message: str, *, phone: str) -> str:
        if self.db is None:
            return "Delivery lookup is temporarily unavailable. Please try again later."

        repo = DeliveryRepository(self.db)
        digits = re.sub(r"\D", "", message)
        search = ""
        invoice_match = re.search(r"\b\d{4,10}\b", message)
        if invoice_match:
            search = invoice_match.group(0)
        elif len(digits) >= 10:
            search = digits[-10:]
        elif phone:
            search = re.sub(r"\D", "", phone)[-10:]

        if not search:
            return (
                "Please send your invoice number or the mobile number used on the invoice.\n"
                "Example: 12345 or 03001234567"
            )

        rows = repo.list_orders(skip=0, limit=5, search=search, order_status=None, rider_id=None)
        if not rows:
            return (
                f"No delivery order found for '{search}'.\n"
                "Check the invoice number / mobile, or reply 4 to talk to staff."
            )

        lines = ["Delivery status:"]
        for row in rows[:3]:
            invoice = row.get("invoice_id") or "—"
            status = row.get("status") or "—"
            rider = row.get("rider_name") or "Not assigned"
            mobile = row.get("customer_mobile_no") or "—"
            lines.append(
                f"Invoice {invoice}\n"
                f"Status: {status}\n"
                f"Rider: {rider}\n"
                f"Mobile: {mobile}"
            )
        if len(rows) > 3:
            lines.append(f"...and {len(rows) - 3} more. Reply 4 for staff help.")
        return "\n\n".join(lines)

    @staticmethod
    def _mobile_key(phone: str) -> str:
        digits = re.sub(r"\D", "", phone or "")
        return digits[-10:] if len(digits) >= 10 else ""

    @staticmethod
    def _mobile_for_storage(phone: str) -> str:
        """Store as local 03XXXXXXXXX when possible (matches CUST_SMS habit)."""
        digits = re.sub(r"\D", "", phone or "")
        if not digits:
            return ""
        if digits.startswith("92") and len(digits) >= 12:
            return "0" + digits[2:12]
        if len(digits) >= 11 and digits.startswith("0"):
            return digits[:11]
        if len(digits) >= 10:
            return "0" + digits[-10:]
        return digits

    @classmethod
    def _display_mobile(cls, phone: str) -> str:
        """Human-facing local mobile for chat (03XXXXXXXXX)."""
        return cls._mobile_for_storage(phone) or (phone or "").strip()

    def _resolved_mobile(
        self,
        conversation: dict[str, Any],
        phone: str = "",
        context: dict[str, Any] | None = None,
    ) -> str:
        """Prefer known WhatsApp / conversation / CUST_SMS mobile — never invent."""
        ctx = context or conversation.get("context") or {}
        candidates = [
            ctx.get("customer_mobile") or "",
            conversation.get("phone") or "",
            phone or "",
        ]
        for raw in candidates:
            if self._mobile_key(raw):
                return raw
        return ""

    def _lookup_cust_sms(self, phone: str) -> dict[str, Any] | None:
        if self.db is None:
            return None
        key = self._mobile_key(phone)
        if not key:
            return None
        try:
            row = DeliveryRepository(self.db).find_delivery_customer(key)
        except Exception:
            return None
        if not row:
            return None
        name = (row.get("name") or "").strip()
        if not name:
            return None
        return {
            "cust_id": int(row.get("cust_sms_id") or 0),
            "name": name,
            "mobile": (row.get("mobile") or "").strip(),
            "address": (row.get("address") or "").strip(),
            "is_new": False,
        }

    def _ensure_cust_sms(
        self,
        *,
        name: str,
        mobile: str,
        address: str = "",
    ) -> dict[str, Any] | None:
        """Find CUST_SMS by mobile; create when missing. Safe no-op without DB."""
        if self.db is None:
            return None
        clean_name = (name or "").strip()[:150]
        if len(clean_name) < 2:
            return None
        existing = self._lookup_cust_sms(mobile)
        if existing:
            return existing
        storage_mobile = self._mobile_for_storage(mobile)
        if len(self._mobile_key(storage_mobile)) < 10:
            return None
        try:
            cust_id = DeliveryRepository(self.db).create_delivery_customer(
                name=clean_name,
                mobile=storage_mobile,
                address=(address or "").strip()[:500],
            )
            self.db.commit()
        except Exception:
            try:
                self.db.rollback()
            except Exception:
                pass
            # Race: another insert may have won — re-read.
            return self._lookup_cust_sms(mobile)
        return {
            "cust_id": int(cust_id),
            "name": clean_name,
            "mobile": storage_mobile,
            "address": (address or "").strip(),
            "is_new": True,
        }

    def _attach_known_customer(self, conversation: dict[str, Any]) -> dict[str, Any]:
        phone = conversation.get("phone") or ""
        profile = self._lookup_cust_sms(phone)
        if not profile:
            return conversation
        updated = store.upsert_conversation(
            conversation_id=conversation["conversation_id"],
            display_name=profile["name"],
            phone=phone or profile.get("mobile") or "",
            channel=conversation.get("channel") or "offline",
        )
        return updated

    def _format_welcome(
        self,
        config: WhatsAppBotConfig,
        *,
        company: str,
        conversation: dict[str, Any],
        phone: str,
    ) -> str:
        profile = self._lookup_cust_sms(
            conversation.get("phone") or phone or ""
        )
        name = ""
        if profile:
            name = profile.get("name") or ""
        if not name:
            raw = (conversation.get("display_name") or "").strip()
            if raw and raw.lower() not in {"guest", (phone or "").lower()}:
                # Only treat as known name if CUST_SMS matched; else soft label.
                if profile:
                    name = raw
        menu = self.MAIN_MENU_TEXT
        mobile_show = self._display_mobile(
            (profile or {}).get("mobile")
            or conversation.get("phone")
            or phone
            or ""
        )
        mobile_line = f"Mobile: *{mobile_show}*\n" if mobile_show else ""
        if profile and name:
            try:
                text = config.returning_welcome_message.format(
                    company=company,
                    name=name,
                    mobile=mobile_show,
                )
            except (KeyError, ValueError, AttributeError):
                text = (
                    f"Assalam-o-Alaikum, *{name}*!\n"
                    f"Welcome back to {company}.\n"
                    "It is our pleasure to serve you again.\n\n"
                    f"How may we assist you today?\n{menu}"
                )
            if mobile_show and "Mobile:" not in text:
                text = text.replace(
                    f"Welcome back to {company}.\n",
                    f"Welcome back to {company}.\n{mobile_line}",
                    1,
                )
            return self._with_main_menu(text)
        name_part = f", *{name}*" if name else ""
        try:
            text = config.welcome_message.format(
                company=company,
                name=name or "Customer",
                name_part=name_part,
                mobile=mobile_show,
            )
        except (KeyError, ValueError):
            text = (
                f"Assalam-o-Alaikum{name_part}!\n"
                f"Welcome to {company}.\n"
                "We are pleased to assist you.\n\n"
                f"How may we help you today?\n{menu}"
            )
        if mobile_show and "Mobile:" not in text:
            text = text.replace(
                f"Welcome to {company}.\n",
                f"Welcome to {company}.\n{mobile_line}",
                1,
            )
        return self._with_main_menu(text)

    MAIN_MENU_TEXT = (
        "1 Delivery status\n"
        "2 Store info\n"
        "3 Price list (text / voice)\n"
        "4 Place order\n"
        "5 Talk to staff\n"
        "6 My order status"
    )

    @classmethod
    def _with_main_menu(cls, text: str) -> str:
        """Force the full 1–6 menu into welcome text (config may be stale)."""
        body = (text or "").strip()
        if not body:
            return (
                "How may we help you today?\n"
                f"{cls.MAIN_MENU_TEXT}"
            )
        # Drop any prior numbered menu block so option 6 cannot be omitted.
        cleaned = re.sub(
            r"(?is)(?:^|\n)\s*1\s+Delivery status\b.*$",
            "",
            body,
        ).rstrip()
        cleaned = re.sub(
            r"(?im)^\s*[1-6]\s+.+$",
            "",
            cleaned,
        ).rstrip()
        prompt = "How may we help you today?"
        if not re.search(r"(?i)how may we (help|assist) you today\??", cleaned):
            cleaned = f"{cleaned}\n\n{prompt}" if cleaned else prompt
        return f"{cleaned}\n{cls.MAIN_MENU_TEXT}"

    @classmethod
    def _main_menu_quick_replies(cls) -> list[ChatQuickReply]:
        return [
            ChatQuickReply(title="1 Delivery", payload="1", style="chip"),
            ChatQuickReply(title="2 Store info", payload="2", style="chip"),
            ChatQuickReply(title="3 Price list", payload="3", style="chip"),
            ChatQuickReply(title="4 Place order", payload="4", style="chip"),
            ChatQuickReply(title="5 Staff", payload="5", style="chip"),
            ChatQuickReply(title="6 My order", payload="6", style="chip"),
        ]

    @staticmethod
    def _money_label(value: Any) -> str:
        try:
            number = float(value or 0)
        except (TypeError, ValueError):
            return ""
        if abs(number - int(number)) < 1e-9:
            return f"Rs {int(number):,}"
        return f"Rs {number:,.2f}"

    def _item_choice_replies(
        self,
        options: list[dict[str, Any]],
        *,
        page: int = 0,
        page_size: int = 8,
        extra_actions: list[ChatQuickReply] | None = None,
    ) -> list[ChatQuickReply]:
        options = [
            raw
            for raw in (options or [])
            if not is_hidden_shop_title(str(raw.get("item_title") or ""))
        ]
        start = page * page_size
        chunk = options[start : start + page_size]
        buttons: list[ChatQuickReply] = []
        for idx, raw in enumerate(chunk, start=start + 1):
            title = str(raw.get("item_title") or f"Item {idx}").strip()
            if len(title) > 90:
                title = title[:87] + "…"
            code = raw.get("manual_id")
            short = str(raw.get("item_short") or "").strip()
            subtitle_parts = []
            if code:
                subtitle_parts.append(f"Code {code}")
            if short:
                subtitle_parts.append(short)
            buttons.append(
                ChatQuickReply(
                    title=title,
                    payload=str(idx),
                    style="item",
                    subtitle=" | ".join(subtitle_parts),
                    meta=self._money_label(raw.get("sales_rate")),
                    manual_id=int(code) if code else None,
                )
            )
        actions: list[ChatQuickReply] = list(extra_actions or [])
        if start + len(chunk) < len(options):
            actions.insert(0, ChatQuickReply(title="More items", payload="MORE", style="action"))
        actions.append(ChatQuickReply(title="Menu", payload="MENU", style="action"))
        buttons.extend(actions)
        return buttons

    @classmethod
    def _input_prompt_for(cls, conversation: dict[str, Any]) -> tuple[str, str]:
        """Placeholder + short hint for the guest chat input, based on current options."""
        context = conversation.get("context") or {}
        mode = context.get("mode")
        step = context.get("step") or ""
        options = list(
            context.get("all_options") or context.get("pending_options") or []
        )

        if not mode:
            return (
                "Tap a menu option, or type 1–6…",
                "Main menu — choose Delivery, Price, Order, My order…",
            )

        if mode == "order_status":
            return (
                "Order no. WO-… or mobile 03XXXXXXXXX",
                "My order status — send order number or mobile",
            )

        if mode == "price":
            if options:
                return (
                    "Tap an item, or type a new brand/name…",
                    "Price list — select a match or search again",
                )
            return (
                "Type brand/item e.g. Dalda…",
                "Price list — search by name, brand, or barcode",
            )

        if mode == "order":
            if step == "await_name":
                return ("Type your full name…", "Place order — enter your name")
            if step == "await_mobile":
                return ("Type mobile 03XXXXXXXXX…", "Place order — enter mobile")
            if step == "await_fulfill":
                return ("Tap Delivery or Pick-up…", "How should we fulfil this order?")
            if step == "await_area":
                return ("City and area, e.g. Lahore, Shad Bagh…", "Delivery area — GPS not required")
            if step == "confirm_address":
                return (
                    "Tap Keep / Update / Skip, or type a new address…",
                    "Confirm delivery address",
                )
            if step == "await_address":
                return (
                    "Type delivery address…",
                    "Place order — enter delivery address",
                )
            if step == "await_location":
                return (
                    "Share location or type SKIP…",
                    "Optional Google Maps pin",
                )
            if step == "await_notes":
                return (
                    "Optional note, or type SKIP…",
                    "Any delivery note before confirm",
                )
            if step == "await_qty" and context.get("pending_item"):
                return (
                    "Type quantity e.g. 1 or 2…",
                    "How many units do you want?",
                )
            cat_title = str(context.get("shop_category_title") or "").strip()
            shop_view = context.get("shop_view") or ""
            if shop_view in {"products", "offers"} and cat_title:
                return (
                    f"Search in {cat_title}…",
                    f"Search results stay in {cat_title}",
                )
            if shop_view == "categories":
                return (
                    "Tap a category, or MORE…",
                    "Shop by category",
                )
            if options:
                return (
                    "Tap an item to add, or type a new name…",
                    "Order — select product or search again",
                )
            if step == "cart_view" and context.get("cart"):
                return (
                    "Change qty below, or type item name to add…",
                    "Your cart — confirm qty, then Confirm order",
                )
            if context.get("cart"):
                return (
                    "Type item name to add more, or CONFIRM…",
                    "Order in progress — add items or confirm",
                )
            return (
                "Type brand/item to order e.g. Dalda…",
                "Place order — search products to add",
            )

        return (
            "Type your message…",
            "Chat",
        )

    def _quick_replies_for(self, conversation: dict[str, Any]) -> list[ChatQuickReply]:
        """Tap controls for guest web chat — context decides meaning of numbers."""
        context = conversation.get("context") or {}
        mode = context.get("mode")
        if not mode:
            return self._main_menu_quick_replies()

        menu_btn = ChatQuickReply(title="Menu", payload="MENU", style="action")
        if mode == "order":
            step = context.get("step") or "browse"
            if step in {"await_name", "await_mobile"}:
                return [menu_btn]
            if step == "await_fulfill":
                return [
                    ChatQuickReply(title="Delivery", payload="DELIVERY", style="action"),
                    ChatQuickReply(title="Pick-up", payload="PICKUP", style="action"),
                    menu_btn,
                ]
            if step == "await_area":
                return [
                    ChatQuickReply(title="Use store area", payload="Shad Bagh", style="action"),
                    menu_btn,
                ]
            if step == "confirm_address":
                return [
                    ChatQuickReply(title="Keep address", payload="KEEP", style="action"),
                    ChatQuickReply(title="Update address", payload="UPDATE", style="action"),
                    ChatQuickReply(title="Skip", payload="SKIP", style="action"),
                    menu_btn,
                ]
            if step in {"await_notes", "await_address", "await_location"}:
                return [
                    ChatQuickReply(title="Skip", payload="SKIP", style="action"),
                    menu_btn,
                ]
            if step == "await_qty" and context.get("pending_item"):
                return [
                    ChatQuickReply(title="Qty 1", payload="1", style="action"),
                    ChatQuickReply(title="Qty 2", payload="2", style="action"),
                    ChatQuickReply(title="Qty 3", payload="3", style="action"),
                    ChatQuickReply(title="Qty 5", payload="5", style="action"),
                    menu_btn,
                ]
            shop_list = [
                row
                for row in list(context.get("shop_list") or [])
                if str(row.get("kind") or "") == "category"
                or not is_hidden_shop_title(str(row.get("item_title") or ""))
            ]
            if shop_list != list(context.get("shop_list") or []):
                context["shop_list"] = shop_list
                store.update_context(conversation["conversation_id"], context)
            shop_subs = [
                row
                for row in list(context.get("shop_subs") or [])
                if not is_hidden_shop_title(str(row.get("item_title") or ""))
            ]
            shop_view = context.get("shop_view") or ""
            if (shop_list or shop_subs) and step == "browse":
                extra = self._shop_nav_extras(context)
                if shop_view == "categories":
                    cat_items: list[ChatQuickReply] = []
                    for idx, row in enumerate(shop_list, start=1):
                        cid = int(row.get("category_id") or 0)
                        title = str(row.get("item_title") or f"Category {idx}")
                        if is_hidden_shop_title(title):
                            continue
                        cat_items.append(
                            ChatQuickReply(
                                title=title,
                                payload=f"CAT {cid} {title}"[:200],
                                style="item",
                                subtitle="Open category",
                            )
                        )
                    cat_items.extend(extra)
                    cat_items.append(menu_btn)
                    return cat_items
                for row in shop_subs:
                    cid = int(row.get("category_id") or 0)
                    title = str(row.get("item_title") or "Category")
                    if is_hidden_shop_title(title):
                        continue
                    extra.insert(
                        1,
                        ChatQuickReply(
                            title=title,
                            payload=f"CAT {cid} {title}"[:200],
                            style="chip",
                        ),
                    )
                return self._item_choice_replies(
                    shop_list,
                    page=0,
                    page_size=max(len(shop_list), 1),
                    extra_actions=extra,
                )
            options = [
                row
                for row in list(
                    context.get("all_options") or context.get("pending_options") or []
                )
                if not is_hidden_shop_title(str(row.get("item_title") or ""))
            ]
            if options:
                return self._item_choice_replies(
                    options,
                    page=int(context.get("page") or 0),
                    extra_actions=[
                        ChatQuickReply(
                            title="New search", payload="NEW", style="action"
                        ),
                        ChatQuickReply(title="Cart", payload="CART", style="action"),
                    ],
                )
            if step == "cart_view" and context.get("cart"):
                return self._cart_line_replies(context.get("cart") or [])
            buttons: list[ChatQuickReply] = [
                ChatQuickReply(title="Categories", payload="CATEGORIES", style="action"),
                ChatQuickReply(title="Search", payload="SEARCH", style="action"),
                ChatQuickReply(title="Offers", payload="OFFERS", style="action"),
            ]
            if context.get("cart"):
                buttons.extend(
                    [
                        ChatQuickReply(
                            title=self._view_cart_label(context),
                            payload="CART",
                            style="action",
                        ),
                        ChatQuickReply(
                            title="Confirm", payload="CONFIRM", style="action"
                        ),
                        ChatQuickReply(title="Clear", payload="CLEAR", style="action"),
                    ]
                )
            buttons.append(menu_btn)
            return buttons

        if mode == "price":
            options = list(
                context.get("all_options") or context.get("pending_options") or []
            )
            if options:
                return self._item_choice_replies(
                    options,
                    page=int(context.get("page") or 0),
                    extra_actions=[
                        ChatQuickReply(
                            title="New search", payload="NEW", style="action"
                        ),
                    ],
                )
            return [
                ChatQuickReply(title="New search", payload="NEW", style="action"),
                menu_btn,
            ]

        if mode == "order_status":
            return [
                ChatQuickReply(title="Place order", payload="4", style="action"),
                menu_btn,
            ]

        return self._main_menu_quick_replies()

    @staticmethod
    def _is_menu(lower: str) -> bool:
        return lower in {"menu", "help", "0", "hi", "hello", "start", "سلام"}

    @staticmethod
    def _wants_human(lower: str) -> bool:
        return lower in {"5", "human", "staff", "agent", "help me"} or any(
            word in lower for word in ("talk to", "call me", "representative", "operator")
        )

    @staticmethod
    def _wants_order(lower: str) -> bool:
        # Do not match bare "orders" / "my order" — those are order-status.
        return lower in {
            "4",
            "order",
            "buy",
            "purchase",
            "place order",
            "new order",
            "shopping",
            "shop",
            "categories",
        } or any(
            word in lower
            for word in ("place order", "i want to order", "order please", "buy now")
        )

    @staticmethod
    def _wants_store_info(lower: str) -> bool:
        return lower in {"2", "info", "store", "address", "timing", "hours"} or any(
            word in lower for word in ("store info", "location", "where are you", "timings")
        )

    @staticmethod
    def _wants_price_menu(lower: str) -> bool:
        return lower in {
            "3",
            "price",
            "prices",
            "rate",
            "rates",
            "barcode",
            "pricelist",
            "price list",
        } or any(
            word in lower
            for word in (
                "price check",
                "check price",
                "price list",
                "item price",
                "scan barcode",
            )
        )

    @staticmethod
    def _looks_like_price_query(lower: str) -> bool:
        if not lower or len(lower) < 3:
            return False
        triggers = (
            "price of",
            "price for",
            "rate of",
            "rate for",
            "kitna",
            "kitni",
            "price ",
            "rate ",
            "rs ",
            "cost of",
        )
        if any(lower.startswith(t) or f" {t}" in f" {lower}" for t in triggers):
            # Ignore bare menu words already handled elsewhere
            if lower.strip() in {"price", "rate", "prices", "rates"}:
                return False
            return True
        return False

    @staticmethod
    def _main_menu_digit(lower: str) -> str:
        """Return '1'..'6' when the user tapped/typed a bare main-menu option."""
        text = (lower or "").strip().lower()
        if text in {"1", "2", "3", "4", "5", "6"}:
            return text
        match = re.fullmatch(
            r"([1-6])\s*(?:[\.\):\-]|\s+)\s*(.+)",
            text,
        )
        if not match:
            return ""
        digit, label = match.group(1), match.group(2)
        labels = {
            "1": ("delivery",),
            "2": ("store", "info", "address", "hours"),
            "3": ("price", "rate", "list"),
            "4": ("place", "order", "buy"),
            "5": ("staff", "human", "agent", "talk"),
            "6": ("my order", "order status", "orders", "track"),
        }
        if any(token in label for token in labels.get(digit, ())):
            return digit
        return ""

    @staticmethod
    def _wants_chat_order_status(lower: str) -> bool:
        text = (lower or "").strip().lower()
        if text in {
            "6",
            "my order",
            "my orders",
            "order status",
            "track order",
            "check order",
        }:
            return True
        return any(
            word in text
            for word in (
                "my order",
                "order status",
                "track order",
                "check order",
                "where is my order",
            )
        )

    @staticmethod
    def _wants_delivery(lower: str) -> bool:
        return lower in {"1", "delivery"} or any(
            word in lower
            for word in (
                "delivery status",
                "where is my rider",
                "rider status",
                "invoice status",
            )
        )

    @staticmethod
    def _looks_like_invoice(digits: str, lower: str) -> bool:
        text = (lower or "").strip()
        # Never treat main-menu digits 1–6 as invoice numbers.
        if text in {"1", "2", "3", "4", "5", "6"}:
            return False
        return bool(re.fullmatch(r"\d{4,10}", text)) or (
            len(digits) >= 10 and digits.startswith(("03", "3", "92"))
        )

    def _configuration_hint(self, config: WhatsAppBotConfig) -> str:
        if not settings.whatsapp_bot_enabled:
            return "Set WHATSAPP_BOT_ENABLED=true in .env and restart."
        if not self.whatsapp.is_configured():
            return (
                "Customer WhatsApp delivery is OFF. "
                "Set WHATSAPP_ENABLED=true, WHATSAPP_API_TOKEN, and "
                "WHATSAPP_PHONE_NUMBER_ID in .env, then restart. "
                "Staff replies will not reach the customer until this is done."
            )
        if not config.online_mode:
            return (
                "WhatsApp API credentials are ready, but “Deliver to WhatsApp phones” is OFF. "
                "Turn that switch ON in Bot Settings so replies reach the customer’s WhatsApp. "
                "This is separate from the guest web chat page."
            )
        if not settings.whatsapp_verify_token.strip():
            return "Set WHATSAPP_VERIFY_TOKEN in .env for Meta webhook verification."
        return (
            "Online mode ready. Configure Meta webhook to the URL shown, "
            "using WHATSAPP_VERIFY_TOKEN. Staff replies will send to WhatsApp."
        )

    @staticmethod
    def _to_conversation(row: dict[str, Any]) -> ChatConversation:
        messages = []
        for item in row.get("messages") or []:
            messages.append(ChatMessage(**item))
        return ChatConversation(
            conversation_id=row["conversation_id"],
            phone=row.get("phone") or "",
            display_name=row.get("display_name") or "",
            channel=row.get("channel") or "offline",
            status=row.get("status") or "bot",
            unread=int(row.get("unread") or 0),
            updated_at=row["updated_at"],
            last_message=row.get("last_message") or "",
            messages=messages,
        )
