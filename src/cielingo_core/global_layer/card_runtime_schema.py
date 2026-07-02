"""CIELingo card runtime schema v0.3.

This module defines additive runtime/operator extensions for cards.

It does not replace lexical slots or language-local cards. It adds the
fields needed by GLOBAL v0.2/v0.3:
- operator bindings,
- semantic mass,
- affective charge,
- consent/memory/risk effects,
- residue profile,
- NOEMA holonomic marker.

No card is SOURCE or canon by default.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

from .contracts import SourceBindingType
from .operator_algebra import DEFAULT_OPERATORS
from .residue_taxonomy import ResidueType


class CardOntologyClass(str, Enum):
    KOTO = "koto"
    MONO = "mono"
    UNRESOLVED = "unresolved"


class CardValidationStatus(str, Enum):
    DRAFT = "draft"
    VALIDATED = "validated"
    QUARANTINED = "quarantined"
    REJECTED = "rejected"
    NEEDS_REVIEW = "needs_review"


class ConsentEffect(str, Enum):
    NONE = "none"
    REQUIRES_CONSENT = "requires_consent"
    BLOCKS_ACTION = "blocks_action"
    PAUSE = "pause"


class MemoryEffect(str, Enum):
    NONE = "none"
    CANDIDATE = "candidate"
    EPISODIC_CANDIDATE = "episodic_candidate"
    SCAR_CANDIDATE = "scar_candidate"
    REPAIR_REQUIRED = "repair_required"


def _bounded01(v: float) -> bool:
    return 0.0 <= float(v) <= 1.0


@dataclass
class RiskProfile:
    semantic_risk: float = 0.0
    hallucination_risk: float = 0.0
    consent_pressure: float = 0.0
    source_confusion_risk: float = 0.0
    canon_promotion_risk: float = 0.0

    def validate(self) -> list[str]:
        issues: list[str] = []
        for name, value in asdict(self).items():
            if not _bounded01(value):
                issues.append(f"risk_profile.{name} must be in [0, 1]")
        return issues


@dataclass
class ResidueProfile:
    expected_residue_types: list[ResidueType] = field(default_factory=list)
    default_residue_weight: float = 0.0
    notes: list[str] = field(default_factory=list)

    def validate(self) -> list[str]:
        if not _bounded01(self.default_residue_weight):
            return ["residue_profile.default_residue_weight must be in [0, 1]"]
        return []


@dataclass
class NoemaHolonomicMarker:
    """Public-safe NOEMA holonomic marker.

    This is a marker/commitment object, not a NOEMA writeback and not SOURCE.
    """

    marker_id: str
    marker_schema: str = "NOEMA_HOLONOMIC_MARKER/0.3"
    source_binding: SourceBindingType = SourceBindingType.ARTIFACT_GROUNDED
    semantic_phase: float = 0.0
    affective_phase: float = 0.0
    consent_phase: float = 0.0
    memory_phase: float = 0.0
    residue_phase: float = 0.0
    operator_phase: float = 0.0
    stable_fingerprint: str | None = None
    noema_writeback_required: bool = False
    noema_current_update_allowed: bool = False
    notes: list[str] = field(default_factory=list)

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.marker_id:
            issues.append("marker_id is required")
        if self.source_binding == SourceBindingType.SOURCE:
            issues.append("NOEMA marker must not be SOURCE by default")
        for name in (
            "semantic_phase",
            "affective_phase",
            "consent_phase",
            "memory_phase",
            "residue_phase",
            "operator_phase",
        ):
            if not _bounded01(getattr(self, name)):
                issues.append(f"{name} must be in [0, 1]")
        if self.noema_current_update_allowed:
            issues.append("NOEMA CURRENT update is not allowed from card marker")
        return issues


@dataclass
class RuntimeCardExtension:
    operator_bindings: list[str] = field(default_factory=list)
    semantic_mass: float = 0.0
    affective_charge: float = 0.0
    consent_effect: ConsentEffect = ConsentEffect.NONE
    memory_effect: MemoryEffect = MemoryEffect.NONE
    risk_profile: RiskProfile = field(default_factory=RiskProfile)
    residue_profile: ResidueProfile = field(default_factory=ResidueProfile)
    noema_holonomic_marker: NoemaHolonomicMarker | None = None

    def validate(self) -> list[str]:
        issues: list[str] = []
        for op in self.operator_bindings:
            if op not in DEFAULT_OPERATORS:
                issues.append(f"unknown operator binding: {op}")
        if not _bounded01(self.semantic_mass):
            issues.append("semantic_mass must be in [0, 1]")
        if not _bounded01(abs(self.affective_charge)):
            issues.append("abs(affective_charge) must be in [0, 1]")
        issues.extend(self.risk_profile.validate())
        issues.extend(self.residue_profile.validate())
        if self.noema_holonomic_marker is not None:
            issues.extend(self.noema_holonomic_marker.validate())
        return issues


@dataclass
class CielingoRuntimeCard:
    card_id: str
    slot_id: int
    language_id: str
    lemma: str | None
    surface_forms: list[str]
    ontology_class: CardOntologyClass = CardOntologyClass.UNRESOLVED
    function: str = ""
    validation_status: CardValidationStatus = CardValidationStatus.DRAFT
    source_binding: SourceBindingType = SourceBindingType.ARTIFACT_GROUNDED
    canon_allowed: bool = False
    runtime: RuntimeCardExtension = field(default_factory=RuntimeCardExtension)
    notes: list[str] = field(default_factory=list)

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.card_id:
            issues.append("card_id is required")
        if self.slot_id <= 0:
            issues.append("slot_id must be positive")
        if not self.language_id:
            issues.append("language_id is required")
        if self.source_binding == SourceBindingType.SOURCE:
            issues.append("card must not default to SOURCE")
        if self.canon_allowed:
            issues.append("card must not allow canon by default")
        if self.ontology_class != CardOntologyClass.UNRESOLVED and not self.lemma:
            issues.append("resolved card requires lemma")
        if self.lemma and self.lemma not in self.surface_forms:
            issues.append("lemma should be included in surface_forms")
        issues.extend(self.runtime.validate())
        return issues

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
