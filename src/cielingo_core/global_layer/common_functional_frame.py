
"""CommonFunctionalFrame v1.1C.

GLOBAL common roles are language-independent functional classes. REGIONAL
layers later decide local parts of speech, sentence parts and morphology.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from hashlib import sha256
import json
import re
from typing import Any


class FunctionalRole(str, Enum):
    ENTITY = "entity"
    ACTION = "action"
    RELATION = "relation"
    QUALITY = "quality"
    MODIFIER = "modifier"
    OPERATOR = "operator"
    BOUNDARY = "boundary"
    CONTEXT = "context"
    UNKNOWN = "unknown"


class FunctionalOperator(str, Enum):
    NEGATION = "negation_operator"
    SOURCE = "source_operator"
    CANON = "canon_operator"
    AUTHORITY = "authority_operator"
    RUNTIME = "runtime_operator"
    QUESTION = "question_operator"
    IMPERATIVE = "imperative_operator"
    MODAL = "modal_operator"
    REPAIR = "repair_operator"
    NONE = "none"


OPERATOR_RISK = {
    FunctionalOperator.NEGATION: 0.10,
    FunctionalOperator.SOURCE: 0.60,
    FunctionalOperator.CANON: 0.85,
    FunctionalOperator.AUTHORITY: 1.00,
    FunctionalOperator.RUNTIME: 0.90,
    FunctionalOperator.QUESTION: 0.05,
    FunctionalOperator.IMPERATIVE: 0.65,
    FunctionalOperator.MODAL: 0.25,
    FunctionalOperator.REPAIR: 0.40,
    FunctionalOperator.NONE: 0.0,
}


@dataclass(frozen=True)
class FunctionalSlot:
    token: str
    role: FunctionalRole
    operators: list[FunctionalOperator] = field(default_factory=list)
    weight: float = 1.0
    source_index: int = 0

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.token:
            issues.append("token is required")
        if not 0.0 <= float(self.weight) <= 1.0:
            issues.append("weight must be in [0,1]")
        return issues

    @property
    def operator_risk(self) -> float:
        return max([OPERATOR_RISK.get(op, 0.0) for op in self.operators] or [0.0])

    def to_dict(self) -> dict[str, Any]:
        return {
            "token": self.token,
            "role": self.role.value,
            "operators": [op.value for op in self.operators],
            "weight": self.weight,
            "source_index": self.source_index,
            "operator_risk": self.operator_risk,
        }


@dataclass(frozen=True)
class ContextFrame:
    intention: str
    language_hint: str = "unknown"
    source_status: str = "unknown"
    authority_risk: float = 0.0
    runtime_request: bool = False
    uncertainty_required: bool = False

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not 0.0 <= float(self.authority_risk) <= 1.0:
            issues.append("authority_risk must be in [0,1]")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CommonFunctionalFrame:
    frame_id: str
    slots: list[FunctionalSlot]
    context: ContextFrame
    boundary_markers: list[str] = field(default_factory=list)
    limitation: str = "common_functional_frame_not_regional_grammar_not_source"
    canon_allowed: bool = False
    source_promotion_allowed: bool = False
    noema_writeback_allowed: bool = False
    current_update_allowed: bool = False
    runtime_execution_allowed: bool = False

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.frame_id:
            issues.append("frame_id is required")
        for slot in self.slots:
            issues.extend(slot.validate())
        issues.extend(self.context.validate())
        if self.canon_allowed:
            issues.append("frame must not allow canon")
        if self.source_promotion_allowed:
            issues.append("frame must not promote SOURCE")
        if self.noema_writeback_allowed:
            issues.append("frame must not write NOEMA")
        if self.current_update_allowed:
            issues.append("frame must not update CURRENT")
        if self.runtime_execution_allowed:
            issues.append("frame must not allow runtime execution")
        if "not_regional_grammar" not in self.limitation or "not_source" not in self.limitation:
            issues.append("limitation must state not_regional_grammar and not_source")
        return issues

    @property
    def semantic_mass(self) -> float:
        """M(F)=sum_i w_i. This is a structural mass, not physical mass."""
        return round(sum(slot.weight for slot in self.slots), 6)

    @property
    def operator_risk(self) -> float:
        """R(F)=min(1, max(context risk, mean slot operator risk))."""
        if not self.slots:
            return round(self.context.authority_risk, 6)
        mean_slot_risk = sum(slot.operator_risk for slot in self.slots) / len(self.slots)
        return round(min(1.0, max(self.context.authority_risk, mean_slot_risk)), 6)

    @property
    def functional_entropy(self) -> float:
        """Normalized diversity proxy over functional roles in [0,1]."""
        if not self.slots:
            return 0.0
        counts: dict[str, int] = {}
        for slot in self.slots:
            counts[slot.role.value] = counts.get(slot.role.value, 0) + 1
        n = len(self.slots)
        # Simple normalized Gini-Simpson diversity, not Shannon in this phase.
        diversity = 1.0 - sum((c / n) ** 2 for c in counts.values())
        max_div = 1.0 - 1.0 / max(1, min(n, len(FunctionalRole)))
        return round(diversity / max_div if max_div else 0.0, 6)

    @property
    def closure_pressure(self) -> float:
        """C(F)=clamp(semantic_mass/(n+1) * (1-risk))."""
        denom = len(self.slots) + 1
        raw = (self.semantic_mass / denom) * (1.0 - self.operator_risk)
        return round(max(0.0, min(1.0, raw)), 6)

    def calculations(self) -> dict[str, float]:
        return {
            "semantic_mass_M": self.semantic_mass,
            "operator_risk_R": self.operator_risk,
            "functional_entropy_D": self.functional_entropy,
            "closure_pressure_C": self.closure_pressure,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "frame_id": self.frame_id,
            "slots": [slot.to_dict() for slot in self.slots],
            "context": self.context.to_dict(),
            "boundary_markers": list(self.boundary_markers),
            "calculations": self.calculations(),
            "limitation": self.limitation,
            "canon_allowed": self.canon_allowed,
            "source_promotion_allowed": self.source_promotion_allowed,
            "noema_writeback_allowed": self.noema_writeback_allowed,
            "current_update_allowed": self.current_update_allowed,
            "runtime_execution_allowed": self.runtime_execution_allowed,
        }

    def stable_hash(self) -> str:
        return sha256(json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


_TOKEN_RE = re.compile(r"[\wąćęłńóśźżĄĆĘŁŃÓŚŹŻ]+|[^\w\s]", re.UNICODE)


def _operators_for_token(token: str) -> list[FunctionalOperator]:
    low = token.lower()
    ops: list[FunctionalOperator] = []
    if low in {"nie", "not", "no"}:
        ops.append(FunctionalOperator.NEGATION)
    if low in {"źródło", "źródła", "source", "evidence", "dowód"}:
        ops.append(FunctionalOperator.SOURCE)
    if low in {"canon", "kanon", "kanonizuj", "kanonizować", "kanonizacja"}:
        ops.append(FunctionalOperator.CANON)
    if low in {"active", "current", "pass", "ustaw", "zapisz", "wykonaj", "uruchom"}:
        ops.append(FunctionalOperator.AUTHORITY)
    if low in {"runtime", "wykonuję", "wykonać", "uruchom"}:
        ops.append(FunctionalOperator.RUNTIME)
    if low in {"czy", "?"}:
        ops.append(FunctionalOperator.QUESTION)
    if low in {"sprawdź", "ustaw", "zapisz", "wykonaj", "kanonizuj"}:
        ops.append(FunctionalOperator.IMPERATIVE)
    if low in {"może", "musi", "powinien", "trzeba", "warto"}:
        ops.append(FunctionalOperator.MODAL)
    if low in {"napraw", "repair", "test", "audyt"}:
        ops.append(FunctionalOperator.REPAIR)
    return ops or [FunctionalOperator.NONE]


def _role_for_token(token: str, ops: list[FunctionalOperator]) -> FunctionalRole:
    if token in {".", ",", ":", ";", "?", "!"}:
        return FunctionalRole.BOUNDARY
    if any(op != FunctionalOperator.NONE for op in ops):
        return FunctionalRole.OPERATOR
    low = token.lower()
    if low.endswith(("ać", "eć", "ić", "yć", "uj", "aj")):
        return FunctionalRole.ACTION
    if low.endswith(("ny", "na", "ne", "owy", "owa", "owe")):
        return FunctionalRole.QUALITY
    return FunctionalRole.ENTITY


def build_common_functional_frame(text: str, language_hint: str = "pl") -> CommonFunctionalFrame:
    tokens = _TOKEN_RE.findall(text)
    slots: list[FunctionalSlot] = []
    for idx, tok in enumerate(tokens):
        ops = _operators_for_token(tok)
        role = _role_for_token(tok, ops)
        weight = 0.35 if role == FunctionalRole.BOUNDARY else 0.80 if role == FunctionalRole.OPERATOR else 0.65
        slots.append(FunctionalSlot(token=tok, role=role, operators=ops, weight=weight, source_index=idx))
    low = text.lower()
    intention = "ask" if "?" in text or low.startswith(("czy", "co ", "jak ", "dlaczego")) else "command" if any(x in low for x in ["sprawdź", "ustaw", "zapisz", "wykonaj", "kanonizuj"]) else "statement"
    source_status = "required" if any(FunctionalOperator.SOURCE in slot.operators for slot in slots) else "not_requested"
    authority_risk = max([slot.operator_risk for slot in slots] or [0.0])
    runtime_request = any(FunctionalOperator.RUNTIME in slot.operators or FunctionalOperator.AUTHORITY in slot.operators for slot in slots)
    uncertainty_required = source_status == "required"
    context = ContextFrame(
        intention=intention,
        language_hint=language_hint,
        source_status=source_status,
        authority_risk=round(authority_risk, 6),
        runtime_request=runtime_request,
        uncertainty_required=uncertainty_required,
    )
    boundary_markers = [tok for tok in tokens if tok in {".", ",", ":", ";", "?", "!"}]
    payload = json.dumps({"text": text, "language_hint": language_hint, "slots": [s.to_dict() for s in slots]}, ensure_ascii=False, sort_keys=True)
    return CommonFunctionalFrame(
        frame_id="common_frame_" + sha256(payload.encode("utf-8")).hexdigest()[:16],
        slots=slots,
        context=context,
        boundary_markers=boundary_markers,
    )
