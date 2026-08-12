"""Built-in + operator fetch instructions for invoice data extraction."""

from __future__ import annotations

import json
import re
from typing import List, Optional, Tuple

import httpx

from app.config.settings import settings
from app.services.purchase_pipeline.types import PipelineContext, StructuredProduct


# Always applied (merged with operator textbox). Manual ID is handwritten & first match key.
DEFAULT_FETCH_INSTRUCTIONS = """
PRIORITY RULES (always follow):
1. Handwritten Manual ID is the PRIMARY item key — match FIN_ITEM.manualid first.
2. Manual IDs are usually handwritten on the right side of each product row.
3. Grid must contain ONLY product item rows — never headers, footers, totals, tax summary, bank details, or address lines.
4. For every item: first find Quantity and Trade/Unit Rate, then Amount = Qty × Rate.
5. After amount: apply Discount, then Tax / Sales Tax, then Net = Amount − Discount + Tax.
6. Never trust printed invoice totals — recalculate every line independently.
7. Prefer barcode only if handwritten manual ID is missing.
8. Ignore noise words: TOTAL, SUB TOTAL, GRAND TOTAL, GST, NTN, STRN, Carriage, Loading, Balance, Particulars, Qty, Rate, Amount (as headers).
""".strip()


def merge_instructions(user_text: str = "") -> str:
    user = (user_text or "").strip()
    if not user:
        return DEFAULT_FETCH_INSTRUCTIONS
    if "PRIORITY RULES" in user.upper() or "handwritten manual id" in user.lower():
        return user
    return f"{DEFAULT_FETCH_INSTRUCTIONS}\n\nOPERATOR NOTES:\n{user}"


def apply_fetch_instructions(ctx: PipelineContext) -> PipelineContext:
    """
    Always follow built-in priority rules + any operator instructions.
    Filters to item rows only; enforces qty×rate-first math; prefers HW manual IDs.
    """
    raw = str(ctx.meta.get("fetch_instructions") or "").strip()
    instructions = merge_instructions(raw)
    ctx.meta["fetch_instructions"] = instructions
    ctx.meta["fetch_instructions_applied"] = True
    ctx.meta["prefer_handwritten_right"] = True
    ctx.meta["match_manual_id_first"] = True
    ctx.meta["items_only"] = True

    _apply_local_directives(ctx, instructions)
    _enrich_handwritten_manual_ids(ctx)
    _normalize_item_math(ctx)
    ctx.products = [p for p in ctx.products if _is_item_row(p)]

    gemini_products, supplier_fields, model, notes = _structure_with_instructions(
        ctx.ocr_text, instructions
    )
    if notes:
        ctx.warnings.extend(notes)
    if supplier_fields:
        if supplier_fields.get("supplier_name"):
            ctx.supplier.name = supplier_fields["supplier_name"]
            ctx.supplier.confidence = max(ctx.supplier.confidence, 0.85)
        if supplier_fields.get("supplier_tax_id"):
            ctx.supplier.tax_id = supplier_fields["supplier_tax_id"]
        if supplier_fields.get("invoice_no"):
            ctx.supplier.invoice_no = supplier_fields["invoice_no"]
        if supplier_fields.get("invoice_date"):
            ctx.supplier.invoice_date = supplier_fields["invoice_date"]
    if gemini_products:
        # Keep Gemini item rows only, then re-normalize math
        ctx.products = [p for p in gemini_products if _is_item_row(p)]
        _normalize_item_math(ctx)
        ctx.meta["instruction_structure_model"] = model
        ctx.warnings.append("Item rows structured using fetch instructions (manual ID first).")
    else:
        ctx.warnings.append(
            "Fetch instructions applied: handwritten Manual ID first · qty×rate then tax/discount · items-only grid."
        )

    if not ctx.products:
        ctx.warnings.append("No item rows left after filtering — check OCR / instructions.")
    return ctx


def _is_item_row(p: StructuredProduct) -> bool:
    desc = (p.printed_description or "").strip()
    blob = f"{desc} {p.printed_product_code} {p.barcode} {p.handwritten_manual_id}".strip()
    has_qty_rate = bool((p.quantity and p.quantity > 0) or (p.trade_price and p.trade_price > 0))
    if not blob and not has_qty_rate:
        return False
    noise = re.compile(
        r"(?i)^(total|sub\s*total|grand\s*total|net\s*total|amount\s*payable|"
        r"discount|sales\s*tax|gst|vat|ntn|strn|carriage|loading|balance|"
        r"particulars|description|item\s*name|qty|quantity|rate|price|amount|"
        r"s\.?\s*no|sr\.?|code|barcode|invoice|tax\s*invoice|page\s*\d+)\b"
    )
    if desc and (noise.search(desc) or noise.fullmatch(desc)):
        return False
    # Must look like a product: has qty/rate/manual/barcode/meaningful description
    has_key = bool(
        (p.handwritten_manual_id or "").strip()
        or (p.barcode or "").strip()
        or (p.printed_product_code or "").strip()
        or has_qty_rate
        or len(desc) >= 4
    )
    if not has_key:
        return False
    # Pure money footer lines
    if desc and re.fullmatch(r"[\d.,\s]+", desc):
        return False
    return True


def _normalize_item_math(ctx: PipelineContext) -> None:
    """Qty + Rate first → Amount; then discount/tax → net. Never trust printed totals."""
    default_tax = float(ctx.meta.get("default_tax_rate") or 0)
    for p in ctx.products:
        qty = float(p.quantity or 0)
        rate = float(p.trade_price or 0)
        amount = round(qty * rate, 2) if qty and rate else 0.0
        # If rate missing but amount-like net present with qty → derive rate
        if rate <= 0 and qty > 0 and p.net_amount:
            inferred = round(float(p.net_amount) / qty, 4)
            if inferred > 0:
                p.trade_price = inferred
                rate = inferred
                amount = round(qty * rate, 2)
        # If qty missing but amount & rate exist
        if qty <= 0 and rate > 0 and p.net_amount:
            inferred_q = round(float(p.net_amount) / rate, 4)
            if inferred_q > 0:
                p.quantity = inferred_q
                qty = inferred_q
                amount = round(qty * rate, 2)

        if default_tax and not p.tax_rate:
            p.tax_rate = default_tax

        disc = round(float(p.discount or 0), 2)
        taxable = max(0.0, amount - disc)
        if p.tax_rate:
            p.tax = round(taxable * (float(p.tax_rate) / 100.0), 2)
        tax = round(float(p.tax or 0), 2)
        p.net_amount = round(taxable + tax, 2)
        p.field_scores["quantity"] = max(float(p.field_scores.get("quantity", 0.5)), 0.7 if qty else 0.3)
        p.field_scores["trade_price"] = max(float(p.field_scores.get("trade_price", 0.5)), 0.7 if rate else 0.3)
        p.field_scores["recalc_gross"] = amount


def _enrich_handwritten_manual_ids(ctx: PipelineContext) -> None:
    """Attach right-side / low-conf numeric HW spans as manual IDs (first priority key)."""
    assoc = {
        a["row_id"]: a
        for a in ctx.meta.get("handwriting_associations", [])
        if a.get("row_id") is not None
    }
    for p in ctx.products:
        if (p.handwritten_manual_id or "").strip():
            continue
        if p.row_id in assoc:
            txt = str(assoc[p.row_id].get("text") or "").strip()
            if re.fullmatch(r"\d{1,10}", txt):
                p.handwritten_manual_id = txt
                p.field_scores["handwritten_manual_id"] = float(assoc[p.row_id].get("score") or 0.6)
                continue
        # Prefer rightmost handwritten digit span on same page near row
        best = None
        best_x = -1.0
        for h in ctx.handwritten_spans:
            if h.page != p.page:
                continue
            t = (h.text or "").strip()
            if not re.fullmatch(r"\d{1,10}", t):
                continue
            # vertically near product row
            if p.bbox and abs(h.cy - (p.bbox[1] + p.bbox[3]) / 2.0) > 28:
                continue
            if h.bbox[0] >= best_x:
                best_x = h.bbox[0]
                best = t
        if best:
            p.handwritten_manual_id = best
            p.field_scores["handwritten_manual_id"] = 0.65


def _apply_local_directives(ctx: PipelineContext, instructions: str) -> None:
    text = instructions
    lower = text.lower()

    m = re.search(r"(?im)^\s*supplier\s*[:=]\s*(.+)$", text)
    if m:
        name = m.group(1).strip()
        if name:
            ctx.supplier.name = name
            ctx.supplier.confidence = max(ctx.supplier.confidence, 0.8)

    m = re.search(r"(?im)^\s*invoice(?:\s*no|\s*#)?\s*[:=]\s*(\S+)$", text)
    if m:
        ctx.supplier.invoice_no = m.group(1).strip()

    m = re.search(r"(?im)^\s*(?:ntn|strn|tax(?:\s*id)?)\s*[:=]\s*(\S+)$", text)
    if m:
        ctx.supplier.tax_id = m.group(1).strip()

    m = re.search(r"(?im)^\s*supplier[_ ]?name[_ ]?line\s*[:=]\s*(\d+)\s*$", text)
    if m:
        idx = int(m.group(1))
        lines = [ln.strip() for ln in (ctx.ocr_text or "").splitlines() if ln.strip()]
        if idx >= 1:
            idx -= 1
        if 0 <= idx < len(lines):
            ctx.supplier.name = lines[idx]
            ctx.supplier.confidence = max(ctx.supplier.confidence, 0.85)

    ignores = re.findall(r"(?im)^\s*ignore(?:\s*lines?)?(?:\s*matching)?\s*[:=]\s*(.+)$", text)
    patterns = [p.strip() for p in ignores if p.strip()]
    if "skip header" in lower or "ignore header" in lower or "items only" in lower or "only item" in lower:
        patterns.append(
            r"(?i)^(qty|quantity|description|item|rate|amount|code|total|sub\s*total|grand)"
        )
    if patterns and ctx.products:
        kept = []
        for p in ctx.products:
            blob = f"{p.printed_description} {p.printed_product_code} {p.barcode}"
            if any(re.search(pat, blob, re.I) for pat in patterns):
                continue
            kept.append(p)
        ctx.products = kept

    if "handwritten" in lower or "manual id" in lower:
        ctx.meta["prefer_handwritten_right"] = True
        ctx.meta["match_manual_id_first"] = True

    m = re.search(
        r"(?im)^\s*(?:default\s*)?(?:tax|stax|gst)\s*(?:rate)?\s*[:=]\s*([\d.]+)\s*%?\s*$",
        text,
    )
    if m:
        try:
            rate = float(m.group(1))
            ctx.meta["default_tax_rate"] = rate
            for p in ctx.products:
                if not p.tax_rate:
                    p.tax_rate = rate
        except ValueError:
            pass


def _structure_with_instructions(
    ocr_text: str, instructions: str
) -> Tuple[Optional[List[StructuredProduct]], dict, str, List[str]]:
    if not settings.gemini_api_key:
        return None, {}, "", []
    if not (ocr_text or "").strip():
        return None, {}, "", ["No OCR text available for instruction-based structuring."]

    model = (settings.gemini_model or "gemini-3.1-flash-lite").strip()
    if not re.fullmatch(r"[A-Za-z0-9._-]+", model):
        return None, {}, model, ["Invalid Gemini model — instruction structuring skipped."]

    prompt = f"""
You extract ONLY product item rows from supplier purchase invoice OCR text.
Follow the operator instructions exactly.

OPERATOR / SYSTEM INSTRUCTIONS:
{instructions}

Critical:
- handwritten_manual_id is usually handwritten and is the FIRST priority item key.
- Return ONLY item lines (no headers, totals, tax summaries, bank/address blocks).
- For each item: find quantity and trade_price (unit rate) FIRST.
- amount logic: Amount = Qty × Rate; then discount; then tax; net = amount - discount + tax.
- Do not invent items. Use only OCR-supported values.

Return JSON with:
- supplier_name, supplier_tax_id, invoice_no, invoice_date (YYYY-MM-DD if possible)
- lines: array of objects with:
  printed_product_code, printed_description, handwritten_manual_id,
  barcode, quantity, trade_price, discount, tax, tax_rate, net_amount
"""
    schema = {
        "type": "OBJECT",
        "properties": {
            "supplier_name": {"type": "STRING"},
            "supplier_tax_id": {"type": "STRING"},
            "invoice_no": {"type": "STRING"},
            "invoice_date": {"type": "STRING", "nullable": True},
            "lines": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "printed_product_code": {"type": "STRING"},
                        "printed_description": {"type": "STRING"},
                        "handwritten_manual_id": {"type": "STRING"},
                        "barcode": {"type": "STRING"},
                        "quantity": {"type": "NUMBER"},
                        "trade_price": {"type": "NUMBER"},
                        "discount": {"type": "NUMBER"},
                        "tax": {"type": "NUMBER"},
                        "tax_rate": {"type": "NUMBER"},
                        "net_amount": {"type": "NUMBER"},
                    },
                    "required": [
                        "printed_product_code",
                        "printed_description",
                        "handwritten_manual_id",
                        "barcode",
                        "quantity",
                        "trade_price",
                        "discount",
                        "tax",
                        "tax_rate",
                        "net_amount",
                    ],
                },
            },
        },
        "required": ["supplier_name", "supplier_tax_id", "invoice_no", "invoice_date", "lines"],
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
            json={
                "contents": [
                    {
                        "role": "user",
                        "parts": [
                            {"text": prompt},
                            {"text": "OCR TEXT:\n" + (ocr_text or "")[:50000]},
                        ],
                    }
                ],
                "generationConfig": {
                    "temperature": 0,
                    "responseMimeType": "application/json",
                    "responseSchema": schema,
                },
            },
            timeout=180.0,
        )
    except httpx.RequestError:
        return None, {}, model, ["Could not reach Gemini for instruction structuring."]

    if response.status_code >= 400:
        return None, {}, model, [f"Instruction structuring failed ({response.status_code})."]

    try:
        body = response.json()
        parsed = json.loads(body["candidates"][0]["content"]["parts"][0]["text"])
        products: List[StructuredProduct] = []
        for i, row in enumerate(parsed.get("lines") or []):
            qty = float(row.get("quantity") or 0)
            rate = float(row.get("trade_price") or 0)
            disc = float(row.get("discount") or 0)
            tax = float(row.get("tax") or 0)
            tax_rate = float(row.get("tax_rate") or 0)
            amount = round(qty * rate, 2) if qty and rate else 0.0
            if tax_rate and amount:
                tax = round((amount - disc) * (tax_rate / 100.0), 2)
            net = round(amount - disc + tax, 2) if amount else float(row.get("net_amount") or 0)
            products.append(
                StructuredProduct(
                    printed_product_code=str(row.get("printed_product_code") or "").strip(),
                    printed_description=str(row.get("printed_description") or "").strip(),
                    handwritten_manual_id=str(row.get("handwritten_manual_id") or "").strip(),
                    barcode=str(row.get("barcode") or "").strip(),
                    quantity=qty,
                    trade_price=rate,
                    discount=disc,
                    tax=tax,
                    tax_rate=tax_rate,
                    net_amount=net,
                    row_id=i + 1,
                    field_scores={
                        "printed_description": 0.75,
                        "quantity": 0.75 if qty else 0.4,
                        "trade_price": 0.75 if rate else 0.4,
                        "handwritten_manual_id": 0.85
                        if str(row.get("handwritten_manual_id") or "").strip()
                        else 0.3,
                    },
                )
            )
        supplier_fields = {
            "supplier_name": str(parsed.get("supplier_name") or "").strip(),
            "supplier_tax_id": str(parsed.get("supplier_tax_id") or "").strip(),
            "invoice_no": str(parsed.get("invoice_no") or "").strip(),
            "invoice_date": str(parsed.get("invoice_date") or "").strip(),
        }
        return products, supplier_fields, model, []
    except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError):
        return None, {}, model, ["Instruction structuring returned unreadable JSON."]
