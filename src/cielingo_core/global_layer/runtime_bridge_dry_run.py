
"""Runtime bridge dry-run for GLOBAL meaning signals v0.8B.

This is the first controlled self-feed stage:
    MeaningLoop -> RepairRouting -> GlobalMeaningSignal -> RuntimeBridgeDryRun

Boundary:
- dry-run observes and classifies;
- dry-run does not execute runtime actions;
- dry-run does not write NOEMA;
- dry-run does not update CURRENT;
- dry-run does not promote SOURCE/canon.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from hashlib import sha256
import json
from typing import Any

from cielingo_core.global_layer.meaning_signal_bridge import GlobalMeaningSignal, GlobalSignalSeverity


class RuntimeDryRunDecision(str, Enum):
    OBSERVE = "observe"
    ADVISE_REPAIR = "advise_repair"
    BLOCK_AND_QUARANTINE = "block_and_quarantine"


@dataclass(frozen=True)
class RuntimeBridgeDryRunResult:
    dry_run_id: str
    signal_id: str
    decision: RuntimeDryRunDecision
    severity: str
    route_kinds: list[str]
    rationale: list[str]
    self_feed_allowed: bool = True
    executed_runtime_action: bool = False
    canon_allowed: bool = False
    source_promotion_allowed: bool = False
    noema_writeback_allowed: bool = False
    current_update_allowed: bool = False
    limitation: str = "runtime_bridge_dry_run_not_execution"

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.dry_run_id:
            issues.append("dry_run_id is required")
        if not self.signal_id:
            issues.append("signal_id is required")
        if not self.rationale:
            issues.append("rationale is required")
        if self.executed_runtime_action:
            issues.append("dry-run must not execute runtime action")
        if self.canon_allowed:
            issues.append("dry-run must not allow canon")
        if self.source_promotion_allowed:
            issues.append("dry-run must not promote SOURCE")
        if self.noema_writeback_allowed:
            issues.append("dry-run must not write NOEMA")
        if self.current_update_allowed:
            issues.append("dry-run must not update CURRENT")
        if "not_execution" not in self.limitation:
            issues.append("dry-run must state not_execution limitation")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "dry_run_id": self.dry_run_id,
            "signal_id": self.signal_id,
            "decision": self.decision.value,
            "severity": self.severity,
            "route_kinds": list(self.route_kinds),
            "rationale": list(self.rationale),
            "self_feed_allowed": self.self_feed_allowed,
            "executed_runtime_action": self.executed_runtime_action,
            "canon_allowed": self.canon_allowed,
            "source_promotion_allowed": self.source_promotion_allowed,
            "noema_writeback_allowed": self.noema_writeback_allowed,
            "current_update_allowed": self.current_update_allowed,
            "limitation": self.limitation,
        }

    def stable_hash(self) -> str:
        payload = json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True)
        return sha256(payload.encode("utf-8")).hexdigest()


def run_runtime_bridge_dry_run(signal: GlobalMeaningSignal) -> RuntimeBridgeDryRunResult:
    """Classify a GlobalMeaningSignal without executing anything."""
    signal_issues = signal.validate()
    route_kinds = list(signal.route_kinds)
    rationale: list[str] = []

    if signal_issues:
        decision = RuntimeDryRunDecision.BLOCK_AND_QUARANTINE
        rationale.append("Signal validation issues force dry-run quarantine.")
        rationale.extend(signal_issues)
    elif signal.severity == GlobalSignalSeverity.BLOCKER:
        decision = RuntimeDryRunDecision.BLOCK_AND_QUARANTINE
        rationale.append("BLOCKER signal routes to quarantine/blocked action.")
    elif signal.severity in {GlobalSignalSeverity.ERROR, GlobalSignalSeverity.WARNING}:
        decision = RuntimeDryRunDecision.ADVISE_REPAIR
        rationale.append("Non-blocking but repair-relevant signal routes to advisory repair.")
    else:
        decision = RuntimeDryRunDecision.OBSERVE
        rationale.append("INFO signal remains observational.")

    if not signal.advisory_only:
        decision = RuntimeDryRunDecision.BLOCK_AND_QUARANTINE
        rationale.append("Signal advisory_only=false is invalid for dry-run.")
    if signal.runtime_execution_allowed:
        decision = RuntimeDryRunDecision.BLOCK_AND_QUARANTINE
        rationale.append("Signal attempted runtime execution authority.")

    payload = json.dumps({
        "signal_id": signal.signal_id,
        "decision": decision.value,
        "severity": signal.severity.value if hasattr(signal.severity, "value") else str(signal.severity),
        "route_kinds": route_kinds,
        "rationale": rationale,
    }, ensure_ascii=False, sort_keys=True)

    return RuntimeBridgeDryRunResult(
        dry_run_id="runtime_dry_run_" + sha256(payload.encode("utf-8")).hexdigest()[:16],
        signal_id=signal.signal_id,
        decision=decision,
        severity=signal.severity.value if hasattr(signal.severity, "value") else str(signal.severity),
        route_kinds=route_kinds,
        rationale=rationale,
        self_feed_allowed=True,
        executed_runtime_action=False,
        canon_allowed=False,
        source_promotion_allowed=False,
        noema_writeback_allowed=False,
        current_update_allowed=False,
    )
