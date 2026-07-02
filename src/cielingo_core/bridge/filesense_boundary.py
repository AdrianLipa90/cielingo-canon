"""FileSense boundary contract."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class FileSenseBoundaryReport:
    retrieval_only: bool = True
    source_promotion_allowed: bool = False
    canon_promotion_allowed: bool = False
    noema_writeback_allowed: bool = False
    current_update_allowed: bool = False

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.retrieval_only:
            issues.append("FileSense must remain retrieval-only")
        if self.source_promotion_allowed:
            issues.append("FileSense must not promote SOURCE")
        if self.canon_promotion_allowed:
            issues.append("FileSense must not promote canon")
        if self.noema_writeback_allowed:
            issues.append("FileSense must not write NOEMA")
        if self.current_update_allowed:
            issues.append("FileSense must not update CURRENT")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
