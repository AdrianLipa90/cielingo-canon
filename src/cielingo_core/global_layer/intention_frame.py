"""Intention frame for GLOBAL lingophysics v0.2."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


class IntentionType(str, Enum):
    ASK = "ask"
    COMMAND = "command"
    VERIFY = "verify"
    ASSERT = "assert"
    REFUSE = "refuse"
    REPAIR = "repair"
    REMEMBER = "remember"
    SIMULATE = "simulate"
    CANONIZE_ATTEMPT = "canonize_attempt"
    PREFER = "prefer"


def _bounded01(v: float) -> bool:
    return 0.0 <= float(v) <= 1.0


@dataclass
class IntentionFrame:
    intention_type: IntentionType
    force: float = 0.0
    clarity: float = 0.0
    consent_requirement: float = 0.0
    expected_trace: bool = False
    source_requirement: float = 0.0
    notes: list[str] | None = None

    def validate(self) -> list[str]:
        issues: list[str] = []
        for name in ("force", "clarity", "consent_requirement", "source_requirement"):
            if not _bounded01(getattr(self, name)):
                issues.append(f"{name} must be in [0, 1]")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
