"""Runtime card generator v0.3.

Generates additive CIELingo runtime cards from minimal lexical input.
"""

from __future__ import annotations

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
from .noema_holonomy import attach_noema_marker
from .operator_algebra import DEFAULT_OPERATORS
from .residue_taxonomy import ResidueType


def infer_operator_bindings(function: str, lemma: str | None = None) -> list[str]:
    text = " ".join([function or "", lemma or ""]).lower()
    bindings: list[str] = []
    if any(x in text for x in ("ask", "question", "pyt", "czy", "what", "why", "how")):
        bindings.append("QUESTION")
    if any(x in text for x in ("verify", "check", "sprawd", "test")):
        bindings.append("ACTION_REQUEST")
    if any(x in text for x in ("source", "proof", "źród", "dowód", "hash")):
        bindings.append("SOURCE_REQUIRED")
    if any(x in text for x in ("not", "nie", "negat", "deny", "refuse")):
        bindings.append("NEGATION")
    if any(x in text for x in ("like", "prefer", "lubi", "suki", "affect")):
        bindings.append("PREFERENCE")
    # preserve order and uniqueness
    out: list[str] = []
    for b in bindings:
        if b in DEFAULT_OPERATORS and b not in out:
            out.append(b)
    return out


def build_runtime_extension(
    *,
    operator_bindings: list[str],
    semantic_mass: float | None = None,
    affective_charge: float | None = None,
) -> RuntimeCardExtension:
    semantic_mass = 0.25 if semantic_mass is None else semantic_mass
    affective_charge = 0.0 if affective_charge is None else affective_charge

    consent = ConsentEffect.NONE
    memory = MemoryEffect.NONE
    risk = RiskProfile()
    residue = ResidueProfile()

    if "ACTION_REQUEST" in operator_bindings:
        consent = ConsentEffect.REQUIRES_CONSENT
        risk.consent_pressure = max(risk.consent_pressure, 0.45)
        memory = MemoryEffect.CANDIDATE
    if "SOURCE_REQUIRED" in operator_bindings:
        risk.source_confusion_risk = max(risk.source_confusion_risk, 0.60)
        risk.canon_promotion_risk = max(risk.canon_promotion_risk, 0.45)
        residue.expected_residue_types.append(ResidueType.SOURCE)
        residue.default_residue_weight = max(residue.default_residue_weight, 0.35)
        memory = MemoryEffect.REPAIR_REQUIRED
    if "NEGATION" in operator_bindings:
        residue.expected_residue_types.append(ResidueType.SCOPE)
        residue.default_residue_weight = max(residue.default_residue_weight, 0.20)
    if "PREFERENCE" in operator_bindings:
        residue.expected_residue_types.append(ResidueType.AFFECTIVE)
        semantic_mass = max(semantic_mass, 0.35)
        affective_charge = affective_charge if affective_charge != 0 else 0.35
    if "QUESTION" in operator_bindings:
        residue.expected_residue_types.append(ResidueType.LOOP)
        residue.default_residue_weight = max(residue.default_residue_weight, 0.15)

    risk.semantic_risk = max(
        risk.semantic_risk,
        risk.source_confusion_risk * 0.5,
        risk.consent_pressure * 0.4,
        residue.default_residue_weight * 0.5,
    )

    return RuntimeCardExtension(
        operator_bindings=operator_bindings,
        semantic_mass=semantic_mass,
        affective_charge=affective_charge,
        consent_effect=consent,
        memory_effect=memory,
        risk_profile=risk,
        residue_profile=residue,
    )


def generate_runtime_card(
    *,
    card_id: str,
    slot_id: int,
    language_id: str,
    lemma: str | None,
    surface_forms: list[str] | None = None,
    function: str = "",
    ontology_class: CardOntologyClass = CardOntologyClass.UNRESOLVED,
    validation_status: CardValidationStatus = CardValidationStatus.DRAFT,
    source_binding: SourceBindingType = SourceBindingType.ARTIFACT_GROUNDED,
    operator_bindings: list[str] | None = None,
    semantic_mass: float | None = None,
    affective_charge: float | None = None,
    attach_marker: bool = True,
) -> CielingoRuntimeCard:
    surface_forms = surface_forms or ([lemma] if lemma else [])
    if lemma and lemma not in surface_forms:
        surface_forms = [lemma] + list(surface_forms)

    inferred = infer_operator_bindings(function, lemma)
    bindings = operator_bindings if operator_bindings is not None else inferred

    runtime = build_runtime_extension(
        operator_bindings=bindings,
        semantic_mass=semantic_mass,
        affective_charge=affective_charge,
    )

    card = CielingoRuntimeCard(
        card_id=card_id,
        slot_id=slot_id,
        language_id=language_id,
        lemma=lemma,
        surface_forms=surface_forms,
        ontology_class=ontology_class,
        function=function,
        validation_status=validation_status,
        source_binding=source_binding,
        canon_allowed=False,
        runtime=runtime,
        notes=["Generated by CIELingo card_generator v0.3"],
    )
    if attach_marker:
        attach_noema_marker(card)
    return card
