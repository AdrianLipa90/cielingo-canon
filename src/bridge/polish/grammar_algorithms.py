"""Algorithmized Polish grammar surface for CIELingo.

The goal is not a complete parser. It is a deterministic grammar-control layer:
parts of speech, sentence functions, case hints, valency roles, punctuation
operators and unresolved states instead of guessing.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

from .linguistic_database import PolishLinguisticDatabase, load_polish_database
from .lingophysics_bridge import load_valency_frames
from .semantic_mass import utterance_semantic_mass

_TOKEN_RE = re.compile(r"\w+|[.,;:!?…—]", re.UNICODE)


@dataclass(frozen=True)
class TokenAnalysis:
    surface: str
    lemma: str | None
    pos: str
    case: str | None
    sentence_part: str | None
    operator: str | None = None
    unresolved: bool = False

    def as_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


def tokenize_polish(text: str) -> list[str]:
    return _TOKEN_RE.findall(text)


def _sentence_part_for(pos: str, case: str | None, has_predicate: bool) -> str | None:
    if pos == "verb":
        return "predicate"
    if pos == "particle":
        return "modal_operator"
    if pos == "conjunction":
        return "connector"
    if pos == "preposition":
        return "prepositional_operator"
    if pos == "punctuation":
        return "phase_boundary"
    if pos == "noun":
        if case == "Nom" and not has_predicate:
            return "subject"
        if case == "Nom":
            return "subject"
        if case in {"Acc", "Gen", "Dat"}:
            return "object"
        return "argument"
    return None


def analyze_tokens(text: str, db: PolishLinguisticDatabase) -> list[TokenAnalysis]:
    out: list[TokenAnalysis] = []
    has_predicate = False
    for surface in tokenize_polish(text):
        punct = db.punctuation_operator(surface)
        if punct:
            out.append(TokenAnalysis(surface, surface, "punctuation", None, "phase_boundary", punct.get("operator")))
            continue
        lex = db.lookup_form(surface)
        if lex is None:
            out.append(TokenAnalysis(surface, None, "unknown", None, None, None, True))
            continue
        case = lex.case_for(surface)
        part = _sentence_part_for(lex.pos, case, has_predicate)
        if lex.pos == "verb":
            has_predicate = True
        out.append(TokenAnalysis(surface, lex.lemma, lex.pos, case, part, lex.payload.get("operator"), False))
    return out


def _find_predicate(tokens: list[TokenAnalysis], db: PolishLinguisticDatabase):
    for token in tokens:
        if token.pos == "verb" and token.lemma:
            return db.lookup_form(token.surface)
    return None


def validate_valency(tokens: list[TokenAnalysis], db: PolishLinguisticDatabase, repo_root: str = ".") -> dict[str, Any]:
    predicate = _find_predicate(tokens, db)
    if predicate is None:
        return {"status": "UNRESOLVED", "reason": "NO_PREDICATE", "missing_roles": [], "roles": {}}
    required = predicate.payload.get("valency", {})
    roles: dict[str, str] = {}
    for role, required_case in required.items():
        match = next((t for t in tokens if t.case == required_case and t.pos == "noun" and t.surface not in roles.values()), None)
        if match:
            roles[role] = match.surface
    missing = [role for role in required if role not in roles]
    return {
        "status": "PASS" if not missing else "UNRESOLVED",
        "predicate": predicate.lemma,
        "frame_id": predicate.payload.get("frame_id"),
        "required_case_roles": required,
        "roles": roles,
        "missing_roles": missing,
        "lingophysics_frame_count": len(load_valency_frames(repo_root).get("frames", [])),
    }


def analyze_polish_sentence(text: str, repo_root: str = ".") -> dict[str, Any]:
    db = load_polish_database(repo_root)
    tokens = analyze_tokens(text, db)
    token_surfaces = [t.surface for t in tokens]
    unresolved = [t.surface for t in tokens if t.unresolved]
    valency = validate_valency(tokens, db, repo_root)
    mass = utterance_semantic_mass(token_surfaces, db)
    return {
        "schema": "cielingo/polish-sentence-analysis/v0.1",
        "text": text,
        "tokens": [t.as_dict() for t in tokens],
        "unresolved_tokens": unresolved,
        "valency": valency,
        "semantic_mass": mass,
        "grammar_status": "PASS" if not unresolved and valency["status"] == "PASS" else "UNRESOLVED",
    }


__all__ = ["TokenAnalysis", "tokenize_polish", "analyze_tokens", "validate_valency", "analyze_polish_sentence"]
