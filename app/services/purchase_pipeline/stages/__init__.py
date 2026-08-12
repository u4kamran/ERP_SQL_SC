"""Stage package exports."""

from app.services.purchase_pipeline.stages.apply_instructions import ApplyFetchInstructionsStage
from app.services.purchase_pipeline.stages.associate_handwriting import AssociateHandwritingStage
from app.services.purchase_pipeline.stages.classify import ClassifyDocumentStage
from app.services.purchase_pipeline.stages.confidence import ConfidenceScoringStage
from app.services.purchase_pipeline.stages.identify_supplier import IdentifySupplierStage
from app.services.purchase_pipeline.stages.layout import AnalyzeLayoutStage
from app.services.purchase_pipeline.stages.learn import LearnFromCorrectionsStage
from app.services.purchase_pipeline.stages.match_products import MatchProductsStage
from app.services.purchase_pipeline.stages.ocr_handwritten import DetectHandwrittenStage
from app.services.purchase_pipeline.stages.ocr_printed import ExtractPrintedOcrStage
from app.services.purchase_pipeline.stages.recalculate import RecalculateFinancialsStage
from app.services.purchase_pipeline.stages.structure_json import StructureProductsStage
from app.services.purchase_pipeline.stages.tables import DetectTablesStage
from app.services.purchase_pipeline.stages.validation_messages import ValidationMessagesStage

DEFAULT_STAGES = [
    # Stage IDs stay as specified; run order ensures OCR spans exist for layout/tables.
    ClassifyDocumentStage(),            # 1
    ExtractPrintedOcrStage(),           # 5 (split printed early)
    DetectHandwrittenStage(),           # 6
    AnalyzeLayoutStage(),               # 3
    DetectTablesStage(),                # 4
    IdentifySupplierStage(),            # 2 (after text available)
    AssociateHandwritingStage(),        # 7
    StructureProductsStage(),           # 8
    ApplyFetchInstructionsStage(),      # follow operator fetch instructions (saved)
    MatchProductsStage(),               # 9
    RecalculateFinancialsStage(),       # 10
    ValidationMessagesStage(),          # 11
    ConfidenceScoringStage(),           # 12
    LearnFromCorrectionsStage(),        # 13
]

__all__ = [
    "DEFAULT_STAGES",
    "ClassifyDocumentStage",
    "IdentifySupplierStage",
    "AnalyzeLayoutStage",
    "DetectTablesStage",
    "ExtractPrintedOcrStage",
    "DetectHandwrittenStage",
    "AssociateHandwritingStage",
    "StructureProductsStage",
    "ApplyFetchInstructionsStage",
    "MatchProductsStage",
    "RecalculateFinancialsStage",
    "ValidationMessagesStage",
    "ConfidenceScoringStage",
    "LearnFromCorrectionsStage",
]
