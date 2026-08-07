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

        model = settings.gemini_model.strip()
        if not re.fullmatch(r"[A-Za-z0-9._-]+", model):
            raise SpeechToTextError("Configured Gemini model name is invalid.")

        prompt = (
            "Transcribe this customer voice note for a shop price chatbot. "
            f"Language may be {language_hint}. "
            "Return only the spoken words as plain text. "
            "If unclear, return the best guess of product name words only. "
            "Do not add commentary."
        )
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": mime_type or "audio/ogg",
                                "data": base64.b64encode(audio_bytes).decode("ascii"),
                            }
                        },
                    ],
                }
            ],
            "generationConfig": {"temperature": 0},
        }
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
            raise SpeechToTextError(f"Could not reach speech service: {exc}") from exc

        if response.status_code >= 400:
            detail = "Speech service rejected the audio."
            try:
                api_message = response.json().get("error", {}).get("message", "")
                if api_message:
                    detail = str(api_message)[:300]
            except (ValueError, TypeError):
                pass
            raise SpeechToTextError(detail)

        try:
            body = response.json()
            text = body["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise SpeechToTextError("Could not read transcription.") from exc

        text = (text or "").strip().strip('"').strip("'")
        if not text:
            raise SpeechToTextError("No speech detected.")
        return text[:500]
