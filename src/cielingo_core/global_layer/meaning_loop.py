"""MeaningLoop model and loop evaluation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

from .semantic_scar import SemanticScar, ScarType


class LoopState(str, Enum):
    OPEN = "open"
    CLOSING = "closing"
    CLOSED = "closed"
    SCARRED = "scarred"
    FAILED = "failed"


def _bounded01(v: float) -> bool:
    return 0.0 <= float(v) <= 1.0


@dataclass
class MeaningLoop:
    loop_id: str
    input_equation_id: str
    response_equation_id: str | None = None
    loop_state: LoopState = LoopState.OPEN
    closure_score: float = 0.0
    contradiction_score: float = 0.0
    return_required: bool = True
    scars: list[SemanticScar] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.loop_id:
            issues.append("loop_id is required")
        if not self.input_equation_id:
            issues.append("input_equation_id is required")
        if not _bounded01(self.closure_score):
            issues.append("closure_score must be in [0, 1]")
        if not _bounded01(self.contradiction_score):
            issues.append("contradiction_score must be in [0, 1]")
        for scar in self.scars:
            issues.extend(scar.validate())
        return issues

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate_loop_state(loop: MeaningLoop) -> LoopState:
    if loop.contradiction_score >= 0.75:
        return LoopState.FAILED
    if loop.scars:
        return LoopState.SCARRED
    if loop.closure_score >= 0.85:
        return LoopState.CLOSED
    if loop.response_equation_id:
        return LoopState.CLOSING
    return LoopState.OPEN


def attach_scar(loop: MeaningLoop, scar: SemanticScar) -> MeaningLoop:
    scars = list(loop.scars) + [scar]
    updated = MeaningLoop(
        loop_id=loop.loop_id,
        input_equation_id=loop.input_equation_id,
        response_equation_id=loop.response_equation_id,
        loop_state=LoopState.SCARRED,
        closure_score=loop.closure_score,
        contradiction_score=loop.contradiction_score,
        return_required=True,
        scars=scars,
        notes=list(loop.notes) + [f"scar_attached:{scar.scar_type.value}"],
    )
    return updated
