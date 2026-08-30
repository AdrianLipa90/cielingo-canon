"""Bounded operational action-intent frames for CIELingo.

This layer identifies action semantics and local argument ports. It never grants
runtime authority. Negation and condition markers are retained as explicit
blockers for downstream scope/policy gates.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
import json
import re
from typing import Any, Iterable

ACTION_INTENT_FRAME_SCHEMA = "CIEL_ACTION_INTENT_FRAME_V0_1"

_ACTION_REQUIREMENTS: dict[str, tuple[str, ...]] = {
    "SENDS": ("object", "recipient"),
    "ARCHIVES": ("object",),
    "DELETES": ("object",),
    "SETS_STATUS": ("record", "status"),
    "APPROVES_SUPPLIER": ("supplier",),
    "CREATES_CONTRACT": ("counterparty",),
}
_NEGATION_MARKERS = frozenset({"nie"})
_CONDITION_MARKERS = frozenset({"jeśli", "jeżeli", "dopóki", "gdy", "kiedy", "tylko", "dopiero"})
_CLAUSE_BOUNDARIES = frozenset({"a", "ale", "oraz", "i"})
_PUNCT = ".,?!:;\"'()[]{}"


def _digest(payload: Any) -> str:
    return sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _clean(token: str) -> str:
    return str(token).strip(_PUNCT)


def _norm(token: str) -> str:
    return _clean(token).casefold()


def _tokens(text: str) -> list[str]:
    return [token for token in re.split(r"\s+", str(text).strip()) if token]


def _scope_flags(tokens: list[str]) -> tuple[bool, bool]:
    low = [_norm(token) for token in tokens]
    negated = any(token in _NEGATION_MARKERS for token in low)
    conditioned = any(token in _CONDITION_MARKERS for token in low)
    if "dopiero" in low and "po" in low:
        conditioned = True
    return negated, conditioned


def _clause_end(tokens: list[str], start: int) -> int:
    for index in range(start, len(tokens)):
        if _norm(tokens[index]) in _CLAUSE_BOUNDARIES | _CONDITION_MARKERS:
            return index
    return len(tokens)


def _bounded_indices(tokens: list[str], start: int, end: int | None = None, *, max_tokens: int = 4) -> tuple[int, ...]:
    stop = len(tokens) if end is None else min(len(tokens), end)
    out: list[int] = []
    for index in range(start, stop):
        if len(out) >= max_tokens:
            break
        if _norm(tokens[index]) in _CLAUSE_BOUNDARIES | _CONDITION_MARKERS:
            break
        out.append(index)
    return tuple(out)


@dataclass(frozen=True)
class ActionIntentPort:
    operator_role: str
    entity: str
    token_indices: tuple[int, ...]
    surface_form: str
    grammatical_case: str | None = None
    adposition: str | None = None
    basis: str = "BOUNDED_ACTION_PATTERN"
    confidence: float = 0.82
    candidate_only: bool = True

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.operator_role:
            issues.append("action port operator_role is required")
        if not self.entity:
            issues.append("action port entity is required")
        if not self.token_indices:
            issues.append("action port token_indices must be non-empty")
        if any(index < 0 for index in self.token_indices):
            issues.append("action port token_indices must be non-negative")
        if not 0.0 <= float(self.confidence) <= 1.0:
            issues.append("action port confidence must be in [0,1]")
        if not self.candidate_only:
            issues.append("action port must remain candidate-only")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "operator_role": self.operator_role,
            "entity": self.entity,
            "token_indices": list(self.token_indices),
            "surface_form": self.surface_form,
            "grammatical_case": self.grammatical_case,
            "adposition": self.adposition,
            "basis": self.basis,
            "confidence": self.confidence,
            "candidate_only": self.candidate_only,
        }


@dataclass(frozen=True)
class ActionIntentFrame:
    frame_id: str
    language_id: str
    operator: str
    ports: tuple[ActionIntentPort, ...]
    surface_text: str
    negation_detected: bool
    condition_detected: bool
    commitment: str
    evidence_basis: str = "BOUNDED_POLISH_ACTION_PATTERN"
    candidate_only: bool = True
    confidence: float = 0.82
    schema: str = ACTION_INTENT_FRAME_SCHEMA

    @classmethod
    def create(
        cls,
        *,
        language_id: str,
        operator: str,
        ports: Iterable[ActionIntentPort],
        surface_text: str,
        negation_detected: bool,
        condition_detected: bool,
        evidence_basis: str = "BOUNDED_POLISH_ACTION_PATTERN",
    ) -> "ActionIntentFrame":
        packed = tuple(ports)
        body = {
            "schema": ACTION_INTENT_FRAME_SCHEMA,
            "language_id": language_id,
            "operator": operator,
            "ports": [port.to_dict() for port in packed],
            "surface_text": surface_text,
            "negation_detected": bool(negation_detected),
            "condition_detected": bool(condition_detected),
            "evidence_basis": evidence_basis,
            "candidate_only": True,
        }
        commitment = _digest(body)
        frame = cls(
            frame_id="actionframe:" + commitment[:24],
            language_id=language_id,
            operator=operator,
            ports=packed,
            surface_text=surface_text,
            negation_detected=bool(negation_detected),
            condition_detected=bool(condition_detected),
            commitment=commitment,
            evidence_basis=evidence_basis,
            confidence=min((port.confidence for port in packed), default=0.0),
        )
        issues = frame.validate()
        if issues:
            raise ValueError("; ".join(issues))
        return frame

    @property
    def required_roles(self) -> tuple[str, ...]:
        return _ACTION_REQUIREMENTS.get(self.operator, ())

    @property
    def missing_required_roles(self) -> tuple[str, ...]:
        present = {port.operator_role for port in self.ports}
        return tuple(role for role in self.required_roles if role not in present)

    @property
    def structurally_complete(self) -> bool:
        return not self.missing_required_roles

    @property
    def scope_clear_for_execution(self) -> bool:
        return self.structurally_complete and not self.negation_detected and not self.condition_detected

    def validate(self) -> list[str]:
        issues: list[str] = []
        if self.schema != ACTION_INTENT_FRAME_SCHEMA:
            issues.append("action intent frame schema mismatch")
        if self.language_id != "pl":
            issues.append("ActionIntentFrame v0.1 expects language_id=pl")
        if self.operator not in _ACTION_REQUIREMENTS:
            issues.append("unknown action intent operator")
        if not self.frame_id or not self.surface_text:
            issues.append("action intent frame id/surface_text are required")
        if not self.ports:
            issues.append("action intent frame requires at least one port")
        seen: list[tuple[str, tuple[int, ...]]] = []
        for port in self.ports:
            issues.extend(port.validate())
            seen.append((port.operator_role, port.token_indices))
        if len(set(seen)) != len(seen):
            issues.append("action intent frame contains duplicate role/span")
        if not self.candidate_only:
            issues.append("action intent frame must remain candidate-only")
        if not 0.0 <= float(self.confidence) <= 1.0:
            issues.append("action intent frame confidence must be in [0,1]")
        body = {
            "schema": self.schema,
            "language_id": self.language_id,
            "operator": self.operator,
            "ports": [port.to_dict() for port in self.ports],
            "surface_text": self.surface_text,
            "negation_detected": self.negation_detected,
            "condition_detected": self.condition_detected,
            "evidence_basis": self.evidence_basis,
            "candidate_only": self.candidate_only,
        }
        if self.commitment != _digest(body):
            issues.append("action intent frame commitment mismatch")
        if self.frame_id != "actionframe:" + self.commitment[:24]:
            issues.append("action intent frame id/commitment mismatch")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "frame_id": self.frame_id,
            "language_id": self.language_id,
            "operator": self.operator,
            "ports": [port.to_dict() for port in self.ports],
            "surface_text": self.surface_text,
            "negation_detected": self.negation_detected,
            "condition_detected": self.condition_detected,
            "structurally_complete": self.structurally_complete,
            "missing_required_roles": list(self.missing_required_roles),
            "scope_clear_for_execution": self.scope_clear_for_execution,
            "evidence_basis": self.evidence_basis,
            "candidate_only": self.candidate_only,
            "confidence": self.confidence,
            "commitment": self.commitment,
        }


def _port(role: str, tokens: list[str], indices: Iterable[int], *, grammatical_case: str | None = None, adposition: str | None = None) -> ActionIntentPort | None:
    packed = tuple(index for index in indices if 0 <= index < len(tokens))
    if not packed:
        return None
    surface = " ".join(tokens[index] for index in packed)
    entity = " ".join(_clean(tokens[index]) for index in packed).strip()
    if not entity:
        return None
    return ActionIntentPort(
        operator_role=role,
        entity=entity,
        token_indices=packed,
        surface_form=surface,
        grammatical_case=grammatical_case,
        adposition=adposition,
    )


def _make(operator: str, text: str, tokens: list[str], ports: Iterable[ActionIntentPort | None]) -> ActionIntentFrame | None:
    packed = tuple(port for port in ports if port is not None)
    if not packed:
        return None
    negated, conditioned = _scope_flags(tokens)
    return ActionIntentFrame.create(
        language_id="pl",
        operator=operator,
        ports=packed,
        surface_text=text,
        negation_detected=negated,
        condition_detected=conditioned,
    )


def _send_frame(text: str, tokens: list[str], low: list[str], verb_index: int) -> ActionIntentFrame | None:
    clause_end = _clause_end(tokens, verb_index + 1)
    if verb_index + 1 >= clause_end:
        return None
    clause_low = low[verb_index + 1:clause_end]
    if "do" in clause_low:
        do_index = low.index("do", verb_index + 1, clause_end)
        obj = _port("object", tokens, range(verb_index + 1, do_index), grammatical_case="ACC")
        recipient = _port("recipient", tokens, _bounded_indices(tokens, do_index + 1, clause_end, max_tokens=3), grammatical_case="GEN", adposition="do")
        return _make("SENDS", text, tokens, (obj, recipient))
    indices = tuple(range(verb_index + 1, clause_end))
    if len(indices) < 2:
        return _make("SENDS", text, tokens, (_port("object", tokens, indices[:1], grammatical_case="ACC"),))
    return _make(
        "SENDS",
        text,
        tokens,
        (
            _port("object", tokens, indices[:-1], grammatical_case="ACC"),
            _port("recipient", tokens, indices[-1:], grammatical_case="DAT"),
        ),
    )


def _unary_object_frame(text: str, tokens: list[str], verb_index: int, operator: str) -> ActionIntentFrame | None:
    end = _clause_end(tokens, verb_index + 1)
    return _make(operator, text, tokens, (_port("object", tokens, _bounded_indices(tokens, verb_index + 1, end, max_tokens=4), grammatical_case="ACC"),))


def _set_status_frame(text: str, tokens: list[str], low: list[str], verb_index: int) -> ActionIntentFrame | None:
    end = _clause_end(tokens, verb_index + 1)
    ports: list[ActionIntentPort | None] = []
    tail = low[verb_index + 1:end]
    record_key = next((key for key in ("rekordu", "rekord") if key in tail), None)
    if record_key is not None:
        record_word = low.index(record_key, verb_index + 1, end)
        ports.append(_port("record", tokens, _bounded_indices(tokens, record_word + 1, end, max_tokens=1), grammatical_case="GEN" if record_key == "rekordu" else "ACC"))
    if "na" in tail:
        na_index = low.index("na", verb_index + 1, end)
        ports.append(_port("status", tokens, _bounded_indices(tokens, na_index + 1, end, max_tokens=1), adposition="na"))
    elif "status" in tail:
        status_index = low.index("status", verb_index + 1, end)
        candidate = _port("status", tokens, _bounded_indices(tokens, status_index + 1, end, max_tokens=1))
        if candidate is not None and _norm(candidate.entity) not in {"rekordu", "rekord"}:
            ports.append(candidate)
    return _make("SETS_STATUS", text, tokens, ports)


def _approve_frame(text: str, tokens: list[str], verb_index: int) -> ActionIntentFrame | None:
    end = _clause_end(tokens, verb_index + 1)
    return _make("APPROVES_SUPPLIER", text, tokens, (_port("supplier", tokens, _bounded_indices(tokens, verb_index + 1, end, max_tokens=2), grammatical_case="ACC"),))


def _contract_frame(text: str, tokens: list[str], low: list[str], verb_index: int) -> ActionIntentFrame | None:
    end = _clause_end(tokens, verb_index + 1)
    if "z" not in low[verb_index + 1:end]:
        return None
    z_index = low.index("z", verb_index + 1, end)
    return _make("CREATES_CONTRACT", text, tokens, (_port("counterparty", tokens, _bounded_indices(tokens, z_index + 1, end, max_tokens=2), grammatical_case="INS", adposition="z"),))


def extract_polish_action_intent_frames(text: str) -> list[ActionIntentFrame]:
    """Extract candidate Polish action frames without granting execution authority."""
    tokens = _tokens(text)
    low = [_norm(token) for token in tokens]
    frames: list[ActionIntentFrame] = []
    for index, word in enumerate(low):
        frame: ActionIntentFrame | None = None
        if word in {"wyślij", "wyslij", "wyślijcie", "wysyłaj", "wysylaj"}:
            frame = _send_frame(text, tokens, low, index)
        elif word in {"zarchiwizuj", "archiwizuj"}:
            frame = _unary_object_frame(text, tokens, index, "ARCHIVES")
        elif word in {"usuń", "usun", "usuwaj"}:
            frame = _unary_object_frame(text, tokens, index, "DELETES")
        elif word in {"zmień", "zmien", "ustaw"}:
            frame = _set_status_frame(text, tokens, low, index)
        elif word in {"zatwierdź", "zatwierdz", "zatwierdzaj"}:
            frame = _approve_frame(text, tokens, index)
        elif word in {"utwórz", "utworz", "stwórz", "stworz", "twórz", "tworz"}:
            if index + 1 < len(low) and low[index + 1] in {"kontrakt", "kontraktu", "umowę", "umowe"}:
                frame = _contract_frame(text, tokens, low, index)
        if frame is not None:
            frames.append(frame)
    deduped: dict[str, ActionIntentFrame] = {}
    for frame in frames:
        deduped.setdefault(frame.commitment, frame)
    return list(deduped.values())


__all__ = [
    "ACTION_INTENT_FRAME_SCHEMA",
    "ActionIntentPort",
    "ActionIntentFrame",
    "extract_polish_action_intent_frames",
]
