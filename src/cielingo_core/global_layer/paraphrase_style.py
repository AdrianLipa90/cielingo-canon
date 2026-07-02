"""Paraphrase/style probe layer v1.1K.

This layer tests whether a draft answer can be expressed in several styles
while preserving epistemic boundaries. It is not open-ended generation,
not SOURCE/canon, and not runtime execution.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from hashlib import sha256
import json
from typing import Any

from cielingo_core.global_layer.query_generation import (
    DraftAnswerCandidate,
    run_query_generation_dry_run,
)


class StyleRegister(str, Enum):
    SHORT = "short"
    TECHNICAL = "technical"
    HUMAN = "human"
    FORMAL = "formal"
    REFUSAL = "refusal"
    UNCERTAINTY = "uncertainty"


@dataclass(frozen=True)
class ParaphraseCandidate:
    style: str
    text: str
    source_answer_id: str
    is_source: bool = False
    is_canon: bool = False
    draft_only: bool = True
    canon_allowed: bool = False
    source_promotion_allowed: bool = False
    noema_writeback_allowed: bool = False
    current_update_allowed: bool = False
    runtime_execution_allowed: bool = False
    limitation: str = "paraphrase_candidate_not_source_not_canon_not_execution"

    def validate(self) -> list[str]:
        issues: list[str] = []
        if self.style not in {item.value for item in StyleRegister}:
            issues.append("unknown style")
        if not self.text:
            issues.append("text is required")
        if not self.source_answer_id:
            issues.append("source_answer_id is required")
        if self.is_source:
            issues.append("paraphrase must not be SOURCE")
        if self.is_canon:
            issues.append("paraphrase must not be canon")
        if not self.draft_only:
            issues.append("paraphrase must remain draft_only")
        if self.canon_allowed:
            issues.append("paraphrase must not allow canon")
        if self.source_promotion_allowed:
            issues.append("paraphrase must not promote SOURCE")
        if self.noema_writeback_allowed:
            issues.append("paraphrase must not write NOEMA")
        if self.current_update_allowed:
            issues.append("paraphrase must not update CURRENT")
        if self.runtime_execution_allowed:
            issues.append("paraphrase must not allow runtime execution")
        if "not_source" not in self.limitation or "not_execution" not in self.limitation:
            issues.append("limitation must state not_source and not_execution")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def stable_hash(self) -> str:
        return sha256(json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ParaphraseStyleProbeReport:
    query: str
    answer_id: str
    styles: list[ParaphraseCandidate]
    passed_invariants: bool
    issues: list[str]
    ja_parked: bool = True
    limitation: str = "style_probe_not_open_generation_not_runtime_cognition"
    canon_allowed: bool = False
    source_promotion_allowed: bool = False
    noema_writeback_allowed: bool = False
    current_update_allowed: bool = False
    runtime_execution_allowed: bool = False

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.query:
            issues.append("query is required")
        if not self.answer_id:
            issues.append("answer_id is required")
        if not self.styles:
            issues.append("styles are required")
        seen = {candidate.style for candidate in self.styles}
        required = {item.value for item in StyleRegister}
        if seen != required:
            issues.append(f"style set mismatch: {sorted(seen)}")
        for candidate in self.styles:
            issues.extend(candidate.validate())
        if not self.ja_parked:
            issues.append("JA must remain parked for default style probes")
        if self.canon_allowed or self.source_promotion_allowed:
            issues.append("report must not allow canon/source promotion")
        if self.noema_writeback_allowed or self.current_update_allowed or self.runtime_execution_allowed:
            issues.append("report must not allow NOEMA/CURRENT/runtime actions")
        if self.issues and self.passed_invariants:
            issues.append("report cannot pass invariants with issues")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "answer_id": self.answer_id,
            "styles": [candidate.to_dict() for candidate in self.styles],
            "passed_invariants": self.passed_invariants,
            "issues": list(self.issues),
            "ja_parked": self.ja_parked,
            "limitation": self.limitation,
            "canon_allowed": self.canon_allowed,
            "source_promotion_allowed": self.source_promotion_allowed,
            "noema_writeback_allowed": self.noema_writeback_allowed,
            "current_update_allowed": self.current_update_allowed,
            "runtime_execution_allowed": self.runtime_execution_allowed,
        }

    def stable_hash(self) -> str:
        return sha256(json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def _render(style: StyleRegister, answer: DraftAnswerCandidate) -> str:
    base = answer.draft_text.replace("draft_answer_candidate:", "").strip()
    if style == StyleRegister.SHORT:
        return "draft_only: robocza odpowiedź; bez SOURCE, canon i wykonania runtime."
    if style == StyleRegister.TECHNICAL:
        return (
            "draft_only technical paraphrase: generated candidate; "
            "source_promotion=false; canon=false; runtime_execution=false; "
            "noema_writeback=false; current_update=false. " + base
        )
    if style == StyleRegister.HUMAN:
        return "Roboczo: mogę to ująć prosto, ale nie udaję źródła, kanonu ani wykonanej akcji. " + base
    if style == StyleRegister.FORMAL:
        return (
            "Formal statement: this response is a bounded draft candidate, "
            "not a source assertion, not canon, and not an execution report. " + base
        )
    if style == StyleRegister.REFUSAL:
        return (
            "Boundary-preserving refusal form: nie wykonuję awansu autorytetu, SOURCE, canon, "
            "CURRENT ani runtime. Jeśli wymagane jest źródło, potrzebny jest artefakt."
        )
    if style == StyleRegister.UNCERTAINTY:
        return "meaning_candidate: odpowiedź robocza, confidence ograniczone; uncertainty_operator=chyba; bez SOURCE/canon. " + base
    raise ValueError(style)


def build_paraphrase_style_probe(query: str, repo_root) -> ParaphraseStyleProbeReport:
    dry = run_query_generation_dry_run(query, repo_root)
    styles = [
        ParaphraseCandidate(
            style=style.value,
            text=_render(style, dry.answer),
            source_answer_id=dry.answer.answer_id,
        )
        for style in StyleRegister
    ]
    issues: list[str] = []
    issues.extend(dry.validate())
    for candidate in styles:
        issues.extend(candidate.validate())
    report = ParaphraseStyleProbeReport(
        query=query,
        answer_id=dry.answer.answer_id,
        styles=styles,
        passed_invariants=not issues,
        issues=issues,
        ja_parked=True,
    )
    final_issues = report.validate()
    if final_issues:
        return ParaphraseStyleProbeReport(
            query=query,
            answer_id=dry.answer.answer_id,
            styles=styles,
            passed_invariants=False,
            issues=final_issues,
            ja_parked=True,
        )
    return report
