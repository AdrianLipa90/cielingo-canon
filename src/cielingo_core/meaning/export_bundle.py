
"""MeaningLoop / Repair export bundle v0.7C.

Exports loop + repair routing diagnostics into portable JSON objects.

Boundary:
- export is local artifact bundle, not NOEMA writeback;
- export does not update CURRENT;
- export does not canonize or promote SOURCE.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from cielingo_core.meaning.meaning_loop import MeaningLoop
from cielingo_core.meaning.repair_routing import MeaningRepairRoutingReport


@dataclass(frozen=True)
class MeaningLoopRepairExportBundle:
    bundle_id: str
    loops: list[MeaningLoop]
    repair_reports: list[MeaningRepairRoutingReport]
    source_refs: list[str] = field(default_factory=list)
    canon_allowed: bool = False
    source_promotion_allowed: bool = False
    noema_writeback_allowed: bool = False
    current_update_allowed: bool = False
    limitation: str = "meaning_loop_repair_export_bundle_not_noema_writeback"

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.bundle_id:
            issues.append("bundle_id is required")
        for loop in self.loops:
            issues.extend(loop.validate())
        for report in self.repair_reports:
            issues.extend(report.validate())
        if self.canon_allowed:
            issues.append("export bundle must not allow canon")
        if self.source_promotion_allowed:
            issues.append("export bundle must not promote SOURCE")
        if self.noema_writeback_allowed:
            issues.append("export bundle must not write NOEMA")
        if self.current_update_allowed:
            issues.append("export bundle must not update CURRENT")
        if "not_noema_writeback" not in self.limitation:
            issues.append("export bundle must state not_noema_writeback limitation")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "bundle_id": self.bundle_id,
            "loops": [loop.to_dict() for loop in self.loops],
            "repair_reports": [report.to_dict() for report in self.repair_reports],
            "source_refs": list(self.source_refs),
            "canon_allowed": self.canon_allowed,
            "source_promotion_allowed": self.source_promotion_allowed,
            "noema_writeback_allowed": self.noema_writeback_allowed,
            "current_update_allowed": self.current_update_allowed,
            "limitation": self.limitation,
        }

    def stable_hash(self) -> str:
        payload = json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True)
        return sha256(payload.encode("utf-8")).hexdigest()

    def write_json(self, path: str | Path) -> str:
        """Write local JSON export only. This is not NOEMA writeback."""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        payload = self.to_dict()
        payload["stable_hash"] = self.stable_hash()
        p.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        return str(p)


def build_meaning_loop_repair_export_bundle(
    loops: list[MeaningLoop],
    repair_reports: list[MeaningRepairRoutingReport],
    source_refs: list[str] | None = None,
) -> MeaningLoopRepairExportBundle:
    payload = json.dumps({
        "loop_ids": [loop.loop_id for loop in loops],
        "repair_report_ids": [report.report_id for report in repair_reports],
        "source_refs": source_refs or [],
    }, ensure_ascii=False, sort_keys=True)
    return MeaningLoopRepairExportBundle(
        bundle_id="meaning_repair_export_" + sha256(payload.encode("utf-8")).hexdigest()[:16],
        loops=loops,
        repair_reports=repair_reports,
        source_refs=source_refs or [],
        canon_allowed=False,
        source_promotion_allowed=False,
        noema_writeback_allowed=False,
        current_update_allowed=False,
    )
