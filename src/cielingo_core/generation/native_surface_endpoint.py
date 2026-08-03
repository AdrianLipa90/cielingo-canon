"""Native CIELingo × Lingophysics surface-generation endpoint.

The endpoint realizes text from a previously bound semantic SurfacePlan. It
never parses or invents semantic structure locally. A LanguageBackend may
propose fluent wording, CIELingo owns regional and expressive realization, and
an injected CIELingo × Lingophysics validator must prove a semantic round trip
before the result is acknowledged.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Any, Mapping, Protocol

from cielingo_core.expressive.style_renderer import (
    ExpressiveStyle,
    render_expressive_response,
)
from cielingo_core.global_layer.response_contract import build_response_contract
from cielingo_core.language_spaces.pl.response_realizer import realize_pl_response

REQUEST_SCHEMA = "CIEL_AUX_TEXT_GENERATION_REQUEST_V1"
RESULT_SCHEMA = "CIEL_AUX_TEXT_GENERATION_RESULT_V1"
RECEIPT_SCHEMA = "NOEMA_CIEL_TEXT_GENERATION_RECEIPT_V1"
SURFACE_PLAN_SCHEMA = "CIEL_NATIVE_SURFACE_PLAN_V1"


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(payload).hexdigest()


def _is_sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


@dataclass(frozen=True)
class CandidateProposal:
    """Fluent wording proposed from a bound native semantic plan."""

    text: str
    backend_kind: str
    backend_id: str
    backend_version: str
    source_commit: str
    advisory_only: bool

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.text.strip():
            issues.append("candidate text must not be empty")
        if self.backend_kind not in {
            "cielingo_native",
            "deterministic_regional",
            "language_backend",
            "gguf_advisory",
        }:
            issues.append("unsupported candidate backend_kind")
        if not self.backend_id or not self.backend_version or not self.source_commit:
            issues.append("candidate backend provenance is incomplete")
        if self.backend_kind in {"language_backend", "gguf_advisory"} and not self.advisory_only:
            issues.append("external language backend must be advisory_only")
        return issues


class LanguageBackend(Protocol):
    """Surface proposer; never the semantic source of truth."""

    def propose(self, surface_plan: Mapping[str, Any]) -> CandidateProposal:
        """Return one wording candidate from the bound SurfacePlan."""


@dataclass(frozen=True)
class DeterministicSurfaceBackend:
    """Native deterministic reconstruction for bounded/offline operation.

    This backend joins the ordered CIELingo surface tokens. It is suitable when
    the SurfacePlan already describes the desired response semantics. It is not
    an alternate parser or semantic engine.
    """

    backend_id: str = "cielingo-deterministic-surface"
    backend_version: str = "v1"
    source_commit: str = "cielingo-canon"

    def propose(self, surface_plan: Mapping[str, Any]) -> CandidateProposal:
        surface = surface_plan.get("cielingo_surface", {})
        if not isinstance(surface, Mapping):
            raise ValueError("SurfacePlan cielingo_surface must be an object")
        tokens = [str(token) for token in surface.get("tokens", ())]
        if not tokens:
            raise ValueError("SurfacePlan contains no CIELingo tokens")
        text = _detokenize(tokens)
        return CandidateProposal(
            text=text,
            backend_kind="cielingo_native",
            backend_id=self.backend_id,
            backend_version=self.backend_version,
            source_commit=self.source_commit,
            advisory_only=False,
        )


def _detokenize(tokens: list[str]) -> str:
    text = ""
    no_space_before = set(".,!?;:%)]}")
    no_space_after = set("([{„«")
    for token in tokens:
        if not text:
            text = token
        elif token and token[0] in no_space_before:
            text += token
        elif text[-1:] in no_space_after:
            text += token
        else:
            text += " " + token
    if text and text[-1] not in ".!?":
        text += "."
    return text


@dataclass(frozen=True)
class RoundTripEvidence:
    """Evidence returned by the native CIELingo × Lingophysics validator."""

    generated_surface_solution_sha256: str
    generated_sentence_equation_sha256: str
    generated_semantic_knot_sha256: str
    recovered_invariant_sha256: str
    semantic_equivalence: float
    argument_structure_preserved: bool
    polarity_preserved: bool
    tam_e_preserved: bool
    deictic_anchors_preserved: bool
    conflict_count: int
    validator_source_commit: str

    def validate(
        self,
        *,
        surface_plan: Mapping[str, Any],
        minimum_equivalence: float,
    ) -> list[str]:
        issues: list[str] = []
        for name in (
            "generated_surface_solution_sha256",
            "generated_sentence_equation_sha256",
            "generated_semantic_knot_sha256",
            "recovered_invariant_sha256",
        ):
            if not _is_sha256(getattr(self, name)):
                issues.append(f"{name} must be SHA-256")
        expected_invariant = canonical_sha256(surface_plan.get("invariant"))
        if self.recovered_invariant_sha256 != expected_invariant:
            issues.append("generated text did not preserve semantic invariant")
        if not 0.0 <= float(self.semantic_equivalence) <= 1.0:
            issues.append("semantic_equivalence must be in [0,1]")
        elif float(self.semantic_equivalence) < float(minimum_equivalence):
            issues.append("semantic equivalence below policy threshold")
        if not self.argument_structure_preserved:
            issues.append("operator argument structure was not preserved")
        if not self.polarity_preserved:
            issues.append("polarity was not preserved")
        if not self.tam_e_preserved:
            issues.append("TAM-E was not preserved")
        if not self.deictic_anchors_preserved:
            issues.append("deictic anchors were not preserved")
        if int(self.conflict_count) != 0:
            issues.append("semantic round trip contains unresolved conflicts")
        if not self.validator_source_commit:
            issues.append("validator_source_commit is required")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class RoundTripValidator(Protocol):
    """Native validator implemented by connected CIELingo and Lingophysics."""

    def validate_surface(
        self,
        text: str,
        surface_plan: Mapping[str, Any],
    ) -> RoundTripEvidence:
        """Recompile the surface and return native semantic evidence."""


@dataclass
class NativeSurfaceGenerationEndpoint:
    """Handle one `cielingo.lingophysics.generate_surface` request."""

    validator: RoundTripValidator
    backend: LanguageBackend = DeterministicSurfaceBackend()
    cielingo_source_commit: str = "cielingo-canon"

    def handle(self, request: Mapping[str, Any]) -> dict[str, Any]:
        try:
            return self._handle_ack(request)
        except (KeyError, TypeError, ValueError) as exc:
            return {
                "schema": RESULT_SCHEMA,
                "status": "NACK",
                "request_sha256": request.get("request_sha256"),
                "detail": str(exc),
            }

    def _handle_ack(self, request: Mapping[str, Any]) -> dict[str, Any]:
        if request.get("schema") != REQUEST_SCHEMA:
            raise ValueError("invalid text generation request schema")
        if request.get("operation") != "cielingo.lingophysics.generate_surface":
            raise ValueError("unsupported text generation operation")
        nonce = str(request.get("nonce", ""))
        if not nonce:
            raise ValueError("generation nonce is required")
        request_sha = str(request.get("request_sha256", ""))
        request_body = {key: value for key, value in request.items() if key != "request_sha256"}
        if request_sha != canonical_sha256(request_body):
            raise ValueError("text generation request hash mismatch")

        surface_plan = request.get("surface_plan")
        if not isinstance(surface_plan, Mapping):
            raise ValueError("surface_plan must be an object")
        if surface_plan.get("schema") != SURFACE_PLAN_SCHEMA:
            raise ValueError("invalid native SurfacePlan schema")
        plan_sha = str(request.get("surface_plan_sha256", ""))
        if surface_plan.get("surface_plan_sha256") != plan_sha:
            raise ValueError("request does not bind the SurfacePlan")
        plan_body = {
            key: value
            for key, value in surface_plan.items()
            if key != "surface_plan_sha256"
        }
        if plan_sha != canonical_sha256(plan_body):
            raise ValueError("SurfacePlan hash mismatch")

        native_binding = str(surface_plan.get("native_semantic_binding_sha256", ""))
        phase_receipt = str(surface_plan.get("phase_process_receipt_sha256", ""))
        memory_read_hash = str(surface_plan.get("memory_read_set_sha256", ""))
        for name, value in (
            ("native_semantic_binding_sha256", native_binding),
            ("phase_process_receipt_sha256", phase_receipt),
            ("memory_read_set_sha256", memory_read_hash),
        ):
            if not _is_sha256(value):
                raise ValueError(f"SurfacePlan {name} must be SHA-256")

        policy = surface_plan.get("policy", {})
        if not isinstance(policy, Mapping):
            raise ValueError("SurfacePlan policy must be an object")
        target_language = str(policy.get("target_language", ""))
        style = str(policy.get("style", "plain"))
        max_chars = int(policy.get("max_chars", 8192))
        minimum_equivalence = float(policy.get("min_semantic_equivalence", 0.90))
        if target_language != "pl":
            raise ValueError("native endpoint currently requires target_language=pl")
        if max_chars <= 0:
            raise ValueError("generation max_chars must be positive")
        if not 0.0 <= minimum_equivalence <= 1.0:
            raise ValueError("min_semantic_equivalence must be in [0,1]")

        contract = build_response_contract(
            intention="generate_text",
            answer_kind="draft_text_generation",
            severity="info",
            required_markers=[
                "draft_answer_candidate",
                "nie SOURCE",
                "nie canon",
            ],
            forbidden_claims=[
                "SOURCE confirmed",
                "canon confirmed",
                "runtime executed",
                "CURRENT updated",
            ],
            uncertainty_required=False,
            source_required=False,
            repair_routes=[],
        )
        contract_issues = contract.validate()
        if contract_issues:
            raise ValueError("; ".join(contract_issues))

        candidate = self.backend.propose(surface_plan)
        candidate_issues = candidate.validate()
        if candidate_issues:
            raise ValueError("; ".join(candidate_issues))
        if len(candidate.text) > max_chars:
            raise ValueError("surface candidate exceeds max_chars")

        regional = realize_pl_response(contract, candidate_text=candidate.text)
        regional_issues = regional.validate()
        if regional_issues:
            raise ValueError("; ".join(regional_issues))

        expressive = render_expressive_response(
            contract,
            regional,
            ExpressiveStyle(style),
        )
        expressive_issues = expressive.validate()
        if expressive_issues:
            raise ValueError("; ".join(expressive_issues))
        if len(expressive.text) > max_chars:
            raise ValueError("final generated text exceeds max_chars")

        evidence = self.validator.validate_surface(expressive.text, surface_plan)
        evidence_issues = evidence.validate(
            surface_plan=surface_plan,
            minimum_equivalence=minimum_equivalence,
        )
        if evidence_issues:
            raise ValueError("; ".join(evidence_issues))

        concept_binding = canonical_sha256(
            [
                {
                    "card_id": str(card.get("card_id")),
                    "version": str(card.get("version")),
                }
                for card in surface_plan.get("concept_cards", ())
            ]
        )
        operator_binding = canonical_sha256(
            [
                {
                    "card_id": str(card.get("card_id")),
                    "version": str(card.get("version")),
                    "signature": str(card.get("signature")),
                    "argument_types": {
                        str(key): list(values)
                        for key, values in dict(card.get("argument_types", {})).items()
                    },
                }
                for card in surface_plan.get("operator_cards", ())
            ]
        )
        invariant_sha = canonical_sha256(surface_plan.get("invariant"))
        roundtrip_body = {
            **evidence.to_dict(),
            "source_invariant_sha256": invariant_sha,
            "concept_binding_sha256": concept_binding,
            "operator_binding_sha256": operator_binding,
            "required_markers_preserved": True,
        }
        roundtrip = {
            **roundtrip_body,
            "receipt_sha256": canonical_sha256(roundtrip_body),
        }

        contract_payload = contract.to_dict()
        contract_payload.update(
            {
                "source_commit": self.cielingo_source_commit,
                "receipt_sha256": canonical_sha256(
                    {
                        "contract": contract.to_dict(),
                        "source_commit": self.cielingo_source_commit,
                    }
                ),
            }
        )

        candidate_body = {
            "candidate_id": "surface_candidate_"
            + canonical_sha256(
                {
                    "plan": plan_sha,
                    "backend": candidate.backend_id,
                    "text": candidate.text,
                }
            )[:16],
            "text": candidate.text,
            "backend_kind": candidate.backend_kind,
            "backend_id": candidate.backend_id,
            "backend_version": candidate.backend_version,
            "prompt_binding_sha256": plan_sha,
            "candidate_sha256": canonical_sha256({"text": candidate.text}),
            "advisory_only": candidate.advisory_only,
            "source_commit": candidate.source_commit,
        }
        candidate_payload = {
            **candidate_body,
            "receipt_sha256": canonical_sha256(candidate_body),
        }

        regional_body = {
            "draft_id": regional.draft_id,
            "language_id": regional.language_id,
            "style": "regional",
            "contract_id": regional.contract_id,
            "text": regional.text,
            "preserved_markers": list(regional.preserved_markers),
            "missing_markers": list(regional.missing_markers),
            "forbidden_claims_present": list(regional.forbidden_claims_present),
            "stable_hash": regional.stable_hash(),
            "source_commit": self.cielingo_source_commit,
            "canon_allowed": False,
            "source_promotion_allowed": False,
            "runtime_execution_allowed": False,
            "noema_writeback_allowed": False,
            "current_update_allowed": False,
        }
        regional_payload = {
            **regional_body,
            "receipt_sha256": canonical_sha256(regional_body),
        }

        expressive_body = {
            "draft_id": expressive.expressive_id,
            "language_id": target_language,
            "style": expressive.style.value,
            "contract_id": expressive.contract_id,
            "text": expressive.text,
            "preserved_markers": list(expressive.preserved_markers),
            "missing_markers": list(expressive.missing_markers),
            "forbidden_claims_present": list(expressive.forbidden_claims_present),
            "stable_hash": expressive.stable_hash(),
            "source_commit": self.cielingo_source_commit,
            "canon_allowed": False,
            "source_promotion_allowed": False,
            "runtime_execution_allowed": False,
            "noema_writeback_allowed": False,
            "current_update_allowed": False,
        }
        expressive_payload = {
            **expressive_body,
            "receipt_sha256": canonical_sha256(expressive_body),
        }

        receipt_body = {
            "schema": RECEIPT_SCHEMA,
            "transport": "native_cielingo_endpoint",
            "external_ack": False,
            "nonce": nonce,
            "request_sha256": request_sha,
            "native_semantic_binding_sha256": native_binding,
            "phase_process_receipt_sha256": phase_receipt,
            "memory_read_set_sha256": memory_read_hash,
            "surface_plan_sha256": plan_sha,
            "final_text_sha256": canonical_sha256({"text": expressive.text}),
            "canon_allowed": False,
            "source_promotion_allowed": False,
            "runtime_execution_allowed": False,
            "memory_write_allowed": False,
            "code_update_allowed": False,
        }
        receipt = {
            **receipt_body,
            "receipt_sha256": canonical_sha256(receipt_body),
        }

        return {
            "schema": RESULT_SCHEMA,
            "status": "ACK",
            "request_sha256": request_sha,
            "surface_plan_sha256": plan_sha,
            "target_language": target_language,
            "style": style,
            "final_text": expressive.text,
            "response_contract": contract_payload,
            "candidate": candidate_payload,
            "regional_draft": regional_payload,
            "expressive_draft": expressive_payload,
            "roundtrip": roundtrip,
            "receipt": receipt,
        }
