"""WhatsApp Cloud API webhook + offline chatbot admin APIs."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Header,
    HTTPException,
    Query,
    Request,
    Response,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, require_permission
from app.config.settings import settings
from app.database.business_session import get_business_db
from app.schemas import MessageResponse
from app.schemas.whatsapp_bot import (
    ChatConversation,
    ChatConversationSummary,
    ConversationStatusUpdate,
    MobileOtpResponse,
    MobileOtpSendRequest,
    MobileOtpVerifyRequest,
    OfflineChatRequest,
    OfflineChatResponse,
    StaffReplyRequest,
    VoiceTranscribeResponse,
    WhatsAppBotConfig,
    WhatsAppBotConfigUpdate,
    WhatsAppBotStatus,
)
from app.services.speech_to_text_service import SpeechToTextError, SpeechToTextService
from app.schemas.whatsapp_order import ChatOrder, ChatOrderStatusUpdate, ChatOrderSummary
from app.services import voice_search_control_store as voice_control
from app.services.mobile_otp_service import MobileOtpService
from app.services.whatsapp_bot_service import WhatsAppBotService
from app.services.whatsapp_order_service import WhatsAppOrderService

logger = logging.getLogger("ahsteellab")


def _client_ip(request: Request) -> str:
    forwarded = (request.headers.get("x-forwarded-for") or "").split(",")[0].strip()
    if forwarded:
        return forwarded[:64]
    if request.client and request.client.host:
        return str(request.client.host)[:64]
    return ""

router = APIRouter()
public_router = APIRouter()


def _verify_signature(raw_body: bytes, signature_header: str | None) -> bool:
    secret = settings.whatsapp_app_secret.strip()
    if not secret:
        # Allow webhook without app secret in early setup; still require verify token on GET.
        return True
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = hmac.new(
        secret.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()
    provided = signature_header.split("=", 1)[1].strip()
    return hmac.compare_digest(expected, provided)


@public_router.get("/webhook")
async def whatsapp_webhook_verify(
    hub_mode: str | None = Query(None, alias="hub.mode"),
    hub_verify_token: str | None = Query(None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(None, alias="hub.challenge"),
):
    expected = settings.whatsapp_verify_token.strip()
    if (
        hub_mode == "subscribe"
        and expected
        and hub_verify_token == expected
        and hub_challenge is not None
    ):
        return Response(content=hub_challenge, media_type="text/plain")
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="WhatsApp webhook verification failed.",
    )


@public_router.post("/webhook")
async def whatsapp_webhook_receive(
    request: Request,
    db: Session = Depends(get_business_db),
    x_hub_signature_256: str | None = Header(None, alias="X-Hub-Signature-256"),
):
    raw = await request.body()
    if not _verify_signature(raw, x_hub_signature_256):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid WhatsApp signature.",
        )
    try:
        payload = json.loads(raw.decode("utf-8") or "{}")
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook JSON.",
        ) from None

    service = WhatsAppBotService(db)
    entries = payload.get("entry") or []
    for entry in entries:
        for change in entry.get("changes") or []:
            value = change.get("value") or {}
            contacts = {
                item.get("wa_id"): item.get("profile", {}).get("name", "")
                for item in (value.get("contacts") or [])
                if item.get("wa_id")
            }
            for message in value.get("messages") or []:
                phone = str(message.get("from") or "")
                if not phone:
                    continue
                msg_type = message.get("type")
                try:
                    if msg_type == "text":
                        text = str((message.get("text") or {}).get("body") or "").strip()
                        if not text:
                            continue
                        service.handle_inbound_whatsapp(
                            phone=phone,
                            text=text,
                            profile_name=contacts.get(phone, ""),
                        )
                    elif msg_type in {"audio", "voice"}:
                        audio = message.get("audio") or message.get("voice") or {}
                        media_id = str(audio.get("id") or "").strip()
                        if not media_id:
                            continue
                        service.handle_inbound_whatsapp_audio(
                            phone=phone,
                            media_id=media_id,
                            profile_name=contacts.get(phone, ""),
                            mime_type=str(audio.get("mime_type") or "audio/ogg"),
                        )
                except Exception:
                    logger.exception("WhatsApp inbound handling failed")
    return {"status": "ok"}


@public_router.post("/voice-transcribe", response_model=VoiceTranscribeResponse)
async def public_voice_transcribe(
    request: Request,
    file: UploadFile = File(...),
    mobile: str = Form(""),
    language_hint: str = Query(
        "Urdu or English (Pakistan)",
        max_length=80,
        description="Spoken language hint for Gemini STT",
    ),
) -> VoiceTranscribeResponse:
    """Transcribe guest-chat voice notes (mobile-friendly MediaRecorder upload)."""
    if not settings.whatsapp_bot_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chatbot is disabled.",
        )
    ip = _client_ip(request)
    ua = (request.headers.get("user-agent") or "")[:180]
    mobile_key = voice_control.normalize_mobile(mobile)
    allowed, reason = voice_control.check_allowed(
        channel="guest",
        mobile=mobile_key,
        ip=ip,
    )
    if not allowed:
        voice_control.record_event(
            channel="guest",
            mobile=mobile_key,
            ip=ip,
            status="blocked",
            block_reason=reason,
            user_agent=ua,
            detail="guest voice-transcribe blocked",
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=reason,
        )

    raw = await file.read()
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty audio file.",
        )
    if len(raw) < 800:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Voice note too short. Hold mic 1–2 seconds and speak.",
        )
    if len(raw) > 4_000_000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Voice note is too large. Keep it under 15 seconds.",
        )
    mime = (file.content_type or "audio/webm").split(";")[0].strip() or "audio/webm"
    stt = SpeechToTextService()
    if not stt.is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Voice STT not configured. Set GEMINI_API_KEY in .env.",
        )
    try:
        text, model, body = stt.transcribe_audio_with_meta(
            raw,
            mime_type=mime,
            language_hint=(language_hint or "").strip() or "Urdu or English (Pakistan)",
        )
    except SpeechToTextError as exc:
        voice_control.record_event(
            channel="guest",
            mobile=mobile_key,
            ip=ip,
            status="failed",
            detail=str(exc)[:240],
            user_agent=ua,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    voice_control.record_event(
        channel="guest",
        mobile=mobile_key,
        ip=ip,
        search_text=text,
        status="ok",
        model=model,
        body=body,
        user_agent=ua,
        detail="guest voice-transcribe",
    )
    return VoiceTranscribeResponse(
        text=text,
        message=f"Voice transcribed ({stt.provider_label()}).",
    )


@public_router.post("/offline-chat", response_model=OfflineChatResponse)
def public_offline_chat(
    body: OfflineChatRequest,
    db: Session = Depends(get_business_db),
) -> OfflineChatResponse:
    if not settings.whatsapp_bot_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chatbot is disabled.",
        )
    otp = MobileOtpService()
    if otp.is_required() and body.phone.strip() and not otp.is_verified(body.phone):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "mobile_not_verified",
                "message": (
                    "Please verify your mobile number with the OTP code "
                    "before using web chat."
                ),
            },
        )
    return WhatsAppBotService(db).offline_chat(body)


@public_router.post("/mobile-otp/send", response_model=MobileOtpResponse)
def public_send_mobile_otp(body: MobileOtpSendRequest) -> MobileOtpResponse:
    if not settings.whatsapp_bot_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chatbot is disabled.",
        )
    try:
        result = MobileOtpService().send_otp(body.phone)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    return MobileOtpResponse(**result)


@public_router.post("/mobile-otp/verify", response_model=MobileOtpResponse)
def public_verify_mobile_otp(body: MobileOtpVerifyRequest) -> MobileOtpResponse:
    if not settings.whatsapp_bot_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chatbot is disabled.",
        )
    try:
        result = MobileOtpService().verify_otp(body.phone, body.code)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return MobileOtpResponse(**result)


@router.get("/status", response_model=WhatsAppBotStatus)
def bot_status(
    _user: CurrentUser = Depends(require_permission("marketing.whatsapp_bot.view")),
    db: Session = Depends(get_business_db),
) -> WhatsAppBotStatus:
    return WhatsAppBotService(db).status()


@router.get("/config", response_model=WhatsAppBotConfig)
def get_config(
    _user: CurrentUser = Depends(require_permission("marketing.whatsapp_bot.manage")),
    db: Session = Depends(get_business_db),
) -> WhatsAppBotConfig:
    return WhatsAppBotService(db).get_config()


@router.put("/config", response_model=WhatsAppBotConfig)
def update_config(
    body: WhatsAppBotConfigUpdate,
    _user: CurrentUser = Depends(require_permission("marketing.whatsapp_bot.manage")),
    db: Session = Depends(get_business_db),
) -> WhatsAppBotConfig:
    return WhatsAppBotService(db).update_config(body)


@router.get("/conversations", response_model=list[ChatConversationSummary])
def list_conversations(
    _user: CurrentUser = Depends(require_permission("marketing.whatsapp_bot.view")),
    db: Session = Depends(get_business_db),
) -> list[ChatConversationSummary]:
    return WhatsAppBotService(db).list_conversations()


@router.get("/conversations/{conversation_id}", response_model=ChatConversation)
def get_conversation(
    conversation_id: str,
    _user: CurrentUser = Depends(require_permission("marketing.whatsapp_bot.view")),
    db: Session = Depends(get_business_db),
) -> ChatConversation:
    try:
        return WhatsAppBotService(db).get_conversation(conversation_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        ) from exc


@router.post(
    "/conversations/{conversation_id}/reply",
    response_model=ChatConversation,
)
def staff_reply(
    conversation_id: str,
    body: StaffReplyRequest,
    current_user: CurrentUser = Depends(
        require_permission("marketing.whatsapp_bot.manage")
    ),
    db: Session = Depends(get_business_db),
) -> ChatConversation:
    try:
        return WhatsAppBotService(db).staff_reply(
            conversation_id,
            body,
            actor_username=current_user.username,
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc


@router.put(
    "/conversations/{conversation_id}/status",
    response_model=ChatConversation,
)
def update_status(
    conversation_id: str,
    body: ConversationStatusUpdate,
    _user: CurrentUser = Depends(require_permission("marketing.whatsapp_bot.manage")),
    db: Session = Depends(get_business_db),
) -> ChatConversation:
    try:
        return WhatsAppBotService(db).set_status(conversation_id, body.status)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        ) from exc


@router.post("/offline-chat", response_model=OfflineChatResponse)
def admin_offline_chat(
    body: OfflineChatRequest,
    _user: CurrentUser = Depends(require_permission("marketing.whatsapp_bot.view")),
    db: Session = Depends(get_business_db),
) -> OfflineChatResponse:
    return WhatsAppBotService(db).offline_chat(body)


@router.delete("/conversations/{conversation_id}", response_model=MessageResponse)
def close_conversation(
    conversation_id: str,
    _user: CurrentUser = Depends(require_permission("marketing.whatsapp_bot.manage")),
    db: Session = Depends(get_business_db),
) -> MessageResponse:
    try:
        WhatsAppBotService(db).set_status(conversation_id, "closed")
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        ) from exc
    return MessageResponse(message="Conversation closed.")


@router.get("/orders", response_model=list[ChatOrderSummary])
def list_chat_orders(
    status_filter: str | None = Query(None, alias="status"),
    _user: CurrentUser = Depends(require_permission("marketing.whatsapp_bot.view")),
) -> list[ChatOrderSummary]:
    return WhatsAppOrderService().list_orders(status=status_filter)


@router.get("/orders/{order_id}", response_model=ChatOrder)
def get_chat_order(
    order_id: str,
    _user: CurrentUser = Depends(require_permission("marketing.whatsapp_bot.view")),
) -> ChatOrder:
    try:
        return WhatsAppOrderService().get_order(order_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found.",
        ) from exc


@router.put("/orders/{order_id}/status", response_model=ChatOrder)
def update_chat_order_status(
    order_id: str,
    body: ChatOrderStatusUpdate,
    _user: CurrentUser = Depends(require_permission("marketing.whatsapp_bot.manage")),
) -> ChatOrder:
    try:
        return WhatsAppOrderService().set_status(order_id, body.status)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found.",
        ) from exc
