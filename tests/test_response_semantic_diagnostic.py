from __future__ import annotations

from cielingo_core.generation import (
    CanonicalLingophysicsRoundTripAdapter,
    DeterministicSurfaceBackend,
    PlannedLingophysicsRoundTripAdapter,
)
from cielingo_core.language_spaces.pl.solver import PolishRegionalSolver
from cielingo_core.lingophysics.sentence_equation import calculate_sentence_equation
from tests.test_canonical_lingophysics_adapter import REPO_ROOT, _surface_plan


def test_canonical_response_semantic_diagnostic() -> None:
    plan = _surface_plan()
    candidate = DeterministicSurfaceBackend().propose(plan)
    regional = PolishRegionalSolver(REPO_ROOT).solve(candidate.text)
    equation = calculate_sentence_equation(regional)
    canonical = CanonicalLingophysicsRoundTripAdapter.from_repo_root(REPO_ROOT)
    adapter = PlannedLingophysicsRoundTripAdapter(canonical)
    verdict = adapter.validate_roundtrip(
        source_surface_plan=plan,
        generated_regional_result=regional,
        generated_sentence_equation=equation,
    )

    assert verdict.tam_e_preserved is True, verdict.to_dict()
    assert verdict.conflicts == (), verdict.to_dict()
