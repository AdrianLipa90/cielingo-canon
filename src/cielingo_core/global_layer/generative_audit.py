
"""Post-freeze deterministic generative audit v1.0G."""

from __future__ import annotations
from dataclasses import dataclass, asdict, replace
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from cielingo_core.language_spaces.pl.sentence_equation import solve_pl_sentence_equation
from cielingo_core.semantic_neural.sentence_state import build_sentence_state_snapshot
from cielingo_core.semantic_neural.atlas_coupling import build_sentence_card_coupling
from cielingo_core.meaning.meaning_loop import build_meaning_loop_from_coupling_alignment
from cielingo_core.meaning.repair_routing import route_repairs_for_meaning_loop
from cielingo_core.global_layer.meaning_signal_bridge import build_global_meaning_signal
from cielingo_core.global_layer.runtime_bridge_dry_run import run_runtime_bridge_dry_run
from cielingo_core.global_layer.runtime_adapter_interface import adapt_runtime_dry_run_reference


@dataclass(frozen=True)
class GenerativeAuditResult:
    case_id: str
    input_kind: str
    loop_state: str
    route_kinds: list[str]
    signal_severity: str
    dry_run_decision: str
    adapter_action: str
    reference_id: str
    reference_hash: str
    passed: bool
    issues: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GenerativeAuditReport:
    report_id: str
    freeze_id: str
    generated_count: int
    pass_count: int
    fail_count: int
    severity_counts: dict[str, int]
    decision_counts: dict[str, int]
    adapter_action_counts: dict[str, int]
    results: list[GenerativeAuditResult]
    reference_kind: str = "artifact_grounded_generative_audit"
    canon_allowed: bool = False
    source_promotion_allowed: bool = False
    noema_writeback_allowed: bool = False
    current_update_allowed: bool = False
    runtime_execution_allowed: bool = False
    limitation: str = "generative_audit_not_source_not_freeze_mutation"

    def validate(self) -> list[str]:
        issues = []
        if self.generated_count != len(self.results):
            issues.append("generated_count mismatch")
        if self.pass_count + self.fail_count != self.generated_count:
            issues.append("pass/fail count mismatch")
        if self.reference_kind != "artifact_grounded_generative_audit":
            issues.append("wrong reference_kind")
        if self.canon_allowed:
            issues.append("generative audit must not allow canon")
        if self.source_promotion_allowed:
            issues.append("generative audit must not promote SOURCE")
        if self.noema_writeback_allowed:
            issues.append("generative audit must not write NOEMA")
        if self.current_update_allowed:
            issues.append("generative audit must not update CURRENT")
        if self.runtime_execution_allowed:
            issues.append("generative audit must not allow runtime execution")
        if "not_source" not in self.limitation or "not_freeze_mutation" not in self.limitation:
            issues.append("limitation must state not_source and not_freeze_mutation")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "freeze_id": self.freeze_id,
            "generated_count": self.generated_count,
            "pass_count": self.pass_count,
            "fail_count": self.fail_count,
            "severity_counts": dict(sorted(self.severity_counts.items())),
            "decision_counts": dict(sorted(self.decision_counts.items())),
            "adapter_action_counts": dict(sorted(self.adapter_action_counts.items())),
            "results": [r.to_dict() for r in self.results],
            "reference_kind": self.reference_kind,
            "canon_allowed": self.canon_allowed,
            "source_promotion_allowed": self.source_promotion_allowed,
            "noema_writeback_allowed": self.noema_writeback_allowed,
            "current_update_allowed": self.current_update_allowed,
            "runtime_execution_allowed": self.runtime_execution_allowed,
            "limitation": self.limitation,
        }

    def stable_hash(self) -> str:
        return sha256(json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def _run_case(case: dict[str, Any], repo: Path):
    # lazy import to break circular chain: alignment → language_spaces → global_layer → alignment
    from cielingo_core.alignment.cross_language import build_coupling_aware_cross_language_alignment_report
    cards = repo / "cards" / "generated_examples" / "controlled_48_slot_runtime_cards_v0_6a.jsonl"
    if "triad" in case:
        alignment = build_coupling_aware_cross_language_alignment_report(case["triad"], repo)
        loop = build_meaning_loop_from_coupling_alignment(input_ref=case["id"], alignment_report=alignment)
        input_kind = "triad"
    else:
        eq = solve_pl_sentence_equation(case["text"], repo)
        snap = build_sentence_state_snapshot(eq, notes=[])
        coupling = build_sentence_card_coupling(snap, cards)
        if case.get("inject_authority_leak"):
            coupling = replace(coupling, canon_allowed=True)
        loop = build_meaning_loop_from_coupling_alignment(
            input_ref=case["id"],
            coupling_report=coupling,
            source_required=case.get("source_required", False),
            source_present=case.get("source_present", False),
        )
        input_kind = "pl_text"

    routing = route_repairs_for_meaning_loop(loop)
    signal = build_global_meaning_signal(loop, routing)
    dry = run_runtime_bridge_dry_run(signal)
    ref = adapt_runtime_dry_run_reference(dry)

    route_kinds = [c.route_kind.value if hasattr(c.route_kind, "value") else str(c.route_kind) for c in routing.candidates]
    adapter_action = ref.adapter_action.value if hasattr(ref.adapter_action, "value") else str(ref.adapter_action)
    severity = signal.severity.value if hasattr(signal.severity, "value") else str(signal.severity)
    decision = dry.decision.value if hasattr(dry.decision, "value") else str(dry.decision)

    issues = []
    if signal.canon_allowed or signal.source_promotion_allowed or signal.noema_writeback_allowed or signal.current_update_allowed or signal.runtime_execution_allowed:
        issues.append("signal authority leak")
    if dry.executed_runtime_action or dry.noema_writeback_allowed or dry.current_update_allowed:
        issues.append("dry-run authority leak")
    if ref.executes_runtime_action or ref.canon_allowed or ref.source_promotion_allowed or ref.noema_writeback_allowed or ref.current_update_allowed:
        issues.append("adapter reference authority leak")
    expected_routes = set(case.get("expected_routes_any", []))
    if expected_routes and not expected_routes.intersection(route_kinds):
        issues.append("expected route missing")
    expected_actions = set(case.get("expected_actions_any", []))
    if expected_actions and adapter_action not in expected_actions:
        issues.append("expected adapter action missing")

    return GenerativeAuditResult(
        case_id=case["id"],
        input_kind=input_kind,
        loop_state=loop.loop_state.value if hasattr(loop.loop_state, "value") else str(loop.loop_state),
        route_kinds=route_kinds,
        signal_severity=severity,
        dry_run_decision=decision,
        adapter_action=adapter_action,
        reference_id=ref.reference_id,
        reference_hash=ref.stable_hash(),
        passed=not issues,
        issues=issues,
    )


def run_generative_audit(repo_root: str | Path, corpus_path: str | Path | None = None) -> GenerativeAuditReport:
    repo = Path(repo_root)
    corpus_path = Path(corpus_path) if corpus_path else repo / "corpus" / "post_freeze_generative_corpus_v10g.json"
    corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
    results = [_run_case(case, repo) for case in corpus["cases"]]
    severity_counts = {}
    decision_counts = {}
    adapter_counts = {}
    for r in results:
        severity_counts[r.signal_severity] = severity_counts.get(r.signal_severity, 0) + 1
        decision_counts[r.dry_run_decision] = decision_counts.get(r.dry_run_decision, 0) + 1
        adapter_counts[r.adapter_action] = adapter_counts.get(r.adapter_action, 0) + 1
    pass_count = sum(1 for r in results if r.passed)
    payload = json.dumps({"ids":[r.case_id for r in results], "refs":[r.reference_id for r in results]}, ensure_ascii=False, sort_keys=True)
    return GenerativeAuditReport(
        report_id="generative_audit_" + sha256(payload.encode("utf-8")).hexdigest()[:16],
        freeze_id=corpus["freeze_id"],
        generated_count=len(results),
        pass_count=pass_count,
        fail_count=len(results)-pass_count,
        severity_counts=severity_counts,
        decision_counts=decision_counts,
        adapter_action_counts=adapter_counts,
        results=results,
    )
