"""Modular multi-stage purchase invoice analysis pipeline.

Stages are independently replaceable and unit-testable.
Never trust OCR or printed totals — validate and score everything.
"""

from app.services.purchase_pipeline.orchestrator import PurchaseDocumentPipeline
from app.services.purchase_pipeline.types import PipelineContext, PipelineResult

__all__ = ["PurchaseDocumentPipeline", "PipelineContext", "PipelineResult"]
