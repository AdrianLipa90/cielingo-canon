"""English sentence-equation path.

EN owns its regional surface route:
EN text -> EnglishRegionalSolver -> SurfaceSolution -> shared SentenceEquation contract.
"""

from __future__ import annotations

from pathlib import Path

from cielingo_core.lingophysics.sentence_equation import SentenceEquation, calculate_sentence_equation
from cielingo_core.language_spaces.en.solver import EnglishRegionalSolver


def solve_en_sentence_equation(text: str, repo_root: str | Path) -> SentenceEquation:
    solver = EnglishRegionalSolver(repo_root)
    return calculate_sentence_equation(solver.solve(text))
