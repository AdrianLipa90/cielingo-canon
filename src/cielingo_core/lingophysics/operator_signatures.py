"""Operator-specific CasePort signatures for CIELingo Lingophysics.

The key invariant is that grammatical case and semantic role are independent
axes. A signature validates an operator-local port such as
``INS:counterpart_in_relation``; it never infers a universal semantic role from
``INS`` alone.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Any

from cielingo_core.global_layer.contracts import UniversalRole
from .case_port_frame import CasePort, CasePortCase, CasePortFrame


@dataclass(frozen=True)
class OperatorPortSpec:
    grammatical_case: CasePortCase
    operator_role: str
    required: bool = True
    allowed_adpositions: tuple[str, ...] = ()
    universal_role: UniversalRole | None = None
    normalization_basis: str | None = None

    @property
    def port_key(self) -> str:
        return f"{self.grammatical_case.value}:{self.operator_role}"

    def matches(self, port: CasePort) -> bool:
        if port.grammatical_case is not self.grammatical_case:
            return False
        if port.operator_role != self.operator_role:
            return False
        if self.allowed_adpositions and (port.adposition or "") not in self.allowed_adpositions:
            return False
        return True

    def to_dict(self) -> dict[str, Any]:
        out = asdict(self)
        out["grammatical_case"] = self.grammatical_case.value
        out["allowed_adpositions"] = list(self.allowed_adpositions)
        out["universal_role"] = self.universal_role.value if self.universal_role else None
        return out


@dataclass(frozen=True)
class OperatorSignature:
    operator: str
    ports: tuple[OperatorPortSpec, ...]
    relation_family: str
    directional: bool
    symmetric: bool = False
    candidate_only: bool = True
    version: str = "0.1.0"

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.operator:
            issues.append("operator is required")
        if not self.ports:
            issues.append("operator signature must contain ports")
        keys = [port.port_key for port in self.ports]
        if len(set(keys)) != len(keys):
            issues.append("operator signature contains duplicate port keys")
        if self.directional and self.symmetric:
            issues.append("operator signature cannot be both directional and symmetric")
        if not self.candidate_only:
            issues.append("operator signature v0.1 must remain candidate-only")
        return issues

    @property
    def signature_id(self) -> str:
        return f"{self.operator}@{self.version}"

    @property
    def signature_commitment(self) -> str:
        payload = {
            "operator": self.operator,
            "ports": [port.to_dict() for port in self.ports],
            "relation_family": self.relation_family,
            "directional": self.directional,
            "symmetric": self.symmetric,
            "candidate_only": self.candidate_only,
            "version": self.version,
        }
        return sha256(
            json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "CIEL_OPERATOR_SIGNATURE_V0_1",
            "signature_id": self.signature_id,
            "operator": self.operator,
            "ports": [port.to_dict() for port in self.ports],
            "relation_family": self.relation_family,
            "directional": self.directional,
            "symmetric": self.symmetric,
            "candidate_only": self.candidate_only,
            "version": self.version,
            "signature_commitment": self.signature_commitment,
        }


@dataclass(frozen=True)
class UniversalRoleBinding:
    universal_role: UniversalRole
    operator: str
    operator_role: str
    grammatical_case: CasePortCase
    entity: str
    token_indices: tuple[int, ...]
    normalization_basis: str
    confidence: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "universal_role": self.universal_role.value,
            "operator": self.operator,
            "operator_role": self.operator_role,
            "grammatical_case": self.grammatical_case.value,
            "entity": self.entity,
            "token_indices": list(self.token_indices),
            "normalization_basis": self.normalization_basis,
            "confidence": self.confidence,
        }


@dataclass(frozen=True)
class OperatorTypingReport:
    frame_id: str
    operator: str
    signature_id: str | None
    signature_known: bool
    valid: bool
    missing_ports: tuple[str, ...]
    unexpected_ports: tuple[str, ...]
    adposition_mismatches: tuple[str, ...]
    universal_roles: tuple[UniversalRoleBinding, ...]
    candidate_only: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "CIEL_OPERATOR_TYPING_REPORT_V0_1",
            "frame_id": self.frame_id,
            "operator": self.operator,
            "signature_id": self.signature_id,
            "signature_known": self.signature_known,
            "valid": self.valid,
            "missing_ports": list(self.missing_ports),
            "unexpected_ports": list(self.unexpected_ports),
            "adposition_mismatches": list(self.adposition_mismatches),
            "universal_roles": [binding.to_dict() for binding in self.universal_roles],
            "candidate_only": self.candidate_only,
        }


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


OPERATOR_SIGNATURES: dict[str, OperatorSignature] = {
    "CONNECTED_WITH": OperatorSignature(
        operator="CONNECTED_WITH",
        relation_family="symmetric_association",
        directional=False,
        symmetric=True,
        ports=(
            _p(CasePortCase.NOM, "entity"),
            _p(CasePortCase.INS, "counterpart_in_relation", adpositions=("z",)),
        ),
    ),
    "BELONGS_TO": OperatorSignature(
        operator="BELONGS_TO",
        relation_family="membership",
        directional=True,
        ports=(
            _p(CasePortCase.NOM, "member_or_part", universal_role=UniversalRole.THEME, normalization_basis="OPERATOR_ROLE_MEMBER_AS_THEME"),
            _p(CasePortCase.GEN, "container_or_owner", adpositions=("do",)),
        ),
    ),
    "SPEAKS_ABOUT": OperatorSignature(
        operator="SPEAKS_ABOUT",
        relation_family="communication",
        directional=True,
        ports=(
            _p(CasePortCase.NOM, "speaker", universal_role=UniversalRole.AGENT, normalization_basis="OPERATOR_ROLE_SPEAKER_AS_AGENT"),
            _p(CasePortCase.LOC, "topic", adpositions=("o",), universal_role=UniversalRole.THEME, normalization_basis="OPERATOR_ROLE_TOPIC_AS_THEME"),
            _p(CasePortCase.INS, "interlocutor", adpositions=("z",)),
        ),
    ),
    "NAMES": OperatorSignature(
        operator="NAMES",
        relation_family="designation",
        directional=True,
        ports=(
            _p(CasePortCase.NOM, "namer", universal_role=UniversalRole.AGENT, normalization_basis="OPERATOR_ROLE_NAMER_AS_AGENT"),
            _p(CasePortCase.ACC, "entity_named", universal_role=UniversalRole.THEME, normalization_basis="OPERATOR_ROLE_ENTITY_NAMED_AS_THEME"),
            _p(CasePortCase.INS, "assigned_name"),
        ),
    ),
    "GIVES": OperatorSignature(
        operator="GIVES",
        relation_family="transfer",
        directional=True,
        ports=(
            _p(CasePortCase.NOM, "giver", universal_role=UniversalRole.AGENT, normalization_basis="OPERATOR_ROLE_GIVER_AS_AGENT"),
            _p(CasePortCase.DAT, "recipient", universal_role=UniversalRole.RECIPIENT, normalization_basis="OPERATOR_ROLE_RECIPIENT_AS_RECIPIENT"),
            _p(CasePortCase.ACC, "transferred_object", universal_role=UniversalRole.THEME, normalization_basis="OPERATOR_ROLE_TRANSFERRED_OBJECT_AS_THEME"),
        ),
    ),
    "DESCRIBES": OperatorSignature(
        operator="DESCRIBES",
        relation_family="description",
        directional=True,
        ports=(
            _p(CasePortCase.NOM, "describer", universal_role=UniversalRole.AGENT, normalization_basis="OPERATOR_ROLE_DESCRIBER_AS_AGENT"),
            _p(CasePortCase.ACC, "described_object", universal_role=UniversalRole.THEME, normalization_basis="OPERATOR_ROLE_DESCRIBED_OBJECT_AS_THEME"),
            _p(CasePortCase.LOC, "topic_or_context", adpositions=("o",)),
        ),
    ),
    "ADDRESSES": OperatorSignature(
        operator="ADDRESSES",
        relation_family="address",
        directional=True,
        ports=(
            _p(CasePortCase.VOC, "addressee", universal_role=UniversalRole.RECIPIENT, normalization_basis="OPERATOR_ROLE_ADDRESSEE_AS_RECIPIENT"),
        ),
    ),
}


for _signature in OPERATOR_SIGNATURES.values():
    _issues = _signature.validate()
    if _issues:
        raise RuntimeError(f"invalid operator signature {_signature.operator}: {'; '.join(_issues)}")


def get_operator_signature(operator: str) -> OperatorSignature | None:
    return OPERATOR_SIGNATURES.get(str(operator).upper())


def type_case_port_frame(frame: CasePortFrame) -> OperatorTypingReport:
    """Validate one CasePortFrame against its operator-local typed signature."""
    signature = get_operator_signature(frame.operator)
    if signature is None:
        return OperatorTypingReport(
            frame_id=frame.frame_id,
            operator=frame.operator,
            signature_id=None,
            signature_known=False,
            valid=False,
            missing_ports=(),
            unexpected_ports=tuple(
                f"{port.grammatical_case.value}:{port.operator_role}" for port in frame.ports
            ),
            adposition_mismatches=(),
            universal_roles=(),
        )

    specs_by_key = {spec.port_key: spec for spec in signature.ports}
    frame_by_key = {
        f"{port.grammatical_case.value}:{port.operator_role}": port for port in frame.ports
    }
    missing = tuple(
        spec.port_key
        for spec in signature.ports
        if spec.required and spec.port_key not in frame_by_key
    )
    unexpected = tuple(key for key in frame_by_key if key not in specs_by_key)
    adposition_mismatches: list[str] = []
    bindings: list[UniversalRoleBinding] = []

    for key, port in frame_by_key.items():
        spec = specs_by_key.get(key)
        if spec is None:
            continue
        if spec.allowed_adpositions and (port.adposition or "") not in spec.allowed_adpositions:
            adposition_mismatches.append(
                f"{key}:expected={','.join(spec.allowed_adpositions)}:observed={port.adposition or 'NONE'}"
            )
            continue
        if spec.universal_role is not None and spec.normalization_basis:
            bindings.append(
                UniversalRoleBinding(
                    universal_role=spec.universal_role,
                    operator=frame.operator,
                    operator_role=port.operator_role,
                    grammatical_case=port.grammatical_case,
                    entity=port.entity,
                    token_indices=port.token_indices,
                    normalization_basis=spec.normalization_basis,
                    confidence=min(float(frame.confidence), float(port.confidence)),
                )
            )

    valid = not missing and not unexpected and not adposition_mismatches
    if not valid:
        bindings = []

    return OperatorTypingReport(
        frame_id=frame.frame_id,
        operator=frame.operator,
        signature_id=signature.signature_id,
        signature_known=True,
        valid=valid,
        missing_ports=missing,
        unexpected_ports=unexpected,
        adposition_mismatches=tuple(adposition_mismatches),
        universal_roles=tuple(bindings),
    )


def type_polish_case_port_frames(text: str, tokens: list[str] | None = None) -> tuple[OperatorTypingReport, ...]:
    from .case_port_frame import extract_polish_case_port_frames

    return tuple(
        type_case_port_frame(frame)
        for frame in extract_polish_case_port_frames(text, tokens=tokens)
    )


__all__ = [
    "OPERATOR_SIGNATURES",
    "OperatorPortSpec",
    "OperatorSignature",
    "OperatorTypingReport",
    "UniversalRoleBinding",
    "get_operator_signature",
    "type_case_port_frame",
    "type_polish_case_port_frames",
]
