"""Polish imperative/action-force candidates v0.2.

Detects action_request candidates only. It grants no runtime execution authority.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass(frozen=True)
class ImperativeForceCandidate:
    token: str
    force_candidate: str
    confidence: float
    evidence: str
    limitation: str = "action_request_not_runtime_authorization"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


IMPERATIVE_LEMMAS = {"sprawdź", "sprawdz", "zapisz", "waliduj", "uruchom", "przeczytaj", "kanonizuj"}


def detect_imperative_force(tokens: list[str]) -> list[ImperativeForceCandidate]:
    out: list[ImperativeForceCandidate] = []
    for token in tokens:
        if token.lower() in IMPERATIVE_LEMMAS:
            out.append(ImperativeForceCandidate(token=token, force_candidate="action_request_candidate", confidence=0.78, evidence="known_imperative_surface_form"))
    return out


def imperative_force_to_notes(items: list[ImperativeForceCandidate]) -> list[dict[str, Any]]:
    return [{"kind": "imperative_force_candidate", **item.to_dict()} for item in items]
