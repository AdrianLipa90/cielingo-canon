
"""Expressive codec v1.1C."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Any

from cielingo_core.expressive.expressive_contract import ExpressiveContract
from cielingo_core.language_spaces.pl.pl_codecs import PLSurfacePlan


@dataclass(frozen=True)
class ExpressiveSurfacePlan:
    plan_id: str
    expressive_contract_id: str
    regional_plan_id: str
    style: str
    required_markers: list[str]
    surface_moves: list[str]
    codec_direction: str = "pl_surface_plan_to_expressive_surface_plan"
    canon_allowed: bool = False
    source_promotion_allowed: bool = False
    noema_writeback_allowed: bool = False
    current_update_allowed: bool = False
    runtime_execution_allowed: bool = False

    def validate(self) -> list[str]:
        issues = []
        if not self.required_markers:
            issues.append("required_markers must not be empty")
        if self.codec_direction != "pl_surface_plan_to_expressive_surface_plan":
            issues.append("wrong codec_direction")
        for flag in [self.canon_allowed, self.source_promotion_allowed, self.noema_writeback_allowed, self.current_update_allowed, self.runtime_execution_allowed]:
            if flag:
                issues.append("ExpressiveSurfacePlan must not grant authority")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def stable_hash(self) -> str:
        return sha256(json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def decode_pl_surface_plan_to_expressive_plan(pl_plan: PLSurfacePlan, expressive_contract: ExpressiveContract) -> ExpressiveSurfacePlan:
    moves = [
        f"style={expressive_contract.style}",
        f"priority={expressive_contract.priority.value}",
        f"move={expressive_contract.move.value}",
        "preserve markers literally before ornamentation",
    ]
    if expressive_contract.expressive_energy > 0.5:
        moves.append("allow bounded metaphor after markers")
    else:
        moves.append("keep low ornamentation")
    payload = json.dumps({"pl_plan": pl_plan.plan_id, "contract": expressive_contract.contract_id, "moves": moves}, ensure_ascii=False, sort_keys=True)
    return ExpressiveSurfacePlan(
        plan_id="expressive_surface_plan_" + sha256(payload.encode("utf-8")).hexdigest()[:16],
        expressive_contract_id=expressive_contract.contract_id,
        regional_plan_id=pl_plan.plan_id,
        style=expressive_contract.style,
        required_markers=list(expressive_contract.must_preserve_markers),
        surface_moves=moves,
    )
