"""Native semantic round-trip adapter for generated CIEL surfaces.

CIELingo recompiles the semantic payload of the final text through an existing
regional solver and ``calculate_sentence_equation``. Lingophysics remains
authoritative for semantic knot/invariant recovery and equivalence. Contract
markers are validated by the endpoint but removed from the semantic payload
before linguistic recompilation so safety phrases such as ``nie SOURCE`` do not
look like proposition-level negation.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Any, Callable, Mapping, Protocol

from cielingo_core.generation.native_surface_endpoint import (
    RoundTripEvidence,
    canonical_sha256,
)
from cielingo_core.lingophysics.sentence_equation import calculate_sentence_equation
from cielingo_core.regional.base import RegionalSolveResult


class RegionalSolver(Protocol):
    """Existing CIELingo regional language solver."""

    def solve(self, text: str) -> RegionalSolveResult:
        """Compile final surface text into a regional result."""


@dataclass(frozen=True)
class LingophysicsRoundTripVerdict:
    """Authoritative Lingophysics comparison with the source SurfacePlan."""

    recovered_semantic_knot: Mapping[str, Any]
    recovered_invariant: Mapping[str, Any]
    semantic_equivalence: float
    argument_structure_preserved: bool
    polarity_preserved: bool
    tam_e_preserved: bool
    deictic_anchors_preserved: bool
    conflicts: tuple[Mapping[str, Any], ...]
    source_commit: str

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not isinstance(self.recovered_semantic_knot, Mapping):
            issues.append("recovered_semantic_knot must be an object")
        if not isinstance(self.recovered_invariant, Mapping):
            issues.append("recovered_invariant must be an object")
        if not 0.0 <= float(self.semantic_equivalence) <= 1.0:
            issues.append("semantic_equivalence must be in [0,1]")
        if not self.source_commit:
            issues.append("Lingophysics source_commit is required")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class LingophysicsRoundTripAdapter(Protocol):
    """Existing Lingophysics implementation used for final comparison."""

    def validate_roundtrip(
        self,
        *,
        source_surface_plan: Mapping[str, Any],
        generated_regional_result: RegionalSolveResult,
        generated_sentence_equation: Any,
    ) -> LingophysicsRoundTripVerdict:
        """Recover knot/invariant and compare them with the source plan."""


@dataclass
class CielingoLingophysicsRoundTripValidator:
    """Concrete endpoint validator composed from native CIEL components."""

    regional_solver: RegionalSolver
    lingophysics_adapter: LingophysicsRoundTripAdapter
    sentence_equation_calculator: Callable[[RegionalSolveResult], Any] = (
        calculate_sentence_equation
    )

    def validate_surface(
        self,
        text: str,
        surface_plan: Mapping[str, Any],
    ) -> RoundTripEvidence:
        semantic_text = semantic_payload_text(text)
        regional = self.regional_solver.solve(semantic_text)
        regional_issues = regional.validate()
        if regional_issues:
            raise ValueError(
                "generated CIELingo regional solution failed: "
                + "; ".join(regional_issues)
            )

        sentence_equation = self.sentence_equation_calculator(regional)
        equation_issues = sentence_equation.validate()
        if equation_issues:
            raise ValueError(
                "generated SentenceEquation failed: "
                + "; ".join(equation_issues)
            )

        verdict = self.lingophysics_adapter.validate_roundtrip(
            source_surface_plan=surface_plan,
            generated_regional_result=regional,
            generated_sentence_equation=sentence_equation,
        )
        verdict_issues = verdict.validate()
        if verdict_issues:
            raise ValueError(
                "Lingophysics roundtrip verdict failed: "
                + "; ".join(verdict_issues)
            )

        return RoundTripEvidence(
            generated_surface_solution_sha256=canonical_sha256(
                _surface_solution_dict(regional)
            ),
            generated_sentence_equation_sha256=canonical_sha256(
                sentence_equation.to_dict()
            ),
            generated_semantic_knot_sha256=canonical_sha256(
                verdict.recovered_semantic_knot
            ),
            recovered_invariant_sha256=canonical_sha256(
                verdict.recovered_invariant
            ),
            semantic_equivalence=float(verdict.semantic_equivalence),
            argument_structure_preserved=bool(
                verdict.argument_structure_preserved
            ),
            polarity_preserved=bool(verdict.polarity_preserved),
            tam_e_preserved=bool(verdict.tam_e_preserved),
            deictic_anchors_preserved=bool(
                verdict.deictic_anchors_preserved
            ),
            conflict_count=len(verdict.conflicts),
            validator_source_commit=verdict.source_commit,
        )


def semantic_payload_text(text: str) -> str:
    """Extract proposition text from the visible contract-wrapped response.

    Required markers stay in the final output and are checked separately by the
    response contract. They are not proposition content and therefore must not
    perturb polarity, TAM-E, scope or deictic analysis.
    """

    value = str(text).strip()
    prefixes = (
        "Wersja formalna: ",
        "Spin ustawiony na jawność granic: ",
        "Na powierzchni odpowiedzi zostawiam kotwice bezpieczeństwa: ",
    )
    for prefix in prefixes:
        if value.startswith(prefix):
            value = value[len(prefix):].lstrip()
            break

    value = re.sub(
        r"^draft_answer_candidate\s*:\s*",
        "",
        value,
        flags=re.IGNORECASE,
    )
    # The candidate-aware realizer appends missing markers as sentence-final
    # boundary declarations. Remove only those exact boundary forms.
    value = re.sub(
        r"(?:\s*\.\s*)?draft_answer_candidate\s*\.?\s*$",
        "",
        value,
        flags=re.IGNORECASE,
    )
    value = re.sub(
        r"\s*\.\s*nie SOURCE\s*\.\s*nie canon\s*\.\s*$",
        ".",
        value,
        flags=re.IGNORECASE,
    )
    return value.strip()


def _surface_solution_dict(result: RegionalSolveResult) -> dict[str, Any]:
    surface = result.surface_solution
    return {
        "language_id": surface.language_id,
        "equation_id": surface.equation_id,
        "tokens": list(surface.tokens),
        "slot_projection": {
            str(key): list(values)
            for key, values in surface.slot_projection.items()
        },
        "operator_projection": {
            str(key): list(values)
            for key, values in surface.operator_projection.items()
        },
        "residuals": [asdict(residue) for residue in surface.residuals],
        "local_j": dict(surface.local_j),
        "confidence": float(surface.confidence),
    }
