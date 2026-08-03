from __future__ import annotations

from dataclasses import dataclass

from cielingo_core.generation import (
    CielingoLingophysicsRoundTripValidator,
    LingophysicsRoundTripVerdict,
    canonical_sha256,
)


@dataclass
class FakeSurfaceSolution:
    language_id: str = "pl"
    equation_id: str = "generated-surface"
    tokens: tuple[str, ...] = ("Człowiek", "buduje", "dom", ".")
    slot_projection: dict = None
    operator_projection: dict = None
    residuals: tuple = ()
    local_j: dict = None
    confidence: float = 0.97

    def __post_init__(self) -> None:
        if self.slot_projection is None:
            self.slot_projection = {1: [0], 2: [1], 3: [2]}
        if self.operator_projection is None:
            self.operator_projection = {"BUILD": [1]}
        if self.local_j is None:
            self.local_j = {"J_word_order": 0.4}


@dataclass
class FakeRegionalResult:
    surface_solution: FakeSurfaceSolution

    def validate(self) -> list[str]:
        return []


@dataclass
class FakeSentenceEquation:
    payload: dict

    def validate(self) -> list[str]:
        return []

    def to_dict(self) -> dict:
        return dict(self.payload)


@dataclass
class FakeRegionalSolver:
    def solve(self, text: str) -> FakeRegionalResult:
        assert text
        return FakeRegionalResult(FakeSurfaceSolution())


@dataclass
class FakeLingophysicsAdapter:
    def validate_roundtrip(
        self,
        *,
        source_surface_plan: dict,
        generated_regional_result: FakeRegionalResult,
        generated_sentence_equation: FakeSentenceEquation,
    ) -> LingophysicsRoundTripVerdict:
        assert generated_regional_result.validate() == []
        assert generated_sentence_equation.validate() == []
        return LingophysicsRoundTripVerdict(
            recovered_semantic_knot={"operator": "build"},
            recovered_invariant=dict(source_surface_plan["invariant"]),
            semantic_equivalence=0.99,
            argument_structure_preserved=True,
            polarity_preserved=True,
            tam_e_preserved=True,
            deictic_anchors_preserved=True,
            conflicts=(),
            source_commit="fixture-lingophysics",
        )


def test_composed_roundtrip_uses_regional_equation_and_lingophysics() -> None:
    plan = {
        "invariant": {
            "predicate": "build",
            "agent": "human",
            "patient": "house",
        }
    }
    validator = CielingoLingophysicsRoundTripValidator(
        regional_solver=FakeRegionalSolver(),
        lingophysics_adapter=FakeLingophysicsAdapter(),
        sentence_equation_calculator=lambda result: FakeSentenceEquation(
            {
                "equation_id": "generated-equation",
                "tokens": list(result.surface_solution.tokens),
            }
        ),
    )

    evidence = validator.validate_surface("Człowiek buduje dom.", plan)

    assert evidence.recovered_invariant_sha256 == canonical_sha256(plan["invariant"])
    assert evidence.semantic_equivalence == 0.99
    assert evidence.argument_structure_preserved is True
    assert evidence.polarity_preserved is True
    assert evidence.tam_e_preserved is True
    assert evidence.deictic_anchors_preserved is True
    assert evidence.conflict_count == 0
    assert evidence.validator_source_commit == "fixture-lingophysics"
