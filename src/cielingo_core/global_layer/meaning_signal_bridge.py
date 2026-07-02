
"""GLOBAL signal bridge integration for MeaningLoop repair routing v0.8A.

Converts MeaningLoop + RepairRouting diagnostics into a safe global signal.

Boundary:
- signal is advisory, not execution;
- no SOURCE/canon promotion;
- no NOEMA writeback;
- no CURRENT update.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from hashlib import sha256
import json
from typing import Any

from cielingo_core.meaning.meaning_loop import MeaningLoop
from cielingo_core.meaning.repair_routing import MeaningRepairRoutingReport, RepairRouteKind


class GlobalSignalSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    BLOCKER = "blocker"


@dataclass(frozen=True)
class GlobalMeaningSignal:
    signal_id: str
    loop_id: str
    repair_report_id: str
    severity: GlobalSignalSeverity
    route_kinds: list[str]
    return_required: bool
    repair_required_before_closure: bool
    advisory_only: bool = True
    canon_allowed: bool = False
    source_promotion_allowed: bool = False
    noema_writeback_allowed: bool = False
    current_update_allowed: bool = False
    runtime_execution_allowed: bool = False
    limitation: str = "global_meaning_signal_advisory_not_execution"

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.signal_id:
            issues.append("signal_id is required")
        if not self.loop_id:
            issues.append("loop_id is required")
        if not self.repair_report_id:
            issues.append("repair_report_id is required")
        if not self.advisory_only:
            issues.append("global signal must remain advisory_only")
        if self.canon_allowed:
            issues.append("global signal must not allow canon")
        if self.source_promotion_allowed:
            issues.append("global signal must not promote SOURCE")
        if self.noema_writeback_allowed:
            issues.append("global signal must not write NOEMA")
        if self.current_update_allowed:
            issues.append("global signal must not update CURRENT")
        if self.runtime_execution_allowed:
            issues.append("global signal must not allow runtime execution")
        if "not_execution" not in self.limitation:
            issues.append("global signal must state not_execution limitation")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "signal_id": self.signal_id,
            "loop_id": self.loop_id,
            "repair_report_id": self.repair_report_id,
            "severity": self.severity.value,
            "route_kinds": list(self.route_kinds),
            "return_required": self.return_required,
            "repair_required_before_closure": self.repair_required_before_closure,
            "advisory_only": self.advisory_only,
            "canon_allowed": self.canon_allowed,
            "source_promotion_allowed": self.source_promotion_allowed,
            "noema_writeback_allowed": self.noema_writeback_allowed,
            "current_update_allowed": self.current_update_allowed,
            "runtime_execution_allowed": self.runtime_execution_allowed,
            "limitation": self.limitation,
        }

    def stable_hash(self) -> str:
        payload = json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True)
        return sha256(payload.encode("utf-8")).hexdigest()


def build_global_meaning_signal(loop: MeaningLoop, repair_report: MeaningRepairRoutingReport) -> GlobalMeaningSignal:
    route_kinds = [candidate.route_kind.value if hasattr(candidate.route_kind, "value") else str(candidate.route_kind) for candidate in repair_report.candidates]
    required = any(candidate.required_before_closure for candidate in repair_report.candidates)
    blocker_routes = {RepairRouteKind.BLOCK_AUTHORITY.value, RepairRouteKind.QUARANTINE.value}
    error_routes = {RepairRouteKind.ATTACH_SOURCE.value, RepairRouteKind.ADD_NATIVE_REVIEW.value}
    if any(kind in blocker_routes for kind in route_kinds):
        severity = GlobalSignalSeverity.BLOCKER
    elif required or any(kind in error_routes for kind in route_kinds):
        severity = GlobalSignalSeverity.ERROR
    elif route_kinds:
        severity = GlobalSignalSeverity.WARNING
    else:
        severity = GlobalSignalSeverity.INFO

    payload = json.dumps({
        "loop_id": loop.loop_id,
        "repair_report_id": repair_report.report_id,
        "route_kinds": route_kinds,
        "severity": severity.value,
    }, ensure_ascii=False, sort_keys=True)

    return GlobalMeaningSignal(
        signal_id="global_meaning_signal_" + sha256(payload.encode("utf-8")).hexdigest()[:16],
        loop_id=loop.loop_id,
        repair_report_id=repair_report.report_id,
        severity=severity,
        route_kinds=route_kinds,
        return_required=bool(loop.return_required),
        repair_required_before_closure=bool(required),
        advisory_only=True,
        canon_allowed=False,
        source_promotion_allowed=False,
        noema_writeback_allowed=False,
        current_update_allowed=False,
        runtime_execution_allowed=False,
    )
