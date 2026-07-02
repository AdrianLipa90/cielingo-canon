"""GLOBAL 0.5C slot taxonomy scaffold."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any

from .contracts import SourceBindingType


class SlotFamily(str, Enum):
    EPISTEMIC_SOURCE = "epistemic_source"
    ARTIFACT_MEMORY = "artifact_memory"
    RUNTIME_ACTION = "runtime_action"
    GOVERNANCE_BOUNDARY = "governance_boundary"
    LOGICAL_OPERATOR = "logical_operator"
    ENTITY_PARTICIPANT = "entity_participant"
    AFFECT_VALUE = "affect_value"
    TIME_STATE = "time_state"


class SlotMode(str, Enum):
    ARGUMENT = "argument"
    OPERATOR = "operator"
    STATE = "state"
    ACT = "act"
    RELATION = "relation"
    AFFECT = "affect"
    SOURCE = "source"
    MEMORY = "memory"


@dataclass
class SlotTaxonomyRecord:
    slot_id: int
    slot_key: str
    slot_family: SlotFamily
    slot_mode: SlotMode
    global_operator_candidate: bool = False
    requires_runtime_extension: bool = True
    requires_noema_marker: bool = True
    requires_consent_gate: bool = False
    requires_source_gate: bool = False
    regional_surface_required: bool = True
    can_be_in_blanco: bool = True
    source_binding_default: SourceBindingType = SourceBindingType.ARTIFACT_GROUNDED
    canon_allowed_default: bool = False
    notes: list[str] | None = None

    def validate(self) -> list[str]:
        issues: list[str] = []
        if self.slot_id <= 0:
            issues.append("slot_id must be positive")
        if not self.slot_key:
            issues.append("slot_key is required")
        if self.source_binding_default == SourceBindingType.SOURCE:
            issues.append("slot taxonomy must not default to SOURCE")
        if self.canon_allowed_default:
            issues.append("slot taxonomy must not default to canon_allowed=true")
        if self.slot_family == SlotFamily.EPISTEMIC_SOURCE and self.slot_mode == SlotMode.SOURCE and not self.requires_source_gate:
            issues.append("source-mode epistemic slot must require source gate")
        if self.slot_family == SlotFamily.RUNTIME_ACTION and not self.requires_consent_gate:
            issues.append("runtime-action slot must require consent gate")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
