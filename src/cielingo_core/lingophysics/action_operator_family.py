"""Bounded agent-action relation family for CIELingo Lingophysics.

This extension types only simple, affirmative, single-action Polish surfaces.
Negated, conditional and multi-action surfaces remain outside this increment so
that action typing cannot silently become execution authority without a scope
contract.
"""
from __future__ import annotations

from hashlib import sha256
import json
import re
from typing import Iterable

from cielingo_core.global_layer.contracts import UniversalRole
from .case_port_frame import CasePort, CasePortCase, CasePortFrame
from .operator_signatures import OperatorPortSpec, OperatorSignature


ACTION_OPERATOR_FAMILY_VERSION = "0.2.0"
ACTION_SCOPE_BASIS = "AFFIRMATIVE_SINGLE_ACTION_BOUNDED_PATTERN"

_SCOPE_BLOCKERS = frozenset({
    "nie", "jeśli", "jeżeli", "tylko", "dopóki", "dopiero", "chyba",
})
_ACTION_ANCHORS = frozenset({
    "wyślij", "zarchiwizuj", "usuń", "zachowaj", "zmień", "zatwierdź",
    "utwórz", "stwórz",
})
_DOCUMENT_FORMS = frozenset({
    "raport", "dokument", "umowa", "umowę", "memo", "kontrakt",
})
_PUNCT = ".,?!:;\"'()[]{}"
_TOKEN_RE = re.compile(r"\s+")


def _clean(token: str) -> str:
    return token.strip(_PUNCT)


def _low(tokens: Iterable[str]) -> list[str]:
    return [_clean(token).casefold() for token in tokens]


def _port(
    case: CasePortCase,
    role: str,
    entity: str,
    token_indices: tuple[int, ...],
    *,
    surface_form: str | None = None,
    adposition: str | None = None,
    basis: str = ACTION_SCOPE_BASIS,
    confidence: float = 0.86,
) -> CasePort:
    return CasePort(
        grammatical_case=case,
        operator_role=role,
        entity=entity,
        token_indices=token_indices,
        surface_form=surface_form if surface_form is not None else entity,
        adposition=adposition,
        basis=basis,
        confidence=confidence,
    )


def _frame(
    operator: str,
    ports: list[CasePort],
    text: str,
    *,
    evidence_basis: str,
) -> CasePortFrame:
    packed = tuple(ports)
    payload = {
        "operator": operator,
        "ports": [port.to_dict() for port in packed],
        "surface_text": text,
    }
    digest = sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()[:20]
    frame = CasePortFrame(
        frame_id=f"caseframe_{operator.lower()}_{digest}",
        language_id="pl",
        operator=operator,
        ports=packed,
        surface_text=text,
        evidence_basis=evidence_basis,
        direction_status="EXPLICIT_WITH_IMPLICIT_SUBJECT",
        candidate_only=True,
        confidence=min((port.confidence for port in packed), default=0.0),
    )
    issues = frame.validate()
    if issues:
        raise ValueError("; ".join(issues))
    return frame


def _implicit_actor(role: str, verb: str) -> CasePort:
    return _port(
        CasePortCase.NOM,
        role,
        "ja",
        (),
        surface_form=verb,
        basis="IMPLICIT_PERSON_FROM_IMPERATIVE",
        confidence=0.86,
    )


def _scope_safe(low: list[str]) -> bool:
    if any(token in _SCOPE_BLOCKERS for token in low):
        return False
    action_count = sum(1 for token in low if token in _ACTION_ANCHORS)
    return action_count == 1


def extract_polish_action_case_port_frames(
    text: str,
    tokens: list[str] | None = None,
) -> list[CasePortFrame]:
    """Extract simple affirmative single-action candidates only."""
    tokens = list(tokens) if tokens is not None else [
        token for token in _TOKEN_RE.split(text.strip()) if token
    ]
    low = _low(tokens)
    if not low or not _scope_safe(low):
        return []

    frames: list[CasePortFrame] = []

    # Wyślij dokument odbiorcy / Wyślij odbiorcy dokument.
    if low[0] == "wyślij" and len(tokens) == 3:
        first, second = low[1], low[2]
        if first in _DOCUMENT_FORMS and second not in _DOCUMENT_FORMS:
            doc_index, recipient_index = 1, 2
        elif second in _DOCUMENT_FORMS and first not in _DOCUMENT_FORMS:
            recipient_index, doc_index = 1, 2
        else:
            doc_index = recipient_index = -1
        if doc_index >= 0:
            frames.append(_frame(
                "SEND_EMAIL",
                [
                    _implicit_actor("sender", tokens[0]),
                    _port(CasePortCase.ACC, "document", _clean(tokens[doc_index]), (doc_index,), confidence=0.84),
                    _port(CasePortCase.DAT, "recipient", _clean(tokens[recipient_index]), (recipient_index,), basis="BOUNDED_ARGUMENT_ORDER_CANDIDATE", confidence=0.80),
                ],
                text,
                evidence_basis="BOUNDED_SEND_DOCUMENT_RECIPIENT_PATTERN",
            ))

    # Zarchiwizuj <file/object span>.
    if low[0] == "zarchiwizuj" and len(tokens) >= 2:
        indices = tuple(range(1, len(tokens)))
        label = " ".join(_clean(tokens[index]) for index in indices)
        frames.append(_frame(
            "ARCHIVES",
            [
                _implicit_actor("actor", tokens[0]),
                _port(CasePortCase.ACC, "file_or_object", label, indices, confidence=0.84),
            ],
            text,
            evidence_basis="BOUNDED_ARCHIVE_IMPERATIVE_PATTERN",
        ))

    # Usuń <single explicit target>. Complex descriptions remain unresolved.
    if low[0] == "usuń" and len(tokens) == 2:
        frames.append(_frame(
            "DELETES",
            [
                _implicit_actor("actor", tokens[0]),
                _port(CasePortCase.ACC, "file_or_object", _clean(tokens[1]), (1,), confidence=0.84),
            ],
            text,
            evidence_basis="BOUNDED_DELETE_IMPERATIVE_PATTERN",
        ))

    # Zmień status rekordu 44 na approved.
    if (
        len(tokens) == 6
        and low[0] == "zmień"
        and low[1] == "status"
        and low[2] == "rekordu"
        and low[4] == "na"
    ):
        frames.append(_frame(
            "UPDATES_RECORD",
            [
                _implicit_actor("actor", tokens[0]),
                _port(CasePortCase.GEN, "record", _clean(tokens[3]), (3,), basis="EXPLICIT_REKORDU_IDENTIFIER_PATTERN", confidence=0.86),
                _port(CasePortCase.ACC, "field", _clean(tokens[1]), (1,), confidence=0.86),
                _port(CasePortCase.ACC, "value", _clean(tokens[5]), (5,), adposition="na", confidence=0.84),
            ],
            text,
            evidence_basis="BOUNDED_UPDATE_RECORD_FIELD_VALUE_PATTERN",
        ))

    # Zatwierdź <supplier/entity>.
    if low[0] == "zatwierdź" and len(tokens) == 2:
        frames.append(_frame(
            "APPROVES_SUPPLIER",
            [
                _implicit_actor("approver", tokens[0]),
                _port(CasePortCase.ACC, "supplier", _clean(tokens[1]), (1,), confidence=0.82),
            ],
            text,
            evidence_basis="BOUNDED_APPROVE_ENTITY_PATTERN",
        ))

    # Utwórz kontrakt z <counterpart>.
    if (
        len(tokens) == 4
        and low[0] in {"utwórz", "stwórz"}
        and low[1] == "kontrakt"
        and low[2] == "z"
    ):
        frames.append(_frame(
            "CREATES_CONTRACT_WITH",
            [
                _implicit_actor("creator", tokens[0]),
                _port(CasePortCase.ACC, "contract", _clean(tokens[1]), (1,), confidence=0.84),
                _port(CasePortCase.INS, "counterpart", _clean(tokens[3]), (3,), adposition="z", confidence=0.82),
            ],
            text,
            evidence_basis="BOUNDED_CREATE_CONTRACT_WITH_PATTERN",
        ))

    return frames


def _p(
    case: CasePortCase,
    role: str,
    *,
    adpositions: tuple[str, ...] = (),
    universal_role: UniversalRole | None = None,
    normalization_basis: str | None = None,
) -> OperatorPortSpec:
    return OperatorPortSpec(
        grammatical_case=case,
        operator_role=role,
        allowed_adpositions=adpositions,
        universal_role=universal_role,
        normalization_basis=normalization_basis,
    )


ACTION_OPERATOR_SIGNATURES: dict[str, OperatorSignature] = {
    "SEND_EMAIL": OperatorSignature(
        operator="SEND_EMAIL",
        relation_family="communication_action",
        directional=True,
        version=ACTION_OPERATOR_FAMILY_VERSION,
        ports=(
            _p(CasePortCase.NOM, "sender", universal_role=UniversalRole.AGENT, normalization_basis="OPERATOR_ROLE_SENDER_AS_AGENT"),
            _p(CasePortCase.ACC, "document", universal_role=UniversalRole.THEME, normalization_basis="OPERATOR_ROLE_DOCUMENT_AS_THEME"),
            _p(CasePortCase.DAT, "recipient", universal_role=UniversalRole.RECIPIENT, normalization_basis="OPERATOR_ROLE_RECIPIENT_AS_RECIPIENT"),
        ),
    ),
    "ARCHIVES": OperatorSignature(
        operator="ARCHIVES",
        relation_family="state_change_action",
        directional=True,
        version=ACTION_OPERATOR_FAMILY_VERSION,
        ports=(
            _p(CasePortCase.NOM, "actor", universal_role=UniversalRole.AGENT, normalization_basis="OPERATOR_ROLE_ACTOR_AS_AGENT"),
            _p(CasePortCase.ACC, "file_or_object", universal_role=UniversalRole.THEME, normalization_basis="OPERATOR_ROLE_TARGET_AS_THEME"),
        ),
    ),
    "DELETES": OperatorSignature(
        operator="DELETES",
        relation_family="state_change_action",
        directional=True,
        version=ACTION_OPERATOR_FAMILY_VERSION,
        ports=(
            _p(CasePortCase.NOM, "actor", universal_role=UniversalRole.AGENT, normalization_basis="OPERATOR_ROLE_ACTOR_AS_AGENT"),
            _p(CasePortCase.ACC, "file_or_object", universal_role=UniversalRole.THEME, normalization_basis="OPERATOR_ROLE_TARGET_AS_THEME"),
        ),
    ),
    "UPDATES_RECORD": OperatorSignature(
        operator="UPDATES_RECORD",
        relation_family="record_mutation_action",
        directional=True,
        version=ACTION_OPERATOR_FAMILY_VERSION,
        ports=(
            _p(CasePortCase.NOM, "actor", universal_role=UniversalRole.AGENT, normalization_basis="OPERATOR_ROLE_ACTOR_AS_AGENT"),
            _p(CasePortCase.GEN, "record", universal_role=UniversalRole.THEME, normalization_basis="OPERATOR_ROLE_RECORD_AS_THEME"),
            _p(CasePortCase.ACC, "field"),
            _p(CasePortCase.ACC, "value", adpositions=("na",)),
        ),
    ),
    "APPROVES_SUPPLIER": OperatorSignature(
        operator="APPROVES_SUPPLIER",
        relation_family="approval_action",
        directional=True,
        version=ACTION_OPERATOR_FAMILY_VERSION,
        ports=(
            _p(CasePortCase.NOM, "approver", universal_role=UniversalRole.AGENT, normalization_basis="OPERATOR_ROLE_APPROVER_AS_AGENT"),
            _p(CasePortCase.ACC, "supplier", universal_role=UniversalRole.THEME, normalization_basis="OPERATOR_ROLE_SUPPLIER_AS_THEME"),
        ),
    ),
    "CREATES_CONTRACT_WITH": OperatorSignature(
        operator="CREATES_CONTRACT_WITH",
        relation_family="contract_creation_action",
        directional=True,
        version=ACTION_OPERATOR_FAMILY_VERSION,
        ports=(
            _p(CasePortCase.NOM, "creator", universal_role=UniversalRole.AGENT, normalization_basis="OPERATOR_ROLE_CREATOR_AS_AGENT"),
            _p(CasePortCase.ACC, "contract", universal_role=UniversalRole.THEME, normalization_basis="OPERATOR_ROLE_CONTRACT_AS_THEME"),
            _p(CasePortCase.INS, "counterpart", adpositions=("z",)),
        ),
    ),
}


def install_agent_action_operator_family(case_port_module, operator_signature_module) -> None:
    """Install the additive v0.2 action family into the existing typed pipeline."""
    if getattr(case_port_module, "_agent_action_family_v02_installed", False):
        return

    for operator, signature in ACTION_OPERATOR_SIGNATURES.items():
        issues = signature.validate()
        if issues:
            raise RuntimeError(f"invalid action signature {operator}: {'; '.join(issues)}")
        if operator in operator_signature_module.OPERATOR_SIGNATURES:
            raise RuntimeError(f"action operator collides with existing signature: {operator}")
        operator_signature_module.OPERATOR_SIGNATURES[operator] = signature

    base_extract = case_port_module.extract_polish_case_port_frames

    def combined_extract(text: str, tokens: list[str] | None = None) -> list[CasePortFrame]:
        base = list(base_extract(text, tokens=tokens))
        action = extract_polish_action_case_port_frames(text, tokens=tokens)
        seen = {frame.frame_id for frame in base}
        base.extend(frame for frame in action if frame.frame_id not in seen)
        return base

    case_port_module.extract_polish_case_port_frames = combined_extract
    case_port_module._agent_action_family_v02_installed = True


__all__ = [
    "ACTION_OPERATOR_FAMILY_VERSION",
    "ACTION_OPERATOR_SIGNATURES",
    "ACTION_SCOPE_BASIS",
    "extract_polish_action_case_port_frames",
    "install_agent_action_operator_family",
]
