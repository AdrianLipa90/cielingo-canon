"""Typed grammatical-case relation frames for CIELingo Lingophysics."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from hashlib import sha256
import json
import re
from typing import Any


class CasePortCase(str, Enum):
    NOM = "NOM"
    GEN = "GEN"
    DAT = "DAT"
    ACC = "ACC"
    INS = "INS"
    LOC = "LOC"
    VOC = "VOC"


@dataclass(frozen=True)
class CasePort:
    grammatical_case: CasePortCase
    operator_role: str
    entity: str
    token_indices: tuple[int, ...]
    surface_form: str
    adposition: str | None = None
    basis: str = "EXPLICIT_PATTERN"
    confidence: float = 0.80

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.operator_role:
            issues.append("operator_role is required")
        if not self.entity:
            issues.append("entity is required")
        if any(index < 0 for index in self.token_indices):
            issues.append("token_indices must be non-negative")
        if not 0.0 <= float(self.confidence) <= 1.0:
            issues.append("confidence must be in [0,1]")
        return issues

    def to_dict(self) -> dict[str, Any]:
        out = asdict(self)
        out["grammatical_case"] = self.grammatical_case.value
        out["token_indices"] = list(self.token_indices)
        return out


@dataclass(frozen=True)
class CasePortFrame:
    frame_id: str
    language_id: str
    operator: str
    ports: tuple[CasePort, ...]
    surface_text: str
    evidence_basis: str
    direction_status: str = "EXPLICIT"
    candidate_only: bool = True
    confidence: float = 0.80

    def validate(self) -> list[str]:
        issues: list[str] = []
        if self.language_id != "pl":
            issues.append("CasePortFrame v0.1 expects language_id=pl")
        if not self.frame_id:
            issues.append("frame_id is required")
        if not self.operator:
            issues.append("operator is required")
        if not self.ports:
            issues.append("ports must not be empty")
        for port in self.ports:
            issues.extend(port.validate())
        if not self.candidate_only:
            issues.append("CasePortFrame v0.1 must remain candidate-only")
        if not 0.0 <= float(self.confidence) <= 1.0:
            issues.append("confidence must be in [0,1]")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "CIEL_CASE_PORT_FRAME_V0_1",
            "frame_id": self.frame_id,
            "language_id": self.language_id,
            "operator": self.operator,
            "ports": [port.to_dict() for port in self.ports],
            "surface_text": self.surface_text,
            "evidence_basis": self.evidence_basis,
            "direction_status": self.direction_status,
            "candidate_only": self.candidate_only,
            "confidence": self.confidence,
        }


_PUNCT = ".,?!:;\"'()[]{}"
_TOKEN_RE = re.compile(r"\s+")


def _clean(token: str) -> str:
    return token.strip(_PUNCT)


def _lower(tokens: list[str]) -> list[str]:
    return [_clean(token).casefold() for token in tokens]


def _frame_id(operator: str, ports: tuple[CasePort, ...], surface_text: str) -> str:
    payload = {
        "operator": operator,
        "ports": [port.to_dict() for port in ports],
        "surface_text": surface_text,
    }
    digest = sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()[:20]
    return f"caseframe_{operator.lower()}_{digest}"


def _port(
    grammatical_case: CasePortCase,
    role: str,
    entity: str,
    index: int | None,
    *,
    surface_form: str | None = None,
    adposition: str | None = None,
    basis: str = "EXPLICIT_PATTERN",
    confidence: float = 0.80,
) -> CasePort:
    return CasePort(
        grammatical_case=grammatical_case,
        operator_role=role,
        entity=entity,
        token_indices=() if index is None else (index,),
        surface_form=surface_form if surface_form is not None else entity,
        adposition=adposition,
        basis=basis,
        confidence=confidence,
    )


def _build(
    operator: str,
    ports: list[CasePort],
    surface_text: str,
    *,
    evidence_basis: str,
    direction_status: str = "EXPLICIT",
) -> CasePortFrame:
    packed = tuple(ports)
    confidence = min((port.confidence for port in packed), default=0.0)
    frame = CasePortFrame(
        frame_id=_frame_id(operator, packed, surface_text),
        language_id="pl",
        operator=operator,
        ports=packed,
        surface_text=surface_text,
        evidence_basis=evidence_basis,
        direction_status=direction_status,
        candidate_only=True,
        confidence=confidence,
    )
    issues = frame.validate()
    if issues:
        raise ValueError("; ".join(issues))
    return frame


def extract_polish_case_port_frames(
    text: str,
    tokens: list[str] | None = None,
) -> list[CasePortFrame]:
    """Extract bounded case-typed relation candidates from explicit Polish patterns."""
    tokens = list(tokens) if tokens is not None else [
        token for token in _TOKEN_RE.split(text.strip()) if token
    ]
    low = _lower(tokens)
    frames: list[CasePortFrame] = []

    # X jest związany/związana/związane/związani z Y
    for i in range(max(0, len(low) - 4)):
        if (
            low[i + 1] == "jest"
            and low[i + 2] in {"związany", "związana", "związane", "związani"}
            and low[i + 3] == "z"
            and i + 4 < len(tokens)
        ):
            frames.append(_build(
                "CONNECTED_WITH",
                [
                    _port(CasePortCase.NOM, "entity", _clean(tokens[i]), i, confidence=0.92),
                    _port(
                        CasePortCase.INS,
                        "counterpart_in_relation",
                        _clean(tokens[i + 4]),
                        i + 4,
                        adposition="z",
                        confidence=0.92,
                    ),
                ],
                text,
                evidence_basis="EXPLICIT_COPULA_PARTICIPLE_Z_PATTERN",
            ))

    # X należy do Y
    for i in range(max(0, len(low) - 3)):
        if low[i + 1:i + 3] == ["należy", "do"] and i + 3 < len(tokens):
            frames.append(_build(
                "BELONGS_TO",
                [
                    _port(CasePortCase.NOM, "member_or_part", _clean(tokens[i]), i, confidence=0.94),
                    _port(
                        CasePortCase.GEN,
                        "container_or_owner",
                        _clean(tokens[i + 3]),
                        i + 3,
                        adposition="do",
                        confidence=0.94,
                    ),
                ],
                text,
                evidence_basis="EXPLICIT_NALEZY_DO_PATTERN",
            ))

    # [X] rozmawia/rozmawiam o Y z Z
    for i, word in enumerate(low):
        if word not in {"rozmawia", "rozmawiam"}:
            continue
        if i + 4 >= len(low) or low[i + 1] != "o" or low[i + 3] != "z":
            continue
        ports: list[CasePort] = []
        if word == "rozmawiam":
            ports.append(_port(
                CasePortCase.NOM,
                "speaker",
                "ja",
                None,
                surface_form=tokens[i],
                basis="IMPLICIT_PERSON_FROM_VERB_FORM",
                confidence=0.88,
            ))
            direction = "EXPLICIT_WITH_IMPLICIT_SUBJECT"
        elif i > 0:
            ports.append(_port(CasePortCase.NOM, "speaker", _clean(tokens[i - 1]), i - 1, confidence=0.90))
            direction = "EXPLICIT"
        else:
            continue
        ports.extend([
            _port(CasePortCase.LOC, "topic", _clean(tokens[i + 2]), i + 2, adposition="o", confidence=0.90),
            _port(CasePortCase.INS, "interlocutor", _clean(tokens[i + 4]), i + 4, adposition="z", confidence=0.90),
        ])
        frames.append(_build(
            "SPEAKS_ABOUT",
            ports,
            text,
            evidence_basis="EXPLICIT_ROZMAWIAC_O_Z_PATTERN",
            direction_status=direction,
        ))

    # [X] nazwał/nazwała/nazwałem/nazwałam Y Z
    for i, word in enumerate(low):
        if word not in {"nazwał", "nazwała", "nazwałem", "nazwałam"} or i + 2 >= len(tokens):
            continue
        ports = []
        if word in {"nazwałem", "nazwałam"}:
            ports.append(_port(
                CasePortCase.NOM,
                "namer",
                "ja",
                None,
                surface_form=tokens[i],
                basis="IMPLICIT_PERSON_FROM_VERB_FORM",
                confidence=0.88,
            ))
            direction = "EXPLICIT_WITH_IMPLICIT_SUBJECT"
        elif i > 0:
            ports.append(_port(CasePortCase.NOM, "namer", _clean(tokens[i - 1]), i - 1, confidence=0.90))
            direction = "EXPLICIT"
        else:
            continue
        ports.extend([
            _port(CasePortCase.ACC, "entity_named", _clean(tokens[i + 1]), i + 1, confidence=0.88),
            _port(CasePortCase.INS, "assigned_name", _clean(tokens[i + 2]), i + 2, confidence=0.88),
        ])
        frames.append(_build(
            "NAMES",
            ports,
            text,
            evidence_basis="EXPLICIT_NAZWAC_ARGUMENT_PATTERN",
            direction_status=direction,
        ))

    # [X] daje/daję Y Z; v0.1 keeps the argument-order evidence explicit.
    for i, word in enumerate(low):
        if word not in {"daje", "daję"} or i + 2 >= len(tokens):
            continue
        ports = []
        if word == "daję":
            ports.append(_port(
                CasePortCase.NOM,
                "giver",
                "ja",
                None,
                surface_form=tokens[i],
                basis="IMPLICIT_PERSON_FROM_VERB_FORM",
                confidence=0.86,
            ))
            direction = "EXPLICIT_WITH_IMPLICIT_SUBJECT"
        elif i > 0:
            ports.append(_port(CasePortCase.NOM, "giver", _clean(tokens[i - 1]), i - 1, confidence=0.88))
            direction = "EXPLICIT"
        else:
            continue
        ports.extend([
            _port(CasePortCase.DAT, "recipient", _clean(tokens[i + 1]), i + 1, basis="ARGUMENT_ORDER_CANDIDATE", confidence=0.82),
            _port(CasePortCase.ACC, "transferred_object", _clean(tokens[i + 2]), i + 2, basis="ARGUMENT_ORDER_CANDIDATE", confidence=0.82),
        ])
        frames.append(_build(
            "GIVES",
            ports,
            text,
            evidence_basis="BOUNDED_DAWAC_ARGUMENT_ORDER_PATTERN",
            direction_status=direction,
        ))

    # X opisuje Y o Z
    for i, word in enumerate(low):
        if word != "opisuje" or i == 0 or i + 3 >= len(tokens) or low[i + 2] != "o":
            continue
        frames.append(_build(
            "DESCRIBES",
            [
                _port(CasePortCase.NOM, "describer", _clean(tokens[i - 1]), i - 1, confidence=0.90),
                _port(CasePortCase.ACC, "described_object", _clean(tokens[i + 1]), i + 1, confidence=0.86),
                _port(CasePortCase.LOC, "topic_or_context", _clean(tokens[i + 3]), i + 3, adposition="o", confidence=0.86),
            ],
            text,
            evidence_basis="EXPLICIT_OPISUJE_O_PATTERN",
        ))

    # Vocative opening candidate: "Zosiu, ..."
    if tokens and tokens[0].rstrip().endswith(","):
        first = _clean(tokens[0])
        if first.casefold().endswith(("u", "ie", "o")):
            frames.append(_build(
                "ADDRESSES",
                [_port(CasePortCase.VOC, "addressee", first, 0, surface_form=tokens[0], confidence=0.74)],
                text,
                evidence_basis="VOCATIVE_OPENING_COMMA_PATTERN",
            ))

    deduped: dict[str, CasePortFrame] = {}
    for frame in frames:
        deduped.setdefault(frame.frame_id, frame)
    return list(deduped.values())
