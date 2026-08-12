"""Shared types for the purchase document analysis pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class DocumentClass(str, Enum):
    PURCHASE_INVOICE = "purchase_invoice"
    TAX_INVOICE = "tax_invoice"
    DELIVERY_CHALLAN = "delivery_challan"
    CREDIT_NOTE = "credit_note"
    UNKNOWN = "unknown"


class TextKind(str, Enum):
    PRINTED = "printed"
    HANDWRITTEN = "handwritten"
    MIXED = "mixed"
    UNKNOWN = "unknown"


BBox = Tuple[float, float, float, float]  # x0, y0, x1, y1


@dataclass
class TextSpan:
    text: str
    confidence: float
    kind: TextKind
    page: int = 0
    bbox: BBox = (0.0, 0.0, 0.0, 0.0)
    engine: str = ""
    row_id: Optional[int] = None

    @property
    def cx(self) -> float:
        return (self.bbox[0] + self.bbox[2]) / 2.0

    @property
    def cy(self) -> float:
        return (self.bbox[1] + self.bbox[3]) / 2.0

    @property
    def area(self) -> float:
        return max(0.0, self.bbox[2] - self.bbox[0]) * max(0.0, self.bbox[3] - self.bbox[1])


@dataclass
class LayoutRegion:
    name: str
    page: int
    bbox: BBox
    role: str = ""  # header | table | footer | stamp | notes


@dataclass
class TableRow:
    row_id: int
    page: int
    bbox: BBox
    cells: List[TextSpan] = field(default_factory=list)
    y_center: float = 0.0


@dataclass
class TableBlock:
    page: int
    bbox: BBox
    rows: List[TableRow] = field(default_factory=list)
    header_texts: List[str] = field(default_factory=list)


@dataclass
class FieldConfidence:
    field: str
    value: Any
    score: float  # 0..1
    requires_confirmation: bool = False
    reason: str = ""


@dataclass
class StructuredProduct:
    """Stage 8 product payload."""

    printed_product_code: str = ""
    printed_description: str = ""
    handwritten_manual_id: str = ""
    quantity: float = 0.0
    trade_price: float = 0.0
    discount: float = 0.0
    tax: float = 0.0
    net_amount: float = 0.0
    barcode: str = ""
    tax_rate: float = 0.0
    row_id: Optional[int] = None
    page: int = 0
    bbox: BBox = (0.0, 0.0, 0.0, 0.0)
    source_spans: List[TextSpan] = field(default_factory=list)
    field_scores: Dict[str, float] = field(default_factory=dict)


@dataclass
class ProductMatch:
    product_index: int
    item_id: Optional[float] = None
    item_title: str = ""
    manual_id: Optional[float] = None
    barcodeid: Optional[str] = None
    co_id: Optional[int] = None
    method: str = ""  # barcode|supplier_code|handwritten_manual_id|alias|exact_name|fuzzy|embedding
    score: float = 0.0
    candidates: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class FinancialTotals:
    gross_amount: float = 0.0
    discount: float = 0.0
    tax: float = 0.0
    advance_tax: float = 0.0
    net_amount: float = 0.0
    grand_total: float = 0.0
    # Printed / OCR-claimed values (never trusted)
    claimed_gross: float = 0.0
    claimed_discount: float = 0.0
    claimed_tax: float = 0.0
    claimed_advance_tax: float = 0.0
    claimed_net: float = 0.0
    claimed_grand_total: float = 0.0


@dataclass
class ValidationMessage:
    code: str
    severity: str  # error | warning | info
    message: str
    field: str = ""
    expected: Any = None
    actual: Any = None
    product_index: Optional[int] = None


@dataclass
class StageTrace:
    stage_id: int
    name: str
    ok: bool = True
    detail: str = ""
    duration_ms: float = 0.0


@dataclass
class SupplierHint:
    name: str = ""
    tax_id: str = ""
    invoice_no: str = ""
    invoice_date: str = ""
    address: str = ""
    confidence: float = 0.0
    supplier_id: Optional[int] = None
    candidates: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class PipelineContext:
    """Mutable context passed through every stage."""

    file_bytes: bytes = b""
    mime_type: str = ""
    images: List[Any] = field(default_factory=list)

    document_class: DocumentClass = DocumentClass.UNKNOWN
    document_class_score: float = 0.0

    supplier: SupplierHint = field(default_factory=SupplierHint)

    layout_regions: List[LayoutRegion] = field(default_factory=list)
    tables: List[TableBlock] = field(default_factory=list)

    printed_spans: List[TextSpan] = field(default_factory=list)
    handwritten_spans: List[TextSpan] = field(default_factory=list)
    ocr_text: str = ""
    ocr_engines: List[str] = field(default_factory=list)

    products: List[StructuredProduct] = field(default_factory=list)
    matches: List[ProductMatch] = field(default_factory=list)

    financials: FinancialTotals = field(default_factory=FinancialTotals)
    validations: List[ValidationMessage] = field(default_factory=list)
    field_confidences: List[FieldConfidence] = field(default_factory=list)

    learning_applied: List[str] = field(default_factory=list)
    learning_pending: List[Dict[str, Any]] = field(default_factory=list)

    warnings: List[str] = field(default_factory=list)
    stage_trace: List[StageTrace] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)

    # Optional DB session / learning store injected by orchestrator
    db: Any = None
    learning_store: Any = None
    username: str = ""


@dataclass
class PipelineResult:
    ctx: PipelineContext
    model_label: str = "purchase-pipeline"


# Confidence thresholds — fields below CONFIRM_THRESHOLD require user confirmation
CONFIRM_THRESHOLD = 0.72
HIGH_THRESHOLD = 0.90
MEDIUM_THRESHOLD = 0.72
LOW_THRESHOLD = 0.45
TOLERANCE_MONEY = 0.05  # Rs tolerance for recalculated vs claimed
