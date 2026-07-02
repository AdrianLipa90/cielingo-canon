"""Semantic scar model.

A scar is a preserved trace of unresolved or damaging semantic dynamics:
missing source, contradiction, unresolved word, false closure, etc.
It is not automatically memory writeback.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

from .contracts import SourceBindingType


class ScarType(str, Enum):
    CONTRADICTION = "contradiction"
    MISSING_SOURCE = "missing_source"
    UNRESOLVED_WORD = "unresolved_word"
    TRANSLATION_RESIDUE = "translation_residue"
    CONSENT_PRESSURE = "consent_pressure"
    FALSE_CLOSURE = "false_closure"
    AFFECTIVE_SHIFT = "affective_shift"
    CANON_PROMOTION_ATTEMPT = "canon_promotion_attempt"
    SOURCE_CONFUSION = "source_confusion"


def _bounded01(v: float) -> bool:
    return 0.0 <= float(v) <= 1.0


@dataclass
class SemanticScar:
    scar_id: str
    scar_type: ScarType
    source_equation_id: str
    severity: float
    memory_effect: str = "candidate"
    repair_hint: str = ""
    source_binding: SourceBindingType = SourceBindingType.ARTIFACT_GROUNDED
    evidence: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.scar_id:
            issues.append("scar_id is required")
        if not self.source_equation_id:
            issues.append("source_equation_id is required")
        if not _bounded01(self.severity):
            issues.append("severity must be in [0, 1]")
        if self.source_binding == SourceBindingType.SOURCE and not self.evidence:
            issues.append("SOURCE scar requires evidence")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
