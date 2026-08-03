from __future__ import annotations

import copy

from cielingo_core.generation import (
    DualNativeSurfaceGenerationEndpoint,
    NativeSurfaceGenerationEndpoint,
    canonical_sha256,
)
from tests.test_native_surface_generation import (
    ValidRoundTripValidator,
    _surface_plan,
)


def _dual_surface_plan() -> dict:
    legacy = _surface_plan()
    body = {
        "schema": "CIEL_NATIVE_SURFACE_PLAN_V2",
        "source_native_semantic_binding_sha256": legacy[
            "native_semantic_binding_sha256"
        ],
        "response_native_semantic_binding_sha256": "4" * 64,
        "response_phase_process_receipt_sha256": legacy[
            "phase_process_receipt_sha256"
        ],
        "source_memory_read_set_sha256": legacy["memory_read_set_sha256"],
        "response_memory_read_set_sha256": "5" * 64,
        "response_plan_sha256": legacy["response_plan_sha256"],
        "response_semantics": copy.deepcopy(legacy["response_semantics"]),
        "target_language": legacy["target_language"],
        "style": legacy["style"],
        "cielingo_surface": copy.deepcopy(legacy["cielingo_surface"]),
        "sentence_equation": copy.deepcopy(legacy["sentence_equation"]),
        "semantic_knot": copy.deepcopy(legacy["semantic_knot"]),
        "invariant": copy.deepcopy(legacy["invariant"]),
        "meaning_state": copy.deepcopy(legacy["meaning_state"]),
        "concept_cards": copy.deepcopy(legacy["concept_cards"]),
        "operator_cards": copy.deepcopy(legacy["operator_cards"]),
        "grammar_gauge": copy.deepcopy(legacy["grammar_gauge"]),
        "potential_components": copy.deepcopy(legacy["potential_components"]),
        "orbit": copy.deepcopy(legacy["orbit"]),
        "consensus": copy.deepcopy(legacy["consensus"]),
        "policy": copy.deepcopy(legacy["policy"]),
        "claim_boundary": {
            "meaning_owned_by_response_plan": True,
            "source_and_response_native_states_distinct": True,
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
    plan = plan or _dual_surface_plan()
    body = {
        "schema": "CIEL_AUX_TEXT_GENERATION_REQUEST_V1",
        "operation": "cielingo.lingophysics.generate_surface",
        "client_id": "dual-native-test",
        "nonce": "dual-native-nonce",
        "surface_plan": plan,
        "surface_plan_sha256": plan["surface_plan_sha256"],
    }
    return {**body, "request_sha256": canonical_sha256(body)}


def _endpoint() -> DualNativeSurfaceGenerationEndpoint:
    return DualNativeSurfaceGenerationEndpoint(
        NativeSurfaceGenerationEndpoint(validator=ValidRoundTripValidator())
    )


def test_dual_native_endpoint_binds_source_response_and_both_memories() -> None:
    plan = _dual_surface_plan()
    response = _endpoint().handle(_request(plan))

    assert response["status"] == "ACK"
    receipt = response["receipt"]
    assert receipt["source_native_semantic_binding_sha256"] == plan[
        "source_native_semantic_binding_sha256"
    ]
    assert receipt["response_native_semantic_binding_sha256"] == plan[
        "response_native_semantic_binding_sha256"
    ]
    assert receipt["source_memory_read_set_sha256"] == plan[
        "source_memory_read_set_sha256"
    ]
    assert receipt["response_memory_read_set_sha256"] == plan[
        "response_memory_read_set_sha256"
    ]
    assert receipt["response_phase_process_receipt_sha256"] == plan[
        "response_phase_process_receipt_sha256"
    ]
    assert receipt["surface_plan_sha256"] == plan["surface_plan_sha256"]
    assert receipt["external_ack"] is False


def test_dual_native_endpoint_rejects_collapsed_native_states() -> None:
    plan = _dual_surface_plan()
    plan["response_native_semantic_binding_sha256"] = plan[
        "source_native_semantic_binding_sha256"
    ]
    body = {key: value for key, value in plan.items() if key != "surface_plan_sha256"}
    plan["surface_plan_sha256"] = canonical_sha256(body)

    response = _endpoint().handle(_request(plan))
    assert response["status"] == "NACK"
    assert "must be distinct" in response["detail"]


def test_dual_native_endpoint_rejects_mutated_response_memory_binding() -> None:
    request = _request()
    request["surface_plan"]["response_memory_read_set_sha256"] = "6" * 64

    response = _endpoint().handle(request)
    assert response["status"] == "NACK"
    assert "request hash mismatch" in response["detail"]
