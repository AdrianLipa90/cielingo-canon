"""GLOBAL 0.5C card field policy scaffold."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class FieldPolicy(str, Enum):
    MANDATORY = "mandatory"
    OPTIONAL = "optional"
    EXPERIMENTAL = "experimental"
    FORBIDDEN_DEFAULT = "forbidden_default"


@dataclass
class CardFieldRule:
    field_name: str
    policy: FieldPolicy
    reason: str
    default_allowed: bool = True
    forbidden_values: list[Any] = field(default_factory=list)

    def validate_value(self, value: Any) -> list[str]:
        issues: list[str] = []
        if not self.default_allowed and value is None:
            issues.append(f"{self.field_name} has no allowed default")
        if value in self.forbidden_values:
            issues.append(f"{self.field_name} cannot have forbidden value {value!r}")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


DEFAULT_CARD_FIELD_POLICY: dict[str, CardFieldRule] = {
    "card_id": CardFieldRule("card_id", FieldPolicy.MANDATORY, "stable identity"),
    "slot_id": CardFieldRule("slot_id", FieldPolicy.MANDATORY, "global comparison axis"),
    "language_id": CardFieldRule("language_id", FieldPolicy.MANDATORY, "regional/local holonomy"),
    "lemma": CardFieldRule("lemma", FieldPolicy.MANDATORY, "surface anchor or in_blanco alternative"),
    "surface_forms": CardFieldRule("surface_forms", FieldPolicy.MANDATORY, "regional realizations"),
    "ontology_class": CardFieldRule("ontology_class", FieldPolicy.MANDATORY, "koto/mono/unresolved split"),
    "source_binding": CardFieldRule("source_binding", FieldPolicy.FORBIDDEN_DEFAULT, "SOURCE cannot be default", forbidden_values=["SOURCE"]),
    "canon_allowed": CardFieldRule("canon_allowed", FieldPolicy.FORBIDDEN_DEFAULT, "canon cannot be default", forbidden_values=[True]),
    "operator_bindings": CardFieldRule("operator_bindings", FieldPolicy.MANDATORY, "runtime operator effects"),
    "semantic_mass": CardFieldRule("semantic_mass", FieldPolicy.MANDATORY, "semantic weight"),
    "affective_charge": CardFieldRule("affective_charge", FieldPolicy.MANDATORY, "affect weight"),
    "coherence_effect": CardFieldRule("coherence_effect", FieldPolicy.EXPERIMENTAL, "PDF-derived candidate"),
    "intention_effect": CardFieldRule("intention_effect", FieldPolicy.EXPERIMENTAL, "PDF-derived candidate"),
}


def validate_policy_table(policy: dict[str, CardFieldRule] | None = None) -> list[str]:
    policy = policy or DEFAULT_CARD_FIELD_POLICY
    issues: list[str] = []
    for required in ("card_id", "slot_id", "language_id", "source_binding", "canon_allowed"):
        if required not in policy:
            issues.append(f"missing policy field: {required}")
    if "source_binding" in policy and "SOURCE" not in policy["source_binding"].forbidden_values:
        issues.append("source_binding policy must forbid SOURCE default")
    if "canon_allowed" in policy and True not in policy["canon_allowed"].forbidden_values:
        issues.append("canon_allowed policy must forbid True default")
    return issues
