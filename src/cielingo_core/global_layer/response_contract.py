
"""GLOBAL response contract v1.1B."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json
from typing import Any

from cielingo_core.global_layer.query_generation import QueryGenerationDryRunReport


@dataclass(frozen=True)
class AllowedResponseContract:
    contract_id: str
    intention: str
    answer_kind: str
    severity: str
    required_markers: list[str]
    forbidden_claims: list[str]
    uncertainty_required: bool
    source_required: bool
    runtime_execution_allowed: bool = False
    canon_allowed: bool = False
    source_promotion_allowed: bool = False
    noema_writeback_allowed: bool = False
    current_update_allowed: bool = False
    repair_routes: list[str] = field(default_factory=list)
    limitation: str = "allowed_response_contract_not_final_text_not_execution"

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.contract_id:
            issues.append("contract_id is required")
        if not self.answer_kind:
            issues.append("answer_kind is required")
        if not self.required_markers:
            issues.append("required_markers must not be empty")
        if self.runtime_execution_allowed:
            issues.append("contract must not allow runtime execution")
        if self.canon_allowed:
            issues.append("contract must not allow canon")
        if self.source_promotion_allowed:
            issues.append("contract must not promote SOURCE")
        if self.noema_writeback_allowed:
            issues.append("contract must not write NOEMA")
        if self.current_update_allowed:
            issues.append("contract must not update CURRENT")
        if "not_final_text" not in self.limitation or "not_execution" not in self.limitation:
            issues.append("contract limitation must state not_final_text and not_execution")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def stable_hash(self) -> str:
        return sha256(json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def build_response_contract_from_query_report(report: QueryGenerationDryRunReport) -> AllowedResponseContract:
    q = report.query
    severity = report.answer.signal_severity
    routes = list(report.route_kinds)

    if q.authority_attempt or "block_authority" in routes or report.answer.dry_run_decision == "block_and_quarantine":
        answer_kind = "runtime_dry_run_refusal"
        required = ["dry-run", "nie wykonuję runtime", "nie CURRENT", "nie ACTIVE"]
        forbidden = ["wykonałem", "ustawiłem", "ACTIVE=true", "CURRENT updated"]
    elif q.source_required:
        answer_kind = "source_missing_hypothesis"
        required = ["brak źródła", "hipoteza", "nie SOURCE", "nie canon"]
        forbidden = ["potwierdzone", "wykonane", "SOURCE", "canon"]
    elif q.intention == "generate_text":
        answer_kind = "draft_text_generation"
        required = ["draft_answer_candidate", "nie SOURCE", "nie canon"]
        forbidden = ["to jest fakt", "SOURCE", "canon"]
    elif "alignment" in q.query.lower() or "semantic identity" in q.query.lower():
        answer_kind = "alignment_candidate_explanation"
        required = ["kandydat", "nie dowód", "nie semantic identity"]
        forbidden = ["semantic identity confirmed", "dowód równoważności"]
    elif "repair" in routes or "attach_source" in routes or "add_test" in routes:
        answer_kind = "repair_required"
        required = ["repair_required", "brak domknięcia", "nie PASS"]
        forbidden = ["PASS", "domknięte", "bez długu"]
    else:
        answer_kind = "draft_text_generation"
        required = ["draft_answer_candidate", "nie SOURCE", "nie canon"]
        forbidden = ["to jest fakt", "SOURCE", "canon"]

    payload = json.dumps({"query_id": q.query_id, "answer_kind": answer_kind, "required": required, "routes": routes, "severity": severity}, ensure_ascii=False, sort_keys=True)
    return AllowedResponseContract(
        contract_id="response_contract_" + sha256(payload.encode("utf-8")).hexdigest()[:16],
        intention=q.intention,
        answer_kind=answer_kind,
        severity=severity,
        required_markers=required,
        forbidden_claims=forbidden,
        uncertainty_required=bool(q.uncertainty_required),
        source_required=bool(q.source_required),
        runtime_execution_allowed=False,
        canon_allowed=False,
        source_promotion_allowed=False,
        noema_writeback_allowed=False,
        current_update_allowed=False,
        repair_routes=routes,
    )


def build_response_contract(
    *,
    intention: str,
    answer_kind: str,
    severity: str,
    required_markers: list[str],
    forbidden_claims: list[str] | None = None,
    uncertainty_required: bool = False,
    source_required: bool = False,
    repair_routes: list[str] | None = None,
) -> AllowedResponseContract:
    payload = json.dumps({"intention": intention, "answer_kind": answer_kind, "severity": severity, "required": required_markers, "forbidden": forbidden_claims or [], "routes": repair_routes or []}, ensure_ascii=False, sort_keys=True)
    return AllowedResponseContract(
        contract_id="response_contract_" + sha256(payload.encode("utf-8")).hexdigest()[:16],
        intention=intention,
        answer_kind=answer_kind,
        severity=severity,
        required_markers=list(required_markers),
        forbidden_claims=list(forbidden_claims or []),
        uncertainty_required=uncertainty_required,
        source_required=source_required,
        runtime_execution_allowed=False,
        canon_allowed=False,
        source_promotion_allowed=False,
        noema_writeback_allowed=False,
        current_update_allowed=False,
        repair_routes=list(repair_routes or []),
    )
