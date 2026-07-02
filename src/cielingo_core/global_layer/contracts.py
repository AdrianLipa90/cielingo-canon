"""CIELingo clean-container contracts.

This file defines the isolated Stage 0 ABI. It deliberately avoids importing
ApocalypOS, NOEMA, previous CIELingo modules, or language-specific solvers.

GLOBAL = algebra of slots, relations, equations, projections, residue and J.
REGIONAL = language-local grammar/holonomy, stored under language_spaces/*.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class SourceBindingType(str, Enum):
    SOURCE = "SOURCE"
    ARTIFACT_GROUNDED = "ARTIFACT_GROUNDED"
    PROXY_VERIFIED = "PROXY_VERIFIED"
    HYPOTHESIS = "HYPOTHESIS"
    SIMULATION = "SIMULATION"
    INTERPRETATION = "INTERPRETATION"
    POETIC_SYMBOLIC = "POETIC_SYMBOLIC"
    UNKNOWN = "UNKNOWN"


class EntryStatus(str, Enum):
    PRESENT = "present"
    CANDIDATE = "candidate"
    DRAFT = "draft"
    IN_BLANCO_OPEN = "in_blanco_open"
    IN_BLANCO_STABLE = "in_blanco_stable"
    IN_BLANCO_VALIDATED = "in_blanco_validated"
    NEEDS_NATIVE_REVIEW = "needs_native_review"
    FALSE_FRIEND = "false_friend"
    REJECTED = "rejected"


class UniversalRole(str, Enum):
    AGENT = "AGENT"
    PATIENT = "PATIENT"
    THEME = "THEME"
    RECIPIENT = "RECIPIENT"
    INSTRUMENT = "INSTRUMENT"
    SOURCE = "SOURCE"
    GOAL = "GOAL"
    LOCATION = "LOCATION"
    TIME = "TIME"
    CAUSE = "CAUSE"
    PURPOSE = "PURPOSE"
    CONDITION = "CONDITION"
    MANNER = "MANNER"
    EVIDENCE = "EVIDENCE"
    CLAIM = "CLAIM"
    MEMORY_TRACE = "MEMORY_TRACE"
    CONSENT_TARGET = "CONSENT_TARGET"
    BOUNDARY = "BOUNDARY"


class UniversalOperatorType(str, Enum):
    NEGATION = "NEGATION"
    QUESTION = "QUESTION"
    ASSERTION = "ASSERTION"
    CONDITION = "CONDITION"
    CAUSE = "CAUSE"
    MODAL_POSSIBILITY = "MODAL_POSSIBILITY"
    MODAL_NECESSITY = "MODAL_NECESSITY"
    MODAL_PERMISSION = "MODAL_PERMISSION"
    MODAL_OBLIGATION = "MODAL_OBLIGATION"
    UNCERTAINTY = "UNCERTAINTY"
    SOURCE_REQUIRED = "SOURCE_REQUIRED"
    CANON_BLOCK = "CANON_BLOCK"
    CONSENT_REQUIRED = "CONSENT_REQUIRED"
    ACTION_REQUEST = "ACTION_REQUEST"
    REFUSAL = "REFUSAL"
    PAUSE = "PAUSE"
    SIMULATION_BOUNDARY = "SIMULATION_BOUNDARY"


def _bounded01(value: float) -> bool:
    return 0.0 <= float(value) <= 1.0


@dataclass
class LexicalSlot:
    slot_id: int
    slot_key: str
    universal_anchor: str | None
    primitive_family: list[str]
    gloss: str
    created_from_language: str | None = None
    created_from_surface: str | None = None
    status: str = "open"
    source_binding: SourceBindingType = SourceBindingType.ARTIFACT_GROUNDED
    canon_allowed: bool = False
    confidence: float = 0.0

    def validate(self) -> list[str]:
        issues: list[str] = []
        if self.slot_id <= 0:
            issues.append("slot_id must be positive")
        if not self.slot_key:
            issues.append("slot_key is required")
        if not self.primitive_family:
            issues.append("primitive_family must be non-empty")
        if self.source_binding == SourceBindingType.SOURCE:
            issues.append("LexicalSlot must not default to SOURCE")
        if self.canon_allowed:
            issues.append("LexicalSlot must not allow canon by default")
        if not _bounded01(self.confidence):
            issues.append("confidence must be in [0, 1]")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class LanguageSlotEntry:
    slot_id: int
    language_id: str
    entry_id: str
    lemma: str | None
    surface_forms: list[str]
    pos: str | None
    status: EntryStatus = EntryStatus.DRAFT
    local_j: dict[str, float] = field(default_factory=dict)
    grammar_hints: dict[str, Any] = field(default_factory=dict)
    residue: dict[str, Any] = field(default_factory=dict)
    needs_native_review: bool = False
    source_binding: SourceBindingType = SourceBindingType.ARTIFACT_GROUNDED
    canon_allowed: bool = False
    confidence: float = 0.0

    def validate(self) -> list[str]:
        issues: list[str] = []
        if self.slot_id <= 0:
            issues.append("slot_id must be positive")
        if not self.language_id:
            issues.append("language_id is required")
        if not self.entry_id:
            issues.append("entry_id is required")
        if self.status.name.startswith("IN_BLANCO"):
            if self.lemma is not None or self.surface_forms:
                issues.append("in_blanco entry must not force lemma or surface_forms")
        else:
            if not self.lemma:
                issues.append("non-blank entry requires lemma")
            if not self.surface_forms:
                issues.append("non-blank entry requires surface_forms")
        if self.source_binding == SourceBindingType.SOURCE:
            issues.append("LanguageSlotEntry must not default to SOURCE")
        if self.canon_allowed:
            issues.append("LanguageSlotEntry must not allow canon by default")
        if not _bounded01(self.confidence):
            issues.append("confidence must be in [0, 1]")
        for key, value in self.local_j.items():
            if not _bounded01(value):
                issues.append(f"local_j {key} must be in [0, 1]")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class UniversalOperator:
    operator_type: UniversalOperatorType
    scope: list[str] = field(default_factory=list)
    strength: float = 1.0
    source_binding_effect: str | None = None
    canon_effect: str | None = None
    consent_effect: str | None = None

    def validate(self) -> list[str]:
        return [] if _bounded01(self.strength) else ["operator strength must be in [0, 1]"]


@dataclass
class MeaningEquation:
    equation_id: str
    predicate_slot: int | None
    roles: dict[UniversalRole, int | list[int] | str]
    operators: list[UniversalOperator] = field(default_factory=list)
    pragmatics: dict[str, float] = field(default_factory=dict)
    temporality: dict[str, Any] = field(default_factory=dict)
    modality: dict[str, Any] = field(default_factory=dict)
    source_binding: SourceBindingType = SourceBindingType.HYPOTHESIS
    canon_allowed: bool = False

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.equation_id:
            issues.append("equation_id is required")
        if self.canon_allowed:
            issues.append("MeaningEquation must not allow canon by default")
        if self.source_binding == SourceBindingType.SOURCE:
            issues.append("MeaningEquation must not default to SOURCE")
        for key, value in self.pragmatics.items():
            if not _bounded01(value):
                issues.append(f"pragmatics {key} must be in [0, 1]")
        for operator in self.operators:
            issues.extend(operator.validate())
        return issues

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SlotProjection:
    slot_id: int
    token_indices: list[int]
    projection_type: str
    grammatical_attachments: list[str] = field(default_factory=list)
    confidence: float = 0.0

    def validate(self) -> list[str]:
        issues: list[str] = []
        if self.slot_id <= 0:
            issues.append("slot_id must be positive")
        if not _bounded01(self.confidence):
            issues.append("confidence must be in [0, 1]")
        return issues


@dataclass
class AlignmentResidue:
    residue_type: str
    description: str
    j_weight: float
    source_language: str | None = None
    target_language: str | None = None
    slot_id: int | None = None
    requires_review: bool = False

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.residue_type:
            issues.append("residue_type is required")
        if not _bounded01(self.j_weight):
            issues.append("j_weight must be in [0, 1]")
        return issues


@dataclass
class SurfaceSolution:
    language_id: str
    equation_id: str
    tokens: list[str]
    slot_projection: dict[int, list[int]]
    operator_projection: dict[str, list[int]] = field(default_factory=dict)
    residuals: list[AlignmentResidue] = field(default_factory=list)
    local_j: dict[str, float] = field(default_factory=dict)
    confidence: float = 0.0

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.language_id:
            issues.append("language_id is required")
        if not self.equation_id:
            issues.append("equation_id is required")
        if not _bounded01(self.confidence):
            issues.append("confidence must be in [0, 1]")
        for key, value in self.local_j.items():
            if not _bounded01(value):
                issues.append(f"local_j {key} must be in [0, 1]")
        for residue in self.residuals:
            issues.extend(residue.validate())
        return issues


@dataclass
class HolonomicJReport:
    J_global_structure: float = 0.0
    J_slot_alignment: float = 0.0
    J_residue: float = 0.0
    J_source: float = 0.0
    J_canon: float = 0.0
    J_consent: float = 0.0
    J_surface: float = 0.0
    local_components: dict[str, dict[str, float]] = field(default_factory=dict)

    @property
    def J_total(self) -> float:
        return round(
            self.J_global_structure
            + self.J_slot_alignment
            + self.J_residue
            + self.J_source
            + self.J_canon
            + self.J_consent
            + self.J_surface,
            6,
        )

    def validate(self) -> list[str]:
        issues: list[str] = []
        for name in (
            "J_global_structure",
            "J_slot_alignment",
            "J_residue",
            "J_source",
            "J_canon",
            "J_consent",
            "J_surface",
        ):
            if not _bounded01(getattr(self, name)):
                issues.append(f"{name} must be in [0, 1]")
        for lang, comps in self.local_components.items():
            for key, value in comps.items():
                if not _bounded01(value):
                    issues.append(f"local component {lang}.{key} must be in [0, 1]")
        return issues


@dataclass
class ApocalypOSLinguisticSignal:
    equation_id: str
    J_lingo: float
    source_required: bool
    canon_allowed: bool
    consent_pressure: float
    residue_count: int
    unresolved_slots: list[int] = field(default_factory=list)
    in_blanco_slots: list[int] = field(default_factory=list)
    recommended_mode: str = "standard"
    notes: list[str] = field(default_factory=list)

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not _bounded01(self.J_lingo):
            issues.append("J_lingo must be in [0, 1]")
        if self.canon_allowed:
            issues.append("ApocalypOS signal must not allow canon by default")
        if not _bounded01(self.consent_pressure):
            issues.append("consent_pressure must be in [0, 1]")
        return issues
