
"""Global dry-test reference builder v0.9A.

Runs corpus cases through the full advisory chain and exports reference objects.

This is not SOURCE, not canon, and not NOEMA SoT. It is an artifact-grounded
reference over local dry-run output.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
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
from cielingo_core.global_layer.self_feed_audit import build_runtime_dry_run_export_bundle
from cielingo_core.global_layer.runtime_adapter_interface import RuntimeAdapterReference, adapt_runtime_dry_run_reference


@dataclass(frozen=True)
class GlobalDryTestReference:
    reference_id: str
    case_count: int
    runtime_references: list[RuntimeAdapterReference]
    dry_run_export_hash: str
    severity_counts: dict[str, int]
    decision_counts: dict[str, int]
    reference_kind: str = "artifact_grounded_reference"
    canon_allowed: bool = False
    source_promotion_allowed: bool = False
    noema_writeback_allowed: bool = False
    current_update_allowed: bool = False
    runtime_execution_allowed: bool = False
    limitation: str = "global_dry_test_reference_not_source_not_execution"

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.reference_id:
            issues.append("reference_id is required")
        if self.case_count != len(self.runtime_references):
            issues.append("case_count must equal runtime_references length")
        for ref in self.runtime_references:
            issues.extend(ref.validate())
        if self.reference_kind != "artifact_grounded_reference":
            issues.append("reference_kind must be artifact_grounded_reference")
        if self.canon_allowed:
            issues.append("global reference must not allow canon")
        if self.source_promotion_allowed:
            issues.append("global reference must not promote SOURCE")
        if self.noema_writeback_allowed:
            issues.append("global reference must not write NOEMA")
        if self.current_update_allowed:
            issues.append("global reference must not update CURRENT")
        if self.runtime_execution_allowed:
            issues.append("global reference must not allow runtime execution")
        if "not_source" not in self.limitation or "not_execution" not in self.limitation:
            issues.append("global reference must state not_source and not_execution limitation")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "reference_id": self.reference_id,
            "case_count": self.case_count,
            "runtime_references": [ref.to_dict() for ref in self.runtime_references],
            "dry_run_export_hash": self.dry_run_export_hash,
            "severity_counts": dict(sorted(self.severity_counts.items())),
            "decision_counts": dict(sorted(self.decision_counts.items())),
            "reference_kind": self.reference_kind,
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


def _signal_for_case(case: dict[str, Any], repo_root: Path):
    # lazy import to break circular chain: alignment → language_spaces → global_layer → alignment
    from cielingo_core.alignment.cross_language import build_coupling_aware_cross_language_alignment_report
    cards = repo_root / "cards" / "generated_examples" / "controlled_48_slot_runtime_cards_v0_6a.jsonl"
    if "text" in case:
        eq = solve_pl_sentence_equation(case["text"], repo_root)
        snap = build_sentence_state_snapshot(eq, notes=[])
        coupling = build_sentence_card_coupling(snap, cards)
        if case.get("inject_authority_leak"):
            from dataclasses import replace
            coupling = replace(coupling, canon_allowed=True)
        loop = build_meaning_loop_from_coupling_alignment(
            input_ref=case["id"],
            coupling_report=coupling,
            source_required=case.get("source_required", False),
            source_present=case.get("source_present", False),
        )
    else:
        alignment = build_coupling_aware_cross_language_alignment_report(case["triad"], repo_root)
        loop = build_meaning_loop_from_coupling_alignment(input_ref=case["id"], alignment_report=alignment)

    routing = route_repairs_for_meaning_loop(loop)
    signal = build_global_meaning_signal(loop, routing)
    dry = run_runtime_bridge_dry_run(signal)
    ref = adapt_runtime_dry_run_reference(dry)
    return loop, routing, signal, dry, ref


def run_global_dry_test_reference(repo_root: str | Path, corpus_path: str | Path | None = None) -> tuple[GlobalDryTestReference, Any]:
    repo = Path(repo_root)
    corpus_path = Path(corpus_path) if corpus_path is not None else repo / "corpus" / "global_signal_bridge_corpus_v08b.json"
    corpus = json.loads(corpus_path.read_text(encoding="utf-8"))

    loops = []
    routings = []
    signals = []
    dry_runs = []
    refs = []
    severity_counts: dict[str, int] = {}
    decision_counts: dict[str, int] = {}

    for case in corpus["cases"]:
        loop, routing, signal, dry, ref = _signal_for_case(case, repo)
        loops.append(loop)
        routings.append(routing)
        signals.append(signal)
        dry_runs.append(dry)
        refs.append(ref)
        severity_counts[signal.severity.value if hasattr(signal.severity, "value") else str(signal.severity)] = severity_counts.get(signal.severity.value if hasattr(signal.severity, "value") else str(signal.severity), 0) + 1
        decision_counts[dry.decision.value if hasattr(dry.decision, "value") else str(dry.decision)] = decision_counts.get(dry.decision.value if hasattr(dry.decision, "value") else str(dry.decision), 0) + 1

    export_bundle = build_runtime_dry_run_export_bundle(loops, routings, signals, dry_runs)
    payload = json.dumps({
        "case_count": len(refs),
        "refs": [ref.reference_id for ref in refs],
        "export_hash": export_bundle.stable_hash(),
        "severity_counts": severity_counts,
        "decision_counts": decision_counts,
    }, ensure_ascii=False, sort_keys=True)

    reference = GlobalDryTestReference(
        reference_id="global_dry_reference_" + sha256(payload.encode("utf-8")).hexdigest()[:16],
        case_count=len(refs),
        runtime_references=refs,
        dry_run_export_hash=export_bundle.stable_hash(),
        severity_counts=severity_counts,
        decision_counts=decision_counts,
        reference_kind="artifact_grounded_reference",
        canon_allowed=False,
        source_promotion_allowed=False,
        noema_writeback_allowed=False,
        current_update_allowed=False,
        runtime_execution_allowed=False,
    )
    return reference, export_bundle
