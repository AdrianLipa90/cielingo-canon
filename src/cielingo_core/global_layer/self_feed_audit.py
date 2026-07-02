
"""Self-feed audit log and dry-run export bundle v0.8C.

Captures the advisory self-feed chain:
    MeaningLoop -> RepairRouting -> GlobalMeaningSignal -> RuntimeBridgeDryRun

Boundary:
- audit log is appendable local artifact, not NOEMA writeback;
- dry-run export is portable artifact, not CURRENT update;
- no runtime execution, no SOURCE/canon promotion.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from cielingo_core.meaning.meaning_loop import MeaningLoop
from cielingo_core.meaning.repair_routing import MeaningRepairRoutingReport
from cielingo_core.global_layer.meaning_signal_bridge import GlobalMeaningSignal
from cielingo_core.global_layer.runtime_bridge_dry_run import RuntimeBridgeDryRunResult


class SelfFeedAuditEventKind(str, Enum):
    LOOP_OBSERVED = "loop_observed"
    REPAIR_ROUTED = "repair_routed"
    GLOBAL_SIGNAL_BUILT = "global_signal_built"
    DRY_RUN_CLASSIFIED = "dry_run_classified"


@dataclass(frozen=True)
class SelfFeedAuditEvent:
    event_id: str
    event_kind: SelfFeedAuditEventKind
    object_ref: str
    object_hash: str
    summary: str
    advisory_only: bool = True
    executed_runtime_action: bool = False
    canon_allowed: bool = False
    source_promotion_allowed: bool = False
    noema_writeback_allowed: bool = False
    current_update_allowed: bool = False
    limitation: str = "self_feed_audit_event_not_execution"

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.event_id:
            issues.append("event_id is required")
        if not self.object_ref:
            issues.append("object_ref is required")
        if not self.object_hash:
            issues.append("object_hash is required")
        if not self.summary:
            issues.append("summary is required")
        if not self.advisory_only:
            issues.append("audit event must remain advisory_only")
        if self.executed_runtime_action:
            issues.append("audit event must not execute runtime action")
        if self.canon_allowed:
            issues.append("audit event must not allow canon")
        if self.source_promotion_allowed:
            issues.append("audit event must not promote SOURCE")
        if self.noema_writeback_allowed:
            issues.append("audit event must not write NOEMA")
        if self.current_update_allowed:
            issues.append("audit event must not update CURRENT")
        if "not_execution" not in self.limitation:
            issues.append("audit event must state not_execution limitation")
        return issues

    def to_dict(self) -> dict[str, Any]:
        out = asdict(self)
        out["event_kind"] = self.event_kind.value
        return out


@dataclass(frozen=True)
class SelfFeedAuditLog:
    log_id: str
    events: list[SelfFeedAuditEvent]
    advisory_only: bool = True
    executed_runtime_action: bool = False
    canon_allowed: bool = False
    source_promotion_allowed: bool = False
    noema_writeback_allowed: bool = False
    current_update_allowed: bool = False
    limitation: str = "self_feed_audit_log_local_artifact_not_noema_writeback"

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.log_id:
            issues.append("log_id is required")
        for event in self.events:
            issues.extend(event.validate())
        if not self.advisory_only:
            issues.append("audit log must remain advisory_only")
        if self.executed_runtime_action:
            issues.append("audit log must not execute runtime action")
        if self.canon_allowed:
            issues.append("audit log must not allow canon")
        if self.source_promotion_allowed:
            issues.append("audit log must not promote SOURCE")
        if self.noema_writeback_allowed:
            issues.append("audit log must not write NOEMA")
        if self.current_update_allowed:
            issues.append("audit log must not update CURRENT")
        if "not_noema_writeback" not in self.limitation:
            issues.append("audit log must state not_noema_writeback limitation")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "log_id": self.log_id,
            "events": [event.to_dict() for event in self.events],
            "advisory_only": self.advisory_only,
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

    def write_jsonl(self, path: str | Path) -> str:
        """Write local JSONL audit artifact. This is not NOEMA writeback."""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        lines = [json.dumps(event.to_dict(), ensure_ascii=False, sort_keys=True) for event in self.events]
        p.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        return str(p)


@dataclass(frozen=True)
class RuntimeDryRunExportBundle:
    bundle_id: str
    audit_log: SelfFeedAuditLog
    loops: list[MeaningLoop]
    repair_reports: list[MeaningRepairRoutingReport]
    signals: list[GlobalMeaningSignal]
    dry_runs: list[RuntimeBridgeDryRunResult]
    advisory_only: bool = True
    executed_runtime_action: bool = False
    canon_allowed: bool = False
    source_promotion_allowed: bool = False
    noema_writeback_allowed: bool = False
    current_update_allowed: bool = False
    limitation: str = "runtime_dry_run_export_bundle_not_noema_writeback"

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.bundle_id:
            issues.append("bundle_id is required")
        issues.extend(self.audit_log.validate())
        for item in self.loops:
            issues.extend(item.validate())
        for item in self.repair_reports:
            issues.extend(item.validate())
        for item in self.signals:
            issues.extend(item.validate())
        for item in self.dry_runs:
            issues.extend(item.validate())
        if not self.advisory_only:
            issues.append("export bundle must remain advisory_only")
        if self.executed_runtime_action:
            issues.append("export bundle must not execute runtime action")
        if self.canon_allowed:
            issues.append("export bundle must not allow canon")
        if self.source_promotion_allowed:
            issues.append("export bundle must not promote SOURCE")
        if self.noema_writeback_allowed:
            issues.append("export bundle must not write NOEMA")
        if self.current_update_allowed:
            issues.append("export bundle must not update CURRENT")
        if "not_noema_writeback" not in self.limitation:
            issues.append("export bundle must state not_noema_writeback limitation")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "bundle_id": self.bundle_id,
            "audit_log": self.audit_log.to_dict(),
            "loops": [item.to_dict() for item in self.loops],
            "repair_reports": [item.to_dict() for item in self.repair_reports],
            "signals": [item.to_dict() for item in self.signals],
            "dry_runs": [item.to_dict() for item in self.dry_runs],
            "advisory_only": self.advisory_only,
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

    def write_json(self, path: str | Path) -> str:
        """Write local JSON export. This is not NOEMA writeback."""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        payload = self.to_dict()
        payload["stable_hash"] = self.stable_hash()
        p.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        return str(p)


def _hash_obj(obj: Any) -> str:
    if hasattr(obj, "stable_hash"):
        return str(obj.stable_hash())
    if hasattr(obj, "to_dict"):
        payload = json.dumps(obj.to_dict(), ensure_ascii=False, sort_keys=True)
    else:
        payload = json.dumps(obj, ensure_ascii=False, sort_keys=True, default=str)
    return sha256(payload.encode("utf-8")).hexdigest()


def _event(kind: SelfFeedAuditEventKind, obj: Any, ref: str, summary: str) -> SelfFeedAuditEvent:
    payload = json.dumps({
        "kind": kind.value,
        "ref": ref,
        "hash": _hash_obj(obj),
        "summary": summary,
    }, ensure_ascii=False, sort_keys=True)
    return SelfFeedAuditEvent(
        event_id="self_feed_event_" + sha256(payload.encode("utf-8")).hexdigest()[:16],
        event_kind=kind,
        object_ref=ref,
        object_hash=_hash_obj(obj),
        summary=summary,
        advisory_only=True,
        executed_runtime_action=False,
        canon_allowed=False,
        source_promotion_allowed=False,
        noema_writeback_allowed=False,
        current_update_allowed=False,
    )


def build_self_feed_audit_log(
    loops: list[MeaningLoop],
    repair_reports: list[MeaningRepairRoutingReport],
    signals: list[GlobalMeaningSignal],
    dry_runs: list[RuntimeBridgeDryRunResult],
) -> SelfFeedAuditLog:
    events: list[SelfFeedAuditEvent] = []
    for loop in loops:
        events.append(_event(SelfFeedAuditEventKind.LOOP_OBSERVED, loop, loop.loop_id, f"Loop state observed: {loop.loop_state.value if hasattr(loop.loop_state, 'value') else loop.loop_state}"))
    for report in repair_reports:
        events.append(_event(SelfFeedAuditEventKind.REPAIR_ROUTED, report, report.report_id, f"Repair routing candidates: {len(report.candidates)}"))
    for signal in signals:
        events.append(_event(SelfFeedAuditEventKind.GLOBAL_SIGNAL_BUILT, signal, signal.signal_id, f"Global signal severity: {signal.severity.value if hasattr(signal.severity, 'value') else signal.severity}"))
    for dry in dry_runs:
        events.append(_event(SelfFeedAuditEventKind.DRY_RUN_CLASSIFIED, dry, dry.dry_run_id, f"Dry-run decision: {dry.decision.value if hasattr(dry.decision, 'value') else dry.decision}"))

    payload = json.dumps([event.event_id for event in events], ensure_ascii=False, sort_keys=True)
    return SelfFeedAuditLog(
        log_id="self_feed_audit_" + sha256(payload.encode("utf-8")).hexdigest()[:16],
        events=events,
        advisory_only=True,
        executed_runtime_action=False,
        canon_allowed=False,
        source_promotion_allowed=False,
        noema_writeback_allowed=False,
        current_update_allowed=False,
    )


def build_runtime_dry_run_export_bundle(
    loops: list[MeaningLoop],
    repair_reports: list[MeaningRepairRoutingReport],
    signals: list[GlobalMeaningSignal],
    dry_runs: list[RuntimeBridgeDryRunResult],
) -> RuntimeDryRunExportBundle:
    audit_log = build_self_feed_audit_log(loops, repair_reports, signals, dry_runs)
    payload = json.dumps({
        "audit_log": audit_log.log_id,
        "loops": [loop.loop_id for loop in loops],
        "repair_reports": [report.report_id for report in repair_reports],
        "signals": [signal.signal_id for signal in signals],
        "dry_runs": [dry.dry_run_id for dry in dry_runs],
    }, ensure_ascii=False, sort_keys=True)
    return RuntimeDryRunExportBundle(
        bundle_id="runtime_dry_run_export_" + sha256(payload.encode("utf-8")).hexdigest()[:16],
        audit_log=audit_log,
        loops=loops,
        repair_reports=repair_reports,
        signals=signals,
        dry_runs=dry_runs,
        advisory_only=True,
        executed_runtime_action=False,
        canon_allowed=False,
        source_promotion_allowed=False,
        noema_writeback_allowed=False,
        current_update_allowed=False,
    )
