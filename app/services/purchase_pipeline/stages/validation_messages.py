"""Stage 11 — Produce validation messages for mismatches (never silently accept)."""

from __future__ import annotations

from app.services.purchase_pipeline.base import BaseStage
from app.services.purchase_pipeline.types import (
    PipelineContext,
    TOLERANCE_MONEY,
    ValidationMessage,
)


class ValidationMessagesStage(BaseStage):
    stage_id = 11
    name = "validation_messages"

    def run(self, ctx: PipelineContext) -> PipelineContext:
        msgs: list[ValidationMessage] = []
        f = ctx.financials

        def check(code: str, label: str, calc: float, claimed: float) -> None:
            if claimed <= 0:
                return
            delta = abs(calc - claimed)
            if delta > TOLERANCE_MONEY:
                msgs.append(
                    ValidationMessage(
                        code=code,
                        severity="error" if delta > 1.0 else "warning",
                        message=(
                            f"{label} mismatch: recalculated {calc:.2f} vs printed/OCR {claimed:.2f} "
                            f"(Δ {delta:.2f}). Printed totals are not trusted."
                        ),
                        field=label.lower().replace(" ", "_"),
                        expected=calc,
                        actual=claimed,
                    )
                )

        check("GROSS_MISMATCH", "Gross amount", f.gross_amount, f.claimed_gross)
        check("DISCOUNT_MISMATCH", "Discount", f.discount, f.claimed_discount)
        check("TAX_MISMATCH", "Tax", f.tax, f.claimed_tax)
        check("ADV_TAX_MISMATCH", "Advance tax", f.advance_tax, f.claimed_advance_tax)
        check("NET_MISMATCH", "Net amount", f.net_amount, f.claimed_net)
        check("GRAND_MISMATCH", "Grand total", f.grand_total, f.claimed_grand_total)

        for i, p in enumerate(ctx.products):
            calc_gross = round(float(p.quantity or 0) * float(p.trade_price or 0), 2)
            calc_net = round(calc_gross - float(p.discount or 0) + float(p.tax or 0), 2)
            if p.net_amount and calc_gross > 0 and abs(calc_net - float(p.net_amount)) > TOLERANCE_MONEY:
                msgs.append(
                    ValidationMessage(
                        code="LINE_NET_MISMATCH",
                        severity="warning",
                        message=(
                            f"Line {i + 1} net mismatch for '{p.printed_description[:40]}': "
                            f"recalculated {calc_net:.2f} vs extracted {p.net_amount:.2f}."
                        ),
                        field="net_amount",
                        expected=calc_net,
                        actual=p.net_amount,
                        product_index=i,
                    )
                )
            # Replace extracted net with recalculated when we have qty/rate
            if calc_gross > 0:
                p.net_amount = calc_net

        if ctx.document_class_score < 0.5:
            msgs.append(
                ValidationMessage(
                    code="DOC_CLASS_LOW",
                    severity="warning",
                    message="Document classification confidence is low — confirm this is a purchase invoice.",
                    field="document_class",
                    expected="purchase_invoice",
                    actual=ctx.document_class.value,
                )
            )

        if not ctx.supplier.supplier_id:
            msgs.append(
                ValidationMessage(
                    code="SUPPLIER_UNMATCHED",
                    severity="error",
                    message="Supplier was not matched — select the correct supplier before Save.",
                    field="supplier",
                )
            )

        for m in ctx.matches:
            if not m.item_id:
                msgs.append(
                    ValidationMessage(
                        code="ITEM_UNMATCHED",
                        severity="error",
                        message=f"Product line {m.product_index + 1} has no item match.",
                        field="item_id",
                        product_index=m.product_index,
                    )
                )
            elif m.score < 0.72:
                msgs.append(
                    ValidationMessage(
                        code="ITEM_LOW_CONF",
                        severity="warning",
                        message=(
                            f"Product line {m.product_index + 1} match via {m.method or 'unknown'} "
                            f"is low confidence ({m.score:.2f}) — confirm item."
                        ),
                        field="item_id",
                        product_index=m.product_index,
                        expected=0.72,
                        actual=m.score,
                    )
                )

        ctx.validations = msgs
        # Surface as warnings for existing UI
        for msg in msgs:
            if msg.severity in ("error", "warning"):
                ctx.warnings.append(msg.message)
        return ctx
