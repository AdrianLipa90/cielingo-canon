"""Dual-native wrapper for the canonical CIELingo surface endpoint.

The existing endpoint remains the realization and round-trip engine. This
wrapper validates the v2 transaction, independently recomputes both complete
native semantic bindings, and then delegates a compatibility v1 plan whose
linguistic and Lingophysics payload comes from the response-native state.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .hashing import canonical_sha256, is_sha256
from .native_surface_endpoint import NativeSurfaceGenerationEndpoint
from .response_semantics import parse_response_semantic_plan

DUAL_SURFACE_PLAN_SCHEMA = "CIEL_NATIVE_SURFACE_PLAN_V2"
NATIVE_SEMANTIC_SCHEMA = "CIEL_NATIVE_SEMANTIC_STATE_V1"


def _mapping(value: Any, *, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be an object")
    return value


def _validate_native_payload(
    value: Any,
    *,
    expected_binding: str,
    expected_memory: str,
    name: str,
) -> Mapping[str, Any]:
    payload = _mapping(value, name=name)
    if payload.get("schema") != NATIVE_SEMANTIC_SCHEMA:
        raise ValueError(f"{name} has invalid native semantic schema")
    declared_binding = str(payload.get("binding_sha256", ""))
    if declared_binding != expected_binding:
        raise ValueError(f"{name} declared binding mismatch")
    binding_body = {
        key: item for key, item in payload.items() if key != "binding_sha256"
    }
    if canonical_sha256(binding_body) != expected_binding:
        raise ValueError(f"{name} native semantic binding mismatch")
    if str(payload.get("memory_read_set_sha256", "")) != expected_memory:
        raise ValueError(f"{name} MemoryReadSet binding mismatch")
    _mapping(payload.get("cielingo"), name=f"{name}.cielingo")
    _mapping(payload.get("lingophysics"), name=f"{name}.lingophysics")
    claim_boundary = _mapping(
        payload.get("claim_boundary"), name=f"{name}.claim_boundary"
    )
    for authority in ("canon_promoted", "source_promoted", "code_updated"):
        if bool(claim_boundary.get(authority, False)):
            raise ValueError(f"{name} grants forbidden authority: {authority}")
    return payload


def _require_equal(actual: Any, expected: Any, *, name: str) -> None:
    if actual != expected:
        raise ValueError(f"dual-native response payload mismatch: {name}")


@dataclass
class DualNativeSurfaceGenerationEndpoint:
    """Handle a source-native + response-native generation transaction."""

    inner: NativeSurfaceGenerationEndpoint
    source_commit: str = "cielingo-canon:dual-native-surface-v0.6"

    def handle(self, request: Mapping[str, Any]) -> dict[str, Any]:
        try:
            return self._handle_ack(request)
        except (KeyError, TypeError, ValueError) as exc:
            return {
                "schema": "CIEL_AUX_TEXT_GENERATION_RESULT_V1",
                "status": "NACK",
                "request_sha256": request.get("request_sha256"),
                "detail": str(exc),
            }

    def _handle_ack(self, request: Mapping[str, Any]) -> dict[str, Any]:
        if request.get("schema") != "CIEL_AUX_TEXT_GENERATION_REQUEST_V1":
            raise ValueError("invalid text generation request schema")
        if request.get("operation") != "cielingo.lingophysics.generate_surface":
            raise ValueError("unsupported text generation operation")
        nonce = str(request.get("nonce", ""))
        if not nonce:
            raise ValueError("generation nonce is required")
        request_sha = str(request.get("request_sha256", ""))
        request_body = {
            key: value for key, value in request.items() if key != "request_sha256"
        }
        if request_sha != canonical_sha256(request_body):
            raise ValueError("text generation request hash mismatch")

        surface_plan = _mapping(request.get("surface_plan"), name="surface_plan")
        if surface_plan.get("schema") != DUAL_SURFACE_PLAN_SCHEMA:
            raise ValueError("invalid dual-native SurfacePlan schema")
        surface_sha = str(request.get("surface_plan_sha256", ""))
        if surface_plan.get("surface_plan_sha256") != surface_sha:
            raise ValueError("request does not bind dual-native SurfacePlan")
        surface_body = {
            key: value
            for key, value in surface_plan.items()
            if key != "surface_plan_sha256"
        }
        if surface_sha != canonical_sha256(surface_body):
            raise ValueError("dual-native SurfacePlan hash mismatch")

        surface_claim_boundary = _mapping(
            surface_plan.get("claim_boundary"), name="surface_plan.claim_boundary"
        )
        for required_flag in (
            "full_source_native_payload_bound",
            "full_response_native_payload_bound",
            "remote_native_binding_recomputation_required",
        ):
            if not bool(surface_claim_boundary.get(required_flag, False)):
                raise ValueError(
                    f"dual-native SurfacePlan requires {required_flag}=true"
                )
        for authority in (
            "canon_allowed",
            "source_promotion_allowed",
            "runtime_execution_allowed",
            "memory_write_allowed",
            "code_update_allowed",
        ):
            if bool(surface_claim_boundary.get(authority, False)):
                raise ValueError(
                    f"dual-native SurfacePlan grants forbidden authority: {authority}"
                )

        source_native = str(
            surface_plan.get("source_native_semantic_binding_sha256", "")
        )
        response_native = str(
            surface_plan.get("response_native_semantic_binding_sha256", "")
        )
        response_phase = str(
            surface_plan.get("response_phase_process_receipt_sha256", "")
        )
        source_memory = str(
            surface_plan.get("source_memory_read_set_sha256", "")
        )
        response_memory = str(
            surface_plan.get("response_memory_read_set_sha256", "")
        )
        response_plan_sha = str(surface_plan.get("response_plan_sha256", ""))
        for field_name, value in (
            ("source_native_semantic_binding_sha256", source_native),
            ("response_native_semantic_binding_sha256", response_native),
            ("response_phase_process_receipt_sha256", response_phase),
            ("source_memory_read_set_sha256", source_memory),
            ("response_memory_read_set_sha256", response_memory),
            ("response_plan_sha256", response_plan_sha),
        ):
            if not is_sha256(value):
                raise ValueError(
                    f"dual-native SurfacePlan {field_name} must be SHA-256"
                )
        if source_native == response_native:
            raise ValueError("source and response native bindings must be distinct")

        source_native_payload = _validate_native_payload(
            surface_plan.get("source_native_semantics"),
            expected_binding=source_native,
            expected_memory=source_memory,
            name="source_native_semantics",
        )
        response_native_payload = _validate_native_payload(
            surface_plan.get("response_native_semantics"),
            expected_binding=response_native,
            expected_memory=response_memory,
            name="response_native_semantics",
        )

        response_payload = _mapping(
            surface_plan.get("response_semantics"), name="response_semantics"
        )
        response_plan = parse_response_semantic_plan(response_payload)
        if response_plan.plan_sha256 != response_plan_sha:
            raise ValueError("dual-native SurfacePlan response-plan mismatch")
        if response_plan.source_native_binding_sha256 != source_native:
            raise ValueError("response plan does not bind source native semantics")
        if response_plan.memory_read_set_sha256 != source_memory:
            raise ValueError("response plan does not bind source MemoryReadSet")

        response_cielingo = _mapping(
            response_native_payload.get("cielingo"),
            name="response_native_semantics.cielingo",
        )
        response_lingophysics = _mapping(
            response_native_payload.get("lingophysics"),
            name="response_native_semantics.lingophysics",
        )
        _require_equal(
            list(response_cielingo.get("tokens", ())),
            list(response_plan.surface_seed_tokens),
            name="surface seed tokens",
        )
        _require_equal(
            response_lingophysics.get("sentence_equation"),
            response_plan.response_equation,
            name="response equation",
        )
        _require_equal(
            response_lingophysics.get("semantic_knot"),
            response_plan.semantic_knot,
            name="semantic knot",
        )
        _require_equal(
            response_lingophysics.get("invariant"),
            response_plan.invariant,
            name="response invariant",
        )
        _require_equal(
            response_lingophysics.get("meaning_state"),
            response_plan.meaning_state,
            name="meaning state",
        )

        _require_equal(
            surface_plan.get("cielingo_surface"),
            response_cielingo,
            name="CIELingo surface",
        )
        for field_name in (
            "sentence_equation",
            "semantic_knot",
            "invariant",
            "meaning_state",
            "concept_cards",
            "operator_cards",
            "grammar_gauge",
            "potential_components",
            "orbit",
        ):
            _require_equal(
                surface_plan.get(field_name),
                response_lingophysics.get(field_name),
                name=field_name,
            )
        _require_equal(
            surface_plan.get("consensus"),
            {
                "holonomy_phase": response_lingophysics.get(
                    "consensus_holonomy_phase"
                ),
                "coherence": response_lingophysics.get("consensus_coherence"),
            },
            name="consensus",
        )

        source_cielingo = _mapping(
            source_native_payload.get("cielingo"),
            name="source_native_semantics.cielingo",
        )
        if not source_cielingo.get("tokens"):
            raise ValueError("source native semantics must contain source tokens")

        compatibility_plan_body = {
            "schema": "CIEL_NATIVE_SURFACE_PLAN_V1",
            "native_semantic_binding_sha256": source_native,
            "phase_process_receipt_sha256": response_phase,
            "memory_read_set_sha256": source_memory,
            "response_plan_sha256": response_plan_sha,
            "response_semantics": dict(response_payload),
            "target_language": surface_plan.get("target_language"),
            "style": surface_plan.get("style"),
            "cielingo_surface": surface_plan.get("cielingo_surface"),
            "sentence_equation": surface_plan.get("sentence_equation"),
            "semantic_knot": surface_plan.get("semantic_knot"),
            "invariant": surface_plan.get("invariant"),
            "meaning_state": surface_plan.get("meaning_state"),
            "concept_cards": surface_plan.get("concept_cards", ()),
            "operator_cards": surface_plan.get("operator_cards", ()),
            "grammar_gauge": surface_plan.get("grammar_gauge", {}),
            "potential_components": surface_plan.get("potential_components", {}),
            "orbit": surface_plan.get("orbit", {}),
            "consensus": surface_plan.get("consensus", {}),
            "policy": surface_plan.get("policy", {}),
            "claim_boundary": {
                **dict(surface_claim_boundary),
                "dual_native_compatibility_projection": True,
                "full_native_payloads_recomputed": True,
                "source_native_semantic_binding_sha256": source_native,
                "response_native_semantic_binding_sha256": response_native,
                "response_memory_read_set_sha256": response_memory,
            },
        }
        compatibility_plan = {
            **compatibility_plan_body,
            "surface_plan_sha256": canonical_sha256(compatibility_plan_body),
        }
        compatibility_request_body = {
            "schema": "CIEL_AUX_TEXT_GENERATION_REQUEST_V1",
            "operation": "cielingo.lingophysics.generate_surface",
            "client_id": str(request.get("client_id", "dual-native-client")),
            "nonce": nonce,
            "surface_plan": compatibility_plan,
            "surface_plan_sha256": compatibility_plan["surface_plan_sha256"],
        }
        compatibility_request = {
            **compatibility_request_body,
            "request_sha256": canonical_sha256(compatibility_request_body),
        }
        inner_response = self.inner.handle(compatibility_request)
        if inner_response.get("status") != "ACK":
            return {
                "schema": "CIEL_AUX_TEXT_GENERATION_RESULT_V1",
                "status": "NACK",
                "request_sha256": request_sha,
                "detail": str(
                    inner_response.get("detail", "canonical surface endpoint NACK")
                ),
            }

        out = dict(inner_response)
        inner_receipt = _mapping(
            out.get("receipt"), name="canonical surface endpoint receipt"
        )
        receipt_body = {
            "schema": "NOEMA_CIEL_TEXT_GENERATION_RECEIPT_V1",
            "transport": "native_cielingo_dual_endpoint",
            "external_ack": False,
            "nonce": nonce,
            "request_sha256": request_sha,
            "source_native_semantic_binding_sha256": source_native,
            "response_native_semantic_binding_sha256": response_native,
            "source_memory_read_set_sha256": source_memory,
            "response_memory_read_set_sha256": response_memory,
            "response_phase_process_receipt_sha256": response_phase,
            "response_plan_sha256": response_plan_sha,
            "surface_plan_sha256": surface_sha,
            "final_text_sha256": canonical_sha256(
                {"text": out.get("final_text", "")}
            ),
            "inner_generation_receipt_sha256": inner_receipt.get("receipt_sha256"),
            "endpoint_source_commit": self.source_commit,
            "full_native_payloads_recomputed": True,
            "canon_allowed": False,
            "source_promotion_allowed": False,
            "runtime_execution_allowed": False,
            "memory_write_allowed": False,
            "code_update_allowed": False,
        }
        out.update(
            {
                "request_sha256": request_sha,
                "surface_plan_sha256": surface_sha,
                "response_plan_sha256": response_plan_sha,
                "receipt": {
                    **receipt_body,
                    "receipt_sha256": canonical_sha256(receipt_body),
                },
            }
        )
        return out


__all__ = ["DUAL_SURFACE_PLAN_SCHEMA", "DualNativeSurfaceGenerationEndpoint"]
