"""Stage 8 — Extract structured JSON products from rows + associations."""

from __future__ import annotations

import re
from typing import List, Tuple

from app.services.purchase_pipeline.base import BaseStage
from app.services.purchase_pipeline.types import (
    PipelineContext,
    StructuredProduct,
    TextKind,
    TextSpan,
)


_NUM = re.compile(r"[-+]?\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?")
_BARCODE = re.compile(r"\b(\d{8,14})\b")
_CODE = re.compile(r"\b([A-Z]{0,4}\d{3,12}[A-Z0-9\-]*)\b", re.I)


class StructureProductsStage(BaseStage):
    stage_id = 8
    name = "structure_products"

    def run(self, ctx: PipelineContext) -> PipelineContext:
        products: List[StructuredProduct] = []

        if ctx.tables:
            for table in ctx.tables:
                for row in table.rows:
                    products.append(self._from_row(row.cells, row.row_id, row.page, row.bbox))
        else:
            # Fallback: parse OCR text lines heuristically
            products.extend(self._from_ocr_text(ctx.ocr_text))

        # Attach handwritten manual IDs from associations (prefer right-side digits)
        assoc = {a["row_id"]: a for a in ctx.meta.get("handwriting_associations", []) if a.get("row_id")}
        for p in products:
            if p.row_id in assoc and not p.handwritten_manual_id:
                txt = str(assoc[p.row_id].get("text") or "").strip()
                if re.fullmatch(r"\d{1,10}", txt) or len(txt) <= 12:
                    p.handwritten_manual_id = txt
                    p.field_scores["handwritten_manual_id"] = float(assoc[p.row_id].get("score") or 0.5)

        # Qty × Rate first when possible
        for p in products:
            if p.quantity and p.trade_price:
                amount = round(p.quantity * p.trade_price, 2)
                disc = float(p.discount or 0)
                tax = float(p.tax or 0)
                if p.tax_rate:
                    tax = round((amount - disc) * (p.tax_rate / 100.0), 2)
                    p.tax = tax
                p.net_amount = round(amount - disc + tax, 2)

        from app.services.purchase_pipeline.fetch_instructions import _is_item_row

        ctx.products = [p for p in products if _is_item_row(p)]
        if not ctx.products:
            ctx.warnings.append("No product item rows detected — check OCR text and edit manually.")
        return ctx

    def _from_row(self, cells: List[TextSpan], row_id: int, page: int, bbox) -> StructuredProduct:
        printed = [c for c in cells if c.kind != TextKind.HANDWRITTEN]
        handwritten = [c for c in cells if c.kind == TextKind.HANDWRITTEN]
        texts = [c.text for c in printed]
        joined = "  ".join(texts)

        barcode = ""
        for t in texts:
            m = _BARCODE.search(t)
            if m:
                barcode = m.group(1)
                break

        codes = []
        for t in texts:
            for m in _CODE.finditer(t):
                val = m.group(1)
                if val != barcode and not re.fullmatch(r"\d{1,4}", val):
                    codes.append(val)
        product_code = codes[0] if codes else ""

        # Description: longest alpha-ish cell
        desc = ""
        for t in sorted(texts, key=len, reverse=True):
            if _BARCODE.fullmatch(t):
                continue
            if re.fullmatch(r"[\d.,]+", t):
                continue
            if len(t) >= 3:
                desc = t
                break
        if not desc:
            desc = joined[:120]

        nums = [_to_float(x) for x in _NUM.findall(joined)]
        qty, rate, disc, tax, net = _assign_amounts(nums)

        # Handwritten manual ID: prefer rightmost digit span
        hw_id = ""
        hw_score = 0.0
        digit_hw = [
            h for h in handwritten if re.fullmatch(r"\d{1,10}", (h.text or "").strip())
        ]
        if digit_hw:
            best = max(digit_hw, key=lambda h: h.bbox[0])
            hw_id = best.text.strip()
            hw_score = max(float(best.confidence or 0), 0.6)
        else:
            for h in handwritten:
                if re.fullmatch(r"\d{1,10}", h.text.strip()) or len(h.text) <= 10:
                    hw_id = h.text.strip()
                    hw_score = h.confidence
                    break

        scores = {
            "printed_description": 0.7 if desc else 0.2,
            "printed_product_code": 0.75 if product_code else 0.3,
            "barcode": 0.95 if barcode else 0.2,
            "quantity": 0.65 if qty else 0.2,
            "trade_price": 0.6 if rate else 0.2,
            "discount": 0.55 if disc else 0.4,
            "tax": 0.55 if tax else 0.4,
            "net_amount": 0.55 if net else 0.25,
            "handwritten_manual_id": hw_score if hw_id else 0.3,
        }

        return StructuredProduct(
            printed_product_code=product_code,
            printed_description=desc,
            handwritten_manual_id=hw_id,
            quantity=qty,
            trade_price=rate,
            discount=disc,
            tax=tax,
            net_amount=net,
            barcode=barcode,
            row_id=row_id,
            page=page,
            bbox=bbox,
            source_spans=cells,
            field_scores=scores,
        )

    def _from_ocr_text(self, text: str) -> List[StructuredProduct]:
        products: List[StructuredProduct] = []
        for i, line in enumerate(ln.strip() for ln in (text or "").splitlines() if ln.strip()):
            nums = [_to_float(x) for x in _NUM.findall(line)]
            if len(nums) < 2:
                continue
            qty, rate, disc, tax, net = _assign_amounts(nums)
            if qty <= 0 and rate <= 0:
                continue
            bc = _BARCODE.search(line)
            desc = _BARCODE.sub("", line)
            desc = re.sub(r"[\d.,]+", " ", desc)
            desc = re.sub(r"\s+", " ", desc).strip() or line[:80]
            products.append(
                StructuredProduct(
                    printed_description=desc,
                    quantity=qty,
                    trade_price=rate,
                    discount=disc,
                    tax=tax,
                    net_amount=net or round(qty * rate - disc + tax, 2),
                    barcode=bc.group(1) if bc else "",
                    row_id=i + 1,
                    field_scores={"printed_description": 0.45, "quantity": 0.45, "trade_price": 0.45},
                )
            )
        return products


def _to_float(raw: str) -> float:
    try:
        return float(str(raw).replace(",", ""))
    except (TypeError, ValueError):
        return 0.0


def _assign_amounts(nums: List[float]) -> Tuple[float, float, float, float, float]:
    """Find Qty + Rate first; Amount = Qty×Rate; then discount/tax/net."""
    if not nums:
        return 0.0, 0.0, 0.0, 0.0, 0.0

    # Prefer small integer-ish qty, then next as rate
    qty = 0.0
    rate = 0.0
    rest: List[float] = []
    used = set()
    for i, n in enumerate(nums):
        if n > 0 and n < 10000 and (n == int(n) or n < 500):
            qty = n
            used.add(i)
            break
    for i, n in enumerate(nums):
        if i in used:
            continue
        if n > 0:
            rate = n
            used.add(i)
            break
    rest = [n for i, n in enumerate(nums) if i not in used]

    disc = tax = net = 0.0
    if len(rest) == 1:
        # Could be line amount — if close to qty*rate keep as check; else treat as net
        net = rest[0]
        if qty and rate and abs(net - qty * rate) < 0.05:
            net = round(qty * rate, 2)
        elif qty and not rate and net > 0:
            rate = round(net / qty, 4)
            net = round(qty * rate, 2)
    elif len(rest) == 2:
        # amount, tax OR disc, amount
        a, b = rest[0], rest[1]
        if qty and rate:
            expected = qty * rate
            if abs(a - expected) <= abs(b - expected):
                net, tax = a, 0.0
                # b may be tax
                if b < expected:
                    tax = b
                    net = round(expected + tax, 2) if abs(a - expected) < 1 else a
            else:
                tax, net = a, b
        else:
            tax, net = a, b
    elif len(rest) >= 3:
        disc, tax, net = rest[0], rest[1], rest[-1]

    if qty and rate:
        amount = round(qty * rate, 2)
        if not net:
            net = round(amount - disc + tax, 2)
    return qty, rate, disc, tax, net
