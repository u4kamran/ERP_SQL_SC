"""Stage 2 — Identify supplier from header text / OCR cues."""

from __future__ import annotations

import re
from typing import Optional

from app.services.purchase_pipeline.base import BaseStage
from app.services.purchase_pipeline.types import PipelineContext, SupplierHint


_TAX_RE = re.compile(
    r"(?:ntn|strn|gst|stax|sales\s*tax(?:\s*reg)?(?:\s*no)?)\s*[:#]?\s*([A-Z0-9\-/]{5,20})",
    re.I,
)
_INV_RE = re.compile(
    r"(?:invoice|inv|bill|challan)\s*(?:no|number|#)?\s*[:.]?\s*([A-Z0-9\-/]{2,20})",
    re.I,
)
_DATE_RE = re.compile(
    r"(?:date|dated)\s*[:.]?\s*(\d{1,2}[./\-]\d{1,2}[./\-]\d{2,4}|\d{4}-\d{2}-\d{2})",
    re.I,
)


class IdentifySupplierStage(BaseStage):
    stage_id = 2
    name = "identify_supplier"

    def run(self, ctx: PipelineContext) -> PipelineContext:
        text = ctx.ocr_text or self._spans_text(ctx)
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        header = "\n".join(lines[:25])

        tax = _first(_TAX_RE, header) or ""
        inv = _first(_INV_RE, header) or ""
        inv_date = _first(_DATE_RE, header) or ""
        name = self._guess_name(lines)

        # Learning / extraction rules may override patterns
        supplier_key = tax or name or "unknown"
        if ctx.learning_store:
            rules = ctx.learning_store.get_extraction_rules(supplier_key)
            if rules.get("supplier_name_line") is not None:
                try:
                    idx = int(rules["supplier_name_line"])
                    if 0 <= idx < len(lines):
                        name = lines[idx]
                except (TypeError, ValueError):
                    pass

        conf = 0.35
        if name:
            conf += 0.25
        if tax:
            conf += 0.25
        if inv:
            conf += 0.1

        # DB match if session available
        candidates = []
        supplier_id = None
        if ctx.db is not None and (name or tax):
            try:
                from sqlalchemy import text

                if tax:
                    rows = (
                        ctx.db.execute(
                            text(
                                """
                                SELECT TOP 8 vendor_id, vendor_title, stax_id
                                FROM gl0006
                                WHERE stax_id LIKE :tax
                                ORDER BY vendor_id
                                """
                            ),
                            {"tax": f"%{tax}%"},
                        )
                        .mappings()
                        .all()
                    )
                    for r in rows:
                        candidates.append(
                            {
                                "supplier_id": int(r["vendor_id"]),
                                "vendor_title": str(r["vendor_title"] or ""),
                                "stax_id": str(r["stax_id"] or ""),
                            }
                        )
                if name and len(candidates) < 8:
                    from app.repositories.fin_pur_repository import FinPurRepository, _vget

                    repo = FinPurRepository(ctx.db)
                    for r in repo.search_suppliers(name, limit=10):
                        sid = int(_vget(r, "vendor_id"))
                        if not any(c["supplier_id"] == sid for c in candidates):
                            candidates.append(
                                {
                                    "supplier_id": sid,
                                    "vendor_title": str(_vget(r, "vendor_title", default="") or ""),
                                    "stax_id": str(_vget(r, "stax_id", default="") or ""),
                                }
                            )
                if candidates:
                    supplier_id = candidates[0]["supplier_id"]
                    title = candidates[0]["vendor_title"]
                    if name and title.lower() == name.lower():
                        conf = max(conf, 0.92)
                    elif tax and tax.lower() in (candidates[0].get("stax_id") or "").lower():
                        conf = max(conf, 0.88)
                    else:
                        conf = max(conf, 0.6 if len(candidates) == 1 else 0.45)
                    if not name:
                        name = title
            except Exception:  # noqa: BLE001
                ctx.warnings.append("Supplier DB lookup failed — confirm supplier manually.")

        ctx.supplier = SupplierHint(
            name=name,
            tax_id=tax,
            invoice_no=inv,
            invoice_date=inv_date,
            confidence=min(0.99, conf),
            supplier_id=supplier_id,
            candidates=candidates[:10],
        )
        if conf < 0.72:
            ctx.warnings.append("Supplier identification is low confidence — confirm before Save.")
        return ctx

    def _spans_text(self, ctx: PipelineContext) -> str:
        spans = ctx.printed_spans or []
        return "\n".join(s.text for s in spans[:80])

    def _guess_name(self, lines: list[str]) -> str:
        skip = re.compile(
            r"invoice|challan|gst|ntn|strn|phone|tel|fax|email|www|page|date|bill\s*to",
            re.I,
        )
        for ln in lines[:12]:
            if len(ln) < 4 or skip.search(ln):
                continue
            if re.fullmatch(r"[\d\s\-./]+", ln):
                continue
            return ln[:120]
        return ""


def _first(pattern: re.Pattern, text: str) -> Optional[str]:
    m = pattern.search(text or "")
    return m.group(1).strip() if m else None
