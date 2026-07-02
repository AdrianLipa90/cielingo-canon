"""Thin, bounded ApocalypOS working-state wrapper.

Purpose
-------
Connect CIELingo to an unpacked ApocalypOS repository as an artifact-grounded
working state. This wrapper is intentionally narrow:

- no ApocalypOS runtime imports;
- no subprocess runtime execution;
- no network/listener behavior;
- no NOEMA writeback;
- no CURRENT update;
- no SOURCE/canon promotion.

It may inspect files inside an explicit ApocalypOS root and emit a stable local
working-state JSON for further CIELingo development.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
from pathlib import Path
import json
from typing import Any, Iterable

from cielingo_core.noema_surface.command_prompt import NoemaSurface, NoemaSurfaceResult


BOUNDARY_NOTES = [
    "artifact_grounded_only",
    "not_noema_sot",
    "not_source",
    "not_canon",
    "not_current_update",
    "not_runtime_execution",
    "not_network_listener",
]


@dataclass(frozen=True)
class ApocalypOSArtifactRef:
    """Reference to a file inside the bounded ApocalypOS artifact root."""

    relative_path: str
    exists: bool
    size_bytes: int | None = None
    sha256: str | None = None
    role: str = "working_artifact"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ApocalypOSWorkingState:
    """Local working-state snapshot for CIELingo ⇄ ApocalypOS integration."""

    state_kind: str
    state_id: str
    apocalypos_root: str
    cielingo_root: str
    adapter_mode: str
    source_status: str
    canon_allowed: bool
    noema_writeback_allowed: bool
    current_update_allowed: bool
    runtime_execution_allowed: bool
    network_allowed: bool
    wrapper_version: str
    boundary_notes: list[str] = field(default_factory=list)
    artifact_refs: list[ApocalypOSArtifactRef] = field(default_factory=list)
    working_focus: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        out = asdict(self)
        out["artifact_refs"] = [ref.to_dict() for ref in self.artifact_refs]
        return out

    def validate(self) -> list[str]:
        issues: list[str] = []
        if self.state_kind != "apocalypos_thin_wrapper_working_state":
            issues.append("state_kind must be apocalypos_thin_wrapper_working_state")
        if self.adapter_mode != "observe_only_thin_wrapper":
            issues.append("adapter_mode must remain observe_only_thin_wrapper")
        if self.source_status != "artifact_grounded_not_SOURCE":
            issues.append("source_status must remain artifact_grounded_not_SOURCE")
        if self.canon_allowed:
            issues.append("canon_allowed must be false")
        if self.noema_writeback_allowed:
            issues.append("noema_writeback_allowed must be false")
        if self.current_update_allowed:
            issues.append("current_update_allowed must be false")
        if self.runtime_execution_allowed:
            issues.append("runtime_execution_allowed must be false")
        if self.network_allowed:
            issues.append("network_allowed must be false")
        missing_notes = sorted(set(BOUNDARY_NOTES) - set(self.boundary_notes))
        if missing_notes:
            issues.append(f"missing boundary notes: {missing_notes}")
        if not self.state_id.startswith("apocalypos_working_state_"):
            issues.append("state_id must use apocalypos_working_state_ prefix")
        return issues

    def stable_payload(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload.pop("state_id", None)
        return payload


class ApocalypOSThinWrapper:
    """Bounded surface around an unpacked ApocalypOS repository."""

    wrapper_version = "0.1.0"

    def __init__(self, apocalypos_root: str | Path, cielingo_root: str | Path):
        self.apocalypos_root = Path(apocalypos_root).resolve()
        self.cielingo_root = Path(cielingo_root).resolve()
        self.surface = NoemaSurface(self.apocalypos_root)

    def path(self, relative_path: str | Path) -> Path:
        """Resolve a path using the same no-escape rule as NoemaSurface."""
        return self.surface.path(relative_path)

    def ls(self, relative_path: str | Path = ".", *, recursive: bool = False, pattern: str | None = None) -> NoemaSurfaceResult:
        """List via local NOEMA Surface. This is not external NOEMA SoT."""
        return self.surface.ls(relative_path, recursive=recursive, pattern=pattern)

    def read_text(self, relative_path: str | Path) -> NoemaSurfaceResult:
        """Read text via local NOEMA Surface. This is not SOURCE promotion."""
        return self.surface.read_text(relative_path)

    def artifact_ref(self, relative_path: str, role: str = "working_artifact") -> ApocalypOSArtifactRef:
        path = self.path(relative_path)
        if not path.exists() or not path.is_file():
            return ApocalypOSArtifactRef(relative_path=relative_path, exists=False, role=role)
        data = path.read_bytes()
        return ApocalypOSArtifactRef(
            relative_path=relative_path,
            exists=True,
            size_bytes=len(data),
            sha256=sha256(data).hexdigest(),
            role=role,
        )

    def build_state(self, artifact_paths: Iterable[tuple[str, str]] | None = None) -> ApocalypOSWorkingState:
        default_paths = [
            ("README.md", "orientation"),
            ("AGENT.md", "agent_boundary"),
            ("CIEL_CANON.py", "canon_file_observed_not_promoted"),
            ("pyproject.toml", "python_project_metadata"),
            ("src/ciel_sot_agent/noema_sot.py", "noema_sot_module_observed_not_loaded"),
            ("src/ciel_sot_agent/noema_file_sense.py", "filesense_module_observed_not_loaded"),
            ("integration/reports/noema_sot_report.json", "integration_report_observed"),
            ("tests/test_noema_file_sense.py", "test_surface_observed"),
            ("tests/test_noema_doctor_cycle.py", "test_surface_observed"),
        ]
        refs = [self.artifact_ref(path, role) for path, role in (artifact_paths or default_paths)]
        blockers: list[str] = []
        if not self.apocalypos_root.exists():
            blockers.append("apocalypos_root_missing")
        if not self.cielingo_root.exists():
            blockers.append("cielingo_root_missing")
        missing = [ref.relative_path for ref in refs if not ref.exists]
        if missing:
            blockers.append("missing_expected_artifacts:" + ",".join(missing))

        provisional = ApocalypOSWorkingState(
            state_kind="apocalypos_thin_wrapper_working_state",
            state_id="apocalypos_working_state_PENDING",
            apocalypos_root=str(self.apocalypos_root),
            cielingo_root=str(self.cielingo_root),
            adapter_mode="observe_only_thin_wrapper",
            source_status="artifact_grounded_not_SOURCE",
            canon_allowed=False,
            noema_writeback_allowed=False,
            current_update_allowed=False,
            runtime_execution_allowed=False,
            network_allowed=False,
            wrapper_version=self.wrapper_version,
            boundary_notes=list(BOUNDARY_NOTES),
            artifact_refs=refs,
            working_focus=[
                "CIELingo remains linguistic/semantic-neural input layer",
                "ApocalypOS is connected as artifact-grounded observed runtime substrate",
                "No runtime connector extraction until wrapper invariants stay green",
            ],
            blockers=blockers,
        )
        payload = json.dumps(provisional.stable_payload(), ensure_ascii=False, sort_keys=True)
        state_id = "apocalypos_working_state_" + sha256(payload.encode("utf-8")).hexdigest()[:16]
        return ApocalypOSWorkingState(**{**provisional.to_dict(), "state_id": state_id, "artifact_refs": refs})

    def write_state(self, relative_output_path: str | Path = "state/apocalypos_working/APOCALYPOS_THIN_WRAPPER_WORKING_STATE.json") -> ApocalypOSWorkingState:
        state = self.build_state()
        issues = state.validate()
        if issues:
            raise ValueError("invalid ApocalypOSWorkingState: " + "; ".join(issues))
        target = (self.cielingo_root / relative_output_path).resolve()
        if self.cielingo_root != target and self.cielingo_root not in target.parents:
            raise ValueError(f"output path escapes CIELingo root: {relative_output_path}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(state.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return state


def build_working_state(apocalypos_root: str | Path, cielingo_root: str | Path) -> ApocalypOSWorkingState:
    """Convenience function for tests and handoff scripts."""
    return ApocalypOSThinWrapper(apocalypos_root, cielingo_root).build_state()
