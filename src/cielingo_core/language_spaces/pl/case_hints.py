"""Polish case hints v0.2.

This module emits case_hint candidates only. It is not a full Polish
morphological analyzer and must not claim final grammatical case recognition.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass(frozen=True)
class CaseHint:
    token: str
    case_hint: str
    confidence: float
    evidence: str
    limitation: str = "case_hint_not_full_case"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


GENITIVE_PREPOSITIONS = {"bez", "dla", "od", "do", "z"}
LOCATIVE_PREPOSITIONS = {"w", "na", "o", "po", "przy"}
INSTRUMENTAL_PREPOSITIONS = {"z", "ze"}
ACCUSATIVE_LIKE_SUFFIXES = ("ę", "ą", "e", "y", "i")
GENITIVE_LIKE_SUFFIXES = ("a", "u", "ów", "ej", "ego")


def infer_case_hints(tokens: list[str]) -> list[CaseHint]:
    """Return conservative Polish case hints.

    Hints are intentionally low-confidence unless supported by a preposition.
    """
    hints: list[CaseHint] = []
    lowered = [t.lower() for t in tokens]
    for idx, token in enumerate(lowered):
        prev = lowered[idx - 1] if idx else ""
        if prev in GENITIVE_PREPOSITIONS:
            hints.append(CaseHint(token=tokens[idx], case_hint="genitive_candidate", confidence=0.62, evidence=f"preposition:{prev}"))
        elif prev in LOCATIVE_PREPOSITIONS:
            hints.append(CaseHint(token=tokens[idx], case_hint="locative_candidate", confidence=0.55, evidence=f"preposition:{prev}"))
        elif prev in INSTRUMENTAL_PREPOSITIONS:
            hints.append(CaseHint(token=tokens[idx], case_hint="instrumental_candidate", confidence=0.50, evidence=f"preposition:{prev}"))
        elif token.endswith(GENITIVE_LIKE_SUFFIXES) and len(token) > 3:
            hints.append(CaseHint(token=tokens[idx], case_hint="genitive_like_suffix_candidate", confidence=0.30, evidence="suffix"))
        elif token.endswith(ACCUSATIVE_LIKE_SUFFIXES) and len(token) > 3:
            hints.append(CaseHint(token=tokens[idx], case_hint="accusative_like_suffix_candidate", confidence=0.28, evidence="suffix"))
    return hints


def case_hints_to_notes(hints: list[CaseHint]) -> list[dict[str, Any]]:
    return [{"kind": "case_hint", **hint.to_dict()} for hint in hints]
