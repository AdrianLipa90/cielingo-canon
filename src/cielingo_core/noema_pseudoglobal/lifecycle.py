"""Lifecycle audit for local pseudo-global NOEMA tools.

This module joins two local constructs:
- NoemaSurface global gadget registry
- LocalNoemaPseudoGlobalNode packet/instance registry

It never claims NOEMA SoT, external ACK, account-global GPT infrastructure,
or CURRENT/latest-state update.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
import hashlib
import json

from cielingo_core.noema_surface.command_prompt import NoemaSurface
from cielingo_core.noema_pseudoglobal.node import LocalNoemaPseudoGlobalNode


SCHEMA = "NOEMA_PSEUDOGLOBAL_LIFECYCLE_AUDIT_V0_1"


def _canonical(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True)
class PseudoGlobalLifecycleReport:
    schema: str = SCHEMA
    surface_registry_present: bool = False
    pseudo_global_entry_visible: bool = False
    outside_sot: bool = True
    sot_available: bool = False
    current_updated: bool = False
    memory_writeback_performed: bool = False
    account_global_claimed: bool = False
    canon_allowed: bool = False
    gadgets: list[str] = field(default_factory=list)
    instances: list[str] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["report_sha256"] = hashlib.sha256(_canonical(data).encode("utf-8")).hexdigest()
        return data


def install_default_noema_global_gadgets(surface: NoemaSurface) -> dict[str, Any]:
    """Install default repo-global NOEMA Surface entries.

    The entries describe tools already exposed by NoemaSurface, plus the
    pseudo-global node lifecycle. This is a local registry action only.
    """
    installed = []
    specs = [
        (
            "surface_packaging_suite",
            "Repo-global NOEMA Surface package/hash/zip-test suite.",
            ["zip_paths", "zip_test", "sha256_file", "compileall"],
        ),
        (
            "pseudoglobal_node_lifecycle",
            "Local pseudo-global node bootstrap/discovery/packet lifecycle outside SoT.",
            ["install_global_gadget", "list_global_gadgets", "audit_global_gadgets"],
        ),
        (
            "bounded_surface_audit",
            "Boundary audit for no SOURCE/CURRENT/ACK/canon promotion.",
            ["command_registry", "audit_global_gadgets"],
        ),
    ]
    for name, description, commands in specs:
        result = surface.install_global_gadget(name, description=description, commands=commands)
        if not result.ok:
            return {"ok": False, "failed": name, "issues": result.issues, "installed": installed}
        installed.append(result.payload)
    audit = surface.audit_global_gadgets()
    return {"ok": audit.ok, "installed": installed, "audit": audit.to_dict()}


def audit_pseudoglobal_lifecycle(repo_root: str | Path, node_root: str | Path = "state/noema_pseudoglobal") -> dict[str, Any]:
    repo_root = Path(repo_root).resolve()
    surface = NoemaSurface(repo_root)
    node = LocalNoemaPseudoGlobalNode(repo_root / node_root)
    surface_list = surface.list_global_gadgets()
    discovery = node.discover()
    issues: list[str] = []
    if not surface_list.payload.get("registry_exists"):
        issues.append("surface global gadget registry missing")
    if discovery.get("outside_sot") is not True:
        issues.append("pseudo-global discovery is not marked outside_sot")
    if discovery.get("status", {}).get("account_global_claimed") is not False:
        issues.append("pseudo-global node claims account-global state")
    report = PseudoGlobalLifecycleReport(
        surface_registry_present=bool(surface_list.payload.get("registry_exists")),
        pseudo_global_entry_visible=bool(discovery.get("entry_visible")),
        gadgets=list(surface_list.payload.get("gadgets", [])),
        instances=list(discovery.get("registered_instances", [])),
        issues=issues,
    )
    return report.to_dict()
