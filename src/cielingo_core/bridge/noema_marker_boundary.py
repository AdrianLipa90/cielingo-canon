"""NOEMA marker boundary contract."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class NoemaMarkerBoundaryReport:
    marker_is_commitment: bool = True
    marker_is_source: bool = False
    marker_updates_current: bool = False
    marker_writes_memory: bool = False
    requires_external_ack_for_sot: bool = True

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.marker_is_commitment:
            issues.append("marker must remain a commitment")
        if self.marker_is_source:
            issues.append("marker must not be SOURCE")
        if self.marker_updates_current:
            issues.append("marker must not update CURRENT")
        if self.marker_writes_memory:
            issues.append("marker must not write memory")
        if not self.requires_external_ack_for_sot:
            issues.append("marker requires external ACK for SoT")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
