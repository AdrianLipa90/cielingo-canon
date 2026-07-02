"""Polish canon phrase candidates v0.2.

Detects canon_attempt/canon_block candidates. It must not promote canon.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass(frozen=True)
class CanonPhraseCandidate:
    phrase: str
    signal: str
    confidence: float
    evidence: str
    limitation: str = "canon_attempt_not_canon"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def detect_canon_phrases(tokens: list[str]) -> list[CanonPhraseCandidate]:
    lowered = [t.lower() for t in tokens]
    joined = " ".join(lowered)
    out: list[CanonPhraseCandidate] = []
    if "kanonizuj" in joined or "kanon" in joined:
        signal = "canon_block_candidate" if "nie" in lowered or "bez źródła" in joined or "bez zrodla" in joined else "canon_attempt_candidate"
        out.append(CanonPhraseCandidate("kanon", signal, 0.78, "lexeme_or_phrase_match"))
    return out


def canon_phrases_to_notes(items: list[CanonPhraseCandidate]) -> list[dict[str, Any]]:
    return [{"kind": "canon_phrase_candidate", **item.to_dict()} for item in items]
