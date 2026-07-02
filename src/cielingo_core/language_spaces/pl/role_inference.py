"""Polish role inference v0.2.

Emits role_candidate objects only. It does not assert final semantic roles.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass(frozen=True)
class RoleCandidate:
    token: str
    role_candidate: str
    confidence: float
    evidence: str
    limitation: str = "role_candidate_not_final_role"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


PREFERENCE_PREDICATES = {"lubi", "lubie", "lubię", "kocha", "preferuje", "preferuję"}
ACTION_PREDICATES = {"sprawdź", "sprawdz", "zapisz", "waliduj", "uruchom", "przeczytaj", "kanonizuj"}


def infer_role_candidates(tokens: list[str]) -> list[RoleCandidate]:
    lowered = [t.lower() for t in tokens]
    roles: list[RoleCandidate] = []

    for idx, token in enumerate(lowered):
        original = tokens[idx]
        if token in PREFERENCE_PREDICATES:
            roles.append(RoleCandidate(original, "preference_predicate_candidate", 0.80, "known_preference_predicate"))
            if idx > 0:
                roles.append(RoleCandidate(tokens[idx - 1], "experiencer_candidate", 0.58, "token_before_preference_predicate"))
            if idx + 1 < len(tokens):
                roles.append(RoleCandidate(tokens[idx + 1], "theme_candidate", 0.58, "token_after_preference_predicate"))
        if token in ACTION_PREDICATES:
            roles.append(RoleCandidate(original, "action_predicate_candidate", 0.72, "known_action_predicate"))
            if idx + 1 < len(tokens):
                roles.append(RoleCandidate(tokens[idx + 1], "patient_candidate", 0.48, "token_after_action_predicate"))

    # Flexible Polish order heuristic for "Książki lubi Adrian".
    for idx, token in enumerate(lowered):
        if token in PREFERENCE_PREDICATES and idx > 0 and idx + 1 < len(tokens):
            roles.append(RoleCandidate(tokens[idx - 1], "theme_candidate", 0.48, "token_before_preference_predicate_flexible_order"))
            roles.append(RoleCandidate(tokens[idx + 1], "experiencer_candidate", 0.48, "token_after_preference_predicate_flexible_order"))

    return roles


def role_candidates_to_notes(candidates: list[RoleCandidate]) -> list[dict[str, Any]]:
    return [{"kind": "role_candidate", **candidate.to_dict()} for candidate in candidates]
