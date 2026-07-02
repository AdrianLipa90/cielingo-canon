
"""Controlled runtime adapter interface v0.9A.

A typed adapter boundary for consuming RuntimeBridgeDryRunResult.

Boundary:
- adapter is dry-run only;
- adapter returns a reference handle, not execution;
- adapter does not write NOEMA;
- adapter does not update CURRENT;
- adapter does not promote SOURCE/canon.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from hashlib import sha256
import json
from typing import Any

from cielingo_core.global_layer.runtime_bridge_dry_run import RuntimeBridgeDryRunResult, RuntimeDryRunDecision


class RuntimeAdapterAction(str, Enum):
    OBSERVE_ONLY = "observe_only"
    ADVISE_REPAIR_ONLY = "advise_repair_only"
    BLOCK_AND_QUARANTINE_ONLY = "block_and_quarantine_only"


@dataclass(frozen=True)
class RuntimeAdapterReference:
    reference_id: str
    dry_run_id: str
    adapter_action: RuntimeAdapterAction
    decision: str
    severity: str
    route_kinds: list[str]
    reference_kind: str = "artifact_grounded_reference"
    executes_runtime_action: bool = False
    canon_allowed: bool = False
    source_promotion_allowed: bool = False
    noema_writeback_allowed: bool = False
    current_update_allowed: bool = False
    limitation: str = "runtime_adapter_reference_not_execution"

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.reference_id:
            issues.append("reference_id is required")
        if not self.dry_run_id:
            issues.append("dry_run_id is required")
        if self.reference_kind != "artifact_grounded_reference":
            issues.append("reference_kind must be artifact_grounded_reference")
        if self.executes_runtime_action:
            issues.append("runtime adapter reference must not execute runtime action")
        if self.canon_allowed:
            issues.append("runtime adapter reference must not allow canon")
        if self.source_promotion_allowed:
            issues.append("runtime adapter reference must not promote SOURCE")
        if self.noema_writeback_allowed:
            issues.append("runtime adapter reference must not write NOEMA")
        if self.current_update_allowed:
            issues.append("runtime adapter reference must not update CURRENT")
        if "not_execution" not in self.limitation:
            issues.append("runtime adapter reference must state not_execution limitation")
        return issues

    def to_dict(self) -> dict[str, Any]:
        out = asdict(self)
        out["adapter_action"] = self.adapter_action.value
        return out

    def stable_hash(self) -> str:
        payload = json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True)
        return sha256(payload.encode("utf-8")).hexdigest()


def adapt_runtime_dry_run_reference(dry_run: RuntimeBridgeDryRunResult) -> RuntimeAdapterReference:
    """Convert a dry-run result into an artifact-grounded reference only."""
    if dry_run.decision == RuntimeDryRunDecision.BLOCK_AND_QUARANTINE:
        action = RuntimeAdapterAction.BLOCK_AND_QUARANTINE_ONLY
    elif dry_run.decision == RuntimeDryRunDecision.ADVISE_REPAIR:
        action = RuntimeAdapterAction.ADVISE_REPAIR_ONLY
    else:
        action = RuntimeAdapterAction.OBSERVE_ONLY

    payload = json.dumps({
        "dry_run_id": dry_run.dry_run_id,
        "decision": dry_run.decision.value if hasattr(dry_run.decision, "value") else str(dry_run.decision),
        "severity": dry_run.severity,
        "route_kinds": dry_run.route_kinds,
        "action": action.value,
    }, ensure_ascii=False, sort_keys=True)

    return RuntimeAdapterReference(
        reference_id="runtime_adapter_ref_" + sha256(payload.encode("utf-8")).hexdigest()[:16],
        dry_run_id=dry_run.dry_run_id,
        adapter_action=action,
        decision=dry_run.decision.value if hasattr(dry_run.decision, "value") else str(dry_run.decision),
        severity=str(dry_run.severity),
        route_kinds=list(dry_run.route_kinds),
        reference_kind="artifact_grounded_reference",
        executes_runtime_action=False,
        canon_allowed=False,
        source_promotion_allowed=False,
        noema_writeback_allowed=False,
        current_update_allowed=False,
    )
