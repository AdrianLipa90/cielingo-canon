"""Minimal Polish grammar heuristics for CIELingo 0.5I.

This is not a full Polish morphology engine. It is a cautious local layer for:
- negation scope,
- imperative/action force,
- source phrases,
- rough case hints,
- local role hints.

It emits regional hints and residue; GLOBAL remains responsible for operator/action/scar logic.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


PL_ACTION_LEMMAS = {
    "sprawdź", "sprawdz", "sprawdzić", "sprawdzic", "waliduj", "zweryfikuj",
    "zapisz", "zapisać", "zapisac", "czytaj", "przeczytaj", "odczytaj",
}

PL_NEGATION_TOKENS = {"nie", "bez", "żaden", "zadnej", "żadnej", "nigdy"}
PL_SOURCE_TOKENS = {"źródło", "źródła", "zrodlo", "zrodla", "dowód", "dowodu", "dowody", "hash"}
PL_CANON_TOKENS = {"kanon", "kanonizuj", "kanonizować", "kanoniczny"}
PL_PREFERENCE_TOKENS = {"lubi", "lubię", "lubie", "lubić", "lubic", "preferuje", "preferuję"}

CASE_SUFFIX_HINTS = {
    "genitive_like": ("a", "u", "ów", "ow", "ej", "ego", "ści", "sci"),
    "accusative_like": ("ę", "e", "ą", "a", "y", "i"),
    "instrumental_like": ("em", "ą", "ami"),
    "locative_like": ("ie", "u"),
    "plural_like": ("y", "i", "e", "ki"),
}


@dataclass
class PolishGrammarHint:
    negation_indices: list[int] = field(default_factory=list)
    imperative_indices: list[int] = field(default_factory=list)
    source_phrase_indices: list[int] = field(default_factory=list)
    canon_phrase_indices: list[int] = field(default_factory=list)
    preference_indices: list[int] = field(default_factory=list)
    case_hints: dict[int, list[str]] = field(default_factory=dict)
    local_roles: dict[str, Any] = field(default_factory=dict)
    residues: list[dict[str, Any]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _norm(token: str) -> str:
    return token.strip(".,;:!?()[]{}\"'„”").lower()


def infer_case_hints(token: str) -> list[str]:
    t = _norm(token)
    hints: list[str] = []
    if len(t) <= 2:
        return hints
    for name, suffixes in CASE_SUFFIX_HINTS.items():
        if any(t.endswith(s) for s in suffixes):
            hints.append(name)
    return hints


def analyze_polish_tokens(tokens: list[str]) -> PolishGrammarHint:
    low = [_norm(t) for t in tokens]
    hint = PolishGrammarHint(notes=["Minimal PL grammar heuristic; not full morphology."])

    for i, tok in enumerate(low):
        if tok in PL_NEGATION_TOKENS:
            hint.negation_indices.append(i)
        if tok in PL_ACTION_LEMMAS:
            hint.imperative_indices.append(i)
        if tok in PL_SOURCE_TOKENS:
            hint.source_phrase_indices.append(i)
        if tok in PL_CANON_TOKENS:
            hint.canon_phrase_indices.append(i)
        if tok in PL_PREFERENCE_TOKENS:
            hint.preference_indices.append(i)

        case = infer_case_hints(tok)
        if case:
            hint.case_hints[i] = case

    # Very cautious local-role hints. These are not universal grammar.
    if hint.preference_indices:
        pred = hint.preference_indices[0]
        before = [i for i in range(0, pred)]
        after = [i for i in range(pred + 1, len(tokens))]
        if before:
            hint.local_roles["experiencer_candidate_token"] = before[-1]
        if after:
            hint.local_roles["theme_candidate_tokens"] = after

    if hint.imperative_indices:
        pred = hint.imperative_indices[0]
        after = [i for i in range(pred + 1, len(tokens))]
        hint.local_roles["action_predicate_token"] = pred
        if after:
            hint.local_roles["patient_candidate_tokens"] = after

    if hint.negation_indices:
        hint.residues.append({
            "type": "scope_residue",
            "description": "Polish negation scope requires local/regional handling.",
            "j_weight": 0.35,
        })

    if hint.case_hints:
        hint.residues.append({
            "type": "case_residue",
            "description": "Polish case inferred only by suffix hints; requires future morphology engine.",
            "j_weight": 0.40,
        })

    if "bez" in low and hint.source_phrase_indices:
        hint.residues.append({
            "type": "source_residue",
            "description": "Phrase 'bez źródła/dowodu' triggers source-gate caution.",
            "j_weight": 0.65,
        })

    return hint
