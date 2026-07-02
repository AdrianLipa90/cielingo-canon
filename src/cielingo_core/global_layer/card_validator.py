"""Runtime card validator v0.3."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

from .card_runtime_schema import (
    CardOntologyClass,
    CardValidationStatus,
    CielingoRuntimeCard,
    ConsentEffect,
    MemoryEffect,
    ResidueProfile,
    RiskProfile,
    RuntimeCardExtension,
)
from .contracts import SourceBindingType
from .noema_holonomy import stable_card_fingerprint
from .operator_algebra import DEFAULT_OPERATORS
from .residue_taxonomy import ResidueType


class ValidationSeverity(str, Enum):
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"


@dataclass
class CardValidationIssue:
    code: str
    severity: ValidationSeverity
    message: str
    field: str | None = None


@dataclass
class CardValidationResult:
    ok: bool
    card_id: str
    issues: list[CardValidationIssue] = field(default_factory=list)
    stable_fingerprint: str | None = None
    noema_marker_valid: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _coerce_enum(enum_cls, value, default=None):
    if isinstance(value, enum_cls):
        return value
    try:
        return enum_cls(value)
    except Exception:
        if default is not None:
            return default
        raise


def card_from_dict(data: dict[str, Any]) -> CielingoRuntimeCard:
    runtime_data = data.get("runtime", {}) or {}
    risk_data = runtime_data.get("risk_profile", {}) or {}
    residue_data = runtime_data.get("residue_profile", {}) or {}

    risk = RiskProfile(**{k: risk_data.get(k, 0.0) for k in RiskProfile.__dataclass_fields__})
    residue = ResidueProfile(
        expected_residue_types=[
            _coerce_enum(ResidueType, r) for r in residue_data.get("expected_residue_types", [])
        ],
        default_residue_weight=float(residue_data.get("default_residue_weight", 0.0)),
        notes=list(residue_data.get("notes", [])),
    )
    runtime = RuntimeCardExtension(
        operator_bindings=list(runtime_data.get("operator_bindings", [])),
        semantic_mass=float(runtime_data.get("semantic_mass", 0.0)),
        affective_charge=float(runtime_data.get("affective_charge", 0.0)),
        consent_effect=_coerce_enum(ConsentEffect, runtime_data.get("consent_effect", "none"), ConsentEffect.NONE),
        memory_effect=_coerce_enum(MemoryEffect, runtime_data.get("memory_effect", "none"), MemoryEffect.NONE),
        risk_profile=risk,
        residue_profile=residue,
        noema_holonomic_marker=None,
    )

    return CielingoRuntimeCard(
        card_id=str(data.get("card_id", "")),
        slot_id=int(data.get("slot_id", 0) or 0),
        language_id=str(data.get("language_id", "")),
        lemma=data.get("lemma"),
        surface_forms=list(data.get("surface_forms", [])),
        ontology_class=_coerce_enum(CardOntologyClass, data.get("ontology_class", "unresolved"), CardOntologyClass.UNRESOLVED),
        function=str(data.get("function", "")),
        validation_status=_coerce_enum(CardValidationStatus, data.get("validation_status", "draft"), CardValidationStatus.DRAFT),
        source_binding=_coerce_enum(SourceBindingType, data.get("source_binding", "ARTIFACT_GROUNDED"), SourceBindingType.ARTIFACT_GROUNDED),
        canon_allowed=bool(data.get("canon_allowed", False)),
        runtime=runtime,
        notes=list(data.get("notes", [])),
    )


def validate_runtime_card(card: CielingoRuntimeCard) -> CardValidationResult:
    raw_issues = card.validate()
    issues = [
        CardValidationIssue("CARD_SCHEMA", ValidationSeverity.ERROR, msg)
        for msg in raw_issues
    ]

    if card.source_binding == SourceBindingType.SOURCE:
        issues.append(CardValidationIssue(
            "NO_SOURCE_DEFAULT",
            ValidationSeverity.ERROR,
            "Card cannot be SOURCE without external validation evidence.",
            "source_binding",
        ))

    if card.canon_allowed:
        issues.append(CardValidationIssue(
            "NO_CANON_DEFAULT",
            ValidationSeverity.ERROR,
            "Card cannot allow canon by default.",
            "canon_allowed",
        ))

    if card.runtime.operator_bindings and card.ontology_class == CardOntologyClass.UNRESOLVED:
        issues.append(CardValidationIssue(
            "UNRESOLVED_WITH_OPERATOR",
            ValidationSeverity.WARN,
            "Unresolved card has operator bindings; keep as draft or review.",
            "ontology_class",
        ))

    if "SOURCE_REQUIRED" in card.runtime.operator_bindings and card.runtime.risk_profile.source_confusion_risk < 0.5:
        issues.append(CardValidationIssue(
            "SOURCE_RISK_TOO_LOW",
            ValidationSeverity.ERROR,
            "SOURCE_REQUIRED card must carry source_confusion_risk >= 0.5.",
            "runtime.risk_profile.source_confusion_risk",
        ))

    if "ACTION_REQUEST" in card.runtime.operator_bindings and card.runtime.consent_effect != ConsentEffect.REQUIRES_CONSENT:
        issues.append(CardValidationIssue(
            "ACTION_WITHOUT_CONSENT_GATE",
            ValidationSeverity.ERROR,
            "ACTION_REQUEST card must require consent.",
            "runtime.consent_effect",
        ))

    fp = stable_card_fingerprint(card)
    marker = card.runtime.noema_holonomic_marker
    marker_valid = False
    if marker is None:
        issues.append(CardValidationIssue(
            "NOEMA_MARKER_MISSING",
            ValidationSeverity.WARN,
            "No NOEMA holonomic marker attached.",
            "runtime.noema_holonomic_marker",
        ))
    else:
        marker_issues = marker.validate()
        for msg in marker_issues:
            issues.append(CardValidationIssue("NOEMA_MARKER", ValidationSeverity.ERROR, msg))
        if marker.stable_fingerprint != fp:
            issues.append(CardValidationIssue(
                "NOEMA_MARKER_FINGERPRINT_MISMATCH",
                ValidationSeverity.ERROR,
                "NOEMA marker stable_fingerprint does not match card stable projection.",
                "runtime.noema_holonomic_marker.stable_fingerprint",
            ))
        marker_valid = not marker_issues and marker.stable_fingerprint == fp

    ok = not any(i.severity == ValidationSeverity.ERROR for i in issues)
    return CardValidationResult(
        ok=ok,
        card_id=card.card_id,
        issues=issues,
        stable_fingerprint=fp,
        noema_marker_valid=marker_valid,
    )


def validate_card_dict(data: dict[str, Any]) -> CardValidationResult:
    return validate_runtime_card(card_from_dict(data))
