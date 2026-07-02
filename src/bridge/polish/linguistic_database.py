"""Polish linguistic database for CIELingo.

This is a compact runtime database and adapter. It does not pretend to be a
complete Polish grammar; it gives the executable surface required by CIELingo:
parts of speech, sentence parts, morphology, punctuation, word order,
semantic mass axes, vocabulary seed and links to lingophysics LNS.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


DEFAULT_DB_REL = Path("data/cielingo/polish/polish_linguistic_surface_v01.json")


@dataclass(frozen=True)
class Lexeme:
    lemma: str
    forms: tuple[str, ...]
    pos: str
    payload: dict[str, Any]

    def case_for(self, form: str) -> str | None:
        if "case_forms" in self.payload:
            return self.payload["case_forms"].get(form)
        return self.payload.get("case")


class PolishLinguisticDatabase:
    def __init__(self, payload: dict[str, Any]):
        self.payload = payload
        self.lexemes = [
            Lexeme(
                lemma=item["lemma"],
                forms=tuple(item.get("forms", [item["lemma"]])),
                pos=item.get("pos", "unknown"),
                payload=item,
            )
            for item in payload.get("vocabulary", [])
        ]
        self._form_index: dict[str, Lexeme] = {}
        for lex in self.lexemes:
            for form in lex.forms:
                self._form_index[form.lower()] = lex

    def lookup_form(self, surface: str) -> Lexeme | None:
        return self._form_index.get(surface.lower())

    @property
    def parts_of_speech(self) -> dict[str, Any]:
        return self.payload.get("parts_of_speech", {})

    @property
    def sentence_parts(self) -> dict[str, Any]:
        return self.payload.get("sentence_parts", {})

    @property
    def morphology(self) -> dict[str, Any]:
        return self.payload.get("morphology", {})

    @property
    def semantic_mass_axes(self) -> list[str]:
        return list(self.payload.get("semantic_mass_axes", []))

    def semantic_mass(self, surface: str) -> dict[str, float]:
        lex = self.lookup_form(surface)
        if not lex:
            return {axis: 0.0 for axis in self.semantic_mass_axes}
        mass = lex.payload.get("semantic_mass", {})
        return {axis: float(mass.get(axis, 0.0)) for axis in self.semantic_mass_axes}

    def punctuation_operator(self, mark: str) -> dict[str, Any] | None:
        return self.payload.get("punctuation", {}).get(mark)

    def database_summary(self) -> dict[str, Any]:
        return {
            "schema": self.payload.get("schema"),
            "status": self.payload.get("status"),
            "parts_of_speech": sorted(self.parts_of_speech.keys()),
            "sentence_parts": sorted(self.sentence_parts.keys()),
            "case_count": len(self.morphology.get("cases", {})),
            "semantic_mass_axes": self.semantic_mass_axes,
            "lexeme_count": len(self.lexemes),
            "epistemic_boundary": self.payload.get("epistemic_boundary", {}),
        }


def load_polish_database(repo_root: str | Path = ".", rel_path: str | Path = DEFAULT_DB_REL) -> PolishLinguisticDatabase:
    root = Path(repo_root).resolve()
    path = root / rel_path
    if not path.exists():
        # Support running directly from patch root or source package tests.
        alt = Path(__file__).resolve().parents[3] / rel_path
        path = alt if alt.exists() else path
    payload = json.loads(path.read_text(encoding="utf-8"))
    return PolishLinguisticDatabase(payload)


__all__ = ["Lexeme", "PolishLinguisticDatabase", "load_polish_database"]
