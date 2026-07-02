"""Deprecated thin router for sentence equations.

Architecture rule:
- canonical regional paths live in language_spaces/{pl,en,ja}/sentence_equation.py
- this module is kept only for CLI/backward-compatible tests
- it must not contain grammar, solver logic, regional J logic, or mixed-language state
"""

from __future__ import annotations

from pathlib import Path
import warnings

from cielingo_core.lingophysics.sentence_equation import SentenceEquation
from cielingo_core.language_spaces.pl.sentence_equation import solve_pl_sentence_equation
from cielingo_core.language_spaces.en.sentence_equation import solve_en_sentence_equation
from cielingo_core.language_spaces.ja.sentence_equation import solve_ja_sentence_equation


def solve_sentence_equation(text: str, language_id: str, repo_root: str | Path) -> SentenceEquation:
    warnings.warn(
        "solve_sentence_equation is a deprecated thin router; use language_spaces.<lang>.sentence_equation directly.",
        DeprecationWarning,
        stacklevel=2,
    )
    if language_id == "pl":
        return solve_pl_sentence_equation(text, repo_root)
    if language_id == "en":
        return solve_en_sentence_equation(text, repo_root)
    if language_id == "ja":
        return solve_ja_sentence_equation(text, repo_root)
    raise ValueError(f"Unsupported language_id: {language_id}")
