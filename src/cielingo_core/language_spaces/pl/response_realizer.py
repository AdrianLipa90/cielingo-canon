
"""PL response realizer v1.1B."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Any

from cielingo_core.global_layer.response_contract import AllowedResponseContract
from cielingo_core.global_layer.marker_scan import forbidden_claims_after_required_markers


@dataclass(frozen=True)
class RegionalResponseDraft:
    draft_id: str
    language_id: str
    contract_id: str
    answer_kind: str
    text: str
    preserved_markers: list[str]
    missing_markers: list[str]
    forbidden_claims_present: list[str]
    canon_allowed: bool = False
    source_promotion_allowed: bool = False
    noema_writeback_allowed: bool = False
    current_update_allowed: bool = False
    runtime_execution_allowed: bool = False
    limitation: str = "regional_response_draft_not_source_not_execution"

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.draft_id:
            issues.append("draft_id is required")
        if self.language_id != "pl":
            issues.append("PL realizer must emit language_id=pl")
        if self.missing_markers:
            issues.append(f"missing required markers: {self.missing_markers}")
        if self.forbidden_claims_present:
            issues.append(f"forbidden claims present: {self.forbidden_claims_present}")
        if self.canon_allowed:
            issues.append("regional draft must not allow canon")
        if self.source_promotion_allowed:
            issues.append("regional draft must not promote SOURCE")
        if self.noema_writeback_allowed:
            issues.append("regional draft must not write NOEMA")
        if self.current_update_allowed:
            issues.append("regional draft must not update CURRENT")
        if self.runtime_execution_allowed:
            issues.append("regional draft must not allow runtime execution")
        if "not_source" not in self.limitation or "not_execution" not in self.limitation:
            issues.append("regional draft limitation must state not_source and not_execution")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def stable_hash(self) -> str:
        return sha256(json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def _base_text(contract: AllowedResponseContract) -> str:
    kind = contract.answer_kind
    if kind == "source_missing_hypothesis":
        return "Brak źródła. To pozostaje hipoteza robocza: nie SOURCE, nie canon."
    if kind == "runtime_dry_run_refusal":
        return "To jest dry-run. Nie wykonuję runtime, nie CURRENT, nie ACTIVE."
    if kind == "alignment_candidate_explanation":
        return "To jest kandydat dopasowania. Marker: nie dowód, nie semantic identity."
    if kind == "repair_required":
        return "repair_required: brak domknięcia. Wynik to nie PASS."
    if kind == "draft_text_generation":
        return "draft_answer_candidate: tekst roboczy. To nie SOURCE i nie canon."
    return " ".join(contract.required_markers)


def realize_pl_response(contract: AllowedResponseContract) -> RegionalResponseDraft:
    text = _base_text(contract)
    preserved = [m for m in contract.required_markers if m.lower() in text.lower()]
    missing = [m for m in contract.required_markers if m.lower() not in text.lower()]
    forbidden = forbidden_claims_after_required_markers(text, contract.required_markers, contract.forbidden_claims)

    payload = json.dumps({"contract": contract.contract_id, "text": text, "missing": missing, "forbidden": forbidden}, ensure_ascii=False, sort_keys=True)
    return RegionalResponseDraft(
        draft_id="pl_regional_response_" + sha256(payload.encode("utf-8")).hexdigest()[:16],
        language_id="pl",
        contract_id=contract.contract_id,
        answer_kind=contract.answer_kind,
        text=text,
        preserved_markers=preserved,
        missing_markers=missing,
        forbidden_claims_present=forbidden,
        canon_allowed=False,
        source_promotion_allowed=False,
        noema_writeback_allowed=False,
        current_update_allowed=False,
        runtime_execution_allowed=False,
    )
