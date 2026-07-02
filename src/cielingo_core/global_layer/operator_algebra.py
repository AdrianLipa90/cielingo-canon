"""CIELingo GLOBAL v0.2 operator algebra.

Scope:
- Defines language-independent semantic operators.
- Does not parse regional grammar.
- Does not grant SOURCE/canon by default.

Operator is not a word. A word/card may realize an operator in a language,
but GLOBAL only handles the operator contract.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class OperatorKind(str, Enum):
    IDENTITY = "IDENTITY"          # =
    DIFFERENCE = "DIFFERENCE"      # !=
    ORDER = "ORDER"                # >
    COMPOSITION = "COMPOSITION"    # x
    ADDITION = "ADDITION"          # +
    FORCE = "FORCE"                # !
    QUESTION = "QUESTION"          # ?
    NEGATION = "NEGATION"          # not / nie / ない
    TRANSFORM = "TRANSFORM"        # ->
    RETURN = "RETURN"              # loop/return
    FOLD = "FOLD"                  # semantic folding
    BOUNDARY = "BOUNDARY"          # scope/gate
    SCOPE = "SCOPE"                # parentheses, clauses
    AFFECT = "AFFECT"              # preference, love, aversion
    CONSENT = "CONSENT"            # consent gate
    SOURCE = "SOURCE"              # source/proof demand
    MEMORY = "MEMORY"              # memory/scar/snap effect
    RISK = "RISK"                  # semantic immune pressure


class OperatorDomain(str, Enum):
    SLOT = "slot"
    EQUATION = "equation"
    SURFACE = "surface"
    LOOP = "loop"
    SCAR = "scar"
    MEMORY = "memory"
    SOURCE_BINDING = "source_binding"
    CONSENT_STATE = "consent_state"
    AFFECTIVE_STATE = "affective_state"
    ANY = "any"


def _bounded01(v: float) -> bool:
    return 0.0 <= float(v) <= 1.0


@dataclass
class RelationalOperator:
    operator_id: str
    operator_kind: OperatorKind
    symbol: str | None
    arity: int | str
    input_domains: list[OperatorDomain]
    output_domain: OperatorDomain
    scope_rules: dict[str, Any] = field(default_factory=dict)
    j_weights: dict[str, float] = field(default_factory=dict)
    source_required: bool = False
    canon_effect: str = "none"
    consent_effect: str = "none"
    notes: list[str] = field(default_factory=list)

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.operator_id:
            issues.append("operator_id is required")
        if isinstance(self.arity, int) and self.arity < 0:
            issues.append("arity must be non-negative")
        if not self.input_domains:
            issues.append("input_domains must be non-empty")
        if self.canon_effect not in {"none", "block", "allow_candidate_only"}:
            issues.append("invalid canon_effect")
        if self.consent_effect not in {"none", "requires_consent", "blocks_action", "pause"}:
            issues.append("invalid consent_effect")
        for key, value in self.j_weights.items():
            if not _bounded01(value):
                issues.append(f"j_weight {key} must be in [0, 1]")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


DEFAULT_OPERATORS: dict[str, RelationalOperator] = {
    "QUESTION": RelationalOperator(
        operator_id="QUESTION",
        operator_kind=OperatorKind.QUESTION,
        symbol="?",
        arity=1,
        input_domains=[OperatorDomain.EQUATION],
        output_domain=OperatorDomain.EQUATION,
        j_weights={"J_closure_pressure": 0.25},
        notes=["Opens an information gap / loop."],
    ),
    "ACTION_REQUEST": RelationalOperator(
        operator_id="ACTION_REQUEST",
        operator_kind=OperatorKind.FORCE,
        symbol="!",
        arity=1,
        input_domains=[OperatorDomain.EQUATION],
        output_domain=OperatorDomain.EQUATION,
        consent_effect="requires_consent",
        j_weights={"J_consent_pressure": 0.45, "J_trace_pressure": 0.25},
        notes=["Requests an act; does not execute."],
    ),
    "SOURCE_REQUIRED": RelationalOperator(
        operator_id="SOURCE_REQUIRED",
        operator_kind=OperatorKind.SOURCE,
        symbol="SOURCE",
        arity=1,
        input_domains=[OperatorDomain.EQUATION],
        output_domain=OperatorDomain.SOURCE_BINDING,
        source_required=True,
        canon_effect="block",
        j_weights={"J_source_pressure": 0.70, "J_canon_pressure": 0.35},
        notes=["Requires evidence before canon/source promotion."],
    ),
    "NEGATION": RelationalOperator(
        operator_id="NEGATION",
        operator_kind=OperatorKind.NEGATION,
        symbol="¬",
        arity=1,
        input_domains=[OperatorDomain.EQUATION, OperatorDomain.SLOT],
        output_domain=OperatorDomain.EQUATION,
        j_weights={"J_scope_pressure": 0.20},
        notes=["Negates a scoped proposition/operator."],
    ),
    "PREFERENCE": RelationalOperator(
        operator_id="PREFERENCE",
        operator_kind=OperatorKind.AFFECT,
        symbol="LIKE",
        arity=2,
        input_domains=[OperatorDomain.SLOT, OperatorDomain.SLOT],
        output_domain=OperatorDomain.AFFECTIVE_STATE,
        j_weights={"J_affective_charge": 0.35, "J_role_binding": 0.25},
        notes=["Affective relation: experiencer prefers theme."],
    ),
    "RETURN": RelationalOperator(
        operator_id="RETURN",
        operator_kind=OperatorKind.RETURN,
        symbol="↺",
        arity=1,
        input_domains=[OperatorDomain.LOOP],
        output_domain=OperatorDomain.LOOP,
        j_weights={"J_loop_closure": 0.40},
        notes=["Attempts closure/return to a loop."],
    ),
}


def get_default_operator(operator_id: str) -> RelationalOperator | None:
    return DEFAULT_OPERATORS.get(operator_id)


def validate_operator_registry(registry: dict[str, RelationalOperator] | None = None) -> list[str]:
    registry = registry or DEFAULT_OPERATORS
    issues: list[str] = []
    for key, operator in registry.items():
        if key != operator.operator_id:
            issues.append(f"registry key mismatch: {key} != {operator.operator_id}")
        for issue in operator.validate():
            issues.append(f"{key}: {issue}")
    return issues
