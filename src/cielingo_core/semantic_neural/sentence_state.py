"""Semantic-neural sentence state scaffold v0.5P.

This module creates explicit sentence-state snapshots from SentenceEquation
objects. It is a scaffold for card/slot/J/residue dynamics, not a full neural
runtime or consciousness claim.

Boundaries:
- no SOURCE promotion;
- no canon promotion;
- no external NOEMA writeback;
- no CURRENT update;
- no physical Kuramoto measurement;
- no runtime cognition claim.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json
from typing import Any


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


@dataclass(frozen=True)
class CardOscillatorState:
    """A symbolic card/token oscillator state.

    This is a semantic diagnostic object, not a biological neuron.
    """

    node_id: str
    token: str
    slot_ids: list[int] = field(default_factory=list)
    activation: float = 0.0
    phase: float = 0.0
    semantic_mass: float = 0.0
    residue: float = 0.0
    limitation: str = "card_oscillator_state_not_biological_neuron"

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.node_id:
            issues.append("node_id is required")
        for name in ("activation", "phase", "semantic_mass", "residue"):
            value = getattr(self, name)
            if not 0.0 <= float(value) <= 1.0:
                issues.append(f"{self.node_id}.{name} must be in [0,1]")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class JVectorState:
    values: dict[str, float]
    limitation: str = "j_vector_state_not_physical_measurement"

    def validate(self) -> list[str]:
        issues: list[str] = []
        for key, value in self.values.items():
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                issues.append(f"J value {key} must be numeric")
            elif not 0.0 <= float(value) <= 1.0:
                issues.append(f"J value {key} must be in [0,1]")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return {"values": dict(sorted((k, float(v)) for k, v in self.values.items())), "limitation": self.limitation}


@dataclass(frozen=True)
class SentenceStateSnapshot:
    snapshot_id: str
    language_id: str
    text: str
    tokens: list[str]
    nodes: list[CardOscillatorState]
    j_vector: JVectorState
    notes_digest: str
    source_promotion_allowed: bool = False
    canon_allowed: bool = False
    noema_writeback_allowed: bool = False
    current_update_allowed: bool = False
    limitation: str = "semantic_neural_sentence_state_scaffold_not_runtime_cognition"

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.snapshot_id:
            issues.append("snapshot_id is required")
        if not self.language_id:
            issues.append("language_id is required")
        if not isinstance(self.tokens, list):
            issues.append("tokens must be a list")
        for node in self.nodes:
            issues.extend(node.validate())
        issues.extend(self.j_vector.validate())
        if self.source_promotion_allowed:
            issues.append("SentenceStateSnapshot must not promote SOURCE")
        if self.canon_allowed:
            issues.append("SentenceStateSnapshot must not promote canon")
        if self.noema_writeback_allowed:
            issues.append("SentenceStateSnapshot must not write NOEMA")
        if self.current_update_allowed:
            issues.append("SentenceStateSnapshot must not update CURRENT")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "language_id": self.language_id,
            "text": self.text,
            "tokens": list(self.tokens),
            "nodes": [node.to_dict() for node in self.nodes],
            "j_vector": self.j_vector.to_dict(),
            "notes_digest": self.notes_digest,
            "source_promotion_allowed": self.source_promotion_allowed,
            "canon_allowed": self.canon_allowed,
            "noema_writeback_allowed": self.noema_writeback_allowed,
            "current_update_allowed": self.current_update_allowed,
            "limitation": self.limitation,
        }

    def stable_hash(self) -> str:
        payload = json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True)
        return sha256(payload.encode("utf-8")).hexdigest()


def _slot_ids_for_token(slot_projection: dict[Any, list[int]], token_index: int) -> list[int]:
    out: list[int] = []
    for slot_id, indices in slot_projection.items():
        if token_index in list(indices):
            out.append(int(slot_id))
    return sorted(set(out))


def build_sentence_state_snapshot(sentence_equation: Any, *, notes: list[Any] | None = None) -> SentenceStateSnapshot:
    """Build a semantic-neural sentence-state snapshot from a SentenceEquation-like object."""

    data = sentence_equation.to_dict() if hasattr(sentence_equation, "to_dict") else {}
    surface = data.get("surface_solution") or data.get("surface") or {}
    tokens = list(surface.get("tokens") or getattr(sentence_equation, "tokens", []) or [])
    local_j = dict(surface.get("local_j") or getattr(sentence_equation, "local_j", {}) or {})
    slot_projection = dict(surface.get("slot_projection") or {})

    j_vector = JVectorState(values={str(k): clamp01(float(v)) for k, v in local_j.items() if isinstance(v, (int, float)) and not isinstance(v, bool)})
    notes_payload = json.dumps(notes or [], ensure_ascii=False, sort_keys=True, default=str)
    notes_digest = sha256(notes_payload.encode("utf-8")).hexdigest()

    # Simple scaffold: token activation is informed by whether the token maps to a slot and by average J pressure.
    avg_j = sum(j_vector.values.values()) / len(j_vector.values) if j_vector.values else 0.0
    nodes: list[CardOscillatorState] = []
    for idx, token in enumerate(tokens):
        slots = _slot_ids_for_token(slot_projection, idx)
        activation = clamp01((0.45 if slots else 0.20) + 0.35 * avg_j)
        phase = clamp01(((idx + 1) / max(1, len(tokens))) * 0.70 + 0.30 * avg_j)
        semantic_mass = clamp01(activation * (0.75 if slots else 0.45))
        residue = clamp01(1.0 - activation)
        nodes.append(CardOscillatorState(
            node_id=f"token_{idx}",
            token=str(token),
            slot_ids=slots,
            activation=round(activation, 6),
            phase=round(phase, 6),
            semantic_mass=round(semantic_mass, 6),
            residue=round(residue, 6),
        ))

    base_id = json.dumps({
        "language_id": getattr(sentence_equation, "language_id", data.get("language_id", "")),
        "text": getattr(sentence_equation, "text", data.get("text", "")),
        "tokens": tokens,
        "j": j_vector.to_dict(),
        "notes_digest": notes_digest,
    }, ensure_ascii=False, sort_keys=True)
    snapshot_id = "sent_state_" + sha256(base_id.encode("utf-8")).hexdigest()[:16]

    return SentenceStateSnapshot(
        snapshot_id=snapshot_id,
        language_id=str(getattr(sentence_equation, "language_id", data.get("language_id", ""))),
        text=str(getattr(sentence_equation, "text", data.get("text", ""))),
        tokens=tokens,
        nodes=nodes,
        j_vector=j_vector,
        notes_digest=notes_digest,
        source_promotion_allowed=False,
        canon_allowed=False,
        noema_writeback_allowed=False,
        current_update_allowed=False,
    )
