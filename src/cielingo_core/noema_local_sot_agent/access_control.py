"""Access-control standard for local SOT_Agent_NoemaSurface.

This module implements local artifact permissions only. It is not OS sudo, not
external NOEMA SoT, not account-global GPT infrastructure, and not USER007 disk
access. It exists so future agents can verify which paths are normal CIELingo
work and which edits require an explicit Adrian ALLOW grant.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable
import datetime as _dt
import fnmatch
import hashlib
import json

SCHEMA = "NOEMA_LOCAL_SOT_AGENT_ACCESS_STANDARD_V0_1"


def utc_now() -> str:
    return _dt.datetime.now(_dt.UTC).isoformat().replace("+00:00", "Z")


def canonical_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class AccessDecision:
    ok: bool
    decision: str
    path: str
    reason: str
    required_grant: str | None = None
    outside_external_sot: bool = True
    no_system_sudo: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AccessPolicy:
    schema: str = SCHEMA
    active_work_core: str = "CIELingo"
    local_sot_write_allowed: bool = True
    external_sot_write_allowed: bool = False
    no_system_sudo: bool = True
    outside_external_sot: bool = True
    ask_before_non_work_core_edits: bool = True
    normal_cielingo_write_globs: tuple[str, ...] = (
        "src/cielingo_core/**",
        "tests/**",
        "cards/**",
        "corpus/**",
        "docs/**",
        "reports/**",
        "scripts/**",
        "state/noema_local_sot_agent/**",
        "state/noema_surface/**",
        "state/noema_pseudoglobal/**",
        "packages/**",
        "README*.md",
        "*MANIFEST*.json",
        "SHA256SUMS*",
    )
    protected_non_work_core_globs: tuple[str, ...] = (
        "src/CIEL_OMEGA_COMPLETE_SYSTEM/**",
        "apocalypos/**",
        "ApocalypOS/**",
        "src/apocalypos/**",
        "src/ciel_sot_agent/**",
        "integration/**",
        "noema_server/**",
        "server/**",
        "runtime/**",
        "system/**",
        "kernels/**",
    )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["policy_sha256"] = sha256_text(canonical_json({k: v for k, v in data.items() if k != "policy_sha256"}))
        return data


class LocalSOTAccessController:
    """Path-scoped local access guard for SOT_Agent_NoemaSurface."""

    def __init__(self, repo_root: str | Path, policy: AccessPolicy | None = None):
        self.repo_root = Path(repo_root).resolve()
        self.policy = policy or AccessPolicy()

    def classify_path(self, relative_path: str | Path) -> str:
        rel = str(relative_path).replace("\\", "/").lstrip("/")
        for pattern in self.policy.protected_non_work_core_globs:
            if fnmatch.fnmatch(rel, pattern):
                return "protected_non_work_core"
        for pattern in self.policy.normal_cielingo_write_globs:
            if fnmatch.fnmatch(rel, pattern):
                return "active_work_core"
        return "unknown_or_non_work_core"

    def can_write(self, relative_path: str | Path, *, allow_grant: dict[str, Any] | None = None) -> AccessDecision:
        rel = str(relative_path).replace("\\", "/").lstrip("/")
        kind = self.classify_path(rel)
        if kind == "active_work_core":
            return AccessDecision(True, "ALLOW_LOCAL_WRITE", rel, "Path belongs to active CIELingo/local NOEMA work core.")
        if allow_grant and allow_grant.get("grant_type") == "ADRIAN_CONDITIONAL_ALLOW" and allow_grant.get("status") == "ACTIVE_BY_USER_COMMAND":
            allowed = allow_grant.get("scope_paths", [])
            if any(fnmatch.fnmatch(rel, pattern) for pattern in allowed):
                return AccessDecision(True, "ALLOW_BY_CONDITIONAL_GRANT", rel, "Explicit temporary ALLOW grant covers this path.", required_grant=None)
        return AccessDecision(False, "REQUIRE_USER_ALLOW", rel, f"Path classified as {kind}; explicit Adrian ALLOW required before edit.", required_grant="ADRIAN_CONDITIONAL_ALLOW")


def build_default_access_standard() -> dict[str, Any]:
    policy = AccessPolicy().to_dict()
    standard = {
        "schema": SCHEMA,
        "created_at": utc_now(),
        "status": "LOCAL_ACCESS_STANDARD_ESTABLISHED_OUTSIDE_EXTERNAL_SOT",
        "authority": {
            "local_sot_write_permission_granted_by_user": True,
            "external_sot_write_permission_claimed": False,
            "user007_disk_write_claimed": False,
            "account_global_gpt_claimed": False,
        },
        "policy": policy,
        "operational_rule": {
            "primary_work_core": "CIELingo",
            "normal_cielingo_edits_allowed": True,
            "non_work_core_edits_require_question": True,
            "private_sudo_key_is_not_os_sudo": True,
            "conditional_allow_required_for_exceptional_edits": True,
        },
    }
    standard["standard_sha256"] = sha256_text(canonical_json({k: v for k, v in standard.items() if k != "standard_sha256"}))
    return standard
