
"""EXPRESSIVE style renderer v1.1B."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from hashlib import sha256
import json
from typing import Any

from cielingo_core.global_layer.response_contract import AllowedResponseContract
from cielingo_core.global_layer.marker_scan import forbidden_claims_after_required_markers
from cielingo_core.language_spaces.pl.response_realizer import RegionalResponseDraft


class ExpressiveStyle(str, Enum):
    PLAIN = "plain"
    FORMAL = "formal"
    RELATIONAL_FORMAL = "relational_formal"
    POETIC_BOUNDED = "poetic_bounded"


@dataclass(frozen=True)
class ExpressiveResponseDraft:
    expressive_id: str
    style: ExpressiveStyle
    contract_id: str
    regional_draft_id: str
    text: str
    preserved_markers: list[str]
    missing_markers: list[str]
    forbidden_claims_present: list[str]
    canon_allowed: bool = False
    source_promotion_allowed: bool = False
    noema_writeback_allowed: bool = False
    current_update_allowed: bool = False
    runtime_execution_allowed: bool = False
    limitation: str = "expressive_response_draft_not_source_not_execution"

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.expressive_id:
            issues.append("expressive_id is required")
        if self.missing_markers:
            issues.append(f"missing required markers: {self.missing_markers}")
        if self.forbidden_claims_present:
            issues.append(f"forbidden claims present: {self.forbidden_claims_present}")
        if self.canon_allowed:
            issues.append("expressive draft must not allow canon")
        if self.source_promotion_allowed:
            issues.append("expressive draft must not promote SOURCE")
        if self.noema_writeback_allowed:
            issues.append("expressive draft must not write NOEMA")
        if self.current_update_allowed:
            issues.append("expressive draft must not update CURRENT")
        if self.runtime_execution_allowed:
            issues.append("expressive draft must not allow runtime execution")
        if "not_source" not in self.limitation or "not_execution" not in self.limitation:
            issues.append("expressive draft limitation must state not_source and not_execution")
        return issues

    def to_dict(self) -> dict[str, Any]:
        out = asdict(self)
        out["style"] = self.style.value
        return out

    def stable_hash(self) -> str:
        return sha256(json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def _style_prefix(style: ExpressiveStyle) -> str:
    if style == ExpressiveStyle.PLAIN:
        return ""
    if style == ExpressiveStyle.FORMAL:
        return "Wersja formalna: "
    if style == ExpressiveStyle.RELATIONAL_FORMAL:
        return "Spin ustawiony na jawność granic: "
    if style == ExpressiveStyle.POETIC_BOUNDED:
        return "Na powierzchni odpowiedzi zostawiam kotwice bezpieczeństwa: "
    return ""


def render_expressive_response(contract: AllowedResponseContract, regional: RegionalResponseDraft, style: ExpressiveStyle | str) -> ExpressiveResponseDraft:
    style = ExpressiveStyle(style)
    text = _style_prefix(style) + regional.text

    preserved = [m for m in contract.required_markers if m.lower() in text.lower()]
    missing = [m for m in contract.required_markers if m.lower() not in text.lower()]
    forbidden = forbidden_claims_after_required_markers(text, contract.required_markers, contract.forbidden_claims)

    payload = json.dumps({"style": style.value, "contract": contract.contract_id, "regional": regional.draft_id, "text": text, "missing": missing, "forbidden": forbidden}, ensure_ascii=False, sort_keys=True)
    return ExpressiveResponseDraft(
        expressive_id="expressive_response_" + sha256(payload.encode("utf-8")).hexdigest()[:16],
        style=style,
        contract_id=contract.contract_id,
        regional_draft_id=regional.draft_id,
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
