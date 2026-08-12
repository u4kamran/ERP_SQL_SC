"""Purchase Automation — 13-stage pipeline → review → manual Fin_Pur save."""

from __future__ import annotations

import json
import re
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.fin_pur_repository import FinPurRepository, _vget
from app.schemas.fin_pur import FinPurHeaderCharges, FinPurLineIn, FinPurSaveRequest, FinPurSaveResponse
from app.schemas.purchase_automation import (
    FieldConfidenceOut,
    FinancialTotalsOut,
    PipelineStageTraceOut,
    PurchaseAutoExtractedInvoice,
    PurchaseAutoExtractedLine,
    PurchaseAutoLearnRequest,
    PurchaseAutoLearnResponse,
    PurchaseAutoProcessResponse,
    PurchaseAutoReviewLine,
    PurchaseAutoSaveRequest,
    PurchaseAutoSupplierMatch,
    ValidationMessageOut,
)
from app.services.fin_pur_service import FinPurService
from app.services.purchase_pipeline import PurchaseDocumentPipeline
from app.services.purchase_pipeline.learning_store import LearningStore
from app.services.purchase_pipeline.stages.learn import apply_user_corrections
from app.services.purchase_pipeline.types import CONFIRM_THRESHOLD, HIGH_THRESHOLD, MEDIUM_THRESHOLD


def _money(v) -> float:
    try:
        return round(float(v or 0), 2)
    except (TypeError, ValueError):
        return 0.0


def _parse_date(raw: Optional[str]) -> date:
    if not raw:
        return date.today()
    text_val = str(raw).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y", "%d.%m.%Y"):
        try:
            return datetime.strptime(text_val[:10] if fmt == "%Y-%m-%d" else text_val, fmt).date()
        except ValueError:
            continue
    try:
        return date.fromisoformat(text_val[:10])
    except ValueError:
        return date.today()


def _score_to_label(score: float) -> str:
    if score >= HIGH_THRESHOLD:
        return "high"
    if score >= MEDIUM_THRESHOLD:
        return "medium"
    if score > 0:
        return "low"
    return "none"


class PurchaseAutomationService:
    def __init__(
        self,
        db: Session,
        *,
        username: str,
        legacy_uid: int,
        is_admin: bool = False,
    ):
        self.db = db
        self.repo = FinPurRepository(db)
        self.username = username
        self.legacy_uid = legacy_uid
        self.is_admin = is_admin
        self.learning_store = LearningStore()
        self.pipeline = PurchaseDocumentPipeline(
            db=db,
            learning_store=self.learning_store,
            username=username,
        )

    def process(
        self, *, file_bytes: bytes, mime_type: str, instructions: str = ""
    ) -> PurchaseAutoProcessResponse:
        cleaned = (instructions or "").strip()
        if cleaned:
            self.learning_store.set_fetch_instructions(cleaned)
        else:
            # Keep previously saved / default instructions — never process with nothing
            from app.services.purchase_pipeline.fetch_instructions import DEFAULT_FETCH_INSTRUCTIONS

            cleaned = self.learning_store.get_fetch_instructions() or DEFAULT_FETCH_INSTRUCTIONS

        result = self.pipeline.run(
            file_bytes=file_bytes, mime_type=mime_type, instructions=cleaned
        )
        ctx = result.ctx

        extracted = PurchaseAutoExtractedInvoice(
            supplier_name=ctx.supplier.name,
            supplier_tax_id=ctx.supplier.tax_id,
            invoice_no=ctx.supplier.invoice_no,
            invoice_date=ctx.supplier.invoice_date or None,
            discount_amt=ctx.financials.discount,
            lines=[
                PurchaseAutoExtractedLine(
                    description=p.printed_description,
                    barcode=p.barcode,
                    printed_product_code=p.printed_product_code,
                    handwritten_manual_id=p.handwritten_manual_id,
                    qty=p.quantity,
                    rate=p.trade_price,
                    amount=round(p.quantity * p.trade_price, 2) if p.quantity and p.trade_price else p.net_amount,
                    stax_amt=p.tax,
                    disc_amt=p.discount,
                    field_scores=dict(p.field_scores or {}),
                )
                for p in ctx.products
            ],
            notes="; ".join(ctx.warnings[:5]),
            document_class=ctx.document_class.value,
        )

        supplier = self._supplier_from_ctx(ctx)
        doc_date = _parse_date(ctx.supplier.invoice_date)
        charges = FinPurHeaderCharges(
            discount=_money(ctx.financials.discount),
            claim=0.0,
            other_ded=0.0,
            loading=0.0,
            carriage=0.0,
            other_charges=0.0,
        )

        match_by_idx = {m.product_index: m for m in ctx.matches}
        lines: List[PurchaseAutoReviewLine] = []
        for i, product in enumerate(ctx.products):
            m = match_by_idx.get(i)
            qty = _money(product.quantity)
            rate = _money(product.trade_price)
            amount = round(qty * rate, 2) if qty and rate else _money(product.net_amount)
            stax_amt = _money(product.tax)
            disc_amt = _money(product.discount)
            total = round(amount - disc_amt + stax_amt, 2)
            score = float(m.score) if m else 0.0
            item_title = ""
            item_id = None
            co_id = None
            method = ""
            candidates: list = []
            if m:
                item_id = m.item_id
                item_title = m.item_title
                co_id = m.co_id
                method = m.method
                candidates = m.candidates
            if item_id and not item_title:
                item = self.repo.get_item(item_id)
                if item:
                    item_title = f"{_vget(item, 'item_title', default='')} --- {_vget(item, 'manualid', default='')}"
                    co_id = co_id or (int(_vget(item, "co_id") or 0) or None)

            lines.append(
                PurchaseAutoReviewLine(
                    source_description=product.printed_description,
                    source_barcode=product.barcode,
                    printed_product_code=product.printed_product_code,
                    handwritten_manual_id=product.handwritten_manual_id,
                    item_id=item_id,
                    item_title=item_title or product.printed_description,
                    co_id=co_id,
                    qty=qty,
                    rate=rate,
                    pur_amt=amount,
                    stax_rate=_money(product.tax_rate),
                    stax_amt=stax_amt,
                    disc_per=round((disc_amt / amount) * 100, 2) if amount and disc_amt else 0.0,
                    disc_amt=disc_amt,
                    total_amt=total,
                    remarks=(product.handwritten_manual_id or "")[:10],
                    exp_date=doc_date,
                    match_method=method,
                    match_confidence=_score_to_label(score),
                    match_score=score,
                    notes="",
                    candidates=candidates,
                    requires_confirmation=score < CONFIRM_THRESHOLD or not item_id,
                    field_scores=dict(product.field_scores or {}),
                )
            )

        remarks = "Nil"
        if ctx.supplier.invoice_no:
            remarks = f"Nil Inv:{ctx.supplier.invoice_no}"[:100]

        return PurchaseAutoProcessResponse(
            model=result.model_label,
            warnings=list(dict.fromkeys(ctx.warnings)),
            ocr_text=ctx.ocr_text,
            ocr_engines=ctx.ocr_engines,
            extracted=extracted,
            supplier=supplier,
            doc_date=doc_date,
            gp_id=(ctx.supplier.invoice_no or "")[:8],
            remarks=remarks,
            payment_type=0,
            charges=charges,
            lines=lines,
            document_class=ctx.document_class.value,
            document_class_score=ctx.document_class_score,
            validations=[
                ValidationMessageOut(
                    code=v.code,
                    severity=v.severity,
                    message=v.message,
                    field=v.field,
                    expected=v.expected,
                    actual=v.actual,
                    product_index=v.product_index,
                )
                for v in ctx.validations
            ],
            field_confidences=[
                FieldConfidenceOut(
                    field=f.field,
                    value=f.value,
                    score=f.score,
                    requires_confirmation=f.requires_confirmation,
                    reason=f.reason,
                )
                for f in ctx.field_confidences
            ],
            financials=FinancialTotalsOut(
                gross_amount=ctx.financials.gross_amount,
                discount=ctx.financials.discount,
                tax=ctx.financials.tax,
                advance_tax=ctx.financials.advance_tax,
                net_amount=ctx.financials.net_amount,
                grand_total=ctx.financials.grand_total,
                claimed_gross=ctx.financials.claimed_gross,
                claimed_discount=ctx.financials.claimed_discount,
                claimed_tax=ctx.financials.claimed_tax,
                claimed_advance_tax=ctx.financials.claimed_advance_tax,
                claimed_net=ctx.financials.claimed_net,
                claimed_grand_total=ctx.financials.claimed_grand_total,
            ),
            stage_trace=[
                PipelineStageTraceOut(
                    stage_id=s.stage_id,
                    name=s.name,
                    ok=s.ok,
                    detail=s.detail,
                    duration_ms=s.duration_ms,
                )
                for s in ctx.stage_trace
            ],
            learning_pending=list(ctx.learning_pending),
        )

    def _supplier_from_ctx(self, ctx) -> PurchaseAutoSupplierMatch:
        conf = _score_to_label(ctx.supplier.confidence)
        requires = ctx.supplier.confidence < CONFIRM_THRESHOLD or not ctx.supplier.supplier_id
        if not ctx.supplier.supplier_id:
            return PurchaseAutoSupplierMatch(
                vendor_title=ctx.supplier.name,
                stax_id=ctx.supplier.tax_id,
                match_confidence=conf,
                match_score=ctx.supplier.confidence,
                candidates=ctx.supplier.candidates,
                requires_confirmation=True,
            )
        try:
            supplier = FinPurService(
                self.db, username=self.username, legacy_uid=self.legacy_uid, is_admin=True
            ).get_supplier(ctx.supplier.supplier_id)
            stax_type = 0 if supplier.registration == "Registered" else 1
            return PurchaseAutoSupplierMatch(
                supplier_id=supplier.supplier_id,
                vendor_title=supplier.vendor_title,
                registration=supplier.registration,
                stax_type=stax_type,
                address=supplier.address,
                stax_id=supplier.stax_id,
                city_id=supplier.city_id,
                match_confidence=conf,
                match_score=ctx.supplier.confidence,
                candidates=ctx.supplier.candidates,
                requires_confirmation=requires,
            )
        except HTTPException:
            return PurchaseAutoSupplierMatch(
                vendor_title=ctx.supplier.name,
                stax_id=ctx.supplier.tax_id,
                match_confidence="none",
                match_score=0.0,
                candidates=ctx.supplier.candidates,
                requires_confirmation=True,
            )

    def save(self, payload: PurchaseAutoSaveRequest) -> FinPurSaveResponse:
        """Manual Save only — reuses Fin_PurM CmdSave path; learns from corrections."""
        for line in payload.lines:
            if not line.item_id or _money(line.qty) <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Every line needs a matched Item ID and Quantity before Save.",
                )

        if payload.learn_corrections:
            self._learn_from_save(payload)

        save_req = FinPurSaveRequest(
            prod_id=None,
            serial_no=None,
            doc_date=payload.doc_date,
            supplier_id=payload.supplier_id,
            remarks=payload.remarks or "Nil",
            payment_type=payload.payment_type,
            stax_type=payload.stax_type,
            gp_id=payload.gp_id,
            gp_time=payload.gp_time or datetime.now().strftime("%H:%M"),
            vendor_title=payload.vendor_title,
            address=payload.address,
            stax_id=payload.stax_id,
            city_id=payload.city_id,
            charges=payload.charges,
            lines=[
                FinPurLineIn(
                    item_id=line.item_id,
                    item_title=line.item_title,
                    qty=line.qty,
                    rate=line.rate,
                    pur_amt=line.pur_amt or round(line.rate * line.qty, 2),
                    stax_rate=line.stax_rate,
                    stax_amt=line.stax_amt,
                    disc_per=line.disc_per,
                    disc_amt=line.disc_amt,
                    disc_per_oi=line.disc_per_oi,
                    disc_amt_oi=line.disc_amt_oi,
                    total_amt=line.total_amt
                    or round(
                        ((line.pur_amt or line.rate * line.qty) + line.stax_amt)
                        - line.disc_amt
                        - line.disc_amt_oi,
                        2,
                    ),
                    remarks=line.remarks,
                    exp_date=line.exp_date or payload.doc_date,
                )
                for line in payload.lines
            ],
        )
        pur_svc = FinPurService(
            self.db,
            username=self.username,
            legacy_uid=self.legacy_uid,
            is_admin=self.is_admin,
        )
        for line in payload.lines:
            co_id = line.co_id
            if not co_id:
                item = self.repo.get_item(line.item_id)
                co_id = int(_vget(item, "co_id") or 0) if item else 0
            if co_id and line.qty:
                try:
                    pur_svc.update_item_from_detail(
                        item_id=line.item_id,
                        mrp=0,
                        stax_rate=line.stax_rate,
                        stax_amt=line.stax_amt,
                        qty=line.qty,
                        amount=line.pur_amt or (line.rate * line.qty),
                        disc_amt=line.disc_amt,
                        off_inv_disc_amt=line.disc_amt_oi,
                        rate=line.rate,
                        co_id=int(co_id),
                    )
                except HTTPException:
                    pass

        return pur_svc.save_document(save_req)

    def _learn_from_save(self, payload: PurchaseAutoSaveRequest) -> None:
        supplier_key = str(payload.supplier_id)
        corrections = []
        for line in payload.lines:
            corrections.append(
                {
                    "supplier_key": supplier_key,
                    "item_id": line.item_id,
                    "alias": line.printed_description or line.item_title,
                    "handwritten_manual_id": line.handwritten_manual_id,
                    "supplier_product_code": line.printed_product_code,
                }
            )
        apply_user_corrections(self.learning_store, supplier_key=supplier_key, corrections=corrections)

    def learn(self, payload: PurchaseAutoLearnRequest) -> PurchaseAutoLearnResponse:
        key = payload.supplier_key or (str(payload.supplier_id) if payload.supplier_id else "unknown")
        applied = apply_user_corrections(
            self.learning_store, supplier_key=key, corrections=payload.corrections
        )
        return PurchaseAutoLearnResponse(
            applied=applied,
            message=f"Learned {len(applied)} mapping(s)." if applied else "No mappings applied.",
        )

    def get_instructions(self) -> "PurchaseAutoInstructionsResponse":
        from app.schemas.purchase_automation import PurchaseAutoInstructionsResponse
        from app.services.purchase_pipeline.fetch_instructions import DEFAULT_FETCH_INSTRUCTIONS

        saved = self.learning_store.get_fetch_instructions()
        if not saved.strip() or "Handwritten Manual ID" not in saved:
            # Seed / refresh built-in priority rules so operators always see them
            saved = self.learning_store.set_fetch_instructions(DEFAULT_FETCH_INSTRUCTIONS)
        return PurchaseAutoInstructionsResponse(
            instructions=saved,
            message="ok",
        )

    def save_instructions(self, instructions: str) -> "PurchaseAutoInstructionsResponse":
        from app.schemas.purchase_automation import PurchaseAutoInstructionsResponse

        saved = self.learning_store.set_fetch_instructions(instructions)
        return PurchaseAutoInstructionsResponse(
            instructions=saved,
            message="Fetch instructions saved for future Process runs.",
        )

    # ----- Paste JSON → review grid -----

    def import_json(
        self, *, json_text: str = "", data: Optional[Dict[str, Any]] = None
    ) -> PurchaseAutoProcessResponse:
        """Fill the review grid from pasted JSON. Items resolve by manual_id first."""
        payload = data if isinstance(data, dict) else _parse_json_text(json_text)
        raw_items = _pick_items(payload)
        if not raw_items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="JSON has no items. Expected an 'items' (or 'lines'/'products') array.",
            )

        warnings: List[str] = []
        validations: List[ValidationMessageOut] = []

        invoice_no = str(_pick(payload, "invoice_no", "invoice", "invoice_number", "bill_no") or "").strip()
        reference_no = str(_pick(payload, "reference_no", "reference", "ref_no", "gp_id") or "").strip()
        supplier_name = str(
            _pick(payload, "supplier", "supplier_name", "customer", "vendor", "party") or ""
        ).strip()
        doc_date = _parse_date(str(_pick(payload, "date", "invoice_date", "doc_date") or ""))

        lines: List[PurchaseAutoReviewLine] = []
        extracted_lines: List[PurchaseAutoExtractedLine] = []
        gross = discount_total = tax_total = net_total = 0.0
        unmatched = 0

        for idx, raw in enumerate(raw_items):
            if not isinstance(raw, dict):
                continue
            manual_id = str(
                _pick(raw, "manual_id", "manualid", "manual", "item_code", "code") or ""
            ).strip()
            description = str(_pick(raw, "description", "item_title", "name", "particulars") or "").strip()
            barcode = str(_pick(raw, "barcode", "barcodeid") or "").strip()
            uom = str(_pick(raw, "uom", "unit") or "").strip()

            qty = _num(_pick(raw, "qty", "quantity"))
            rate = _num(_pick(raw, "rate", "trade_price", "price", "unit_rate"))
            amount = _num(_pick(raw, "amount", "value", "line_total"))
            disc_amt = _num(_pick(raw, "discount", "disc_amt", "disc"))
            stax_rate = _num(_pick(raw, "tax_rate", "stax_rate", "gst_rate"))
            stax_amt = _num(_pick(raw, "tax", "stax_amt", "sales_tax", "gst"))

            # Qty × Rate first; back-fill whichever value is missing
            if qty and rate:
                amount = round(qty * rate, 2)
            elif qty and amount and not rate:
                rate = round(amount / qty, 4)
                amount = round(qty * rate, 2)
            elif rate and amount and not qty:
                qty = round(amount / rate, 4)
                amount = round(qty * rate, 2)

            if stax_rate and amount:
                stax_amt = round((amount - disc_amt) * (stax_rate / 100.0), 2)
            total = round(amount - disc_amt + stax_amt, 2)

            item_id = None
            item_title = ""
            co_id = None
            method = ""
            score = 0.0
            candidates: List[dict] = []

            item = self._lookup_by_manual_id(manual_id)
            if item:
                method, score = "manual_id", 0.97
            if item is None and barcode:
                item = self._lookup_by_barcode(barcode)
                if item:
                    method, score = "barcode", 0.9
            if item is None and description:
                found, cands = self._lookup_by_description(description)
                candidates = cands
                if found:
                    item = found
                    method, score = "title", 0.7 if len(cands) <= 1 else 0.5

            if item:
                item_id = float(_vget(item, "item_id"))
                item_title = _item_title_with_manual(item)
                co_id = int(_vget(item, "co_id") or 0) or None
            else:
                unmatched += 1
                validations.append(
                    ValidationMessageOut(
                        code="ITEM_UNMATCHED",
                        severity="error",
                        message=(
                            f"Line {idx + 1}: no item found for manual ID "
                            f"'{manual_id or '—'}' ({description or 'no description'})."
                        ),
                        field="item_id",
                        product_index=idx,
                    )
                )

            if amount and _num(_pick(raw, "amount", "value", "line_total")):
                claimed_amt = _num(_pick(raw, "amount", "value", "line_total"))
                if abs(claimed_amt - amount) > 0.05:
                    validations.append(
                        ValidationMessageOut(
                            code="LINE_AMOUNT_MISMATCH",
                            severity="warning",
                            message=(
                                f"Line {idx + 1}: recalculated {amount:.2f} vs JSON amount "
                                f"{claimed_amt:.2f}. Recalculated value kept."
                            ),
                            field="pur_amt",
                            expected=amount,
                            actual=claimed_amt,
                            product_index=idx,
                        )
                    )

            gross += amount
            discount_total += disc_amt
            tax_total += stax_amt
            net_total += total

            extracted_lines.append(
                PurchaseAutoExtractedLine(
                    description=description,
                    barcode=barcode,
                    handwritten_manual_id=manual_id,
                    qty=qty,
                    rate=rate,
                    amount=amount,
                    stax_rate=stax_rate,
                    stax_amt=stax_amt,
                    disc_amt=disc_amt,
                )
            )
            lines.append(
                PurchaseAutoReviewLine(
                    source_description=description,
                    source_barcode=barcode,
                    handwritten_manual_id=manual_id,
                    item_id=item_id,
                    # Title always carries the manual ID, matched or not
                    item_title=item_title
                    or (f"{description} --- {manual_id}" if manual_id else description),
                    co_id=co_id,
                    qty=qty,
                    rate=rate,
                    pur_amt=amount,
                    stax_rate=stax_rate,
                    stax_amt=stax_amt,
                    disc_per=round((disc_amt / amount) * 100, 2) if amount and disc_amt else 0.0,
                    disc_amt=disc_amt,
                    total_amt=total,
                    remarks=(manual_id or uom or "")[:10],
                    exp_date=doc_date,
                    match_method=method,
                    match_confidence=_score_to_label(score),
                    match_score=score,
                    candidates=candidates,
                    requires_confirmation=score < CONFIRM_THRESHOLD or not item_id,
                )
            )

        totals = payload.get("totals") if isinstance(payload.get("totals"), dict) else {}
        claimed_gross = _num(_pick(totals, "gross_amount", "gross", "sub_total"))
        claimed_net = _num(_pick(totals, "net_amount", "net"))
        claimed_grand = _num(_pick(totals, "grand_total", "total", "amount_payable"))
        claimed_disc = _num(_pick(totals, "discount", "disc_amt"))
        claimed_tax = _num(_pick(totals, "tax", "sales_tax", "gst"))
        advance_tax = _num(_pick(totals, "advance_tax", "wht"))

        gross = round(gross, 2)
        discount_total = round(discount_total, 2)
        tax_total = round(tax_total, 2)
        net_total = round(net_total, 2)
        grand_total = round(net_total + advance_tax, 2)

        for label, code, calc, claimed in (
            ("Gross amount", "GROSS_MISMATCH", gross, claimed_gross),
            ("Discount", "DISCOUNT_MISMATCH", discount_total, claimed_disc),
            ("Tax", "TAX_MISMATCH", tax_total, claimed_tax),
            ("Net amount", "NET_MISMATCH", net_total, claimed_net),
            ("Grand total", "GRAND_MISMATCH", grand_total, claimed_grand),
        ):
            if claimed and abs(calc - claimed) > 0.05:
                validations.append(
                    ValidationMessageOut(
                        code=code,
                        severity="error" if abs(calc - claimed) > 1.0 else "warning",
                        message=(
                            f"{label} mismatch: recalculated {calc:.2f} vs JSON {claimed:.2f}. "
                            "JSON totals are not trusted."
                        ),
                        field=label.lower().replace(" ", "_"),
                        expected=calc,
                        actual=claimed,
                    )
                )

        supplier = self._match_supplier_by_name(supplier_name)
        if not supplier.supplier_id:
            warnings.append("Supplier not matched from JSON — select the supplier before Save.")
        if unmatched:
            warnings.append(f"{unmatched} line(s) had no manual ID match — fix before Save.")
        warnings.append(
            f"Imported {len(lines)} item line(s) from JSON · matched by manual ID first · totals recalculated."
        )

        remarks = f"Nil Inv:{invoice_no}"[:100] if invoice_no else "Nil"

        return PurchaseAutoProcessResponse(
            model="json-import/manual-id-first",
            warnings=warnings,
            ocr_text="",
            ocr_engines=[],
            extracted=PurchaseAutoExtractedInvoice(
                supplier_name=supplier_name,
                invoice_no=invoice_no,
                invoice_date=doc_date.isoformat(),
                lines=extracted_lines,
                document_class="json_import",
            ),
            supplier=supplier,
            doc_date=doc_date,
            gp_id=(reference_no or invoice_no or "")[:8],
            remarks=remarks,
            payment_type=0,
            charges=FinPurHeaderCharges(),
            lines=lines,
            document_class="json_import",
            document_class_score=1.0,
            validations=validations,
            financials=FinancialTotalsOut(
                gross_amount=gross,
                discount=discount_total,
                tax=tax_total,
                advance_tax=advance_tax,
                net_amount=net_total,
                grand_total=grand_total,
                claimed_gross=claimed_gross,
                claimed_discount=claimed_disc,
                claimed_tax=claimed_tax,
                claimed_advance_tax=advance_tax,
                claimed_net=claimed_net,
                claimed_grand_total=claimed_grand,
            ),
            stage_trace=[
                PipelineStageTraceOut(
                    stage_id=1,
                    name="json_import",
                    ok=True,
                    detail=f"{len(lines)} line(s)",
                )
            ],
        )

    def _lookup_by_manual_id(self, manual_id: str) -> Optional[dict]:
        digits = re.sub(r"[^\d.]", "", str(manual_id or "").strip())
        if not digits:
            return None
        try:
            view = self.repo.get_item_view(manual_id=float(digits))
        except (TypeError, ValueError):
            return None
        if not view:
            return None
        return self.repo.get_item(float(_vget(view, "item_id"))) or view

    def _lookup_by_barcode(self, barcode: str) -> Optional[dict]:
        view = self.repo.get_item_view(barcode=barcode) or self.repo.get_item_view(barcode_ws=barcode)
        if not view:
            return None
        return self.repo.get_item(float(_vget(view, "item_id"))) or view

    def _lookup_by_description(self, description: str):
        rows = self.repo.search_items(description[:60], limit=8)
        candidates = [
            {
                "item_id": float(_vget(r, "item_id")),
                "item_title": str(_vget(r, "item_title", default="") or ""),
                "manualid": _vget(r, "manualid"),
                "barcodeid": _vget(r, "barcodeid"),
            }
            for r in rows
        ]
        if not candidates:
            return None, []
        wanted = description.strip().lower()
        exact = next((c for c in candidates if c["item_title"].strip().lower() == wanted), None)
        chosen = exact or (candidates[0] if len(candidates) == 1 else None)
        if not chosen:
            # Ambiguous — let the operator pick from candidates instead of guessing
            return None, candidates
        return self.repo.get_item(chosen["item_id"]), candidates

    def _match_supplier_by_name(self, name: str) -> PurchaseAutoSupplierMatch:
        name = (name or "").strip()
        if not name:
            return PurchaseAutoSupplierMatch(match_confidence="none", requires_confirmation=True)

        rows = self.repo.search_suppliers(name, limit=10)
        candidates = [
            {
                "supplier_id": int(_vget(r, "vendor_id")),
                "vendor_title": str(_vget(r, "vendor_title", default="") or ""),
                "stax_id": str(_vget(r, "stax_id", default="") or ""),
            }
            for r in rows
        ]
        if not candidates:
            return PurchaseAutoSupplierMatch(
                vendor_title=name,
                match_confidence="none",
                requires_confirmation=True,
            )

        best = candidates[0]
        score = 0.95 if best["vendor_title"].strip().lower() == name.lower() else 0.55
        try:
            supplier = FinPurService(
                self.db, username=self.username, legacy_uid=self.legacy_uid, is_admin=True
            ).get_supplier(best["supplier_id"])
            return PurchaseAutoSupplierMatch(
                supplier_id=supplier.supplier_id,
                vendor_title=supplier.vendor_title,
                registration=supplier.registration,
                stax_type=0 if supplier.registration == "Registered" else 1,
                address=supplier.address,
                stax_id=supplier.stax_id,
                city_id=supplier.city_id,
                match_confidence=_score_to_label(score),
                match_score=score,
                candidates=candidates,
                requires_confirmation=score < CONFIRM_THRESHOLD,
            )
        except HTTPException:
            return PurchaseAutoSupplierMatch(
                vendor_title=name,
                match_confidence="none",
                candidates=candidates,
                requires_confirmation=True,
            )


def _parse_json_text(text: str) -> Dict[str, Any]:
    raw = (text or "").strip()
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Paste the invoice JSON before importing.",
        )
    # Tolerate fenced code blocks pasted from chat/AI output
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-zA-Z]*\s*|\s*```$", "", raw).strip()
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON: {exc.msg} (line {exc.lineno}, column {exc.colno}).",
        ) from exc
    if isinstance(parsed, list):
        return {"items": parsed}
    if not isinstance(parsed, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="JSON must be an object with an 'items' array, or an array of items.",
        )
    return parsed


def _pick_items(payload: Dict[str, Any]) -> List[Any]:
    for key in ("items", "lines", "products", "details", "rows"):
        value = payload.get(key)
        if isinstance(value, list) and value:
            return value
    return []


def _pick(source: Any, *keys: str) -> Any:
    if not isinstance(source, dict):
        return None
    lowered = {str(k).strip().lower(): v for k, v in source.items()}
    for key in keys:
        value = lowered.get(key.lower())
        if value not in (None, ""):
            return value
    return None


def _num(value: Any) -> float:
    if value in (None, ""):
        return 0.0
    try:
        return round(float(str(value).replace(",", "").strip()), 4)
    except (TypeError, ValueError):
        return 0.0


def _item_title_with_manual(item: Any) -> str:
    """Always show item title together with its manual ID (VB6 grid convention)."""
    title = str(_vget(item, "item_title", default="") or "").strip()
    manual = _vget(item, "manualid")
    if manual in (None, ""):
        return title
    try:
        manual_num = float(manual)
        manual_txt = str(int(manual_num)) if manual_num.is_integer() else str(manual_num)
    except (TypeError, ValueError):
        manual_txt = str(manual)
    return f"{title} --- {manual_txt}"
