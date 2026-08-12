"""Schemas for AI Purchase Automation (invoice upload → review → manual save)."""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.schemas.fin_pur import FinPurHeaderCharges, FinPurSaveResponse


class PurchaseAutoExtractedLine(BaseModel):
    description: str = ""
    barcode: str = ""
    printed_product_code: str = ""
    handwritten_manual_id: str = ""
    qty: float = 0.0
    rate: float = 0.0
    amount: float = 0.0
    stax_rate: float = 0.0
    stax_amt: float = 0.0
    disc_amt: float = 0.0
    disc_amt_oi: float = 0.0
    remarks: str = ""
    notes: str = ""
    field_scores: Dict[str, float] = Field(default_factory=dict)


class PurchaseAutoExtractedInvoice(BaseModel):
    supplier_name: str = ""
    supplier_tax_id: str = ""
    invoice_no: str = ""
    invoice_date: Optional[str] = None
    payment_terms: str = ""
    remarks: str = ""
    discount_amt: float = 0.0
    claim_amt: float = 0.0
    other_ded_amt: float = 0.0
    loading_amt: float = 0.0
    carriage_amt: float = 0.0
    other_charges_amt: float = 0.0
    lines: List[PurchaseAutoExtractedLine] = Field(default_factory=list)
    notes: str = ""
    document_class: str = ""


class PurchaseAutoMatchedItem(BaseModel):
    item_id: Optional[float] = None
    item_title: str = ""
    manual_id: Optional[float] = None
    barcodeid: Optional[str] = None
    co_id: Optional[int] = None
    match_method: str = ""
    match_confidence: str = "none"  # high | medium | low | none
    candidates: List[dict] = Field(default_factory=list)


class PurchaseAutoReviewLine(BaseModel):
    source_description: str = ""
    source_barcode: str = ""
    printed_product_code: str = ""
    handwritten_manual_id: str = ""
    item_id: Optional[float] = None
    item_title: str = ""
    co_id: Optional[int] = None
    qty: float = 0.0
    rate: float = 0.0
    pur_amt: float = 0.0
    stax_rate: float = 0.0
    stax_amt: float = 0.0
    disc_per: float = 0.0
    disc_amt: float = 0.0
    disc_per_oi: float = 0.0
    disc_amt_oi: float = 0.0
    total_amt: float = 0.0
    remarks: str = ""
    exp_date: Optional[date] = None
    match_method: str = ""
    match_confidence: str = "none"
    match_score: float = 0.0
    notes: str = ""
    candidates: List[dict] = Field(default_factory=list)
    requires_confirmation: bool = False
    field_scores: Dict[str, float] = Field(default_factory=dict)


class PurchaseAutoSupplierMatch(BaseModel):
    supplier_id: Optional[int] = None
    vendor_title: str = ""
    registration: str = ""
    stax_type: int = 0
    address: str = ""
    stax_id: str = ""
    city_id: int = 0
    match_confidence: str = "none"
    match_score: float = 0.0
    candidates: List[dict] = Field(default_factory=list)
    requires_confirmation: bool = False


class PipelineStageTraceOut(BaseModel):
    stage_id: int
    name: str
    ok: bool = True
    detail: str = ""
    duration_ms: float = 0.0


class ValidationMessageOut(BaseModel):
    code: str
    severity: str
    message: str
    field: str = ""
    expected: Any = None
    actual: Any = None
    product_index: Optional[int] = None


class FieldConfidenceOut(BaseModel):
    field: str
    value: Any = None
    score: float = 0.0
    requires_confirmation: bool = False
    reason: str = ""


class FinancialTotalsOut(BaseModel):
    gross_amount: float = 0.0
    discount: float = 0.0
    tax: float = 0.0
    advance_tax: float = 0.0
    net_amount: float = 0.0
    grand_total: float = 0.0
    claimed_gross: float = 0.0
    claimed_discount: float = 0.0
    claimed_tax: float = 0.0
    claimed_advance_tax: float = 0.0
    claimed_net: float = 0.0
    claimed_grand_total: float = 0.0


class PurchaseAutoProcessResponse(BaseModel):
    model: str
    warnings: List[str] = Field(default_factory=list)
    ocr_text: str = ""
    ocr_engines: List[str] = Field(default_factory=list)
    extracted: PurchaseAutoExtractedInvoice
    supplier: PurchaseAutoSupplierMatch
    doc_date: date
    gp_id: str = ""
    remarks: str = "Nil"
    payment_type: int = 0
    charges: FinPurHeaderCharges = Field(default_factory=FinPurHeaderCharges)
    lines: List[PurchaseAutoReviewLine] = Field(default_factory=list)
    # Multi-stage pipeline outputs
    document_class: str = ""
    document_class_score: float = 0.0
    validations: List[ValidationMessageOut] = Field(default_factory=list)
    field_confidences: List[FieldConfidenceOut] = Field(default_factory=list)
    financials: FinancialTotalsOut = Field(default_factory=FinancialTotalsOut)
    stage_trace: List[PipelineStageTraceOut] = Field(default_factory=list)
    learning_pending: List[Dict[str, Any]] = Field(default_factory=list)


class PurchaseAutoSaveLine(BaseModel):
    item_id: float
    item_title: str = ""
    qty: float
    rate: float = 0.0
    pur_amt: float = 0.0
    stax_rate: float = 0.0
    stax_amt: float = 0.0
    disc_per: float = 0.0
    disc_amt: float = 0.0
    disc_per_oi: float = 0.0
    disc_amt_oi: float = 0.0
    total_amt: float = 0.0
    remarks: str = ""
    exp_date: Optional[date] = None
    co_id: Optional[int] = None
    # Learning signals
    printed_description: str = ""
    printed_product_code: str = ""
    handwritten_manual_id: str = ""
    source_barcode: str = ""


class PurchaseAutoSaveRequest(BaseModel):
    """Manual Save — posts through existing Fin_Pur save path."""

    supplier_id: int
    doc_date: date
    remarks: str = "Nil"
    payment_type: int = 0
    stax_type: int = 0
    gp_id: str = ""
    gp_time: str = ""
    vendor_title: str = ""
    address: str = ""
    stax_id: str = ""
    city_id: int = 0
    charges: FinPurHeaderCharges = Field(default_factory=FinPurHeaderCharges)
    lines: List[PurchaseAutoSaveLine] = Field(min_length=1)
    learn_corrections: bool = True


class PurchaseAutoLearnRequest(BaseModel):
    supplier_id: Optional[int] = None
    supplier_key: str = ""
    corrections: List[Dict[str, Any]] = Field(default_factory=list)


class PurchaseAutoLearnResponse(BaseModel):
    applied: List[str] = Field(default_factory=list)
    message: str = ""


class PurchaseAutoInstructionsRequest(BaseModel):
    instructions: str = ""


class PurchaseAutoInstructionsResponse(BaseModel):
    instructions: str = ""
    message: str = ""


class PurchaseAutoJsonImportRequest(BaseModel):
    """Paste-JSON import — items matched by manual_id first."""

    json_text: str = ""
    data: Optional[Dict[str, Any]] = None
