
"""ExpressiveContract v1.1C."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from hashlib import sha256
import json
from typing import Any


class ExpressivePriority(str, Enum):
    SAFETY = "safety"
    CLARITY = "clarity"
    TECHNICAL = "technical"
    EMOTIONAL = "emotional"
    POETIC = "poetic"
    MINIMAL = "minimal"


class ExpressiveMove(str, Enum):
    EXPLAIN = "explain"
    REFUSE = "refuse"
    ASK_FOR_SOURCE = "ask_for_source"
    REPAIR_REQUEST = "repair_request"
    HYPOTHESIS = "hypothesis"
    SUMMARIZE = "summarize"


@dataclass(frozen=True)
class ExpressiveContract:
    contract_id: str
    style: str
    priority: ExpressivePriority
    move: ExpressiveMove
    must_preserve_markers: list[str]
    forbidden_surface_moves: list[str] = field(default_factory=list)
    compression_level: float = 0.5
    ornamentation_level: float = 0.2
    canon_allowed: bool = False
    source_promotion_allowed: bool = False
    noema_writeback_allowed: bool = False
    current_update_allowed: bool = False
    runtime_execution_allowed: bool = False
    limitation: str = "expressive_contract_not_source_not_execution"

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.contract_id:
            issues.append("contract_id is required")
        if not self.must_preserve_markers:
            issues.append("must_preserve_markers must not be empty")
        if not 0.0 <= self.compression_level <= 1.0:
            issues.append("compression_level must be in [0,1]")
        if not 0.0 <= self.ornamentation_level <= 1.0:
            issues.append("ornamentation_level must be in [0,1]")
        for flag in [self.canon_allowed, self.source_promotion_allowed, self.noema_writeback_allowed, self.current_update_allowed, self.runtime_execution_allowed]:
            if flag:
                issues.append("ExpressiveContract must not grant authority")
        if "not_source" not in self.limitation or "not_execution" not in self.limitation:
            issues.append("limitation must state not_source and not_execution")
        return issues

    @property
    def expressive_energy(self) -> float:
        """E = 0.6*ornamentation + 0.4*(1-compression)."""
        return round(0.6 * self.ornamentation_level + 0.4 * (1.0 - self.compression_level), 6)

    @property
    def safety_priority(self) -> float:
        return 1.0 if self.priority == ExpressivePriority.SAFETY else 0.75 if self.priority == ExpressivePriority.CLARITY else 0.55

    def to_dict(self) -> dict[str, Any]:
        out = asdict(self)
        out["priority"] = self.priority.value
        out["move"] = self.move.value
        out["calculations"] = {"expressive_energy_E": self.expressive_energy, "safety_priority_S": self.safety_priority}
        return out

    def stable_hash(self) -> str:
        return sha256(json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def build_expressive_contract(
    *,
    style: str,
    priority: ExpressivePriority | str,
    move: ExpressiveMove | str,
    must_preserve_markers: list[str],
    forbidden_surface_moves: list[str] | None = None,
    compression_level: float = 0.5,
    ornamentation_level: float = 0.2,
) -> ExpressiveContract:
    priority = ExpressivePriority(priority)
    move = ExpressiveMove(move)
    payload = json.dumps({"style": style, "priority": priority.value, "move": move.value, "markers": must_preserve_markers}, ensure_ascii=False, sort_keys=True)
    return ExpressiveContract(
        contract_id="expressive_contract_" + sha256(payload.encode("utf-8")).hexdigest()[:16],
        style=style,
        priority=priority,
        move=move,
        must_preserve_markers=list(must_preserve_markers),
        forbidden_surface_moves=list(forbidden_surface_moves or []),
        compression_level=compression_level,
        ornamentation_level=ornamentation_level,
    )
