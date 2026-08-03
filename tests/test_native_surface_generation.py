from __future__ import annotations

from dataclasses import dataclass

from cielingo_core.generation.native_surface_endpoint import (
    CandidateProposal,
    NativeSurfaceGenerationEndpoint,
    RoundTripEvidence,
    canonical_sha256,
)
from cielingo_core.global_layer.response_contract import build_response_contract
from cielingo_core.language_spaces.pl.response_realizer import realize_pl_response


def _surface_plan() -> dict:
    body = {
        "schema": "CIEL_NATIVE_SURFACE_PLAN_V1",
        "native_semantic_binding_sha256": "1" * 64,
        "phase_process_receipt_sha256": "2" * 64,
        "memory_read_set_sha256": "3" * 64,
        "target_language": "pl",
        "style": "plain",
        "cielingo_surface": {
            "language_id": "pl",
            "equation_id": "surface-fixture",
            "tokens": ["Człowiek", "buduje", "dom"],
            "slot_projection": {
                "agent": [0],
                "action": [1],
                "patient": [2],
            },
            "local_j": {"J_word_order": 0.4},
            "confidence": 0.95,
            "source_commit": "fixture-cielingo",
        },
        "sentence_equation": {
            "equation_id": "sentence-fixture",
            "expression": "Build(Human,House)",
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
            "tam_e": {"tense": "present", "aspect": "imperfective"},
            "deictic_anchors": [],
        },
        "concept_cards": [
            {"card_id": "concept:human", "version": "1"},
            {"card_id": "concept:house", "version": "1"},
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
        "client_id": "test-client",
        "nonce": "fixture-nonce",
        "surface_plan": plan,
        "surface_plan_sha256": plan["surface_plan_sha256"],
    }
    return {**body, "request_sha256": canonical_sha256(body)}


@dataclass
class ValidRoundTripValidator:
    recovered_invariant_sha256: str | None = None
    polarity_preserved: bool = True

    def validate_surface(self, text: str, surface_plan: dict) -> RoundTripEvidence:
        return RoundTripEvidence(
            generated_surface_solution_sha256=canonical_sha256(
                {"text": text, "kind": "SurfaceSolution"}
            ),
            generated_sentence_equation_sha256=canonical_sha256(
                {"text": text, "kind": "SentenceEquation"}
            ),
            generated_semantic_knot_sha256=canonical_sha256(
                {"text": text, "kind": "SemanticKnot"}
            ),
            recovered_invariant_sha256=self.recovered_invariant_sha256
            or canonical_sha256(surface_plan["invariant"]),
            semantic_equivalence=0.98,
            argument_structure_preserved=True,
            polarity_preserved=self.polarity_preserved,
            tam_e_preserved=True,
            deictic_anchors_preserved=True,
            conflict_count=0,
            validator_source_commit="fixture-native-validator",
        )


@dataclass
class UnsafeGGUFBackend:
    def propose(self, surface_plan: dict) -> CandidateProposal:
        return CandidateProposal(
            text="Człowiek buduje dom.",
            backend_kind="gguf_advisory",
            backend_id="unsafe-gguf",
            backend_version="fixture",
            source_commit="fixture-gguf",
            advisory_only=False,
        )


def test_endpoint_generates_receipted_polish_surface() -> None:
    endpoint = NativeSurfaceGenerationEndpoint(
        validator=ValidRoundTripValidator(),
        cielingo_source_commit="fixture-cielingo-commit",
    )
    response = endpoint.handle(_request())

    assert response["status"] == "ACK"
    assert response["schema"] == "CIEL_AUX_TEXT_GENERATION_RESULT_V1"
    assert "Człowiek buduje dom." in response["final_text"]
    assert "draft_answer_candidate" in response["final_text"]
    assert "nie SOURCE" in response["final_text"]
    assert "nie canon" in response["final_text"]
    assert response["candidate"]["backend_kind"] == "cielingo_native"
    assert response["roundtrip"]["semantic_equivalence"] == 0.98
    assert response["receipt"]["external_ack"] is False
    assert response["receipt"]["memory_write_allowed"] is False
    assert response["receipt"]["final_text_sha256"] == canonical_sha256(
        {"text": response["final_text"]}
    )


def test_candidate_aware_realizer_preserves_content_and_contract() -> None:
    contract = build_response_contract(
        intention="generate_text",
        answer_kind="draft_text_generation",
        severity="info",
        required_markers=["draft_answer_candidate", "nie SOURCE", "nie canon"],
        forbidden_claims=["SOURCE confirmed", "canon confirmed"],
    )
    regional = realize_pl_response(
        contract,
        candidate_text="Dom powstaje dzięki pracy człowieka.",
    )

    assert "Dom powstaje dzięki pracy człowieka." in regional.text
    assert regional.missing_markers == []
    assert regional.forbidden_claims_present == []
    assert regional.validate() == []


def test_endpoint_rejects_semantic_invariant_loss() -> None:
    endpoint = NativeSurfaceGenerationEndpoint(
        validator=ValidRoundTripValidator(recovered_invariant_sha256="f" * 64)
    )
    response = endpoint.handle(_request())

    assert response["status"] == "NACK"
    assert "semantic invariant" in response["detail"]


def test_endpoint_rejects_non_advisory_gguf() -> None:
    endpoint = NativeSurfaceGenerationEndpoint(
        validator=ValidRoundTripValidator(),
        backend=UnsafeGGUFBackend(),
    )
    response = endpoint.handle(_request())

    assert response["status"] == "NACK"
    assert "advisory_only" in response["detail"]


def test_endpoint_rejects_lost_polarity() -> None:
    endpoint = NativeSurfaceGenerationEndpoint(
        validator=ValidRoundTripValidator(polarity_preserved=False)
    )
    response = endpoint.handle(_request())

    assert response["status"] == "NACK"
    assert "polarity" in response["detail"]


def test_endpoint_rejects_request_hash_mutation() -> None:
    request = _request()
    request["surface_plan"]["style"] = "formal"
    endpoint = NativeSurfaceGenerationEndpoint(validator=ValidRoundTripValidator())
    response = endpoint.handle(request)

    assert response["status"] == "NACK"
    assert "request hash mismatch" in response["detail"]
