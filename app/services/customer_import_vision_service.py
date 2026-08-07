"""Gemini Vision extraction for handwritten customer delivery sheets."""

import base64
import json
import re

import httpx
from fastapi import HTTPException, status
from pydantic import ValidationError

from app.config.settings import settings
from app.schemas.customer_import import (
    CustomerImportExtractResponse,
    CustomerImportExtractedRecord,
)


_PROMPT = """
Read this stock delivery report image carefully.

Extract every numbered data row from the table. The sheet may contain handwritten
English, Urdu, phone numbers, addresses, rider names, and tick marks.

For each row return:
- source_row: printed serial number
- name: customer name, transliterated into English when written in Urdu
- mobile: Pakistan mobile in +923XXXXXXXXX format
- original_address: address exactly as written in Urdu/English
- english_address: accurate English translation/transliteration of the address
- rider_name: rider name transliterated into English
- notes: describe unclear characters; never silently guess

Rules:
- Do not treat printed headings as records.
- Preserve blank fields as empty strings.
- If a digit or word is unclear, use ? in that value and explain it in notes.
- Do not invent missing values.
- Return rows in printed serial-number order.
"""

_RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "records": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "source_row": {"type": "INTEGER", "nullable": True},
                    "name": {"type": "STRING"},
                    "mobile": {"type": "STRING"},
                    "original_address": {"type": "STRING"},
                    "english_address": {"type": "STRING"},
                    "rider_name": {"type": "STRING"},
                    "notes": {"type": "STRING"},
                },
                "required": [
                    "source_row",
                    "name",
                    "mobile",
                    "original_address",
                    "english_address",
                    "rider_name",
                    "notes",
                ],
            },
        }
    },
    "required": ["records"],
}


class CustomerImportVisionService:
    def extract(
        self,
        *,
        image_bytes: bytes,
        mime_type: str,
    ) -> CustomerImportExtractResponse:
        if not settings.gemini_api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="GEMINI_API_KEY is not configured on the server.",
            )
        model = settings.gemini_model.strip()
        if not re.fullmatch(r"[A-Za-z0-9._-]+", model):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Configured Gemini model name is invalid.",
            )

        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": _PROMPT},
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": base64.b64encode(image_bytes).decode("ascii"),
                            }
                        },
                    ],
                }
            ],
            "generationConfig": {
                "temperature": 0,
                "responseMimeType": "application/json",
                "responseSchema": _RESPONSE_SCHEMA,
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
                    "x-goog-api-key": settings.gemini_api_key.get_secret_value(),
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=180.0,
            )
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Could not connect to Gemini Vision.",
            ) from exc

        if response.status_code >= 400:
            detail = "Gemini Vision rejected the request."
            try:
                api_message = response.json().get("error", {}).get("message", "")
                if api_message:
                    detail = str(api_message)[:500]
            except (ValueError, TypeError):
                pass
            raise HTTPException(status_code=response.status_code, detail=detail)

        try:
            body = response.json()
            text = body["candidates"][0]["content"]["parts"][0]["text"]
            parsed = json.loads(text)
            records = [
                CustomerImportExtractedRecord(**item)
                for item in parsed.get("records", [])
            ]
        except (KeyError, IndexError, TypeError, ValueError, ValidationError) as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Gemini returned an unreadable extraction response.",
            ) from exc

        warnings = [
            f"Row {record.source_row or '?'}: {record.notes}"
            for record in records
            if record.notes.strip()
        ]
        return CustomerImportExtractResponse(
            records=records,
            model=model,
            warnings=warnings,
        )
