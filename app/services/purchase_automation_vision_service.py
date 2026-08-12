"""Purchase invoice extraction: EasyOCR + PaddleOCR reading, then structured parse."""

from __future__ import annotations

import json
import re
from typing import List, Optional, Tuple

import httpx
from fastapi import HTTPException, status
from pydantic import ValidationError

from app.config.settings import settings
from app.schemas.purchase_automation import (
    PurchaseAutoExtractedInvoice,
    PurchaseAutoExtractedLine,
)
from app.services.purchase_ocr_service import PurchaseOcrService


_STRUCTURE_PROMPT = """
You are given OCR text from a supplier purchase invoice / challan / tax invoice.
The OCR may contain errors, broken columns, and mixed spacing.

Convert the OCR text into structured purchase data.

Return JSON fields:
- supplier_name
- supplier_tax_id (NTN/STRN/GST if present)
- invoice_no
- invoice_date (YYYY-MM-DD when possible)
- payment_terms
- remarks
- discount_amt, claim_amt, other_ded_amt, loading_amt, carriage_amt, other_charges_amt (0 if absent)
- lines: array of {{description, barcode, qty, rate, amount, stax_rate, stax_amt, disc_amt, disc_amt_oi, remarks, notes}}
- notes: overall warnings

Rules:
- Use ONLY values supported by the OCR text. Do not invent items.
- Prefer rows that look like product lines (description + qty + rate/amount).
- If rate missing but qty and amount exist: rate = amount/qty.
- Ignore headers, footers, bank details, QR noise.
- Keep line order.
"""

_RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "supplier_name": {"type": "STRING"},
        "supplier_tax_id": {"type": "STRING"},
        "invoice_no": {"type": "STRING"},
        "invoice_date": {"type": "STRING", "nullable": True},
        "payment_terms": {"type": "STRING"},
        "remarks": {"type": "STRING"},
        "discount_amt": {"type": "NUMBER"},
        "claim_amt": {"type": "NUMBER"},
        "other_ded_amt": {"type": "NUMBER"},
        "loading_amt": {"type": "NUMBER"},
        "carriage_amt": {"type": "NUMBER"},
        "other_charges_amt": {"type": "NUMBER"},
        "notes": {"type": "STRING"},
        "lines": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "description": {"type": "STRING"},
                    "barcode": {"type": "STRING"},
                    "qty": {"type": "NUMBER"},
                    "rate": {"type": "NUMBER"},
                    "amount": {"type": "NUMBER"},
                    "stax_rate": {"type": "NUMBER"},
                    "stax_amt": {"type": "NUMBER"},
                    "disc_amt": {"type": "NUMBER"},
                    "disc_amt_oi": {"type": "NUMBER"},
                    "remarks": {"type": "STRING"},
                    "notes": {"type": "STRING"},
                },
                "required": [
                    "description",
                    "barcode",
                    "qty",
                    "rate",
                    "amount",
                    "stax_rate",
                    "stax_amt",
                    "disc_amt",
                    "disc_amt_oi",
                    "remarks",
                    "notes",
                ],
            },
        },
    },
    "required": [
        "supplier_name",
        "supplier_tax_id",
        "invoice_no",
        "invoice_date",
        "payment_terms",
        "remarks",
        "discount_amt",
        "claim_amt",
        "other_ded_amt",
        "loading_amt",
        "carriage_amt",
        "other_charges_amt",
        "notes",
        "lines",
    ],
}


def _num(token: str) -> Optional[float]:
    t = token.strip().replace(",", "")
    if not re.fullmatch(r"-?\d+(?:\.\d+)?", t):
        return None
    try:
        return float(t)
    except ValueError:
        return None


def _local_parse(ocr_text: str) -> PurchaseAutoExtractedInvoice:
    """Heuristic fallback when Gemini is unavailable."""
    lines_raw = [ln.strip() for ln in ocr_text.splitlines() if ln.strip()]
    supplier_name = ""
    invoice_no = ""
    invoice_date = None
    tax_id = ""
    payment_terms = ""

    for ln in lines_raw[:25]:
        low = ln.lower()
        if not supplier_name and len(ln) > 4 and not re.search(r"\b(invoice|tax|gst|total|qty|rate)\b", low):
            if not re.fullmatch(r"[\d\s./-]+", ln):
                supplier_name = ln[:80]
        m = re.search(r"(?:invoice|inv|bill|challan|grn)\s*(?:no|#|number)?\s*[:.]?\s*([A-Za-z0-9 sp/-]{3,})", ln, re.I)
        if m and not invoice_no:
            invoice_no = m.group(1).strip()[:40]
        m = re.search(r"(?:date)\s*[:.]?\s*(\d{1,4}[./-]\d{1,2}[./-]\d{1,4})", ln, re.I)
        if m and not invoice_date:
            invoice_date = m.group(1)
        m = re.search(r"(?:ntn|strn|gst|stn)\s*[:.]?\s*([A-Za-z0-9-]+)", ln, re.I)
        if m and not tax_id:
            tax_id = m.group(1)
        if "credit" in low:
            payment_terms = "Credit"
        elif "cash" in low:
            payment_terms = "Cash"

    items: List[PurchaseAutoExtractedLine] = []
    # Row pattern: description ... qty rate amount  OR description amount with barcode
    barcode_re = re.compile(r"\b(\d{8,14})\b")
    for ln in lines_raw:
        low = ln.lower()
        if re.search(r"\b(total|subtotal|grand|amount in words|bank|ntn|strn|page)\b", low):
            continue
        nums = [_num(t) for t in re.findall(r"-?\d+(?:,\d{3})*(?:\.\d+)?", ln)]
        nums = [n for n in nums if n is not None]
        # strip barcode-like from numeric candidates used as qty/rate if 8+ digits int
        money_nums = []
        for n in nums:
            if n >= 10_000_000 and float(n).is_integer():
                continue
            money_nums.append(n)
        if len(money_nums) < 2:
            continue
        qty = money_nums[0]
        rate = money_nums[1] if len(money_nums) > 1 else 0.0
        amount = money_nums[-1]
        if qty <= 0 or amount <= 0:
            continue
        if rate <= 0 and qty:
            rate = round(amount / qty, 4)
        # description = text without trailing number cluster
        desc = re.sub(r"(\s+-?\d+(?:,\d{3})*(?:\.\d+)?)+\s*$", "", ln).strip()
        desc = barcode_re.sub("", desc).strip(" -|")
        if len(desc) < 3:
            continue
        bc = ""
        bm = barcode_re.search(ln)
        if bm:
            bc = bm.group(1)
        items.append(
            PurchaseAutoExtractedLine(
                description=desc[:120],
                barcode=bc,
                qty=float(qty),
                rate=float(rate),
                amount=float(amount),
                notes="local-ocr-parse",
            )
        )

    return PurchaseAutoExtractedInvoice(
        supplier_name=supplier_name,
        supplier_tax_id=tax_id,
        invoice_no=invoice_no,
        invoice_date=invoice_date,
        payment_terms=payment_terms,
        remarks="",
        lines=items[:80],
        notes="Structured from OCR via local parser (Gemini unavailable or failed).",
    )


def _structure_with_gemini(ocr_text: str) -> Tuple[Optional[PurchaseAutoExtractedInvoice], str, List[str]]:
    if not settings.gemini_api_key:
        return None, "", ["GEMINI_API_KEY not set — used local OCR parser."]
    model = settings.gemini_model.strip()
    if not re.fullmatch(r"[A-Za-z0-9._-]+", model):
        return None, model, ["Invalid Gemini model — used local OCR parser."]

    clipped = ocr_text[:50000]
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": _STRUCTURE_PROMPT},
                    {"text": "OCR TEXT:\n" + clipped},
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
    except httpx.RequestError:
        return None, model, ["Could not reach Gemini for structuring — used local OCR parser."]

    if response.status_code >= 400:
        return None, model, [f"Gemini structure failed ({response.status_code}) — used local OCR parser."]

    try:
        body = response.json()
        text = body["candidates"][0]["content"]["parts"][0]["text"]
        parsed = json.loads(text)
        invoice = PurchaseAutoExtractedInvoice(
            supplier_name=str(parsed.get("supplier_name") or "").strip(),
            supplier_tax_id=str(parsed.get("supplier_tax_id") or "").strip(),
            invoice_no=str(parsed.get("invoice_no") or "").strip(),
            invoice_date=str(parsed.get("invoice_date") or "").strip() or None,
            payment_terms=str(parsed.get("payment_terms") or "").strip(),
            remarks=str(parsed.get("remarks") or "").strip(),
            discount_amt=float(parsed.get("discount_amt") or 0),
            claim_amt=float(parsed.get("claim_amt") or 0),
            other_ded_amt=float(parsed.get("other_ded_amt") or 0),
            loading_amt=float(parsed.get("loading_amt") or 0),
            carriage_amt=float(parsed.get("carriage_amt") or 0),
            other_charges_amt=float(parsed.get("other_charges_amt") or 0),
            notes=str(parsed.get("notes") or "").strip(),
            lines=[PurchaseAutoExtractedLine(**item) for item in parsed.get("lines", [])],
        )
        return invoice, model, []
    except (KeyError, IndexError, TypeError, ValueError, ValidationError):
        return None, model, ["Gemini returned unreadable structure — used local OCR parser."]


class PurchaseAutomationVisionService:
    """
    Read invoice with EasyOCR + PaddleOCR, then structure fields.
    Gemini (if configured) is used only on OCR text — not as image vision.
    """

    def __init__(self) -> None:
        self.ocr = PurchaseOcrService()

    def extract(
        self, *, file_bytes: bytes, mime_type: str
    ) -> Tuple[PurchaseAutoExtractedInvoice, str, List[str], str, List[str]]:
        """
        Returns: invoice, model_label, warnings, ocr_text, engines_used
        """
        ocr = self.ocr.read(file_bytes=file_bytes, mime_type=mime_type)
        warnings = list(ocr.warnings)
        engines = list(ocr.engines_used)
        engine_label = "+".join(engines) if engines else "ocr"

        invoice, gemini_model, struct_warnings = _structure_with_gemini(ocr.text)
        warnings.extend(struct_warnings)
        if invoice is None:
            invoice = _local_parse(ocr.text)
            model = f"{engine_label}/local-parser"
        else:
            model = f"{engine_label}/gemini:{gemini_model}" if gemini_model else f"{engine_label}/gemini"

        if invoice.notes:
            warnings.append(invoice.notes)
        for i, line in enumerate(invoice.lines, start=1):
            if line.notes.strip() and line.notes != "local-ocr-parse":
                warnings.append(f"Line {i}: {line.notes.strip()}")
        if not invoice.lines:
            warnings.append("No product lines detected — check OCR text and edit manually.")

        warnings.insert(0, f"OCR engines: {', '.join(engines) or 'none'} · pages: {ocr.page_count}")
        return invoice, model, warnings, ocr.text, engines
