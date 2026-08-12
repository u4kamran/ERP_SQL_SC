"""Stage 10 — Recalculate every financial value independently. Never trust printed totals."""

from __future__ import annotations

import re

from app.services.purchase_pipeline.base import BaseStage
from app.services.purchase_pipeline.types import FinancialTotals, PipelineContext, TOLERANCE_MONEY


class RecalculateFinancialsStage(BaseStage):
    stage_id = 10
    name = "recalculate_financials"

    def run(self, ctx: PipelineContext) -> PipelineContext:
        claimed = _parse_claimed_totals(ctx.ocr_text)
        # Keep items-only before money math
        from app.services.purchase_pipeline.fetch_instructions import _is_item_row, _normalize_item_math

        if ctx.meta.get("items_only", True):
            ctx.products = [p for p in ctx.products if _is_item_row(p)]
        _normalize_item_math(ctx)

        gross = discount = tax = net = 0.0
        for p in ctx.products:
            # Rule: Qty × Rate first, then discount/tax
            qty = float(p.quantity or 0)
            rate = float(p.trade_price or 0)
            line_gross = round(qty * rate, 2)
            line_disc = round(float(p.discount or 0), 2)
            if p.tax_rate and line_gross:
                line_tax = round((line_gross - line_disc) * (float(p.tax_rate) / 100.0), 2)
                p.tax = line_tax
            else:
                line_tax = round(float(p.tax or 0), 2)
            line_net = round(line_gross - line_disc + line_tax, 2)
            p.net_amount = line_net
            p.field_scores["recalc_gross"] = line_gross
            gross += line_gross
            discount += line_disc
            tax += line_tax
            net += line_net

        advance = claimed.get("advance_tax", 0.0)
        grand = round(net + advance, 2)

        ctx.financials = FinancialTotals(
            gross_amount=round(gross, 2),
            discount=round(discount, 2),
            tax=round(tax, 2),
            advance_tax=round(advance, 2),
            net_amount=round(net, 2),
            grand_total=grand,
            claimed_gross=claimed.get("gross", 0.0),
            claimed_discount=claimed.get("discount", 0.0),
            claimed_tax=claimed.get("tax", 0.0),
            claimed_advance_tax=claimed.get("advance_tax", 0.0),
            claimed_net=claimed.get("net", 0.0),
            claimed_grand_total=claimed.get("grand_total", 0.0),
        )
        ctx.meta["money_tolerance"] = TOLERANCE_MONEY
        return ctx


def _parse_claimed_totals(text: str) -> dict:
    """Extract printed/OCR-claimed totals for comparison only."""
    out = {
        "gross": 0.0,
        "discount": 0.0,
        "tax": 0.0,
        "advance_tax": 0.0,
        "net": 0.0,
        "grand_total": 0.0,
    }
    if not text:
        return out
    patterns = {
        "gross": r"(?:gross|sub\s*total|taxable)\s*[:.]?\s*([\d,]+\.?\d*)",
        "discount": r"(?:discount|disc\.?)\s*[:.]?\s*([\d,]+\.?\d*)",
        "tax": r"(?:sales\s*tax|s\.?\s*tax|gst|vat)\s*[:.]?\s*([\d,]+\.?\d*)",
        "advance_tax": r"(?:advance\s*tax|wht|withholding)\s*[:.]?\s*([\d,]+\.?\d*)",
        "net": r"(?:net\s*amount|net\s*total)\s*[:.]?\s*([\d,]+\.?\d*)",
        "grand_total": r"(?:grand\s*total|total\s*amount|amount\s*payable|invoice\s*total)\s*[:.]?\s*([\d,]+\.?\d*)",
    }
    for key, pat in patterns.items():
        m = re.search(pat, text, re.I)
        if m:
            try:
                out[key] = float(m.group(1).replace(",", ""))
            except ValueError:
                pass
    return out
