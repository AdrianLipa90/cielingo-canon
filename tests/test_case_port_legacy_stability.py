from __future__ import annotations

from pathlib import Path

from cielingo_core.language_spaces.pl.solver import PolishRegionalSolver
from cielingo_core.lingophysics.sentence_equation import calculate_sentence_equation


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_legacy_sentence_without_case_frame_does_not_gain_roles_section() -> None:
    result = PolishRegionalSolver(REPO_ROOT).solve("Człowiek buduje dom.")
    equation = calculate_sentence_equation(result)
    assert "Roles(" not in equation.expression
    assert all(term.kind.value != "role" for term in equation.terms)
