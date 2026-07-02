from __future__ import annotations
from dataclasses import asdict, dataclass, field
from typing import Any
from cielingo_core.global_layer.contracts import SurfaceSolution

@dataclass
class SurfaceSegments:
    language_id: str
    text: str
    tokens: list[str]
    notes: list[str] = field(default_factory=list)
    def validate(self) -> list[str]:
        issues = []
        if not self.language_id: issues.append("language_id is required")
        if not isinstance(self.tokens, list): issues.append("tokens must be a list")
        return issues
    def to_dict(self) -> dict[str, Any]: return asdict(self)

@dataclass
class CardCandidate:
    card_id: str
    slot_id: int
    language_id: str
    lemma: str | None
    token_indices: list[int]
    operator_bindings: list[str] = field(default_factory=list)
    score: float = 0.0
    needs_native_review: bool = False
    def validate(self) -> list[str]:
        issues = []
        if not self.card_id: issues.append("card_id is required")
        if self.slot_id <= 0: issues.append("slot_id must be positive")
        if not self.token_indices: issues.append("candidate must point to at least one token")
        if not 0 <= self.score <= 1: issues.append("score must be in [0,1]")
        return issues
    def to_dict(self) -> dict[str, Any]: return asdict(self)

@dataclass
class RegionalSolveResult:
    language_id: str
    text: str
    segments: SurfaceSegments
    candidates: list[CardCandidate]
    surface_solution: SurfaceSolution
    no_source_promotion: bool = True
    no_canon_promotion: bool = True
    no_noema_writeback: bool = True
    current_update_performed: bool = False
    notes: list[str] = field(default_factory=list)
    def validate(self) -> list[str]:
        issues = []
        issues.extend(self.segments.validate())
        for c in self.candidates: issues.extend(c.validate())
        issues.extend(self.surface_solution.validate())
        if not self.no_source_promotion: issues.append("regional solver must not promote SOURCE")
        if not self.no_canon_promotion: issues.append("regional solver must not promote canon")
        if not self.no_noema_writeback: issues.append("regional solver must not write NOEMA")
        if self.current_update_performed: issues.append("regional solver must not update CURRENT")
        return issues
    def to_dict(self) -> dict[str, Any]: return asdict(self)
