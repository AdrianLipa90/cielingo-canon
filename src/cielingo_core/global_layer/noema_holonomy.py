"""NOEMA holonomic marker generation for CIELingo cards v0.3.

The marker is deterministic and public-safe. It is a commitment to semantic
card structure, not a NOEMA writeback and not runtime proof.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict
from typing import Any

from .card_runtime_schema import (
    CielingoRuntimeCard,
    NoemaHolonomicMarker,
)
from .contracts import SourceBindingType


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def _phase_from_text(text: str, salt: str) -> float:
    digest = hashlib.sha256((salt + "::" + text).encode("utf-8")).hexdigest()
    raw = int(digest[:12], 16)
    return round((raw % 1_000_000) / 1_000_000, 6)


def stable_card_projection(card: CielingoRuntimeCard) -> dict[str, Any]:
    """Return the stable subset used for fingerprinting.

    Excludes fields that would imply runtime NOEMA writeback.
    """

    return {
        "card_id": card.card_id,
        "slot_id": card.slot_id,
        "language_id": card.language_id,
        "lemma": card.lemma,
        "surface_forms": list(card.surface_forms),
        "ontology_class": card.ontology_class.value,
        "function": card.function,
        "operator_bindings": list(card.runtime.operator_bindings),
        "semantic_mass": card.runtime.semantic_mass,
        "affective_charge": card.runtime.affective_charge,
        "consent_effect": card.runtime.consent_effect.value,
        "memory_effect": card.runtime.memory_effect.value,
        "risk_profile": asdict(card.runtime.risk_profile),
        "residue_profile": {
            "expected_residue_types": [r.value for r in card.runtime.residue_profile.expected_residue_types],
            "default_residue_weight": card.runtime.residue_profile.default_residue_weight,
        },
        "source_binding": card.source_binding.value,
        "canon_allowed": card.canon_allowed,
    }


def stable_card_fingerprint(card: CielingoRuntimeCard) -> str:
    payload = json.dumps(stable_card_projection(card), ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_noema_holonomic_marker(card: CielingoRuntimeCard) -> NoemaHolonomicMarker:
    projection = stable_card_projection(card)
    payload = json.dumps(projection, ensure_ascii=False, sort_keys=True)
    fp = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    text = "|".join([str(card.card_id), str(card.lemma), " ".join(card.surface_forms), card.function])

    marker = NoemaHolonomicMarker(
        marker_id=f"noema-holo:{card.card_id}",
        source_binding=SourceBindingType.ARTIFACT_GROUNDED,
        semantic_phase=_clamp01(card.runtime.semantic_mass),
        affective_phase=_clamp01(abs(card.runtime.affective_charge)),
        consent_phase=_clamp01(card.runtime.risk_profile.consent_pressure),
        memory_phase=_clamp01(0.55 if card.runtime.memory_effect.value != "none" else 0.0),
        residue_phase=_clamp01(card.runtime.residue_profile.default_residue_weight),
        operator_phase=_phase_from_text(text, "operator_phase"),
        stable_fingerprint=fp,
        noema_writeback_required=card.runtime.memory_effect.value in {"episodic_candidate", "scar_candidate", "repair_required"},
        noema_current_update_allowed=False,
        notes=[
            "Marker is deterministic and public-safe.",
            "Marker is not NOEMA SOURCE and does not update CURRENT.",
        ],
    )
    return marker


def attach_noema_marker(card: CielingoRuntimeCard) -> CielingoRuntimeCard:
    card.runtime.noema_holonomic_marker = build_noema_holonomic_marker(card)
    return card
