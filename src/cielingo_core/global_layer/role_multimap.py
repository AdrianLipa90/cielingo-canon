"""Lossless GLOBAL role multimap for typed CIELingo relation bindings."""

from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
import json
import string
from typing import Any

from .contracts import UniversalRole


_HEX = frozenset(string.hexdigits)


def _bounded01(value: float) -> bool:
    return 0.0 <= float(value) <= 1.0


def _is_sha256(value: str) -> bool:
    return len(value) == 64 and all(char in _HEX for char in value)


@dataclass(frozen=True)
class MeaningRoleBinding:
    binding_id: str
    universal_role: UniversalRole
    entity: str
    operator: str
    operator_role: str
    grammatical_case: str
    token_indices: tuple[int, ...]
    source_frame_id: str
    signature_id: str
    signature_commitment: str
    normalization_basis: str
    confidence: float
    candidate_only: bool = True

    def validate(self) -> list[str]:
        issues: list[str] = []
        for name in (
            "binding_id",
            "entity",
            "operator",
            "operator_role",
            "grammatical_case",
            "source_frame_id",
            "signature_id",
            "normalization_basis",
        ):
            if not str(getattr(self, name)).strip():
                issues.append(f"{name} is required")
        if any(int(index) < 0 for index in self.token_indices):
            issues.append("token_indices must be non-negative")
        if not _is_sha256(self.signature_commitment):
            issues.append("signature_commitment must be SHA-256")
        if not _bounded01(self.confidence):
            issues.append("confidence must be in [0,1]")
        if not self.candidate_only:
            issues.append("MeaningRoleBinding v0.1 must remain candidate-only")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "binding_id": self.binding_id,
            "universal_role": self.universal_role.value,
            "entity": self.entity,
            "operator": self.operator,
            "operator_role": self.operator_role,
            "grammatical_case": self.grammatical_case,
            "token_indices": list(self.token_indices),
            "source_frame_id": self.source_frame_id,
            "signature_id": self.signature_id,
            "signature_commitment": self.signature_commitment,
            "normalization_basis": self.normalization_basis,
            "confidence": self.confidence,
            "candidate_only": self.candidate_only,
        }


@dataclass(frozen=True)
class MeaningRoleMultimap:
    equation_id: str
    bindings: tuple[MeaningRoleBinding, ...]
    commitment: str
    candidate_only: bool = True
    schema: str = "CIEL_MEANING_ROLE_MULTIMAP_V0_1"

    @classmethod
    def create(
        cls,
        *,
        equation_id: str,
        bindings: tuple[MeaningRoleBinding, ...] | list[MeaningRoleBinding],
    ) -> "MeaningRoleMultimap":
        packed = tuple(bindings)
        provisional = cls(
            equation_id=equation_id,
            bindings=packed,
            commitment="",
        )
        result = replace(
            provisional,
            commitment=sha256(
                json.dumps(
                    provisional.to_binding_dict(),
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest(),
        )
        issues = result.validate()
        if issues:
            raise ValueError("; ".join(issues))
        return result

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.equation_id:
            issues.append("equation_id is required")
        ids = [binding.binding_id for binding in self.bindings]
        if len(set(ids)) != len(ids):
            issues.append("role multimap binding IDs must be unique")
        for binding in self.bindings:
            issues.extend(binding.validate())
        if not self.candidate_only:
            issues.append("MeaningRoleMultimap v0.1 must remain candidate-only")
        if not _is_sha256(self.commitment):
            issues.append("commitment must be SHA-256")
        elif self.commitment != sha256(
            json.dumps(
                self.to_binding_dict(),
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest():
            issues.append("role multimap commitment mismatch")
        return issues

    def by_role(self, role: UniversalRole) -> tuple[MeaningRoleBinding, ...]:
        return tuple(binding for binding in self.bindings if binding.universal_role is role)

    def to_binding_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "equation_id": self.equation_id,
            "bindings": [binding.to_dict() for binding in self.bindings],
            "candidate_only": self.candidate_only,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.to_binding_dict(), "commitment": self.commitment}


__all__ = ["MeaningRoleBinding", "MeaningRoleMultimap"]
