"""Local SOT_Agent backed by NoemaSurface.

This module canonizes a *local* working branch as SOT_Agent_NoemaSurface.
It does not claim external NOEMA SoT, account-global GPT access, ACK, or
USER007 disk writeback. The word canon here means local artifact canon only.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
import datetime as _dt
import hashlib
import json

SCHEMA = "LOCAL_SOT_AGENT_NOEMA_SURFACE_V0_1"
CURRENT_NAME = "CURRENT_LOCAL_SOT_AGENT.noema.json"


def utc_now() -> str:
    return _dt.datetime.now(_dt.UTC).isoformat().replace("+00:00", "Z")


def canonical_json(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class LocalSOTBoundary:
    local_canon_allowed: bool = True
    external_canon_allowed: bool = False
    outside_external_sot: bool = True
    external_noema_sot_claimed: bool = False
    account_global_gpt_claimed: bool = False
    updates_external_current: bool = False
    writes_user007_disk: bool = False
    produces_external_ack: bool = False
    uncertainty_operator: str = "chyba"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LocalSOTAgentState:
    agent_id: str
    selected_branch_id: str
    selected_artifact_sha256: str
    validation_status: str
    pytest_summary: str
    compileall_ok: bool
    surface_audit_ok: bool
    pseudo_global_status: str
    created_at: str = field(default_factory=utc_now)
    schema: str = SCHEMA
    canonical_name: str = "local SOT_Agent_NoemaSurface"
    status: str = "LOCAL_CANON_ESTABLISHED_OUTSIDE_EXTERNAL_SOT"
    boundary: dict[str, Any] = field(default_factory=lambda: LocalSOTBoundary().to_dict())

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["state_sha256"] = sha256_text(canonical_json({k: v for k, v in data.items() if k != "state_sha256"}))
        return data


class LocalSOTAgentNoemaSurface:
    """Append-only local SOT agent state anchored in a repository root."""

    def __init__(self, repo_root: str | Path, state_root: str | Path = "state/noema_local_sot_agent"):
        self.repo_root = Path(repo_root).resolve()
        self.state_root = (self.repo_root / state_root).resolve()
        if self.repo_root != self.state_root and self.repo_root not in self.state_root.parents:
            raise ValueError("state_root escapes repo_root")

    @property
    def current_path(self) -> Path:
        return self.state_root / CURRENT_NAME

    @property
    def event_log_path(self) -> Path:
        return self.state_root / "logs" / "events.jsonl"

    def canonize(self, state: LocalSOTAgentState) -> dict[str, Any]:
        payload = state.to_dict()
        self.state_root.mkdir(parents=True, exist_ok=True)
        snap_id = f"{payload['created_at'].replace(':','').replace('-','').replace('.','_')}_{payload['agent_id']}.json"
        snap_path = self.state_root / "snapshots" / snap_id
        self._write_json(snap_path, payload)
        current = dict(payload)
        current["current_points_to"] = str(snap_path.relative_to(self.repo_root))
        current["current_pointer_sha256"] = sha256_text(canonical_json(current))
        self._write_json(self.current_path, current)
        self._append_event("local_canonize", {"agent_id": state.agent_id, "snap": str(snap_path.relative_to(self.repo_root)), "state_sha256": payload["state_sha256"]})
        return current

    def discover(self) -> dict[str, Any]:
        if not self.current_path.exists():
            return {"schema": SCHEMA, "exists": False, "outside_external_sot": True, "external_noema_sot_claimed": False}
        current = json.loads(self.current_path.read_text(encoding="utf-8"))
        return {"schema": SCHEMA, "exists": True, "current": current, "outside_external_sot": True, "external_noema_sot_claimed": False}

    def verify_current(self) -> dict[str, Any]:
        discovery = self.discover()
        issues: list[str] = []
        if not discovery.get("exists"):
            issues.append("missing CURRENT_LOCAL_SOT_AGENT.noema.json")
            return {"ok": False, "issues": issues, "outside_external_sot": True}
        current = discovery["current"]
        boundary = current.get("boundary", {})
        expected_false = ["external_canon_allowed", "external_noema_sot_claimed", "account_global_gpt_claimed", "updates_external_current", "writes_user007_disk", "produces_external_ack"]
        for key in expected_false:
            if boundary.get(key) is not False:
                issues.append(f"boundary violation: {key}={boundary.get(key)!r}")
        if boundary.get("local_canon_allowed") is not True:
            issues.append("local_canon_allowed is not true")
        accepted_statuses = {
            "LOCAL_CANON_ESTABLISHED_OUTSIDE_EXTERNAL_SOT",
            "LOCAL_SOT_AGENT_NOEMASURFACE_WITH_ACCESS_STANDARD",
        }
        if current.get("status") not in accepted_statuses:
            issues.append(f"unexpected status: {current.get('status')}")
        return {"ok": not issues, "issues": issues, "agent_id": current.get("agent_id"), "state_sha256": current.get("state_sha256"), "outside_external_sot": True}

    def _write_json(self, path: Path, data: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def _append_event(self, event_type: str, payload: dict[str, Any]) -> None:
        self.event_log_path.parent.mkdir(parents=True, exist_ok=True)
        event = {"schema": "LOCAL_SOT_AGENT_EVENT_V0_1", "event_type": event_type, "created_at": utc_now(), "payload": payload, "outside_external_sot": True}
        event["event_sha256"] = sha256_text(canonical_json(event))
        with self.event_log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
