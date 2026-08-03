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


def _native_payload(
    *,
    cielingo: dict,
    lingophysics: dict,
    memory_read_set_sha256: str,
    marker: str,
) -> dict:
    body = {
        "schema": "CIEL_NATIVE_SEMANTIC_STATE_V1",
        "cielingo": copy.deepcopy(cielingo),
        "lingophysics": copy.deepcopy(lingophysics),
        "phasenav_binding_sha256": canonical_sha256(
            {"kind": "phase", "marker": marker}
        ),
        "memory_read_set_sha256": memory_read_set_sha256,
        "noema_receipt_sha256": canonical_sha256(
            {"kind": "noema", "marker": marker}
        ),
        "claim_boundary": {
            "external_ack": False,
            "canon_promoted": False,
            "source_promoted": False,
            "code_updated": False,
        },
    }
    return {**body, "binding_sha256": canonical_sha256(body)}


def _dual_surface_plan() -> dict:
    legacy = _surface_plan()
    source_memory = legacy["memory_read_set_sha256"]
    response_memory = "5" * 64

    source_equation = {
        "equation_id": "sentence-input",
        "expression": "REQUEST_GENERATION(Build(Human,House))",
    }
    source_cielingo = {
        "language_id": "pl",
        "equation_id": "surface-input",
        "tokens": ["Człowiek", "buduje", "dom"],
        "slot_projection": {
            "agent": [0],
            "action": [1],
            "patient": [2],
        },
        "local_j": {"J_word_order": 0.3},
        "confidence": 0.96,
        "regional_notes_digest": canonical_sha256({"kind": "source-notes"}),
        "source_commit": "fixture-source-cielingo",
        "receipt_sha256": canonical_sha256({"kind": "source-cielingo"}),
    }
    source_lingophysics = {
        "concept_cards": [
            {"card_id": "source:human", "version": "1"},
            {"card_id": "source:house", "version": "1"},
        ],
        "operator_cards": [
            {
                "card_id": "source:build",
                "version": "1",
                "signature": "Build(agent,patient)",
                "argument_types": {
                    "agent": ["person"],
                    "patient": ["artifact"],
                },
            }
        ],
        "relation_graph_sha256": canonical_sha256({"kind": "source-graph"}),
        "grammar_gauge": {"word_order": 0.4},
        "sentence_equation": source_equation,
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
        "semantic_mass_total": 1.0,
        "potential_components": {"source": 0.1},
        "orbit": {"kind": "source", "dimension": 36},
        "consensus_holonomy_phase": 0.0,
        "consensus_coherence": 0.95,
        "conflicts": [],
        "source_commit": "fixture-source-lingophysics",
        "receipt_sha256": canonical_sha256({"kind": "source-lingophysics"}),
    }
    source_native = _native_payload(
        cielingo=source_cielingo,
        lingophysics=source_lingophysics,
        memory_read_set_sha256=source_memory,
        marker="source",
    )

    response_semantics = copy.deepcopy(legacy["response_semantics"])
    response_semantics["source_native_binding_sha256"] = source_native[
        "binding_sha256"
    ]
    response_semantics["memory_read_set_sha256"] = source_memory
    response_body = {
        key: value
        for key, value in response_semantics.items()
        if key != "plan_sha256"
    }
    response_semantics["plan_sha256"] = canonical_sha256(response_body)

    response_cielingo = copy.deepcopy(legacy["cielingo_surface"])
    response_cielingo.update(
        {
            "regional_notes_digest": canonical_sha256(
                {"kind": "response-notes"}
            ),
            "receipt_sha256": canonical_sha256({"kind": "response-cielingo"}),
        }
    )
    response_lingophysics = {
        "concept_cards": copy.deepcopy(legacy["concept_cards"]),
        "operator_cards": copy.deepcopy(legacy["operator_cards"]),
        "relation_graph_sha256": canonical_sha256({"kind": "response-graph"}),
        "grammar_gauge": copy.deepcopy(legacy["grammar_gauge"]),
        "sentence_equation": copy.deepcopy(response_semantics["response_equation"]),
        "semantic_knot": copy.deepcopy(response_semantics["semantic_knot"]),
        "invariant": copy.deepcopy(response_semantics["invariant"]),
        "meaning_state": copy.deepcopy(response_semantics["meaning_state"]),
        "semantic_mass_total": 1.2,
        "potential_components": copy.deepcopy(legacy["potential_components"]),
        "orbit": copy.deepcopy(legacy["orbit"]),
        "consensus_holonomy_phase": legacy["consensus"]["holonomy_phase"],
        "consensus_coherence": legacy["consensus"]["coherence"],
        "conflicts": [],
        "source_commit": "fixture-response-lingophysics",
        "receipt_sha256": canonical_sha256({"kind": "response-lingophysics"}),
    }
    response_native = _native_payload(
        cielingo=response_cielingo,
        lingophysics=response_lingophysics,
        memory_read_set_sha256=response_memory,
        marker="response",
    )

    body = {
        "schema": "CIEL_NATIVE_SURFACE_PLAN_V2",
        "source_native_semantic_binding_sha256": source_native[
            "binding_sha256"
        ],
        "response_native_semantic_binding_sha256": response_native[
            "binding_sha256"
        ],
        "source_native_semantics": source_native,
        "response_native_semantics": response_native,
        "response_phase_process_receipt_sha256": legacy[
            "phase_process_receipt_sha256"
        ],
        "source_memory_read_set_sha256": source_memory,
        "response_memory_read_set_sha256": response_memory,
        "response_plan_sha256": response_semantics["plan_sha256"],
        "response_semantics": response_semantics,
        "target_language": legacy["target_language"],
        "style": legacy["style"],
        "cielingo_surface": response_cielingo,
        "sentence_equation": copy.deepcopy(response_lingophysics["sentence_equation"]),
        "semantic_knot": copy.deepcopy(response_lingophysics["semantic_knot"]),
        "invariant": copy.deepcopy(response_lingophysics["invariant"]),
        "meaning_state": copy.deepcopy(response_lingophysics["meaning_state"]),
        "concept_cards": copy.deepcopy(response_lingophysics["concept_cards"]),
        "operator_cards": copy.deepcopy(response_lingophysics["operator_cards"]),
        "grammar_gauge": copy.deepcopy(response_lingophysics["grammar_gauge"]),
        "potential_components": copy.deepcopy(
            response_lingophysics["potential_components"]
        ),
        "orbit": copy.deepcopy(response_lingophysics["orbit"]),
        "consensus": {
            "holonomy_phase": response_lingophysics[
                "consensus_holonomy_phase"
            ],
            "coherence": response_lingophysics["consensus_coherence"],
        },
        "policy": copy.deepcopy(legacy["policy"]),
        "claim_boundary": {
            "meaning_owned_by_response_plan": True,
            "source_and_response_native_states_distinct": True,
            "full_source_native_payload_bound": True,
            "full_response_native_payload_bound": True,
            "remote_native_binding_recomputation_required": True,
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


def _rebind_plan(plan: dict) -> dict:
    body = {
        key: value for key, value in plan.items() if key != "surface_plan_sha256"
    }
    plan["surface_plan_sha256"] = canonical_sha256(body)
    return plan


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
    assert receipt["full_native_payloads_recomputed"] is True
    assert receipt["external_ack"] is False


def test_dual_native_endpoint_rejects_collapsed_native_states() -> None:
    plan = _dual_surface_plan()
    plan["response_native_semantic_binding_sha256"] = plan[
        "source_native_semantic_binding_sha256"
    ]
    _rebind_plan(plan)

    response = _endpoint().handle(_request(plan))
    assert response["status"] == "NACK"
    assert "must be distinct" in response["detail"]


def test_dual_native_endpoint_rejects_mutated_response_memory_binding() -> None:
    request = _request()
    request["surface_plan"]["response_memory_read_set_sha256"] = "6" * 64

    response = _endpoint().handle(request)
    assert response["status"] == "NACK"
    assert "request hash mismatch" in response["detail"]


def test_dual_native_endpoint_rejects_rehashed_native_payload_mutation() -> None:
    plan = _dual_surface_plan()
    plan["response_native_semantics"]["lingophysics"]["invariant"][
        "predicate"
    ] = "tampered"
    _rebind_plan(plan)

    response = _endpoint().handle(_request(plan))
    assert response["status"] == "NACK"
    assert "native semantic binding mismatch" in response["detail"]


def test_dual_native_endpoint_rejects_rehashed_surface_projection_mutation() -> None:
    plan = _dual_surface_plan()
    plan["concept_cards"][0]["card_id"] = "tampered:concept"
    _rebind_plan(plan)

    response = _endpoint().handle(_request(plan))
    assert response["status"] == "NACK"
    assert "concept_cards" in response["detail"]
