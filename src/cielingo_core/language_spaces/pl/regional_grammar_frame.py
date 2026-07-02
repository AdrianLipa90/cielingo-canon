
"""Polish RegionalGrammarFrame v1.1D."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json
from typing import Any

from cielingo_core.language_spaces.pl.grammar_parts import (
    MorphologyFeature,
    PartOfSpeech,
    SemanticOperatorRole,
    SentencePart,
)


@dataclass(frozen=True)
class TokenGrammarAnalysis:
    token: str
    lemma: str
    part_of_speech: PartOfSpeech
    sentence_part: SentencePart
    morphology: list[MorphologyFeature] = field(default_factory=list)
    semantic_operator_role: SemanticOperatorRole = SemanticOperatorRole.NONE
    confidence: float = 0.5
    notes: list[str] = field(default_factory=list)


    @property
    def token_analyses(self):
        """1.1C compatibility alias for tokens."""
        return self.tokens

    @property
    def pos_counts(self) -> dict[str, int]:
        """1.1C compatibility POS count map."""
        counts: dict[str, int] = {}
        for token in self.tokens:
            counts[token.part_of_speech.value] = counts.get(token.part_of_speech.value, 0) + 1
        return counts

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.token:
            issues.append("token is required")
        if not self.lemma:
            issues.append("lemma is required")
        if not 0.0 <= float(self.confidence) <= 1.0:
            issues.append("confidence must be in [0,1]")
        return issues

    @property
    def case(self) -> str | None:
        cases = {
            MorphologyFeature.NOMINATIVE,
            MorphologyFeature.GENITIVE,
            MorphologyFeature.DATIVE,
            MorphologyFeature.ACCUSATIVE,
            MorphologyFeature.INSTRUMENTAL,
            MorphologyFeature.LOCATIVE,
            MorphologyFeature.VOCATIVE,
        }
        for item in self.morphology:
            if item in cases:
                return item.value
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "token": self.token,
            "lemma": self.lemma,
            "part_of_speech": self.part_of_speech.value,
            "sentence_part": self.sentence_part.value,
            "morphology": [item.value for item in self.morphology],
            "semantic_operator_role": self.semantic_operator_role.value,
            "confidence": self.confidence,
            "notes": list(self.notes),
        }


@dataclass(frozen=True)
class RegionalGrammarFrame:
    frame_id: str
    language_id: str
    surface_text: str
    tokens: list[TokenGrammarAnalysis]
    syntax_path: list[str]
    regional_residue: list[str] = field(default_factory=list)
    confidence: float = 0.5
    canon_allowed: bool = False
    source_promotion_allowed: bool = False
    noema_writeback_allowed: bool = False
    current_update_allowed: bool = False
    runtime_execution_allowed: bool = False
    limitation: str = "regional_grammar_frame_not_global_semantic_identity"


    @property
    def token_analyses(self):
        """1.1C compatibility alias for tokens."""
        return self.tokens

    @property
    def pos_counts(self) -> dict[str, int]:
        """1.1C compatibility POS count map."""
        counts: dict[str, int] = {}
        for token in self.tokens:
            counts[token.part_of_speech.value] = counts.get(token.part_of_speech.value, 0) + 1
        return counts

    def validate(self) -> list[str]:
        issues: list[str] = []
        if self.language_id != "pl":
            issues.append("RegionalGrammarFrame v1.1D expects language_id=pl")
        if not self.surface_text:
            issues.append("surface_text is required")
        if not self.tokens:
            issues.append("tokens must not be empty")
        for token in self.tokens:
            issues.extend(token.validate())
        if not 0.0 <= float(self.confidence) <= 1.0:
            issues.append("confidence must be in [0,1]")
        if self.canon_allowed:
            issues.append("regional grammar frame must not allow canon")
        if self.source_promotion_allowed:
            issues.append("regional grammar frame must not promote SOURCE")
        if self.noema_writeback_allowed:
            issues.append("regional grammar frame must not write NOEMA")
        if self.current_update_allowed:
            issues.append("regional grammar frame must not update CURRENT")
        if self.runtime_execution_allowed:
            issues.append("regional grammar frame must not allow runtime execution")
        if "not_global_semantic_identity" not in self.limitation:
            issues.append("limitation must state not_global_semantic_identity")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "frame_id": self.frame_id,
            "language_id": self.language_id,
            "surface_text": self.surface_text,
            "tokens": [token.to_dict() for token in self.tokens],
            "syntax_path": list(self.syntax_path),
            "regional_residue": list(self.regional_residue),
            "confidence": self.confidence,
            "canon_allowed": self.canon_allowed,
            "source_promotion_allowed": self.source_promotion_allowed,
            "noema_writeback_allowed": self.noema_writeback_allowed,
            "current_update_allowed": self.current_update_allowed,
            "runtime_execution_allowed": self.runtime_execution_allowed,
            "limitation": self.limitation,
        }

    def stable_hash(self) -> str:
        payload = json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True)
        return sha256(payload.encode("utf-8")).hexdigest()
