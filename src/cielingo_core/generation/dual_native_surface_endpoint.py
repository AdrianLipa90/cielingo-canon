"""Dual-native wrapper for the canonical CIELingo surface endpoint.

The existing endpoint remains the realization and round-trip engine. This
wrapper validates the v2 transaction, preserving separate source and response
native bindings, then delegates a compatibility v1 plan whose linguistic and
Lingophysics payload already comes from the response-native state.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .hashing import canonical_sha256, is_sha256
from .native_surface_endpoint import NativeSurfaceGenerationEndpoint
from .response_semantics import parse_response_semantic_plan

DUAL_SURFACE_PLAN_SCHEMA = "CIEL_NATIVE_SURFACE_PLAN_V2"


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

        surface_plan = request.get("surface_plan")
        if not isinstance(surface_plan, Mapping):
            raise ValueError("surface_plan must be an object")
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
        for name, value in (
            ("source_native_semantic_binding_sha256", source_native),
            ("response_native_semantic_binding_sha256", response_native),
            ("response_phase_process_receipt_sha256", response_phase),
            ("source_memory_read_set_sha256", source_memory),
            ("response_memory_read_set_sha256", response_memory),
            ("response_plan_sha256", response_plan_sha),
        ):
            if not is_sha256(value):
                raise ValueError(f"dual-native SurfacePlan {name} must be SHA-256")
        if source_native == response_native:
            raise ValueError("source and response native bindings must be distinct")

        response_payload = surface_plan.get("response_semantics")
        if not isinstance(response_payload, Mapping):
            raise ValueError("dual-native SurfacePlan requires response_semantics")
        response_plan = parse_response_semantic_plan(response_payload)
        if response_plan.plan_sha256 != response_plan_sha:
            raise ValueError("dual-native SurfacePlan response-plan mismatch")
        if response_plan.source_native_binding_sha256 != source_native:
            raise ValueError("response plan does not bind source native semantics")
        if response_plan.memory_read_set_sha256 != source_memory:
            raise ValueError("response plan does not bind source MemoryReadSet")

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
                **dict(surface_plan.get("claim_boundary", {})),
                "dual_native_compatibility_projection": True,
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
        inner_receipt = out.get("receipt")
        if not isinstance(inner_receipt, Mapping):
            raise ValueError("canonical surface endpoint returned no receipt")
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
