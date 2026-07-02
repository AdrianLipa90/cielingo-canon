"""MeaningAction and MeaningBlockAction.

Inspired by the block-action idea: local operators have local effects; a
sequence of operators produces a block-level semantic effect.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .operator_algebra import RelationalOperator


def _bounded_delta(v: float) -> bool:
    return -1.0 <= float(v) <= 1.0


@dataclass
class MeaningAction:
    action_id: str
    operator_id: str
    input_slots: list[int] = field(default_factory=list)
    output_slots: list[int] = field(default_factory=list)
    delta_semantic_mass: float = 0.0
    delta_affect: float = 0.0
    delta_certainty: float = 0.0
    delta_consent_pressure: float = 0.0
    delta_source_pressure: float = 0.0
    residue_delta: float = 0.0
    trace_required: bool = False
    notes: list[str] = field(default_factory=list)

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.action_id:
            issues.append("action_id is required")
        if not self.operator_id:
            issues.append("operator_id is required")
        for name in (
            "delta_semantic_mass",
            "delta_affect",
            "delta_certainty",
            "delta_consent_pressure",
            "delta_source_pressure",
            "residue_delta",
        ):
            if not _bounded_delta(getattr(self, name)):
                issues.append(f"{name} must be in [-1, 1]")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MeaningBlockAction:
    block_id: str
    actions: list[MeaningAction]
    closes_loop: bool = False
    notes: list[str] = field(default_factory=list)

    @property
    def total_semantic_mass_delta(self) -> float:
        return round(sum(a.delta_semantic_mass for a in self.actions), 6)

    @property
    def total_affect_delta(self) -> float:
        return round(sum(a.delta_affect for a in self.actions), 6)

    @property
    def total_certainty_delta(self) -> float:
        return round(sum(a.delta_certainty for a in self.actions), 6)

    @property
    def total_consent_pressure_delta(self) -> float:
        return round(sum(a.delta_consent_pressure for a in self.actions), 6)

    @property
    def total_source_pressure_delta(self) -> float:
        return round(sum(a.delta_source_pressure for a in self.actions), 6)

    @property
    def total_residue_delta(self) -> float:
        return round(sum(a.residue_delta for a in self.actions), 6)

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.block_id:
            issues.append("block_id is required")
        for action in self.actions:
            issues.extend(action.validate())
        return issues

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d.update({
            "total_semantic_mass_delta": self.total_semantic_mass_delta,
            "total_affect_delta": self.total_affect_delta,
            "total_certainty_delta": self.total_certainty_delta,
            "total_consent_pressure_delta": self.total_consent_pressure_delta,
            "total_source_pressure_delta": self.total_source_pressure_delta,
            "total_residue_delta": self.total_residue_delta,
        })
        return d


def action_from_operator(
    operator: RelationalOperator,
    *,
    action_id: str,
    input_slots: list[int] | None = None,
    output_slots: list[int] | None = None,
) -> MeaningAction:
    """Map a RelationalOperator to its initial semantic action effect.

    This is deliberately conservative and deterministic. Regional grammar is
    not interpreted here.
    """

    input_slots = input_slots or []
    output_slots = output_slots or []
    j = operator.j_weights

    return MeaningAction(
        action_id=action_id,
        operator_id=operator.operator_id,
        input_slots=input_slots,
        output_slots=output_slots,
        delta_semantic_mass=min(1.0, j.get("J_role_binding", 0.0) + j.get("J_affective_charge", 0.0)),
        delta_affect=j.get("J_affective_charge", 0.0),
        delta_certainty=-j.get("J_source_pressure", 0.0),
        delta_consent_pressure=j.get("J_consent_pressure", 0.0),
        delta_source_pressure=j.get("J_source_pressure", 0.0),
        residue_delta=j.get("J_scope_pressure", 0.0),
        trace_required=operator.consent_effect == "requires_consent" or operator.source_required,
        notes=[f"Generated from operator {operator.operator_id}"],
    )
