"""Compose response-semantic plans with the existing Lingophysics adapter.

The checked-in Lingophysics adapter validates proposition structure.  A response
plan additionally carries a discourse act and receipt bindings.  This wrapper
normalizes the planned proposition for the existing kernel, then restores the
full response invariant only after every native gate succeeds.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
import copy
from typing import Any, Mapping

from .hashing import canonical_sha256
from .native_roundtrip import (
    LingophysicsRoundTripAdapter,
    LingophysicsRoundTripVerdict,
)
from .response_semantics import parse_response_semantic_plan


@dataclass(frozen=True)
class PlannedLingophysicsRoundTripAdapter:
    """Bind a response plan to an existing Lingophysics round-trip kernel."""

    inner: LingophysicsRoundTripAdapter
    source_commit: str = "cielingo-canon:planned-roundtrip-v0.5"

    def validate_roundtrip(
        self,
        *,
        source_surface_plan: Mapping[str, Any],
        generated_regional_result: Any,
        generated_sentence_equation: Any,
    ) -> LingophysicsRoundTripVerdict:
        payload = source_surface_plan.get("response_semantics")
        if not isinstance(payload, Mapping):
            raise ValueError("planned roundtrip requires response_semantics")
        plan = parse_response_semantic_plan(payload)

        normalized = copy.deepcopy(dict(source_surface_plan))
        normalized["invariant"] = _proposition_invariant(plan.invariant)
        normalized["meaning_state"] = copy.deepcopy(dict(plan.meaning_state))
        normalized["semantic_knot"] = copy.deepcopy(dict(plan.semantic_knot))
        surface = copy.deepcopy(dict(normalized.get("cielingo_surface", {})))
        surface["tokens"] = list(plan.surface_seed_tokens)
        surface["equation_id"] = plan.plan_id
        normalized["cielingo_surface"] = surface
        normalized["sentence_equation"] = copy.deepcopy(
            dict(plan.response_equation)
        )

        verdict = self.inner.validate_roundtrip(
            source_surface_plan=normalized,
            generated_regional_result=generated_regional_result,
            generated_sentence_equation=generated_sentence_equation,
        )
        accepted = (
            verdict.argument_structure_preserved
            and verdict.polarity_preserved
            and verdict.tam_e_preserved
            and verdict.deictic_anchors_preserved
            and not verdict.conflicts
        )
        if not accepted:
            return replace(
                verdict,
                source_commit=f"{verdict.source_commit}|{self.source_commit}",
            )

        recovered_knot = {
            **dict(plan.semantic_knot),
            "inner_recovered_semantic_knot_sha256": canonical_sha256(
                verdict.recovered_semantic_knot
            ),
            "response_plan_sha256": plan.plan_sha256,
        }
        return LingophysicsRoundTripVerdict(
            recovered_semantic_knot=recovered_knot,
            recovered_invariant=dict(plan.invariant),
            semantic_equivalence=float(verdict.semantic_equivalence),
            argument_structure_preserved=True,
            polarity_preserved=True,
            tam_e_preserved=True,
            deictic_anchors_preserved=True,
            conflicts=(),
            source_commit=f"{verdict.source_commit}|{self.source_commit}",
        )


def _proposition_invariant(response_invariant: Mapping[str, Any]) -> dict[str, Any]:
    roles = response_invariant.get("roles", {})
    if not isinstance(roles, Mapping) or not roles:
        raise ValueError("response invariant requires proposition roles")
    return {
        "predicate": str(response_invariant.get("predicate", "")),
        **{str(key): str(value) for key, value in roles.items()},
        "polarity": str(response_invariant.get("polarity", "positive")),
        "tam_e": copy.deepcopy(dict(response_invariant.get("tam_e", {}))),
        "discourse_act": str(response_invariant.get("discourse_act", "")),
        "response_equation_sha256": str(
            response_invariant.get("response_equation_sha256", "")
        ),
    }


__all__ = ["PlannedLingophysicsRoundTripAdapter"]
