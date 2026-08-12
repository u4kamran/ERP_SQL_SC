"""Speech-to-text for chatbot voice messages (Gemini multimodal)."""

from __future__ import annotations

import base64
import re

import httpx

from app.config.settings import settings


class SpeechToTextError(Exception):
    pass


class SpeechToTextService:
    def is_configured(self) -> bool:
        return bool(settings.gemini_api_key)

    def provider_label(self) -> str:
        if settings.gemini_api_key:
            return f"gemini:{settings.gemini_model or 'gemini-3.1-flash-lite'}"
        return "none"

    def _model_candidates(self) -> list[str]:
        primary = (settings.gemini_model or "").strip()
        fallbacks = [
            "gemini-3.1-flash-lite",
            "gemini-flash-lite-latest",
            "gemini-3-flash-preview",
            "gemini-flash-latest",
            "gemini-2.5-flash-lite",
            "gemini-2.5-flash",
        ]
        models: list[str] = []
        for name in [primary, *fallbacks]:
            if name and re.fullmatch(r"[A-Za-z0-9._-]+", name) and name not in models:
                models.append(name)
        return models

    def _should_try_next_model(self, status_code: int, detail: str) -> bool:
        low = (detail or "").lower()
        if status_code in (404, 400, 404):
            markers = (
                "not found",
                "not supported",
                "no longer available",
                "is not found",
                "unknown model",
                "invalid model",
            )
            return any(marker in low for marker in markers)
        return False

    def transcribe_audio(
        self,
        audio_bytes: bytes,
        *,
        mime_type: str = "audio/ogg",
        language_hint: str = "Urdu or English (Pakistan)",
    ) -> str:
        if not audio_bytes:
            raise SpeechToTextError("Empty audio.")
        if not settings.gemini_api_key:
            raise SpeechToTextError("Voice search needs GEMINI_API_KEY on the server.")

        models = self._model_candidates()
        if not models:
            raise SpeechToTextError("Configured Gemini model name is invalid.")

        prompt = (
            "Transcribe this customer voice note for a shop price chatbot. "
            f"Language may be {language_hint}. "
            "Return only the spoken words as plain text. "
            "If unclear, return the best guess of product name words only. "
            "Do not add commentary."
        )
        # Normalize browser recorder mime (strip codecs=...).
        clean_mime = (mime_type or "audio/webm").split(";")[0].strip() or "audio/webm"
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": clean_mime,
                                "data": base64.b64encode(audio_bytes).decode("ascii"),
                            }
                        },
                    ],
                }
            ],
            "generationConfig": {"temperature": 0},
        }

        last_detail = "Speech service rejected the audio."
        for model in models:
            url = (
                "https://generativelanguage.googleapis.com/v1beta/models/"
                f"{model}:generateContent"
            )
            try:
                response = httpx.post(
                    url,
                    headers={
                        "x-goog-api-key": settings.gemini_api_key.get_secret_value(),
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
                    api_message = response.json().get("error", {}).get("message", "")
                    if api_message:
                        detail = str(api_message)[:300]
                except (ValueError, TypeError):
                    pass
                last_detail = detail
                low = detail.lower()
                if "quota" in low or "rate limit" in low or response.status_code == 429:
                    raise SpeechToTextError(
                        "Gemini voice quota exceeded. Try again later or type the item."
                    )
                if self._should_try_next_model(response.status_code, detail):
                    continue
                raise SpeechToTextError(detail)

            try:
                body = response.json()
                text = body["candidates"][0]["content"]["parts"][0]["text"]
            except (KeyError, IndexError, TypeError, ValueError) as exc:
                # Blocked / empty candidates — try next model once.
                last_detail = "Could not read transcription."
                if model != models[-1]:
                    continue
                raise SpeechToTextError(last_detail) from exc

            text = (text or "").strip().strip('"').strip("'")
            if not text:
                raise SpeechToTextError("No speech detected.")
            return text[:500]

        raise SpeechToTextError(last_detail)
