"""Deterministic scope/condition receipt for bounded CIEL agent-action surfaces."""
from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
import json
import re
from typing import Any, Iterable

ACTION_SCOPE_CONDITION_SCHEMA = "CIEL_ACTION_SCOPE_CONDITION_V0_1"
ACTION_SCOPE_CONDITION_VERSION = "0.1.0"
ACTION_SCOPE_BASIS = "LEXICAL_SCOPE_FIREWALL_V0_1"

ACTION_ANCHORS = frozenset({
    "wyślij", "zarchiwizuj", "usuń", "zachowaj", "zmień", "zatwierdź",
    "utwórz", "stwórz",
})
NEGATION_MARKERS = frozenset({"nie"})
CONDITION_MARKERS = frozenset({"jeśli", "jeżeli"})
DELAY_MARKERS = frozenset({"dopóki", "dopiero"})
QUALIFIER_MARKERS = frozenset({"tylko", "chyba"})
_VALID_STATUSES = frozenset({
    "SCOPE_SAFE", "NEGATED", "CONDITIONAL", "DELAYED", "QUALIFIED",
    "MULTI_ACTION", "NOT_ACTION",
})
_PUNCT = ".,?!:;\"'()[]{}"
_TOKEN_RE = re.compile(r"\s+")


def _digest(payload: Any) -> str:
    return sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _clean(token: str) -> str:
    return token.strip(_PUNCT).casefold()


def _tokens(text: str) -> tuple[str, ...]:
    return tuple(token for token in _TOKEN_RE.split(text.strip()) if token)


def surface_commitment(language_id: str, tokens: Iterable[str]) -> str:
    return _digest({"language_id": str(language_id), "tokens": list(tokens)})


def classify_action_scope(tokens: Iterable[str]) -> dict[str, Any]:
    packed = tuple(str(token) for token in tokens)
    low = tuple(_clean(token) for token in packed)
    action = tuple(i for i, token in enumerate(low) if token in ACTION_ANCHORS)
    negation = tuple(i for i, token in enumerate(low) if token in NEGATION_MARKERS)
    condition = tuple(i for i, token in enumerate(low) if token in CONDITION_MARKERS)
    delay = tuple(i for i, token in enumerate(low) if token in DELAY_MARKERS)
    qualifier = tuple(i for i, token in enumerate(low) if token in QUALIFIER_MARKERS)

    if not action:
        status = "NOT_ACTION"
    elif len(action) > 1:
        status = "MULTI_ACTION"
    elif negation:
        status = "NEGATED"
    elif condition:
        status = "CONDITIONAL"
    elif delay:
        status = "DELAYED"
    elif qualifier:
        status = "QUALIFIED"
    else:
        status = "SCOPE_SAFE"

    return {
        "action_anchor_indices": action,
        "negation_indices": negation,
        "condition_indices": condition,
        "delay_indices": delay,
        "qualifier_indices": qualifier,
        "status": status,
    }


@dataclass(frozen=True)
class ActionScopeConditionReceipt:
    language_id: str
    surface_commitment: str
    action_anchor_indices: tuple[int, ...]
    negation_indices: tuple[int, ...]
    condition_indices: tuple[int, ...]
    delay_indices: tuple[int, ...]
    qualifier_indices: tuple[int, ...]
    status: str
    commitment: str
    basis: str = ACTION_SCOPE_BASIS
    candidate_only: bool = True
    schema: str = ACTION_SCOPE_CONDITION_SCHEMA

    @classmethod
    def create(
        cls,
        *,
        language_id: str,
        tokens: Iterable[str],
    ) -> "ActionScopeConditionReceipt":
        packed = tuple(str(token) for token in tokens)
        classified = classify_action_scope(packed)
        provisional = cls(
            language_id=str(language_id),
            surface_commitment=surface_commitment(str(language_id), packed),
            action_anchor_indices=classified["action_anchor_indices"],
            negation_indices=classified["negation_indices"],
            condition_indices=classified["condition_indices"],
            delay_indices=classified["delay_indices"],
            qualifier_indices=classified["qualifier_indices"],
            status=classified["status"],
            commitment="",
        )
        receipt = replace(
            provisional,
            commitment=_digest(provisional.to_binding_dict()),
        )
        issues = receipt.validate()
        if issues:
            raise ValueError("; ".join(issues))
        return receipt

    @property
    def scope_safe(self) -> bool:
        return self.status == "SCOPE_SAFE"

    def validate(self) -> list[str]:
        issues: list[str] = []
        if self.schema != ACTION_SCOPE_CONDITION_SCHEMA:
            issues.append("action scope schema mismatch")
        if self.language_id != "pl":
            issues.append("action scope v0.1 expects language_id=pl")
        if len(self.surface_commitment) != 64:
            issues.append("action scope surface_commitment must be SHA-256")
        if self.status not in _VALID_STATUSES:
            issues.append("action scope status invalid")
        for name in (
            "action_anchor_indices",
            "negation_indices",
            "condition_indices",
            "delay_indices",
            "qualifier_indices",
        ):
            values = tuple(getattr(self, name))
            if any(index < 0 for index in values):
                issues.append(f"{name} must be non-negative")
            if len(set(values)) != len(values):
                issues.append(f"{name} must be unique")
        if self.basis != ACTION_SCOPE_BASIS:
            issues.append("action scope basis mismatch")
        if not self.candidate_only:
            issues.append("action scope receipt must remain candidate-only")
        if len(self.commitment) != 64:
            issues.append("action scope commitment must be SHA-256")
        elif self.commitment != _digest(self.to_binding_dict()):
            issues.append("action scope commitment mismatch")
        return issues

    def to_binding_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "language_id": self.language_id,
            "surface_commitment": self.surface_commitment,
            "action_anchor_indices": list(self.action_anchor_indices),
            "negation_indices": list(self.negation_indices),
            "condition_indices": list(self.condition_indices),
            "delay_indices": list(self.delay_indices),
            "qualifier_indices": list(self.qualifier_indices),
            "status": self.status,
            "basis": self.basis,
            "candidate_only": self.candidate_only,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.to_binding_dict(),
            "scope_safe": self.scope_safe,
            "commitment": self.commitment,
        }


def build_action_scope_condition_receipt(
    text: str,
    *,
    tokens: Iterable[str] | None = None,
    language_id: str = "pl",
) -> ActionScopeConditionReceipt:
    packed = tuple(tokens) if tokens is not None else _tokens(text)
    return ActionScopeConditionReceipt.create(
        language_id=language_id,
        tokens=packed,
    )


__all__ = [
    "ACTION_ANCHORS",
    "ACTION_SCOPE_BASIS",
    "ACTION_SCOPE_CONDITION_SCHEMA",
    "ACTION_SCOPE_CONDITION_VERSION",
    "ActionScopeConditionReceipt",
    "build_action_scope_condition_receipt",
    "classify_action_scope",
    "surface_commitment",
]
