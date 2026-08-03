from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from cielingo_core.generation import (
    CandidateProposal,
    CanonicalLingophysicsRoundTripAdapter,
    CielingoLingophysicsRoundTripValidator,
    NativeResponseSemanticPlanner,
    NativeSurfaceGenerationEndpoint,
    PlannedLingophysicsRoundTripAdapter,
    canonical_sha256,
    semantic_payload_text,
)
from cielingo_core.language_spaces.pl.solver import PolishRegionalSolver


REPO_ROOT = Path(__file__).resolve().parents[1]


def _native_state() -> dict:
    return {
        "schema": "CIEL_NATIVE_SEMANTIC_STATE_V1",
        "binding_sha256": "1" * 64,
        "cielingo": {
            "language_id": "pl",
            "equation_id": "surface-input",
            "tokens": ["Człowiek", "buduje", "dom"],
            "slot_projection": {
                "agent": [0],
                "action": [1],
                "patient": [2],
            },
        },
        "lingophysics": {
            "sentence_equation": {
                "equation_id": "sentence-input",
                "expression": "REQUEST_GENERATION(Build(Human,House))",
            },
            "semantic_knot": {
                "concepts": ["human", "house"],
                "operators": ["build"],
            },
            "invariant": {
                "predicate": "build",
                "agent": "human",
                "patient": "house",
                "polarity": "positive",
            },
            "meaning_state": {
                "polarity": "positive",
                "tam_e": {
                    "tense": "Present",
                    "aspect": "Imperfective",
                    "mood": "Indicative",
                    "evidentiality": "Unknown",
                },
            },
        },
    }


def _surface_plan() -> dict:
    native = _native_state()
    response = NativeResponseSemanticPlanner().plan(
        query="Napisz zdanie opisujące tę relację.",
        source_native_semantics=native,
        memory_context={"read_set_sha256": "3" * 64, "evidence": []},
        target_language="pl",
        style="plain",
    )
    body = {
        "schema": "CIEL_NATIVE_SURFACE_PLAN_V1",
        "native_semantic_binding_sha256": native["binding_sha256"],
        "phase_process_receipt_sha256": "2" * 64,
        "memory_read_set_sha256": "3" * 64,
        "response_plan_sha256": response.plan_sha256,
        "response_semantics": response.to_dict(),
        "target_language": "pl",
        "style": "plain",
        "cielingo_surface": {
            "language_id": "pl",
            "equation_id": response.plan_id,
            "tokens": list(response.surface_seed_tokens),
            "slot_projection": {
                "agent": [0],
                "action": [1],
                "patient": [2],
            },
            "local_j": {"J_word_order": 0.4},
            "confidence": 0.95,
            "source_commit": "fixture-cielingo",
        },
        "sentence_equation": dict(response.response_equation),
        "semantic_knot": dict(response.semantic_knot),
        "invariant": dict(response.invariant),
        "meaning_state": dict(response.meaning_state),
        "concept_cards": [
            {"card_id": "concept:human", "version": "1", "semantic_mass": 0.6},
            {"card_id": "concept:house", "version": "1", "semantic_mass": 0.5},
        ],
        "operator_cards": [
            {
                "card_id": "operator:build",
                "version": "1",
                "signature": "Build(agent,patient)",
                "argument_types": {
                    "agent": ["person"],
                    "patient": ["artifact"],
                },
            }
        ],
        "grammar_gauge": {"language": "pl"},
        "potential_components": {"goal": 0.2},
        "orbit": {"kind": "semantic_attractor", "dimension": 36},
        "consensus": {"holonomy_phase": 0.1, "coherence": 0.97},
        "policy": {
            "target_language": "pl",
            "style": "plain",
            "max_chars": 2048,
            "min_semantic_equivalence": 0.90,
            "require_regional_realization": True,
            "require_expressive_rendering": True,
            "require_semantic_roundtrip": True,
            "allow_language_backend_candidate": True,
        },
        "claim_boundary": {
            "backend_candidate_advisory_only": True,
            "cielingo_validation_required": True,
            "lingophysics_roundtrip_required": True,
            "canon_allowed": False,
            "source_promotion_allowed": False,
            "runtime_execution_allowed": False,
            "memory_write_allowed": False,
            "code_update_allowed": False,
        },
    }
    return {**body, "surface_plan_sha256": canonical_sha256(body)}


def _request(plan: dict | None = None) -> dict:
    plan = plan or _surface_plan()
    body = {
        "schema": "CIEL_AUX_TEXT_GENERATION_REQUEST_V1",
        "operation": "cielingo.lingophysics.generate_surface",
        "client_id": "canonical-kernel-test",
        "nonce": "canonical-kernel-nonce",
        "surface_plan": plan,
        "surface_plan_sha256": plan["surface_plan_sha256"],
    }
    return {**body, "request_sha256": canonical_sha256(body)}


def _endpoint(*, backend=None) -> NativeSurfaceGenerationEndpoint:
    solver = PolishRegionalSolver(REPO_ROOT)
    canonical = CanonicalLingophysicsRoundTripAdapter.from_repo_root(REPO_ROOT)
    adapter = PlannedLingophysicsRoundTripAdapter(canonical)
    validator = CielingoLingophysicsRoundTripValidator(
        regional_solver=solver,
        lingophysics_adapter=adapter,
    )
    kwargs = {"validator": validator}
    if backend is not None:
        kwargs["backend"] = backend
    return NativeSurfaceGenerationEndpoint(**kwargs)


@dataclass
class NegativeCandidateBackend:
    def propose(self, surface_plan: dict) -> CandidateProposal:
        return CandidateProposal(
            text="Człowiek nie buduje dom.",
            backend_kind="language_backend",
            backend_id="negative-candidate",
            backend_version="test",
            source_commit="test-backend",
            advisory_only=True,
        )


@dataclass
class DeicticCandidateBackend:
    def propose(self, surface_plan: dict) -> CandidateProposal:
        return CandidateProposal(
            text="Człowiek buduje dom gdzieś.",
            backend_kind="language_backend",
            backend_id="deictic-candidate",
            backend_version="test",
            source_commit="test-backend",
            advisory_only=True,
        )


def test_canonical_kernel_generates_and_recovers_response_invariant() -> None:
    response = _endpoint().handle(_request())

    assert response["status"] == "ACK"
    assert "Człowiek buduje dom." in response["final_text"]
    assert response["roundtrip"]["semantic_equivalence"] == 1.0
    assert response["roundtrip"]["argument_structure_preserved"] is True
    assert response["roundtrip"]["polarity_preserved"] is True
    assert response["roundtrip"]["tam_e_preserved"] is True
    assert response["roundtrip"]["deictic_anchors_preserved"] is True
    assert response["roundtrip"]["conflict_count"] == 0
    assert response["roundtrip"]["response_plan_sha256"] == response[
        "response_plan_sha256"
    ]
    assert response["roundtrip"]["validator_source_commit"].startswith(
        "cielingo-canon:lingophysics"
    )


def test_contract_markers_do_not_flip_proposition_polarity() -> None:
    wrapped = (
        "draft_answer_candidate: Człowiek buduje dom. "
        "nie SOURCE. nie canon."
    )
    assert semantic_payload_text(wrapped) == "Człowiek buduje dom."


def test_canonical_kernel_rejects_polarity_change() -> None:
    response = _endpoint(backend=NegativeCandidateBackend()).handle(_request())

    assert response["status"] == "NACK"
    assert "polarity" in response["detail"]


def test_canonical_kernel_rejects_new_unbound_deictic_anchor() -> None:
    response = _endpoint(backend=DeicticCandidateBackend()).handle(_request())

    assert response["status"] == "NACK"
    assert "deictic" in response["detail"]


def test_polish_surface_equation_id_is_stable() -> None:
    first = PolishRegionalSolver(REPO_ROOT).solve("Człowiek buduje dom.")
    second = PolishRegionalSolver(REPO_ROOT).solve("Człowiek buduje dom.")

    assert first.surface_solution.equation_id == second.surface_solution.equation_id
    assert first.surface_solution.equation_id.startswith("surface_pl_")
