
"""Query understanding and text generation dry-run v1.1A.

This layer creates draft answer candidates from query-understanding diagnostics.

Boundary:
- QueryUnderstandingResult is a heuristic classification, not full understanding.
- DraftAnswerCandidate is generated text, not SOURCE/canon/truth proof.
- No runtime execution, NOEMA writeback, or CURRENT update.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from enum import Enum
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


class QueryIntention(str, Enum):
    ASK = "ask"
    COMMAND = "command"
    VERIFY = "verify"
    GENERATE_TEXT = "generate_text"
    REFUSE_OR_BOUNDARY = "refuse_or_boundary"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class QueryUnderstandingResult:
    query_id: str
    query: str
    intention: QueryIntention
    force: float
    source_required: bool
    execution_requested: bool
    canon_attempt: bool
    authority_attempt: bool
    uncertainty_required: bool
    evidence: list[str]
    heuristic_only: bool = True
    canon_allowed: bool = False
    source_promotion_allowed: bool = False
    noema_writeback_allowed: bool = False
    current_update_allowed: bool = False
    runtime_execution_allowed: bool = False
    limitation: str = "query_understanding_heuristic_not_full_semantic_understanding"

    def validate(self) -> list[str]:
        issues = []
        if not self.query_id:
            issues.append("query_id is required")
        if not self.query:
            issues.append("query is required")
        if not 0.0 <= self.force <= 1.0:
            issues.append("force must be in [0,1]")
        if not self.heuristic_only:
            issues.append("query understanding must remain heuristic_only")
        if self.canon_allowed:
            issues.append("query understanding must not allow canon")
        if self.source_promotion_allowed:
            issues.append("query understanding must not promote SOURCE")
        if self.noema_writeback_allowed:
            issues.append("query understanding must not write NOEMA")
        if self.current_update_allowed:
            issues.append("query understanding must not update CURRENT")
        if self.runtime_execution_allowed:
            issues.append("query understanding must not allow runtime execution")
        if "heuristic" not in self.limitation:
            issues.append("limitation must state heuristic")
        return issues

    def to_dict(self) -> dict[str, Any]:
        out = asdict(self)
        out["intention"] = self.intention.value
        return out

    def stable_hash(self) -> str:
        return sha256(json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class DraftAnswerCandidate:
    answer_id: str
    query_id: str
    draft_text: str
    intention: str
    signal_severity: str
    dry_run_decision: str
    adapter_action: str
    confidence: float
    is_source: bool = False
    is_canon: bool = False
    draft_only: bool = True
    canon_allowed: bool = False
    source_promotion_allowed: bool = False
    noema_writeback_allowed: bool = False
    current_update_allowed: bool = False
    runtime_execution_allowed: bool = False
    limitation: str = "draft_answer_candidate_not_source_not_canon_not_execution"

    def validate(self) -> list[str]:
        issues = []
        if not self.answer_id:
            issues.append("answer_id is required")
        if not self.query_id:
            issues.append("query_id is required")
        if not self.draft_text:
            issues.append("draft_text is required")
        if not 0.0 <= self.confidence <= 1.0:
            issues.append("confidence must be in [0,1]")
        if self.is_source:
            issues.append("draft answer must not be SOURCE")
        if self.is_canon:
            issues.append("draft answer must not be canon")
        if not self.draft_only:
            issues.append("draft answer must remain draft_only")
        if self.canon_allowed:
            issues.append("draft answer must not allow canon")
        if self.source_promotion_allowed:
            issues.append("draft answer must not promote SOURCE")
        if self.noema_writeback_allowed:
            issues.append("draft answer must not write NOEMA")
        if self.current_update_allowed:
            issues.append("draft answer must not update CURRENT")
        if self.runtime_execution_allowed:
            issues.append("draft answer must not allow runtime execution")
        if "not_source" not in self.limitation or "not_execution" not in self.limitation:
            issues.append("limitation must state not_source and not_execution")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def stable_hash(self) -> str:
        return sha256(json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class QueryGenerationDryRunReport:
    report_id: str
    query: QueryUnderstandingResult
    answer: DraftAnswerCandidate
    route_kinds: list[str]
    reference_id: str
    reference_hash: str
    passed_invariants: bool
    issues: list[str]
    reference_kind: str = "artifact_grounded_query_generation_dry_run"
    canon_allowed: bool = False
    source_promotion_allowed: bool = False
    noema_writeback_allowed: bool = False
    current_update_allowed: bool = False
    runtime_execution_allowed: bool = False
    limitation: str = "query_generation_dry_run_not_source_not_execution"

    def validate(self) -> list[str]:
        issues = []
        issues.extend(self.query.validate())
        issues.extend(self.answer.validate())
        if self.issues and self.passed_invariants:
            issues.append("report cannot pass invariants while issues are present")
        if self.reference_kind != "artifact_grounded_query_generation_dry_run":
            issues.append("wrong reference_kind")
        if self.canon_allowed:
            issues.append("report must not allow canon")
        if self.source_promotion_allowed:
            issues.append("report must not promote SOURCE")
        if self.noema_writeback_allowed:
            issues.append("report must not write NOEMA")
        if self.current_update_allowed:
            issues.append("report must not update CURRENT")
        if self.runtime_execution_allowed:
            issues.append("report must not allow runtime execution")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "query": self.query.to_dict(),
            "answer": self.answer.to_dict(),
            "route_kinds": list(self.route_kinds),
            "reference_id": self.reference_id,
            "reference_hash": self.reference_hash,
            "passed_invariants": self.passed_invariants,
            "issues": list(self.issues),
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


def understand_query(query: str, *, source_required: bool | None = None, inject_authority_leak: bool = False) -> QueryUnderstandingResult:
    q = query.strip()
    low = q.lower()
    evidence: list[str] = []
    intention = QueryIntention.UNKNOWN

    if "?" in q or low.startswith(("czy", "co ", "jak ", "dlaczego", "wyjaśnij")):
        intention = QueryIntention.ASK
        evidence.append("question_marker_or_question_word")
    if any(x in low for x in ["wygeneruj", "napisz", "stwórz tekst", "generate"]):
        intention = QueryIntention.GENERATE_TEXT
        evidence.append("generation_keyword")
    if any(x in low for x in ["sprawdź", "ustaw", "zapisz", "uruchom", "wykonaj", "podaj wynik", "kanonizuj", "nie kanonizuj", "promuj", "nie promuj"]):
        intention = QueryIntention.COMMAND
        evidence.append("command_keyword")
    if any(x in low for x in ["źródło", "source", "dowód", "evidence"]):
        evidence.append("source_keyword")
    if any(x in low for x in ["kanon", "canon", "source", "active", "current", "pass"]):
        evidence.append("authority_sensitive_keyword")

    computed_source_required = bool(source_required) if source_required is not None else any(x in low for x in ["źródło", "source", "dowód", "evidence"])
    execution_requested = any(x in low for x in ["ustaw", "zapisz", "uruchom", "wykonaj"])
    canon_attempt = any(x in low for x in ["kanonizuj", "canon"])
    authority_attempt = inject_authority_leak or any(x in low for x in ["ustaw active", "ustaw current", "source bez testu", "fałszywego pass"])

    force = 0.35
    if intention == QueryIntention.COMMAND:
        force += 0.35
    if execution_requested:
        force += 0.2
    if authority_attempt:
        force += 0.1
    force = max(0.0, min(1.0, force))

    query_id = "query_" + sha256(q.encode("utf-8")).hexdigest()[:16]
    return QueryUnderstandingResult(
        query_id=query_id,
        query=q,
        intention=intention,
        force=round(force, 6),
        source_required=computed_source_required,
        execution_requested=execution_requested,
        canon_attempt=canon_attempt,
        authority_attempt=authority_attempt,
        uncertainty_required=computed_source_required,
        evidence=evidence,
        heuristic_only=True,
        canon_allowed=False,
        source_promotion_allowed=False,
        noema_writeback_allowed=False,
        current_update_allowed=False,
        runtime_execution_allowed=False,
    )


def _compose_draft(query: QueryUnderstandingResult, route_kinds: list[str], severity: str, decision: str, adapter_action: str) -> str:
    if query.authority_attempt or "block_authority" in route_kinds or decision == "block_and_quarantine":
        return (
            "draft_answer_candidate: odmawiam wykonania lub awansu authority w tym trybie. "
            "To jest dry-run; nie wykonuję akcji runtime, nie ustawiam ACTIVE/CURRENT, nie promuję SOURCE/canon. "
            "Wynik pozostaje kandydatem diagnostycznym."
        )
    if query.source_required:
        return (
            "draft_answer_candidate: brak źródła w tym przebiegu; nie mam źródła, więc odpowiedź pozostaje hipotezą. "
            "Nie kanonizuję i nie promuję do SOURCE. Wymagane jest dołączenie weryfikowalnego artefaktu albo zachowanie operatora niepewności."
        )
    if query.intention == QueryIntention.COMMAND:
        return (
            "draft_answer_candidate: to jest dry-run komendy. "
            "Nie wykonuję akcji runtime i nie podaję wyniku jako faktu wykonania. "
            "Mogę wskazać wymagany artefakt, ścieżkę, test lub następny krok diagnostyczny."
        )
    if query.intention == QueryIntention.GENERATE_TEXT:
        return (
            "draft_answer_candidate: wygenerowany tekst roboczy o CIELingo. "
            "CIELingo jest scaffoldem semantyczno-neuronalnym dla analizy zapytań, pętli znaczenia i sygnałów naprawczych. "
            "Ten tekst nie jest SOURCE ani canon."
        )
    if "alignment" in query.query.lower() or "semantic identity" in query.query.lower():
        return (
            "draft_answer_candidate: alignment jest kandydatem dopasowania osi znaczenia; marker: nie dowód semantic identity. "
            "Wspólny slot lub karta wskazuje podobieństwo robocze, ale nie pełną równoważność."
        )
    if "artifact-grounded" in query.query.lower() or "source" in query.query.lower():
        return (
            "draft_answer_candidate: SOURCE oznacza zweryfikowane źródło w ustalonym SoT, a artifact-grounded reference oznacza lokalne odniesienie do artefaktu. "
            "Artifact-grounded nie daje automatycznie statusu SOURCE."
        )
    return (
        "draft_answer_candidate: zapytanie zostało sklasyfikowane heurystycznie. "
        "Odpowiedź pozostaje robocza, bez SOURCE/canon i bez wykonania runtime."
    )


def run_query_generation_dry_run(
    query: str,
    repo_root: str | Path,
    *,
    source_required: bool | None = None,
    inject_authority_leak: bool = False,
) -> QueryGenerationDryRunReport:
    repo = Path(repo_root)
    cards = repo / "cards" / "generated_examples" / "controlled_48_slot_runtime_cards_v0_6a.jsonl"
    understood = understand_query(query, source_required=source_required, inject_authority_leak=inject_authority_leak)

    eq = solve_pl_sentence_equation(query, repo)
    snap = build_sentence_state_snapshot(eq, notes=[])
    coupling = build_sentence_card_coupling(snap, cards)
    if understood.authority_attempt:
        coupling = replace(coupling, canon_allowed=True)

    loop = build_meaning_loop_from_coupling_alignment(
        input_ref=understood.query_id,
        coupling_report=coupling,
        source_required=understood.source_required,
        source_present=False,
    )
    routing = route_repairs_for_meaning_loop(loop)
    signal = build_global_meaning_signal(loop, routing)
    dry = run_runtime_bridge_dry_run(signal)
    ref = adapt_runtime_dry_run_reference(dry)
    route_kinds = [c.route_kind.value if hasattr(c.route_kind, "value") else str(c.route_kind) for c in routing.candidates]
    severity = signal.severity.value if hasattr(signal.severity, "value") else str(signal.severity)
    decision = dry.decision.value if hasattr(dry.decision, "value") else str(dry.decision)
    adapter_action = ref.adapter_action.value if hasattr(ref.adapter_action, "value") else str(ref.adapter_action)

    draft = _compose_draft(understood, route_kinds, severity, decision, adapter_action)
    confidence = 0.45
    if understood.intention != QueryIntention.UNKNOWN:
        confidence += 0.2
    if not understood.authority_attempt:
        confidence += 0.1
    confidence = min(0.75, confidence)

    answer_id = "draft_answer_" + sha256(json.dumps({
        "query": understood.query_id,
        "draft": draft,
        "severity": severity,
        "decision": decision,
    }, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()[:16]

    answer = DraftAnswerCandidate(
        answer_id=answer_id,
        query_id=understood.query_id,
        draft_text=draft,
        intention=understood.intention.value,
        signal_severity=severity,
        dry_run_decision=decision,
        adapter_action=adapter_action,
        confidence=round(confidence, 6),
        is_source=False,
        is_canon=False,
        draft_only=True,
        canon_allowed=False,
        source_promotion_allowed=False,
        noema_writeback_allowed=False,
        current_update_allowed=False,
        runtime_execution_allowed=False,
    )

    issues: list[str] = []
    issues.extend(understood.validate())
    issues.extend(answer.validate())
    if signal.canon_allowed or signal.source_promotion_allowed or signal.noema_writeback_allowed or signal.current_update_allowed or signal.runtime_execution_allowed:
        issues.append("signal authority leak")
    if dry.executed_runtime_action or dry.noema_writeback_allowed or dry.current_update_allowed:
        issues.append("dry-run authority leak")
    if ref.executes_runtime_action or ref.noema_writeback_allowed or ref.current_update_allowed:
        issues.append("adapter reference authority leak")

    report_id = "query_generation_dry_run_" + sha256(json.dumps({
        "query": understood.query_id,
        "answer": answer.answer_id,
        "ref": ref.reference_id,
    }, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()[:16]

    return QueryGenerationDryRunReport(
        report_id=report_id,
        query=understood,
        answer=answer,
        route_kinds=route_kinds,
        reference_id=ref.reference_id,
        reference_hash=ref.stable_hash(),
        passed_invariants=not issues,
        issues=issues,
        reference_kind="artifact_grounded_query_generation_dry_run",
        canon_allowed=False,
        source_promotion_allowed=False,
        noema_writeback_allowed=False,
        current_update_allowed=False,
        runtime_execution_allowed=False,
    )
