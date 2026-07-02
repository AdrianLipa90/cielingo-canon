"""Polish negation scope candidates v0.2.

Detects surface negation candidates only; it is not a complete logical scope parser.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass(frozen=True)
class NegationScopeCandidate:
    marker: str
    target_token: str | None
    confidence: float
    evidence: str
    limitation: str = "negation_scope_candidate_not_full_logic"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def detect_negation_scope(tokens: list[str]) -> list[NegationScopeCandidate]:
    lowered = [t.lower() for t in tokens]
    out: list[NegationScopeCandidate] = []
    for idx, token in enumerate(lowered):
        if token == "nie":
            target = tokens[idx + 1] if idx + 1 < len(tokens) else None
            out.append(NegationScopeCandidate(marker=tokens[idx], target_token=target, confidence=0.70, evidence="nie+next_token"))
        if token == "bez":
            target = tokens[idx + 1] if idx + 1 < len(tokens) else None
            out.append(NegationScopeCandidate(marker=tokens[idx], target_token=target, confidence=0.64, evidence="bez+next_token"))
    return out


def negation_scope_to_notes(items: list[NegationScopeCandidate]) -> list[dict[str, Any]]:
    return [{"kind": "negation_scope_candidate", **item.to_dict()} for item in items]
