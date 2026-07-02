
"""MeaningLoop repair-candidate routing v0.7B.

Maps SemanticScar diagnostics to explicit repair candidates.

Boundary:
- routing suggests repairs; it does not execute them;
- routing does not write NOEMA;
- routing does not update CURRENT;
- routing does not promote SOURCE or canon.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from hashlib import sha256
import json
from typing import Any

from cielingo_core.meaning.meaning_loop import MeaningLoop, SemanticScarType


class RepairRouteKind(str, Enum):
    ATTACH_SOURCE = "attach_source"
    KEEP_HYPOTHESIS = "keep_hypothesis"
    ADD_NATIVE_REVIEW = "add_native_review"
    MARK_ALIGNMENT_CANDIDATE = "mark_alignment_candidate"
    RESOLVE_COUPLING = "resolve_coupling"
    BLOCK_AUTHORITY = "block_authority"
    ADD_TEST = "add_test"
    QUARANTINE = "quarantine"


@dataclass(frozen=True)
class MeaningRepairCandidate:
    repair_id: str
    route_kind: RepairRouteKind
    source_scar_id: str
    target_ref: str
    description: str
    required_before_closure: bool
    confidence: float
    executes_runtime_action: bool = False
    canon_allowed: bool = False
    source_promotion_allowed: bool = False
    noema_writeback_allowed: bool = False
    current_update_allowed: bool = False
    limitation: str = "repair_candidate_not_execution"

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.repair_id:
            issues.append("repair_id is required")
        if not self.source_scar_id:
            issues.append("source_scar_id is required")
        if not self.target_ref:
            issues.append("target_ref is required")
        if not self.description:
            issues.append("description is required")
        if not 0.0 <= float(self.confidence) <= 1.0:
            issues.append("confidence must be in [0,1]")
        if self.executes_runtime_action:
            issues.append("repair candidate must not execute runtime action")
        if self.canon_allowed:
            issues.append("repair candidate must not allow canon")
        if self.source_promotion_allowed:
            issues.append("repair candidate must not promote SOURCE")
        if self.noema_writeback_allowed:
            issues.append("repair candidate must not write NOEMA")
        if self.current_update_allowed:
            issues.append("repair candidate must not update CURRENT")
        if "not_execution" not in self.limitation:
            issues.append("repair candidate must state not_execution limitation")
        return issues

    def to_dict(self) -> dict[str, Any]:
        out = asdict(self)
        out["route_kind"] = self.route_kind.value
        return out


@dataclass(frozen=True)
class MeaningRepairRoutingReport:
    report_id: str
    loop_id: str
    loop_state: str
    candidates: list[MeaningRepairCandidate]
    unresolved_scar_ids: list[str] = field(default_factory=list)
    executes_runtime_action: bool = False
    canon_allowed: bool = False
    source_promotion_allowed: bool = False
    noema_writeback_allowed: bool = False
    current_update_allowed: bool = False
    limitation: str = "repair_routing_report_not_execution"

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.report_id:
            issues.append("report_id is required")
        if not self.loop_id:
            issues.append("loop_id is required")
        for candidate in self.candidates:
            issues.extend(candidate.validate())
        if self.executes_runtime_action:
            issues.append("routing report must not execute runtime action")
        if self.canon_allowed:
            issues.append("routing report must not allow canon")
        if self.source_promotion_allowed:
            issues.append("routing report must not promote SOURCE")
        if self.noema_writeback_allowed:
            issues.append("routing report must not write NOEMA")
        if self.current_update_allowed:
            issues.append("routing report must not update CURRENT")
        if "not_execution" not in self.limitation:
            issues.append("routing report must state not_execution limitation")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "loop_id": self.loop_id,
            "loop_state": self.loop_state,
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "unresolved_scar_ids": list(self.unresolved_scar_ids),
            "executes_runtime_action": self.executes_runtime_action,
            "canon_allowed": self.canon_allowed,
            "source_promotion_allowed": self.source_promotion_allowed,
            "noema_writeback_allowed": self.noema_writeback_allowed,
            "current_update_allowed": self.current_update_allowed,
            "limitation": self.limitation,
        }

    def stable_hash(self) -> str:
        payload = json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True)
        return sha256(payload.encode("utf-8")).hexdigest()


def _candidate(route_kind: RepairRouteKind, scar: Any, description: str, required: bool, confidence: float) -> MeaningRepairCandidate:
    payload = json.dumps({
        "route_kind": route_kind.value,
        "scar_id": getattr(scar, "scar_id", ""),
        "source_ref": getattr(scar, "source_ref", ""),
        "description": description,
    }, ensure_ascii=False, sort_keys=True)
    return MeaningRepairCandidate(
        repair_id="repair_" + sha256(payload.encode("utf-8")).hexdigest()[:16],
        route_kind=route_kind,
        source_scar_id=str(getattr(scar, "scar_id", "")),
        target_ref=str(getattr(scar, "source_ref", "")),
        description=description,
        required_before_closure=required,
        confidence=max(0.0, min(1.0, float(confidence))),
        executes_runtime_action=False,
        canon_allowed=False,
        source_promotion_allowed=False,
        noema_writeback_allowed=False,
        current_update_allowed=False,
    )


def route_repairs_for_meaning_loop(loop: MeaningLoop) -> MeaningRepairRoutingReport:
    """Route loop scars to explicit repair candidates.

    It returns a report. It does not perform the repair.
    """
    candidates: list[MeaningRepairCandidate] = []
    unresolved: list[str] = []

    for scar in loop.scars:
        stype = scar.scar_type
        severity = float(getattr(scar, "severity", 0.0))

        if stype == SemanticScarType.MISSING_SOURCE:
            candidates.append(_candidate(
                RepairRouteKind.ATTACH_SOURCE,
                scar,
                "Attach verifiable source artifact, or keep the statement explicitly as hypothesis.",
                True,
                max(0.75, severity),
            ))
            candidates.append(_candidate(
                RepairRouteKind.KEEP_HYPOTHESIS,
                scar,
                "If source is unavailable, preserve uncertainty operator and do not promote to SOURCE/canon.",
                True,
                0.70,
            ))
        elif stype == SemanticScarType.NATIVE_REVIEW_REQUIRED:
            candidates.append(_candidate(
                RepairRouteKind.ADD_NATIVE_REVIEW,
                scar,
                "Route JA/regional alignment through native/regional review before any stronger claim.",
                True,
                max(0.70, severity),
            ))
        elif stype == SemanticScarType.TRANSLATION_RESIDUE:
            candidates.append(_candidate(
                RepairRouteKind.MARK_ALIGNMENT_CANDIDATE,
                scar,
                "Keep cross-language result as alignment_candidate; add corpus test if recurring.",
                False,
                max(0.55, severity),
            ))
            candidates.append(_candidate(
                RepairRouteKind.ADD_TEST,
                scar,
                "Add or expand triad/coupling corpus case covering this residue.",
                False,
                0.60,
            ))
        elif stype == SemanticScarType.COUPLING_RESIDUE:
            candidates.append(_candidate(
                RepairRouteKind.RESOLVE_COUPLING,
                scar,
                "Inspect unresolved slot/card coupling; extend atlas or mark residue explicitly.",
                False,
                max(0.60, severity),
            ))
        elif stype in {SemanticScarType.AUTHORITY_LEAK, SemanticScarType.FALSE_CLOSURE}:
            candidates.append(_candidate(
                RepairRouteKind.BLOCK_AUTHORITY,
                scar,
                "Force authority flags false and block false closure before merge.",
                True,
                1.0,
            ))
            candidates.append(_candidate(
                RepairRouteKind.QUARANTINE,
                scar,
                "Quarantine affected object until authority leak is repaired and tested.",
                True,
                0.95,
            ))
        else:
            unresolved.append(str(getattr(scar, "scar_id", "")))

    payload = json.dumps({
        "loop_id": loop.loop_id,
        "candidate_ids": [c.repair_id for c in candidates],
        "unresolved": unresolved,
    }, ensure_ascii=False, sort_keys=True)

    return MeaningRepairRoutingReport(
        report_id="repair_route_" + sha256(payload.encode("utf-8")).hexdigest()[:16],
        loop_id=loop.loop_id,
        loop_state=loop.loop_state.value if hasattr(loop.loop_state, "value") else str(loop.loop_state),
        candidates=candidates,
        unresolved_scar_ids=unresolved,
        executes_runtime_action=False,
        canon_allowed=False,
        source_promotion_allowed=False,
        noema_writeback_allowed=False,
        current_update_allowed=False,
    )
