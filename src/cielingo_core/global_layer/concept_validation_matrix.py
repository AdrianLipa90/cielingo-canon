"""GLOBAL 0.5C concept validation matrix scaffold."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


class ValidationStatus(str, Enum):
    PASS_ = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    BLOCK = "BLOCK"


REQUIRED_RELATIONS = [
    "MeaningEquation -> MeaningAction",
    "MeaningAction -> MeaningBlockAction",
    "MeaningBlockAction -> SemanticScar",
    "SemanticScar -> MeaningLoop",
    "SemanticScar -> NOEMA",
    "CardRuntimeExtension -> OperatorAlgebra",
    "CardRuntimeExtension -> LanguageSpace",
    "NoemaHolonomicMarker -> NOEMA SoT",
    "FileSense -> Cards",
    "FileSense -> GLOBAL",
    "FileSense -> SOURCE/canon",
    "GLOBAL -> REGIONAL",
    "GLOBAL -> ApocalypOS",
    "GLOBAL -> NOEMA",
    "IntentionFrame -> MeaningAction",
    "JDecomposition -> HolonomicJReport",
]


@dataclass
class ConceptValidationRow:
    relation: str
    status: ValidationStatus
    boundary: str
    test_required: bool = True
    build_allowed_if_fail: bool = False
    notes: list[str] | None = None

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.relation:
            issues.append("relation is required")
        if not self.boundary:
            issues.append("boundary is required")
        if self.status in {ValidationStatus.FAIL, ValidationStatus.BLOCK} and self.build_allowed_if_fail:
            issues.append("build_allowed_if_fail must be false for FAIL/BLOCK")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ConceptValidationMatrix:
    rows: list[ConceptValidationRow]

    def validate(self) -> list[str]:
        issues: list[str] = []
        present = {row.relation for row in self.rows}
        for rel in REQUIRED_RELATIONS:
            if rel not in present:
                issues.append(f"missing required relation: {rel}")
        for row in self.rows:
            issues.extend(row.validate())
        return issues

    @property
    def build_allowed(self) -> bool:
        return not any(row.status in {ValidationStatus.FAIL, ValidationStatus.BLOCK} for row in self.rows)

    def to_dict(self) -> dict[str, Any]:
        return {"rows": [row.to_dict() for row in self.rows], "build_allowed": self.build_allowed}


def default_concept_validation_matrix() -> ConceptValidationMatrix:
    rows = []
    for rel in REQUIRED_RELATIONS:
        if rel in {"FileSense -> SOURCE/canon", "NoemaHolonomicMarker -> NOEMA SoT"}:
            status = ValidationStatus.BLOCK
            boundary = "Must remain blocked unless external SOURCE/NOEMA evidence exists."
        elif "NOEMA" in rel or "FileSense" in rel:
            status = ValidationStatus.WARN
            boundary = "Boundary-sensitive relation; no writeback/promotion by default."
        else:
            status = ValidationStatus.PASS_
            boundary = "Compatible under current scaffold constraints."
        rows.append(ConceptValidationRow(relation=rel, status=status, boundary=boundary))
    return ConceptValidationMatrix(rows=rows)
