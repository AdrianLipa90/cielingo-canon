"""Japanese sentence-equation path.

JA owns its regional surface route:
JA text -> JapaneseRegionalSolver -> SurfaceSolution -> shared SentenceEquation contract.
Native review remains required.
"""

from __future__ import annotations

from pathlib import Path

from cielingo_core.lingophysics.sentence_equation import SentenceEquation, calculate_sentence_equation
from cielingo_core.language_spaces.ja.solver import JapaneseRegionalSolver


def solve_ja_sentence_equation(text: str, repo_root: str | Path) -> SentenceEquation:
    solver = JapaneseRegionalSolver(repo_root)
    return calculate_sentence_equation(solver.solve(text))
