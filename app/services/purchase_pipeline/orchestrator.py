"""Purchase document pipeline orchestrator — modular, replaceable stages."""

from __future__ import annotations

import logging
import time
from typing import List, Optional, Sequence

from fastapi import HTTPException, status

from app.services.purchase_ocr_service import PurchaseOcrService
from app.services.purchase_pipeline.base import PipelineStage
from app.services.purchase_pipeline.learning_store import LearningStore
from app.services.purchase_pipeline.stages import DEFAULT_STAGES
from app.services.purchase_pipeline.types import (
    PipelineContext,
    PipelineResult,
    StageTrace,
    TextKind,
    TextSpan,
)

logger = logging.getLogger(__name__)


class PurchaseDocumentPipeline:
    """
    Multi-stage invoice analysis.

    Stages are independently replaceable via the ``stages`` constructor argument.
    A bootstrap OCR pass loads images + raw spans so Stages 1–4 can run without
    trusting any single engine; Stages 5–6 then split printed vs handwritten.
    """

    def __init__(
        self,
        *,
        stages: Optional[Sequence[PipelineStage]] = None,
        ocr_service: Optional[PurchaseOcrService] = None,
        learning_store: Optional[LearningStore] = None,
        db=None,
        username: str = "",
    ):
        self.stages: List[PipelineStage] = list(stages) if stages is not None else list(DEFAULT_STAGES)
        self.ocr = ocr_service or PurchaseOcrService()
        self.learning_store = learning_store or LearningStore()
        self.db = db
        self.username = username

    def run(self, *, file_bytes: bytes, mime_type: str, instructions: str = "") -> PipelineResult:
        ctx = PipelineContext(
            file_bytes=file_bytes,
            mime_type=mime_type,
            db=self.db,
            learning_store=self.learning_store,
            username=self.username,
        )
        # Explicit instructions from this request (already persisted by the service)
        text = (instructions or "").strip()
        if not text and self.learning_store:
            try:
                text = (self.learning_store.get_fetch_instructions() or "").strip()
            except Exception:  # noqa: BLE001
                text = ""
        if text:
            ctx.meta["fetch_instructions"] = text
        self._bootstrap_ocr(ctx)

        for stage in self.stages:
            t0 = time.perf_counter()
            ok = True
            detail = ""
            try:
                ctx = stage.run(ctx)
                detail = f"ok"
            except HTTPException:
                raise
            except Exception as exc:  # noqa: BLE001
                ok = False
                detail = str(exc)[:240]
                logger.exception("Pipeline stage %s failed", stage.name)
                ctx.warnings.append(f"Stage {stage.stage_id} ({stage.name}) failed: {detail}")
            ctx.stage_trace.append(
                StageTrace(
                    stage_id=stage.stage_id,
                    name=stage.name,
                    ok=ok,
                    detail=detail,
                    duration_ms=(time.perf_counter() - t0) * 1000.0,
                )
            )

        engines = "+".join(ctx.ocr_engines) if ctx.ocr_engines else "ocr"
        return PipelineResult(ctx=ctx, model_label=f"pipeline[{engines}]/13-stage")

    def _bootstrap_ocr(self, ctx: PipelineContext) -> None:
        """Infrastructure: load pages and dual-engine OCR into context (not a numbered stage)."""
        t0 = time.perf_counter()
        try:
            result = self.ocr.read(file_bytes=ctx.file_bytes, mime_type=ctx.mime_type)
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"OCR bootstrap failed: {exc}",
            ) from exc

        ctx.images = list(result.images or [])
        ctx.ocr_text = result.text or ""
        ctx.ocr_engines = list(result.engines_used or [])
        ctx.warnings.extend(result.warnings or [])

        spans: List[TextSpan] = []
        for ln in result.lines or []:
            spans.append(
                TextSpan(
                    text=ln.text,
                    confidence=float(ln.confidence or 0.0),
                    kind=TextKind.UNKNOWN,
                    page=int(getattr(ln, "page", 0) or 0),
                    bbox=getattr(ln, "bbox", (ln.x, ln.y, ln.x + max(ln.w, 1), ln.y + max(ln.h, 1))),
                    engine=ln.engine,
                )
            )
        ctx.meta["all_spans"] = spans
        ctx.meta["bootstrap_ms"] = (time.perf_counter() - t0) * 1000.0
        ctx.stage_trace.append(
            StageTrace(
                stage_id=0,
                name="bootstrap_ocr",
                ok=bool(spans),
                detail=f"engines={ctx.ocr_engines} spans={len(spans)}",
                duration_ms=ctx.meta["bootstrap_ms"],
            )
        )
