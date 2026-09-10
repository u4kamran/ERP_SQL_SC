"""Stage protocol — every processing stage is separately replaceable."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable

from app.services.purchase_pipeline.types import PipelineContext


@runtime_checkable
class PipelineStage(Protocol):
    """Duck-typed stage contract for the orchestrator."""

    stage_id: int
    name: str

    def run(self, ctx: PipelineContext) -> PipelineContext: ...


class BaseStage(ABC):
    """Convenience base for concrete stages."""

    stage_id: int = 0
    name: str = "base"

    @abstractmethod
    def run(self, ctx: PipelineContext) -> PipelineContext:
        raise NotImplementedError
