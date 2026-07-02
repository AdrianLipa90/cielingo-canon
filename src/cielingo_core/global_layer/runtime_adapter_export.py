
"""Runtime adapter reference export v0.9B.

Exports RuntimeAdapterReference collections and global dry-test references as
local artifact-grounded reference bundles.

Boundary:
- export bundle is not SOURCE;
- export bundle is not canon;
- export bundle does not write NOEMA;
- export bundle does not update CURRENT;
- export bundle does not execute runtime actions.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from cielingo_core.global_layer.runtime_adapter_interface import RuntimeAdapterReference
from cielingo_core.global_layer.global_dry_test_reference import GlobalDryTestReference


@dataclass(frozen=True)
class RuntimeAdapterReferenceExportBundle:
    bundle_id: str
    references: list[RuntimeAdapterReference]
    global_reference: GlobalDryTestReference | None = None
    reference_kind: str = "artifact_grounded_reference_bundle"
    canon_allowed: bool = False
    source_promotion_allowed: bool = False
    noema_writeback_allowed: bool = False
    current_update_allowed: bool = False
    runtime_execution_allowed: bool = False
    limitation: str = "runtime_adapter_reference_export_not_source_not_execution"

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.bundle_id:
            issues.append("bundle_id is required")
        for ref in self.references:
            issues.extend(ref.validate())
        if self.global_reference is not None:
            issues.extend(self.global_reference.validate())
        if self.reference_kind != "artifact_grounded_reference_bundle":
            issues.append("reference_kind must be artifact_grounded_reference_bundle")
        if self.canon_allowed:
            issues.append("adapter reference export must not allow canon")
        if self.source_promotion_allowed:
            issues.append("adapter reference export must not promote SOURCE")
        if self.noema_writeback_allowed:
            issues.append("adapter reference export must not write NOEMA")
        if self.current_update_allowed:
            issues.append("adapter reference export must not update CURRENT")
        if self.runtime_execution_allowed:
            issues.append("adapter reference export must not allow runtime execution")
        if "not_source" not in self.limitation or "not_execution" not in self.limitation:
            issues.append("adapter reference export must state not_source and not_execution limitation")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "bundle_id": self.bundle_id,
            "references": [ref.to_dict() for ref in self.references],
            "global_reference": self.global_reference.to_dict() if self.global_reference is not None else None,
            "reference_kind": self.reference_kind,
            "canon_allowed": self.canon_allowed,
            "source_promotion_allowed": self.source_promotion_allowed,
            "noema_writeback_allowed": self.noema_writeback_allowed,
            "current_update_allowed": self.current_update_allowed,
            "runtime_execution_allowed": self.runtime_execution_allowed,
            "limitation": self.limitation,
        }

    def stable_hash(self) -> str:
        payload = json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True)
        return sha256(payload.encode("utf-8")).hexdigest()

    def write_json(self, path: str | Path) -> str:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        payload = self.to_dict()
        payload["stable_hash"] = self.stable_hash()
        p.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        return str(p)


def build_runtime_adapter_reference_export_bundle(
    references: list[RuntimeAdapterReference],
    global_reference: GlobalDryTestReference | None = None,
) -> RuntimeAdapterReferenceExportBundle:
    payload = json.dumps({
        "references": [ref.reference_id for ref in references],
        "global_reference": global_reference.reference_id if global_reference is not None else None,
    }, ensure_ascii=False, sort_keys=True)
    return RuntimeAdapterReferenceExportBundle(
        bundle_id="runtime_adapter_reference_export_" + sha256(payload.encode("utf-8")).hexdigest()[:16],
        references=references,
        global_reference=global_reference,
        reference_kind="artifact_grounded_reference_bundle",
        canon_allowed=False,
        source_promotion_allowed=False,
        noema_writeback_allowed=False,
        current_update_allowed=False,
        runtime_execution_allowed=False,
    )
