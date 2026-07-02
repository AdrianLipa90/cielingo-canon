"""Polish source phrase candidates v0.2.

Detects source_required candidates. It must not promote SOURCE.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass(frozen=True)
class SourcePhraseCandidate:
    phrase: str
    signal: str
    confidence: float
    evidence: str
    limitation: str = "source_required_not_SOURCE"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def detect_source_phrases(tokens: list[str]) -> list[SourcePhraseCandidate]:
    lowered = [t.lower() for t in tokens]
    joined = " ".join(lowered)
    out: list[SourcePhraseCandidate] = []
    if "bez źródła" in joined or "bez zrodla" in joined:
        out.append(SourcePhraseCandidate("bez źródła", "source_required_candidate", 0.82, "phrase_match"))
    if "wymaga źródła" in joined or "wymaga zrodla" in joined:
        out.append(SourcePhraseCandidate("wymaga źródła", "source_required_candidate", 0.78, "phrase_match"))
    if "źródło" in joined or "zrodlo" in joined or "źródła" in joined or "zrodla" in joined:
        if not out:
            out.append(SourcePhraseCandidate("źródło", "source_context_candidate", 0.50, "lexeme_match"))
    return out


def source_phrases_to_notes(items: list[SourcePhraseCandidate]) -> list[dict[str, Any]]:
    return [{"kind": "source_phrase_candidate", **item.to_dict()} for item in items]
