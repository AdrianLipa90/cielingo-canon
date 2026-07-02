"""Residue taxonomy for CIELingo GLOBAL v0.2."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


class ResidueType(str, Enum):
    TRANSLATION = "translation_residue"
    IDIOM = "idiom_residue"
    SYMBOLIC = "symbolic_residue"
    AFFECTIVE = "affective_residue"
    SOURCE = "source_residue"
    CONSENT = "consent_residue"
    LOOP = "loop_residue"
    SCAR = "scar_residue"
    COLLAPSE = "collapse_residue"
    REGIONAL = "regional_residue"
    UNRESOLVED = "unresolved_residue"
    SCOPE = "scope_residue"
    OPERATOR = "operator_residue"


def _bounded01(v: float) -> bool:
    return 0.0 <= float(v) <= 1.0


@dataclass
class TypedResidue:
    residue_id: str
    residue_type: ResidueType
    description: str
    j_weight: float
    source_language: str | None = None
    target_language: str | None = None
    slot_id: int | None = None
    operator_id: str | None = None
    requires_review: bool = False
    notes: list[str] | None = None

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.residue_id:
            issues.append("residue_id is required")
        if not self.description:
            issues.append("description is required")
        if not _bounded01(self.j_weight):
            issues.append("j_weight must be in [0, 1]")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
