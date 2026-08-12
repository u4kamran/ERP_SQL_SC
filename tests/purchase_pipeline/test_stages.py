"""Unit tests for purchase pipeline stages (no OCR / DB required)."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.services.purchase_pipeline.embeddings import SemanticEmbedder, fuzzy_ratio
from app.services.purchase_pipeline.geometry import best_row_for_span, proximity_score
from app.services.purchase_pipeline.learning_store import LearningStore
from app.services.purchase_pipeline.stages.classify import ClassifyDocumentStage
from app.services.purchase_pipeline.stages.confidence import ConfidenceScoringStage
from app.services.purchase_pipeline.stages.ocr_handwritten import DetectHandwrittenStage
from app.services.purchase_pipeline.stages.ocr_printed import ExtractPrintedOcrStage
from app.services.purchase_pipeline.stages.recalculate import RecalculateFinancialsStage
from app.services.purchase_pipeline.stages.structure_json import StructureProductsStage
from app.services.purchase_pipeline.stages.tables import DetectTablesStage
from app.services.purchase_pipeline.stages.validation_messages import ValidationMessagesStage
from app.services.purchase_pipeline.stages.associate_handwriting import AssociateHandwritingStage
from app.services.purchase_pipeline.stages.layout import AnalyzeLayoutStage
from app.services.purchase_pipeline.types import (
    DocumentClass,
    PipelineContext,
    StructuredProduct,
    TableBlock,
    TableRow,
    TextKind,
    TextSpan,
)


def _span(text, conf, *, x=0, y=0, w=40, h=14, page=0, kind=TextKind.UNKNOWN):
    return TextSpan(
        text=text,
        confidence=conf,
        kind=kind,
        page=page,
        bbox=(x, y, x + w, y + h),
        engine="test",
    )


def test_classify_tax_invoice():
    ctx = PipelineContext(ocr_text="TAX INVOICE\nGST No 123\nItem A")
    out = ClassifyDocumentStage().run(ctx)
    assert out.document_class in (DocumentClass.TAX_INVOICE, DocumentClass.PURCHASE_INVOICE)
    assert out.document_class_score >= 0.4


def test_printed_vs_handwritten_split():
    spans = [
        _span("WIDGET PRO 500ML", 0.92, y=100),
        _span("8842", 0.41, y=102, x=400),
        _span("12", 0.88, y=100, x=300),
    ]
    ctx = PipelineContext(meta={"all_spans": spans})
    ctx = ExtractPrintedOcrStage().run(ctx)
    ctx = DetectHandwrittenStage().run(ctx)
    assert any(s.text == "WIDGET PRO 500ML" for s in ctx.printed_spans)
    assert any(s.text == "8842" for s in ctx.handwritten_spans)


def test_layout_and_tables():
    spans = [
        _span("Desc", 0.9, y=40, x=10),
        _span("Qty", 0.9, y=40, x=200),
        _span("Bolt M8", 0.9, y=120, x=10, w=120),
        _span("10", 0.9, y=120, x=200),
        _span("25.50", 0.9, y=120, x=280),
        _span("Washer", 0.9, y=150, x=10, w=120),
        _span("5", 0.9, y=150, x=200),
        _span("3.00", 0.9, y=150, x=280),
    ]
    ctx = PipelineContext(meta={"all_spans": spans}, printed_spans=spans)
    ctx = AnalyzeLayoutStage().run(ctx)
    assert any(r.role == "table" for r in ctx.layout_regions)
    ctx = DetectTablesStage().run(ctx)
    assert ctx.tables
    assert len(ctx.tables[0].rows) >= 1


def test_handwriting_row_association():
    row = TableRow(row_id=1, page=0, bbox=(0, 100, 500, 130), cells=[])
    ctx = PipelineContext(
        tables=[TableBlock(page=0, bbox=(0, 100, 500, 200), rows=[row])],
        handwritten_spans=[_span("9911", 0.4, x=420, y=112, w=30, h=12)],
    )
    out = AssociateHandwritingStage().run(ctx)
    assoc = out.meta["handwriting_associations"]
    assert assoc and assoc[0]["row_id"] == 1
    assert assoc[0]["score"] > 0.35


def test_structure_product_fields():
    cells = [
        _span("ABC-100", 0.9, x=10, y=100, kind=TextKind.PRINTED),
        _span("Steel Rod 12mm", 0.9, x=80, y=100, w=140, kind=TextKind.PRINTED),
        _span("8901234567890", 0.95, x=250, y=100, w=100, kind=TextKind.PRINTED),
        _span("10", 0.9, x=360, y=100, kind=TextKind.PRINTED),
        _span("100.00", 0.9, x=400, y=100, kind=TextKind.PRINTED),
        _span("7744", 0.4, x=480, y=100, kind=TextKind.HANDWRITTEN),
    ]
    row = TableRow(row_id=7, page=0, bbox=(0, 90, 520, 120), cells=cells)
    ctx = PipelineContext(tables=[TableBlock(page=0, bbox=(0, 90, 520, 120), rows=[row])])
    out = StructureProductsStage().run(ctx)
    assert len(out.products) == 1
    p = out.products[0]
    assert p.printed_description
    assert p.barcode == "8901234567890"
    assert p.handwritten_manual_id == "7744"
    assert "quantity" in p.field_scores


def test_recalculate_ignores_printed_totals():
    ctx = PipelineContext(
        ocr_text="Grand Total: 9999.00\nNet Amount: 9999.00",
        products=[
            StructuredProduct(quantity=2, trade_price=50, discount=0, tax=5, net_amount=999),
            StructuredProduct(quantity=1, trade_price=20, discount=0, tax=0, net_amount=999),
        ],
    )
    out = RecalculateFinancialsStage().run(ctx)
    assert out.financials.gross_amount == pytest.approx(120.0)
    assert out.financials.tax == pytest.approx(5.0)
    assert out.financials.claimed_grand_total == pytest.approx(9999.0)
    assert out.financials.grand_total != out.financials.claimed_grand_total


def test_validation_messages_on_mismatch():
    ctx = PipelineContext(
        ocr_text="Grand Total 500.00",
        products=[StructuredProduct(quantity=1, trade_price=100, tax=0, discount=0)],
    )
    ctx = RecalculateFinancialsStage().run(ctx)
    # Force claimed grand via recalc parser already set; add mismatch check
    ctx.financials.claimed_grand_total = 500.0
    ctx.financials.grand_total = 100.0
    out = ValidationMessagesStage().run(ctx)
    assert any(v.code == "GRAND_MISMATCH" for v in out.validations)


def test_confidence_requires_confirmation():
    ctx = PipelineContext(
        document_class=DocumentClass.PURCHASE_INVOICE,
        document_class_score=0.4,
        products=[StructuredProduct(printed_description="X", field_scores={"quantity": 0.3})],
        matches=[],
    )
    from app.services.purchase_pipeline.types import ProductMatch, SupplierHint

    ctx.supplier = SupplierHint(name="ACME", confidence=0.4)
    ctx.matches = [ProductMatch(product_index=0, item_id=None, score=0.2)]
    out = ConfidenceScoringStage().run(ctx)
    assert any(f.requires_confirmation for f in out.field_confidences)


def test_learning_store_roundtrip(tmp_path: Path):
    store = LearningStore(path=tmp_path / "learning.json")
    applied = store.record_correction(
        supplier_key="42",
        item_id=1001,
        alias="Steel Rod 12mm",
        handwritten_manual_id="7744",
        supplier_product_code="ABC-100",
    )
    assert applied
    assert store.lookup_alias(supplier_key="42", text="steel rod 12mm") == 1001.0
    assert store.lookup_manual_id(supplier_key="42", handwritten="7744") == 1001.0
    assert store.lookup_supplier_code(supplier_key="42", code="ABC-100") == 1001.0


def test_geometry_proximity():
    span = _span("1", 0.5, x=10, y=100)
    score = proximity_score(span, (0, 95, 400, 120))
    assert score > 0.5
    hit = best_row_for_span(span, [(1, (0, 95, 400, 120)), (2, (0, 300, 400, 330))])
    assert hit and hit[0] == 1


def test_embeddings_fuzzy():
    assert fuzzy_ratio("Steel Rod 12mm", "steel rod 12 mm") > 0.7
    emb = SemanticEmbedder(["Steel Rod 12mm", "Copper Pipe 1 inch", "Plastic Cap"])
    i, score = emb.best_match("steel rod", [("Steel Rod 12mm", 1), ("Copper Pipe 1 inch", 2)])
    assert i == 0
    assert score > 0.3
