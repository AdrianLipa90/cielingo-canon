"""Polish sentence-equation path.

PL owns its regional surface route:
PL text -> PolishRegionalSolver -> SurfaceSolution -> shared SentenceEquation contract.
"""

from __future__ import annotations

from pathlib import Path

from cielingo_core.lingophysics.sentence_equation import SentenceEquation, calculate_sentence_equation
from cielingo_core.language_spaces.pl.solver import PolishRegionalSolver


def solve_pl_sentence_equation(text: str, repo_root: str | Path) -> SentenceEquation:
    solver = PolishRegionalSolver(repo_root)
    return calculate_sentence_equation(solver.solve(text))
