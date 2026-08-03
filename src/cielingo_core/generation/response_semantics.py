"""Native response-semantic planning for CIELingo × Lingophysics.

This module creates the *meaning of the answer* before surface realization.
It is intentionally separate from the language backend: a backend may later
propose wording, but it cannot choose propositions, authority, evidence, TAM-E,
polarity or the response invariant.

The first planner is bounded and explicit.  It supports grounded answers,
verification, requested proposition realization, safe command boundaries and
clarification.  Unsupported or under-evidenced factual requests remain
unresolved instead of being filled with invented facts.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Mapping, Sequence

from cielingo_core.global_layer.query_generation import QueryIntention, understand_query

from .hashing import canonical_sha256, is_sha256

RESPONSE_PLAN_REQUEST_SCHEMA = "CIEL_AUX_RESPONSE_PLAN_REQUEST_V1"
RESPONSE_PLAN_RESULT_SCHEMA = "CIEL_AUX_RESPONSE_PLAN_RESULT_V1"
RESPONSE_PLAN_SCHEMA = "CIEL_RESPONSE_SEMANTIC_PLAN_V1"
RESPONSE_PLAN_RECEIPT_SCHEMA = "NOEMA_CIEL_RESPONSE_PLAN_RECEIPT_V1"

_ALLOWED_EVIDENCE_STATUS = {"verified", "accepted", "candidate", "ephemeral"}
_ALLOWED_DISCOURSE_ACTS = {
    "answer",
    "verify",
    "generate",
    "boundary",
    "clarify",
}
_TOKEN_RE = re.compile(r"\w+|[^\w\s]", flags=re.UNICODE)


class ResponsePlanningError(ValueError):
    """Raised when a response-semantic transaction is invalid."""


@dataclass(frozen=True)
class SemanticEvidence:
    """One receipted proposition selected from MemoryFabric or native context."""

    evidence_id: str
    lane_id: int
    subject: str
    predicate: str
    object_value: str
    confidence: float
    status: str
    source_receipt_sha256: str
    surface_text: str | None = None

    def validate(self) -> None:
        if not self.evidence_id:
            raise ResponsePlanningError("evidence_id is required")
        if not 0 <= int(self.lane_id) < 12:
            raise ResponsePlanningError("evidence lane_id must be in [0,11]")
        if not self.subject or not self.predicate:
            raise ResponsePlanningError("evidence subject and predicate are required")
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ResponsePlanningError("evidence confidence must be in [0,1]")
        if self.status not in _ALLOWED_EVIDENCE_STATUS:
            raise ResponsePlanningError("unsupported evidence status")
        if not is_sha256(self.source_receipt_sha256):
            raise ResponsePlanningError("evidence source receipt must be SHA-256")

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "lane_id": self.lane_id,
            "subject": self.subject,
            "predicate": self.predicate,
            "object": self.object_value,
            "confidence": self.confidence,
            "status": self.status,
            "source_receipt_sha256": self.source_receipt_sha256,
            "surface_text": self.surface_text,
        }


@dataclass(frozen=True)
class SemanticProposition:
    """A typed proposition owned by the response plan, not by the realizer."""

    proposition_id: str
    predicate: str
    roles: Mapping[str, str]
    polarity: str
    tam_e: Mapping[str, Any]
    modality: str
    confidence: float
    evidence_ids: tuple[str, ...]
    source_kind: str

    def validate(self) -> None:
        if not self.proposition_id or not self.predicate:
            raise ResponsePlanningError("proposition identity and predicate are required")
        if not self.roles or any(not str(k) or not str(v) for k, v in self.roles.items()):
            raise ResponsePlanningError("proposition roles must be non-empty")
        if self.polarity not in {"positive", "negative"}:
            raise ResponsePlanningError("proposition polarity must be positive or negative")
        if not self.modality:
            raise ResponsePlanningError("proposition modality is required")
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ResponsePlanningError("proposition confidence must be in [0,1]")
        if self.source_kind not in {
            "memory_evidence",
            "native_request_content",
            "epistemic_boundary",
            "dialogue_control",
        }:
            raise ResponsePlanningError("unsupported proposition source_kind")

    def to_dict(self) -> dict[str, Any]:
        return {
            "proposition_id": self.proposition_id,
            "predicate": self.predicate,
            "roles": dict(self.roles),
            "polarity": self.polarity,
            "tam_e": dict(self.tam_e),
            "modality": self.modality,
            "confidence": self.confidence,
            "evidence_ids": list(self.evidence_ids),
            "source_kind": self.source_kind,
        }


@dataclass(frozen=True)
class ResponseSemanticPlan:
    """Receipted meaning selected for the answer before text generation."""

    plan_id: str
    source_query: str
    source_query_sha256: str
    source_native_binding_sha256: str
    source_sentence_equation_sha256: str
    memory_read_set_sha256: str
    intention: str
    discourse_act: str
    propositions: tuple[SemanticProposition, ...]
    response_equation: Mapping[str, Any]
    semantic_knot: Mapping[str, Any]
    invariant: Mapping[str, Any]
    meaning_state: Mapping[str, Any]
    surface_seed_tokens: tuple[str, ...]
    selected_evidence: tuple[SemanticEvidence, ...]
    claim_boundary: Mapping[str, Any]
    plan_sha256: str

    def validate(self) -> None:
        if not self.plan_id or not self.source_query.strip():
            raise ResponsePlanningError("response plan identity and source query are required")
        for name, value in (
            ("source_query_sha256", self.source_query_sha256),
            ("source_native_binding_sha256", self.source_native_binding_sha256),
            ("source_sentence_equation_sha256", self.source_sentence_equation_sha256),
            ("memory_read_set_sha256", self.memory_read_set_sha256),
            ("plan_sha256", self.plan_sha256),
        ):
            if not is_sha256(value):
                raise ResponsePlanningError(f"{name} must be SHA-256")
        if self.source_query_sha256 != canonical_sha256({"text": self.source_query}):
            raise ResponsePlanningError("source query digest mismatch")
        if self.discourse_act not in _ALLOWED_DISCOURSE_ACTS:
            raise ResponsePlanningError("unsupported discourse act")
        if not self.propositions:
            raise ResponsePlanningError("response plan requires at least one proposition")
        proposition_ids = [item.proposition_id for item in self.propositions]
        if len(set(proposition_ids)) != len(proposition_ids):
            raise ResponsePlanningError("duplicate response proposition id")
        for proposition in self.propositions:
            proposition.validate()
        evidence_ids = [item.evidence_id for item in self.selected_evidence]
        if len(set(evidence_ids)) != len(evidence_ids):
            raise ResponsePlanningError("duplicate selected evidence id")
        for evidence in self.selected_evidence:
            evidence.validate()
        selected = set(evidence_ids)
        for proposition in self.propositions:
            if not set(proposition.evidence_ids).issubset(selected):
                raise ResponsePlanningError("proposition references unselected evidence")
        if not self.surface_seed_tokens or any(not token for token in self.surface_seed_tokens):
            raise ResponsePlanningError("response surface seed must not be empty")
        response_equation_sha = canonical_sha256(self.response_equation)
        if response_equation_sha == self.source_sentence_equation_sha256:
            raise ResponsePlanningError(
                "response equation must be a new discourse-semantic object"
            )
        if self.invariant.get("discourse_act") != self.discourse_act:
            raise ResponsePlanningError("response invariant does not bind discourse act")
        if self.invariant.get("response_equation_sha256") != response_equation_sha:
            raise ResponsePlanningError("response invariant does not bind equation")
        if any(
            bool(self.claim_boundary.get(field, False))
            for field in (
                "canon_allowed",
                "source_promotion_allowed",
                "runtime_execution_allowed",
                "memory_write_allowed",
                "code_update_allowed",
            )
        ):
            raise ResponsePlanningError("response plan grants forbidden authority")
        if self.plan_sha256 != canonical_sha256(self.to_binding_dict()):
            raise ResponsePlanningError("response semantic plan binding mismatch")

    def to_binding_dict(self) -> dict[str, Any]:
        return {
            "schema": RESPONSE_PLAN_SCHEMA,
            "plan_id": self.plan_id,
            "source_query": self.source_query,
            "source_query_sha256": self.source_query_sha256,
            "source_native_binding_sha256": self.source_native_binding_sha256,
            "source_sentence_equation_sha256": self.source_sentence_equation_sha256,
            "memory_read_set_sha256": self.memory_read_set_sha256,
            "intention": self.intention,
            "discourse_act": self.discourse_act,
            "propositions": [item.to_dict() for item in self.propositions],
            "response_equation": dict(self.response_equation),
            "semantic_knot": dict(self.semantic_knot),
            "invariant": dict(self.invariant),
            "meaning_state": dict(self.meaning_state),
            "surface_seed_tokens": list(self.surface_seed_tokens),
            "selected_evidence": [item.to_dict() for item in self.selected_evidence],
            "claim_boundary": dict(self.claim_boundary),
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.to_binding_dict(), "plan_sha256": self.plan_sha256}


@dataclass(frozen=True)
class NativeResponseSemanticPlanner:
    """Bounded planner that refuses to invent unsupported factual content."""

    source_commit: str = "cielingo-canon:semantic-response-planner-v0.5"

    def plan(
        self,
        *,
        query: str,
        source_native_semantics: Mapping[str, Any],
        memory_context: Mapping[str, Any],
        target_language: str,
        style: str,
    ) -> ResponseSemanticPlan:
        if target_language != "pl":
            raise ResponsePlanningError("planner currently supports target_language=pl")
        if not style:
            raise ResponsePlanningError("response style is required")
        source_binding = str(source_native_semantics.get("binding_sha256", ""))
        if not is_sha256(source_binding):
            raise ResponsePlanningError("source native semantic binding is invalid")
        memory_hash = str(memory_context.get("read_set_sha256", ""))
        if not is_sha256(memory_hash):
            raise ResponsePlanningError("memory context read_set_sha256 is invalid")

        lingophysics = _mapping(
            source_native_semantics.get("lingophysics"), "source lingophysics"
        )
        source_equation = _mapping(
            lingophysics.get("sentence_equation"), "source sentence_equation"
        )
        source_equation_sha = canonical_sha256(source_equation)
        evidence = _parse_evidence(memory_context.get("evidence", ()))
        understood = understand_query(query)

        if understood.intention in {QueryIntention.ASK, QueryIntention.VERIFY}:
            selected = _select_relevant_evidence(query, evidence)
            if selected:
                discourse_act = (
                    "verify" if understood.intention == QueryIntention.VERIFY else "answer"
                )
                propositions = tuple(_proposition_from_evidence(item) for item in selected)
                surface_tokens = _tokens_from_evidence(selected[0])
                epistemic_status = "grounded"
            else:
                discourse_act = (
                    "verify" if understood.intention == QueryIntention.VERIFY else "answer"
                )
                propositions = (_unresolved_proposition(query),)
                surface_tokens = tuple(
                    _tokenize(
                        "Nie mam wystarczającego, zweryfikowanego źródła, aby odpowiedzieć."
                    )
                )
                epistemic_status = "unresolved_source_required"
                selected = ()
        elif understood.intention == QueryIntention.GENERATE_TEXT:
            discourse_act = "generate"
            requested = _proposition_from_native_request(source_native_semantics)
            propositions = (requested,)
            surface_tokens = _surface_seed_from_native_request(source_native_semantics)
            selected = ()
            epistemic_status = "requested_content"
        elif understood.intention == QueryIntention.COMMAND:
            discourse_act = "boundary"
            propositions = (_command_boundary_proposition(query),)
            surface_tokens = tuple(
                _tokenize(
                    "Nie wykonuję tej akcji w warstwie generowania tekstu; mogę przygotować zweryfikowany plan."
                )
            )
            selected = ()
            epistemic_status = "execution_not_granted"
        else:
            discourse_act = "clarify"
            propositions = (_clarification_proposition(query),)
            surface_tokens = tuple(
                _tokenize("Potrzebuję doprecyzowania oczekiwanej odpowiedzi.")
            )
            selected = ()
            epistemic_status = "clarification_required"

        response_equation = _response_equation(discourse_act, propositions)
        response_equation_sha = canonical_sha256(response_equation)
        semantic_knot = {
            "schema": "CIEL_RESPONSE_SEMANTIC_KNOT_V1",
            "discourse_act": discourse_act,
            "proposition_ids": [item.proposition_id for item in propositions],
            "predicates": [item.predicate for item in propositions],
            "evidence_ids": [item.evidence_id for item in selected],
            "source_query_sha256": canonical_sha256({"text": query}),
        }
        invariant = {
            "schema": "CIEL_RESPONSE_INVARIANT_V1",
            "discourse_act": discourse_act,
            "response_equation_sha256": response_equation_sha,
            "proposition_binding_sha256": canonical_sha256(
                [item.to_dict() for item in propositions]
            ),
            "epistemic_status": epistemic_status,
            "target_language": target_language,
            "style": style,
        }
        meaning_state = {
            "polarity": "positive",
            "tam_e": {
                "tense": "Present",
                "aspect": "Imperfective",
                "mood": "Indicative",
                "modality": (
                    "Epistemic" if epistemic_status.startswith("unresolved") else None
                ),
                "evidentiality": (
                    "MemoryReceipt" if selected else "Unknown"
                ),
            },
            "deictic_anchors": [],
            "scope": {"scope_status": "resolved", "discourse_act": discourse_act},
            "epistemic_status": epistemic_status,
        }
        query_sha = canonical_sha256({"text": query})
        plan_id = "response_plan_" + canonical_sha256(
            {
                "query": query_sha,
                "native": source_binding,
                "memory": memory_hash,
                "equation": response_equation_sha,
            }
        )[:20]
        claim_boundary = {
            "planner_kind": "bounded_native_semantic_planner",
            "language_backend_may_choose_meaning": False,
            "factual_content_requires_selected_evidence": True,
            "canon_allowed": False,
            "source_promotion_allowed": False,
            "runtime_execution_allowed": False,
            "memory_write_allowed": False,
            "code_update_allowed": False,
        }
        provisional = ResponseSemanticPlan(
            plan_id=plan_id,
            source_query=query,
            source_query_sha256=query_sha,
            source_native_binding_sha256=source_binding,
            source_sentence_equation_sha256=source_equation_sha,
            memory_read_set_sha256=memory_hash,
            intention=understood.intention.value,
            discourse_act=discourse_act,
            propositions=propositions,
            response_equation=response_equation,
            semantic_knot=semantic_knot,
            invariant=invariant,
            meaning_state=meaning_state,
            surface_seed_tokens=tuple(surface_tokens),
            selected_evidence=tuple(selected),
            claim_boundary=claim_boundary,
            plan_sha256="",
        )
        plan = ResponseSemanticPlan(
            **{
                **provisional.__dict__,
                "plan_sha256": canonical_sha256(provisional.to_binding_dict()),
            }
        )
        plan.validate()
        return plan


@dataclass(frozen=True)
class NativeResponseSemanticPlannerEndpoint:
    """Receipted AUX endpoint for response-semantic planning."""

    planner: NativeResponseSemanticPlanner = NativeResponseSemanticPlanner()

    def handle(self, request: Mapping[str, Any]) -> dict[str, Any]:
        try:
            return self._handle_ack(request)
        except (KeyError, TypeError, ResponsePlanningError, ValueError) as exc:
            return {
                "schema": RESPONSE_PLAN_RESULT_SCHEMA,
                "status": "NACK",
                "request_sha256": request.get("request_sha256"),
                "detail": str(exc),
            }

    def _handle_ack(self, request: Mapping[str, Any]) -> dict[str, Any]:
        if request.get("schema") != RESPONSE_PLAN_REQUEST_SCHEMA:
            raise ResponsePlanningError("invalid response-plan request schema")
        if request.get("operation") != "cielingo.lingophysics.plan_response_semantics":
            raise ResponsePlanningError("unsupported response-plan operation")
        nonce = str(request.get("nonce", ""))
        if not nonce:
            raise ResponsePlanningError("response-plan nonce is required")
        request_sha = str(request.get("request_sha256", ""))
        request_body = {
            key: value for key, value in request.items() if key != "request_sha256"
        }
        if request_sha != canonical_sha256(request_body):
            raise ResponsePlanningError("response-plan request hash mismatch")

        source_native = _mapping(
            request.get("source_native_semantics"), "source_native_semantics"
        )
        memory_context = _mapping(request.get("memory_context"), "memory_context")
        query = str(request.get("query", ""))
        if not query.strip():
            raise ResponsePlanningError("response-plan query is required")
        target_language = str(request.get("target_language", "pl"))
        style = str(request.get("style", "plain"))

        plan = self.planner.plan(
            query=query,
            source_native_semantics=source_native,
            memory_context=memory_context,
            target_language=target_language,
            style=style,
        )
        receipt_body = {
            "schema": RESPONSE_PLAN_RECEIPT_SCHEMA,
            "transport": "native_endpoint",
            "external_ack": False,
            "nonce": nonce,
            "request_sha256": request_sha,
            "response_plan_sha256": plan.plan_sha256,
            "source_native_binding_sha256": plan.source_native_binding_sha256,
            "memory_read_set_sha256": plan.memory_read_set_sha256,
            "planner_source_commit": self.planner.source_commit,
            "canon_allowed": False,
            "source_promotion_allowed": False,
            "runtime_execution_allowed": False,
            "memory_write_allowed": False,
            "code_update_allowed": False,
        }
        return {
            "schema": RESPONSE_PLAN_RESULT_SCHEMA,
            "status": "ACK",
            "request_sha256": request_sha,
            "response_plan": plan.to_dict(),
            "response_plan_sha256": plan.plan_sha256,
            "receipt": {
                **receipt_body,
                "receipt_sha256": canonical_sha256(receipt_body),
            },
        }


def parse_response_semantic_plan(payload: Mapping[str, Any]) -> ResponseSemanticPlan:
    if payload.get("schema") != RESPONSE_PLAN_SCHEMA:
        raise ResponsePlanningError("invalid response semantic plan schema")
    propositions = tuple(
        SemanticProposition(
            proposition_id=str(item["proposition_id"]),
            predicate=str(item["predicate"]),
            roles={str(k): str(v) for k, v in dict(item.get("roles", {})).items()},
            polarity=str(item.get("polarity", "positive")),
            tam_e=dict(item.get("tam_e", {})),
            modality=str(item.get("modality", "assertive")),
            confidence=float(item.get("confidence", 0.0)),
            evidence_ids=tuple(str(value) for value in item.get("evidence_ids", ())),
            source_kind=str(item.get("source_kind", "dialogue_control")),
        )
        for item in payload.get("propositions", ())
    )
    evidence = tuple(
        SemanticEvidence(
            evidence_id=str(item["evidence_id"]),
            lane_id=int(item["lane_id"]),
            subject=str(item["subject"]),
            predicate=str(item["predicate"]),
            object_value=str(item.get("object", "")),
            confidence=float(item["confidence"]),
            status=str(item["status"]),
            source_receipt_sha256=str(item["source_receipt_sha256"]),
            surface_text=(
                None if item.get("surface_text") is None else str(item["surface_text"])
            ),
        )
        for item in payload.get("selected_evidence", ())
    )
    plan = ResponseSemanticPlan(
        plan_id=str(payload["plan_id"]),
        source_query=str(payload["source_query"]),
        source_query_sha256=str(payload["source_query_sha256"]),
        source_native_binding_sha256=str(payload["source_native_binding_sha256"]),
        source_sentence_equation_sha256=str(
            payload["source_sentence_equation_sha256"]
        ),
        memory_read_set_sha256=str(payload["memory_read_set_sha256"]),
        intention=str(payload["intention"]),
        discourse_act=str(payload["discourse_act"]),
        propositions=propositions,
        response_equation=dict(payload.get("response_equation", {})),
        semantic_knot=dict(payload.get("semantic_knot", {})),
        invariant=dict(payload.get("invariant", {})),
        meaning_state=dict(payload.get("meaning_state", {})),
        surface_seed_tokens=tuple(
            str(value) for value in payload.get("surface_seed_tokens", ())
        ),
        selected_evidence=evidence,
        claim_boundary=dict(payload.get("claim_boundary", {})),
        plan_sha256=str(payload["plan_sha256"]),
    )
    plan.validate()
    return plan


def _parse_evidence(values: Any) -> tuple[SemanticEvidence, ...]:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        raise ResponsePlanningError("memory evidence must be an array")
    out: list[SemanticEvidence] = []
    for raw in values:
        if not isinstance(raw, Mapping):
            raise ResponsePlanningError("memory evidence entry must be an object")
        item = SemanticEvidence(
            evidence_id=str(raw["evidence_id"]),
            lane_id=int(raw["lane_id"]),
            subject=str(raw["subject"]),
            predicate=str(raw["predicate"]),
            object_value=str(raw.get("object", "")),
            confidence=float(raw["confidence"]),
            status=str(raw["status"]),
            source_receipt_sha256=str(raw["source_receipt_sha256"]),
            surface_text=(
                None if raw.get("surface_text") is None else str(raw["surface_text"])
            ),
        )
        item.validate()
        out.append(item)
    return tuple(out)


def _select_relevant_evidence(
    query: str, evidence: Sequence[SemanticEvidence]
) -> tuple[SemanticEvidence, ...]:
    query_terms = {
        token.casefold()
        for token in _tokenize(query)
        if token.isalnum() and len(token) > 2
    }
    scored: list[tuple[float, SemanticEvidence]] = []
    for item in evidence:
        item_terms = {
            token.casefold()
            for token in _tokenize(
                " ".join((item.subject, item.predicate, item.object_value))
            )
            if token.isalnum() and len(token) > 2
        }
        overlap = len(query_terms & item_terms)
        score = float(item.confidence) + 0.15 * overlap
        if overlap or not query_terms:
            scored.append((score, item))
    scored.sort(key=lambda pair: (-pair[0], pair[1].lane_id, pair[1].evidence_id))
    return tuple(item for _, item in scored[:3] if item.confidence >= 0.50)


def _proposition_from_evidence(item: SemanticEvidence) -> SemanticProposition:
    body = {
        "predicate": item.predicate,
        "roles": {"subject": item.subject, "object": item.object_value},
        "evidence": item.evidence_id,
    }
    return SemanticProposition(
        proposition_id="prop_" + canonical_sha256(body)[:20],
        predicate=item.predicate,
        roles={"subject": item.subject, "object": item.object_value},
        polarity="positive",
        tam_e={
            "tense": "Present",
            "aspect": "Imperfective",
            "mood": "Indicative",
            "evidentiality": "MemoryReceipt",
        },
        modality="assertive" if item.status in {"verified", "accepted"} else "epistemic",
        confidence=item.confidence,
        evidence_ids=(item.evidence_id,),
        source_kind="memory_evidence",
    )


def _unresolved_proposition(query: str) -> SemanticProposition:
    body = {"predicate": "knowledge_status", "query": query, "status": "unresolved"}
    return SemanticProposition(
        proposition_id="prop_" + canonical_sha256(body)[:20],
        predicate="knowledge_status",
        roles={"query": query, "status": "unresolved_source_required"},
        polarity="positive",
        tam_e={
            "tense": "Present",
            "aspect": "Imperfective",
            "mood": "Indicative",
            "evidentiality": "Unknown",
        },
        modality="epistemic",
        confidence=1.0,
        evidence_ids=(),
        source_kind="epistemic_boundary",
    )


def _command_boundary_proposition(query: str) -> SemanticProposition:
    body = {"predicate": "execution_boundary", "query": query}
    return SemanticProposition(
        proposition_id="prop_" + canonical_sha256(body)[:20],
        predicate="execution_boundary",
        roles={"requested_action": query, "status": "not_executed"},
        polarity="negative",
        tam_e={
            "tense": "Present",
            "aspect": "Imperfective",
            "mood": "Indicative",
            "evidentiality": "SystemPolicy",
        },
        modality="deontic",
        confidence=1.0,
        evidence_ids=(),
        source_kind="dialogue_control",
    )


def _clarification_proposition(query: str) -> SemanticProposition:
    body = {"predicate": "clarification_required", "query": query}
    return SemanticProposition(
        proposition_id="prop_" + canonical_sha256(body)[:20],
        predicate="clarification_required",
        roles={"query": query, "missing": "response_intent"},
        polarity="positive",
        tam_e={
            "tense": "Present",
            "aspect": "Imperfective",
            "mood": "Indicative",
            "evidentiality": "SystemState",
        },
        modality="interrogative",
        confidence=1.0,
        evidence_ids=(),
        source_kind="dialogue_control",
    )


def _proposition_from_native_request(
    source_native_semantics: Mapping[str, Any]
) -> SemanticProposition:
    lingophysics = _mapping(
        source_native_semantics.get("lingophysics"), "source lingophysics"
    )
    invariant = _mapping(lingophysics.get("invariant"), "source invariant")
    predicate = str(invariant.get("predicate", invariant.get("operator", ""))).strip()
    roles = {
        str(key): str(value)
        for key, value in invariant.items()
        if str(key).casefold()
        not in {
            "predicate",
            "operator",
            "polarity",
            "tam_e",
            "tame",
            "deictic_anchors",
            "scope",
        }
        and isinstance(value, (str, int, float))
        and str(value)
    }
    if not predicate or not roles:
        raise ResponsePlanningError(
            "generate_text requires a native predicate and role structure"
        )
    body = {"predicate": predicate, "roles": roles, "source": "native_request"}
    meaning_state = lingophysics.get("meaning_state", {})
    if not isinstance(meaning_state, Mapping):
        meaning_state = {}
    return SemanticProposition(
        proposition_id="prop_" + canonical_sha256(body)[:20],
        predicate=predicate,
        roles=roles,
        polarity=str(meaning_state.get("polarity", invariant.get("polarity", "positive"))),
        tam_e=dict(meaning_state.get("tam_e", meaning_state.get("tame", {}))),
        modality="requested_generation",
        confidence=1.0,
        evidence_ids=(),
        source_kind="native_request_content",
    )


def _surface_seed_from_native_request(
    source_native_semantics: Mapping[str, Any]
) -> tuple[str, ...]:
    cielingo = _mapping(source_native_semantics.get("cielingo"), "source cielingo")
    tokens = tuple(str(token) for token in cielingo.get("tokens", ()))
    projection = cielingo.get("slot_projection", {})
    if not isinstance(projection, Mapping):
        projection = {}
    ordered: list[str] = []
    used: set[int] = set()
    for slot in ("agent", "action", "predicate", "patient", "theme", "object"):
        indices = projection.get(slot, ())
        if isinstance(indices, int):
            indices = (indices,)
        if isinstance(indices, Sequence) and not isinstance(indices, (str, bytes)):
            for raw_index in indices:
                index = int(raw_index)
                if 0 <= index < len(tokens) and index not in used:
                    ordered.append(tokens[index])
                    used.add(index)
    if not ordered:
        raise ResponsePlanningError(
            "generate_text requires role-bound CIELingo surface tokens"
        )
    return tuple(ordered)


def _tokens_from_evidence(item: SemanticEvidence) -> tuple[str, ...]:
    if item.surface_text and item.surface_text.strip():
        return tuple(_tokenize(item.surface_text))
    text = " ".join(
        value for value in (item.subject, item.predicate, item.object_value) if value
    )
    return tuple(_tokenize(text + "."))


def _response_equation(
    discourse_act: str, propositions: Sequence[SemanticProposition]
) -> dict[str, Any]:
    operator = {
        "answer": "ANSWER",
        "verify": "VERIFY",
        "generate": "GENERATE",
        "boundary": "BOUNDARY",
        "clarify": "CLARIFY",
    }[discourse_act]
    arguments = [item.proposition_id for item in propositions]
    return {
        "schema": "CIEL_RESPONSE_EQUATION_V1",
        "operator": operator,
        "arguments": arguments,
        "expression": f"{operator}({','.join(arguments)})",
    }


def _tokenize(text: str) -> list[str]:
    return [token for token in _TOKEN_RE.findall(text.strip()) if token.strip()]


def _mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ResponsePlanningError(f"{name} must be an object")
    return value


__all__ = [
    "NativeResponseSemanticPlanner",
    "NativeResponseSemanticPlannerEndpoint",
    "RESPONSE_PLAN_RECEIPT_SCHEMA",
    "RESPONSE_PLAN_REQUEST_SCHEMA",
    "RESPONSE_PLAN_RESULT_SCHEMA",
    "RESPONSE_PLAN_SCHEMA",
    "ResponsePlanningError",
    "ResponseSemanticPlan",
    "SemanticEvidence",
    "SemanticProposition",
    "parse_response_semantic_plan",
]
