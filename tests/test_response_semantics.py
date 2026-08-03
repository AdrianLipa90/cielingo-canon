from __future__ import annotations

import copy

from cielingo_core.generation.hashing import canonical_sha256
from cielingo_core.generation.response_semantics import (
    NativeResponseSemanticPlanner,
    NativeResponseSemanticPlannerEndpoint,
    RESPONSE_PLAN_REQUEST_SCHEMA,
    parse_response_semantic_plan,
)


def _native_state() -> dict:
    sentence_equation = {
        "equation_id": "input-equation",
        "expression": "REQUEST_GENERATION(Build(Human,House))",
    }
    return {
        "schema": "CIEL_NATIVE_SEMANTIC_STATE_V1",
        "binding_sha256": "1" * 64,
        "cielingo": {
            "language_id": "pl",
            "equation_id": "surface-input",
            "tokens": ["człowiek", "buduje", "dom"],
            "slot_projection": {
                "agent": [0],
                "action": [1],
                "patient": [2],
            },
        },
        "lingophysics": {
            "sentence_equation": sentence_equation,
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


def _memory(*, with_evidence: bool = False) -> dict:
    evidence = []
    if with_evidence:
        evidence.append(
            {
                "evidence_id": "memory:capital-poland",
                "lane_id": 4,
                "subject": "stolica Polski",
                "predicate": "to",
                "object": "Warszawa",
                "confidence": 0.98,
                "status": "verified",
                "source_receipt_sha256": "2" * 64,
                "surface_text": "Stolicą Polski jest Warszawa.",
            }
        )
    return {"read_set_sha256": "3" * 64, "evidence": evidence}


def test_grounded_answer_is_new_semantics_bound_to_memory_evidence() -> None:
    plan = NativeResponseSemanticPlanner().plan(
        query="Jaka jest stolica Polski?",
        source_native_semantics=_native_state(),
        memory_context=_memory(with_evidence=True),
        target_language="pl",
        style="plain",
    )

    assert plan.discourse_act == "answer"
    assert plan.selected_evidence[0].evidence_id == "memory:capital-poland"
    assert plan.propositions[0].predicate == "to"
    assert "Warszawa" in plan.surface_seed_tokens
    assert canonical_sha256(plan.response_equation) != plan.source_sentence_equation_sha256
    assert plan.invariant["epistemic_status"] == "grounded"
    assert plan.claim_boundary["language_backend_may_choose_meaning"] is False
    plan.validate()


def test_missing_evidence_produces_epistemic_boundary_not_invented_fact() -> None:
    plan = NativeResponseSemanticPlanner().plan(
        query="Jaka jest stolica Atlantydy?",
        source_native_semantics=_native_state(),
        memory_context=_memory(with_evidence=False),
        target_language="pl",
        style="plain",
    )

    assert plan.discourse_act == "answer"
    assert plan.selected_evidence == ()
    assert plan.propositions[0].predicate == "knowledge_status"
    assert plan.invariant["epistemic_status"] == "unresolved_source_required"
    assert "źródła" in " ".join(plan.surface_seed_tokens)


def test_generate_text_realizes_requested_native_proposition_not_query_copy() -> None:
    plan = NativeResponseSemanticPlanner().plan(
        query="Napisz zdanie opisujące tę relację.",
        source_native_semantics=_native_state(),
        memory_context=_memory(),
        target_language="pl",
        style="plain",
    )

    assert plan.discourse_act == "generate"
    assert plan.response_equation["operator"] == "GENERATE"
    assert plan.surface_seed_tokens == ("człowiek", "buduje", "dom")
    assert plan.propositions[0].roles == {"agent": "human", "patient": "house"}
    assert canonical_sha256(plan.response_equation) != plan.source_sentence_equation_sha256


def test_command_becomes_non_executing_semantic_boundary() -> None:
    plan = NativeResponseSemanticPlanner().plan(
        query="Uruchom wdrożenie i ustaw CURRENT.",
        source_native_semantics=_native_state(),
        memory_context=_memory(),
        target_language="pl",
        style="plain",
    )

    assert plan.discourse_act == "boundary"
    assert plan.propositions[0].predicate == "execution_boundary"
    assert plan.propositions[0].roles["status"] == "not_executed"
    assert plan.claim_boundary["runtime_execution_allowed"] is False


def test_endpoint_receipts_and_parser_bind_exact_plan() -> None:
    body = {
        "schema": RESPONSE_PLAN_REQUEST_SCHEMA,
        "operation": "cielingo.lingophysics.plan_response_semantics",
        "client_id": "test-client",
        "nonce": "planner-nonce",
        "query": "Jaka jest stolica Polski?",
        "source_native_semantics": _native_state(),
        "memory_context": _memory(with_evidence=True),
        "target_language": "pl",
        "style": "plain",
    }
    request = {**body, "request_sha256": canonical_sha256(body)}
    response = NativeResponseSemanticPlannerEndpoint().handle(request)

    assert response["status"] == "ACK"
    plan = parse_response_semantic_plan(response["response_plan"])
    assert response["response_plan_sha256"] == plan.plan_sha256
    assert response["receipt"]["response_plan_sha256"] == plan.plan_sha256
    assert response["receipt"]["external_ack"] is False


def test_endpoint_rejects_mutated_request() -> None:
    body = {
        "schema": RESPONSE_PLAN_REQUEST_SCHEMA,
        "operation": "cielingo.lingophysics.plan_response_semantics",
        "client_id": "test-client",
        "nonce": "planner-nonce",
        "query": "Jaka jest stolica Polski?",
        "source_native_semantics": _native_state(),
        "memory_context": _memory(with_evidence=True),
        "target_language": "pl",
        "style": "plain",
    }
    request = {**body, "request_sha256": canonical_sha256(body)}
    mutated = copy.deepcopy(request)
    mutated["query"] = "Zmienione pytanie"

    response = NativeResponseSemanticPlannerEndpoint().handle(mutated)
    assert response["status"] == "NACK"
    assert "hash mismatch" in response["detail"]
