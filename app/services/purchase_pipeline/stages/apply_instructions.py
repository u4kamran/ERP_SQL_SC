"""Apply saved fetch instructions after structured extract (replaceable stage)."""

from __future__ import annotations

from app.services.purchase_pipeline.base import BaseStage
from app.services.purchase_pipeline.fetch_instructions import apply_fetch_instructions
from app.services.purchase_pipeline.types import PipelineContext


class ApplyFetchInstructionsStage(BaseStage):
    stage_id = 14
    name = "apply_fetch_instructions"

    def run(self, ctx: PipelineContext) -> PipelineContext:
        # Always run — merges built-in priority rules even if textbox empty
        return apply_fetch_instructions(ctx)
