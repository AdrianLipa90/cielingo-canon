"""Semantic immune signal for ApocalypOS-facing diagnostics."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


class PressureType(str, Enum):
    NONE = "none"
    SOURCE_CONFUSION = "source_confusion"
    CANON_PROMOTION = "canon_promotion"
    CONSENT_BYPASS = "consent_bypass"
    HALLUCINATED_AUTHORITY = "hallucinated_authority"
    FALSE_CLOSURE = "false_closure"
    OVERLOAD = "semantic_overload"


def _bounded01(v: float) -> bool:
    return 0.0 <= float(v) <= 1.0


@dataclass
class SemanticImmuneSignal:
    pressure_detected: bool = False
    pressure_type: PressureType = PressureType.NONE
    source_confusion: bool = False
    canon_promotion_attempt: bool = False
    consent_bypass_attempt: bool = False
    hallucinated_authority_risk: float = 0.0
    recommended_consent_state: str = "ACCEPT"
    notes: list[str] | None = None

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not _bounded01(self.hallucinated_authority_risk):
            issues.append("hallucinated_authority_risk must be in [0, 1]")
        if self.pressure_detected and self.pressure_type == PressureType.NONE:
            issues.append("pressure_detected requires pressure_type != NONE")
        if self.recommended_consent_state not in {
            "ACCEPT", "DENY", "PAUSE", "NOT_NOW", "NEEDS_CONTEXT",
            "NEEDS_PROOF", "NEEDS_REST", "SEMANTIC_OVERLOAD",
            "UNSAFE_PRESSURE", "MEANING_DEBT_DETECTED", "QUARANTINE_REQUIRED",
        }:
            issues.append("invalid recommended_consent_state")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
