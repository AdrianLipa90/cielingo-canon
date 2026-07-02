"""GLOBAL 0.5C intention-to-action scaling scaffold.

Intention may scale semantic deltas. It never executes runtime actions,
never writes NOEMA, and never claims physical manifestation.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .meaning_action import MeaningAction


def _bounded01(value: float) -> bool:
    return 0.0 <= float(value) <= 1.0


@dataclass
class IntentionActionScaling:
    coherence_omega: float = 0.0
    ethical_bound: float = 0.786
    action_scaling: float = 1.0
    consent_scaling: float = 1.0
    source_scaling: float = 1.0
    affects_physical_runtime: bool = False
    noema_writeback_allowed: bool = False
    notes: list[str] | None = None

    def validate(self) -> list[str]:
        issues: list[str] = []
        for name in ("coherence_omega", "ethical_bound"):
            if not _bounded01(getattr(self, name)):
                issues.append(f"{name} must be in [0, 1]")
        for name in ("action_scaling", "consent_scaling", "source_scaling"):
            if not (0.0 <= float(getattr(self, name)) <= 2.0):
                issues.append(f"{name} must be in [0, 2]")
        if self.affects_physical_runtime:
            issues.append("IntentionActionScaling must not claim physical runtime effect")
        if self.noema_writeback_allowed:
            issues.append("IntentionActionScaling must not allow NOEMA writeback")
        return issues

    @property
    def below_ethical_bound(self) -> bool:
        return self.coherence_omega < self.ethical_bound

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def scale_meaning_action(action: MeaningAction, scaling: IntentionActionScaling) -> MeaningAction:
    """Return a scaled copy of a MeaningAction.

    If coherence is below ethical bound, action/consent/source pressure are
    damped rather than amplified. This is semantic safety gating only.
    """
    if scaling.validate():
        raise ValueError("; ".join(scaling.validate()))

    gate = 0.5 if scaling.below_ethical_bound else 1.0
    return MeaningAction(
        action_id=f"{action.action_id}:scaled",
        operator_id=action.operator_id,
        input_slots=list(action.input_slots),
        output_slots=list(action.output_slots),
        delta_semantic_mass=max(-1.0, min(1.0, action.delta_semantic_mass * scaling.action_scaling * gate)),
        delta_affect=max(-1.0, min(1.0, action.delta_affect * scaling.action_scaling * gate)),
        delta_certainty=max(-1.0, min(1.0, action.delta_certainty)),
        delta_consent_pressure=max(-1.0, min(1.0, action.delta_consent_pressure * scaling.consent_scaling * gate)),
        delta_source_pressure=max(-1.0, min(1.0, action.delta_source_pressure * scaling.source_scaling * gate)),
        residue_delta=action.residue_delta,
        trace_required=action.trace_required,
        notes=list(action.notes) + ["Scaled by IntentionActionScaling; semantic only, no runtime execution."],
    )
