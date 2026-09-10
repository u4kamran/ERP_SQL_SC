"""Speech-to-text for chatbot voice messages (Gemini multimodal)."""

from __future__ import annotations

import base64
import logging
import re

import httpx

from app.config.settings import settings

logger = logging.getLogger("ahsteellab")


class SpeechToTextError(Exception):
    pass


class SpeechToTextService:
    def is_configured(self) -> bool:
        key = settings.gemini_api_key
        if not key:
            return False
        try:
            return bool(key.get_secret_value().strip())
        except Exception:
            return False

    def provider_label(self) -> str:
        if self.is_configured():
            return "gemini:gemini-3.1-flash-lite"
        return "none"

    def _api_key(self) -> str:
        if not settings.gemini_api_key:
            return ""
        return settings.gemini_api_key.get_secret_value().strip()

    def _model_candidates(self) -> list[str]:
        """Cheapest voice model only — no fallbacks to costlier Gemini models."""
        # ~$0.25/M text, ~$0.50/M audio. Change later when user asks.
        return ["gemini-3.1-flash-lite"]

    def _normalize_mime(self, mime_type: str) -> str:
        clean = (mime_type or "audio/webm").split(";")[0].strip().lower() or "audio/webm"
        aliases = {
            "audio/x-wav": "audio/wav",
            "audio/wave": "audio/wav",
            "audio/x-m4a": "audio/mp4",
            "audio/m4a": "audio/mp4",
            "audio/aac": "audio/aac",
            "video/webm": "audio/webm",
            "application/ogg": "audio/ogg",
        }
        return aliases.get(clean, clean)

    def _mime_candidates(self, mime_type: str) -> list[str]:
        primary = self._normalize_mime(mime_type)
        extras = {
            "audio/webm": ["audio/ogg", "audio/wav"],
            "audio/ogg": ["audio/webm"],
            "audio/mp4": ["audio/m4a", "audio/mpeg"],
        }
        out = [primary]
        for item in extras.get(primary, []):
            if item not in out:
                out.append(item)
        return out

    def _should_try_next_model(self, status_code: int, detail: str) -> bool:
        low = (detail or "").lower()
        markers = (
            "not found",
            "not supported",
            "no longer available",
            "is not found",
            "unknown model",
            "invalid model",
            "does not support",
            "unsupported",
            "not available",
        )
        if status_code in {404, 400, 503}:
            return any(marker in low for marker in markers)
        return False

    def _should_retry_mime(self, status_code: int, detail: str) -> bool:
        low = (detail or "").lower()
        markers = (
            "unable to process input audio",
            "invalid argument",
            "unsupported mime",
            "mime type",
            "audio format",
            "could not process",
            "invalid audio",
        )
        return status_code in {400, 415} and any(m in low for m in markers)

    def _extract_text(self, body: dict) -> str:
        # Prefer normal candidates.
        for candidate in body.get("candidates") or []:
            finish = str(candidate.get("finishReason") or "")
            content = candidate.get("content") or {}
            parts = content.get("parts") or []
            chunks: list[str] = []
            for part in parts:
                if isinstance(part, dict) and part.get("text"):
                    chunks.append(str(part["text"]))
            text = " ".join(chunks).strip()
            if text:
                return text
            if finish and finish.upper() not in {"STOP", "END_TURN", ""}:
                # Keep looking; may be blocked.
                continue

        # Prompt feedback / block reasons.
        feedback = body.get("promptFeedback") or {}
        block = feedback.get("blockReason") or feedback.get("block_reason")
        if block:
            raise SpeechToTextError(
                f"Voice blocked by safety filter ({block}). Speak product name clearly."
            )
        return ""

    def _clean_transcript(self, text: str) -> str:
        value = (text or "").strip().strip('"').strip("'")
        value = re.sub(
            r"^(?i)(transcript|transcription|here is the transcript|the user said)\s*[:\-]\s*",
            "",
            value,
        ).strip()
        # Collapse whitespace / newlines from model chatter.
        value = re.sub(r"\s+", " ", value)
        # Drop obvious non-speech refusals.
        low = value.lower()
        if low in {"", "n/a", "none", "null", "inaudible", "(silence)", "silence"}:
            return ""
        if "cannot" in low and "transcrib" in low:
            return ""
        return value[:500]

    def transcribe_audio(
        self,
        audio_bytes: bytes,
        *,
        mime_type: str = "audio/ogg",
        language_hint: str = "Urdu or English (Pakistan)",
    ) -> str:
        text, _model, _body = self.transcribe_audio_with_meta(
            audio_bytes,
            mime_type=mime_type,
            language_hint=language_hint,
        )
        return text

    def transcribe_audio_with_meta(
        self,
        audio_bytes: bytes,
        *,
        mime_type: str = "audio/ogg",
        language_hint: str = "Urdu or English (Pakistan)",
    ) -> tuple[str, str, dict]:
        """Return (transcript, model, raw_api_body)."""
        if not audio_bytes:
            raise SpeechToTextError("Empty audio.")
        if len(audio_bytes) < 800:
            raise SpeechToTextError("Voice note too short. Hold mic 1–2 seconds and speak.")
        if not self.is_configured():
            raise SpeechToTextError("Voice search is not configured on the server.")

        models = self._model_candidates()
        if not models:
            raise SpeechToTextError("Voice model is not configured.")

        lang = (language_hint or "Urdu or English (Pakistan)").strip()[:80]
        prompt = (
            "You are a speech-to-text engine for a Pakistan departmental store chatbot.\n"
            f"Language may be {lang}, including Roman Urdu.\n"
            "Task: transcribe ONLY the spoken product/brand/search words.\n"
            "Rules:\n"
            "- Return plain text only (no quotes, no labels, no explanation).\n"
            "- Prefer product names, brands, sizes (e.g. Dalda 5kg, Surf Excel).\n"
            "- If unclear, return the best short product-name guess.\n"
            "- If there is no speech, return exactly: NO_SPEECH"
        )

        api_key = self._api_key()
        last_detail = "Speech service rejected the audio."
        mime_list = self._mime_candidates(mime_type)

        for model in models:
            for mime in mime_list:
                payload = {
                    "contents": [
                        {
                            "role": "user",
                            "parts": [
                                {"text": prompt},
                                {
                                    "inline_data": {
                                        "mime_type": mime,
                                        "data": base64.b64encode(audio_bytes).decode(
                                            "ascii"
                                        ),
                                    }
                                },
                            ],
                        }
                    ],
                    "generationConfig": {
                        "temperature": 0,
                        "maxOutputTokens": 64,
                    },
                }
                url = (
                    "https://generativelanguage.googleapis.com/v1beta/models/"
                    f"{model}:generateContent"
                )
                try:
                    response = httpx.post(
                        url,
                        headers={
                            "x-goog-api-key": api_key,
                            "Content-Type": "application/json",
                        },
                        json=payload,
                        timeout=90.0,
                    )
                except httpx.RequestError as exc:
                    raise SpeechToTextError(
                        f"Could not reach speech service: {exc}"
                    ) from exc

                if response.status_code >= 400:
                    detail = "Speech service rejected the audio."
                    try:
                        api_message = (
                            response.json().get("error", {}).get("message", "")
                        )
                        if api_message:
                            detail = str(api_message)[:300]
                    except (ValueError, TypeError):
                        pass
                    last_detail = detail
                    low = detail.lower()
                    logger.warning(
                        "Gemini STT failed model=%s mime=%s status=%s detail=%s",
                        model,
                        mime,
                        response.status_code,
                        detail[:180],
                    )
                    if (
                        response.status_code == 429
                        or "quota" in low
                        or "rate limit" in low
                        or "prepayment" in low
                        or "credits are depleted" in low
                        or "billing" in low
                    ):
                        raise SpeechToTextError(
                            "Cloud voice credits are empty. "
                            "Please try again later, or type the item name."
                        )
                    if "api key" in low or "permission" in low or response.status_code in {
                        401,
                        403,
                    }:
                        raise SpeechToTextError(
                            "Cloud voice is not available right now. Please type the item name."
                        )
                    if self._should_retry_mime(response.status_code, detail):
                        continue
                    if self._should_try_next_model(response.status_code, detail):
                        break  # next model
                    # Unknown 400/404 — try next model anyway once.
                    if response.status_code in {400, 404}:
                        break
                    raise SpeechToTextError(detail)

                try:
                    body = response.json()
                    text = self._extract_text(body)
                except SpeechToTextError:
                    raise
                except (KeyError, IndexError, TypeError, ValueError):
                    last_detail = "Could not read transcription."
                    continue

                text = self._clean_transcript(text)
                if text.upper() == "NO_SPEECH" or not text:
                    last_detail = "No speech detected. Speak closer to the mic."
                    # Don't burn more models on silence — fail fast after first clear empty.
                    raise SpeechToTextError(last_detail)

                try:
                    from app.services import gemini_usage_store as usage_store

                    usage_store.record_usage(
                        feature="voice",
                        model=model,
                        body=body,
                        ok=True,
                    )
                except Exception:
                    logger.exception("Gemini usage meter failed (voice)")

                logger.info(
                    "Gemini STT ok model=%s mime=%s chars=%s",
                    model,
                    mime,
                    len(text),
                )
                return text, model, body if isinstance(body, dict) else {}

        raise SpeechToTextError(last_detail)
