"""Bounded local pseudo-global NOEMA node.

Purpose
-------
Create a local filesystem handoff node that multiple local GPT/CIEL instances
can discover by path and use for append-only packet exchange.

Boundary
--------
This is explicitly outside NOEMA SoT. It does not prove access to account-level
state, does not update CURRENT/latest-state, does not produce packet ACK from
external NOEMA, and does not canonize memory. It is a proxy-entry substrate.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
import datetime as _dt
import hashlib
import json
import os
import uuid

SCHEMA = "NOEMA_PSEUDOGLOBAL_LOCAL_NODE_V0_1"
DEFAULT_STATUS = "PSEUDOGLOBAL_ENTRY_EXISTS_OUTSIDE_SOT"


def utc_now() -> str:
    return _dt.datetime.now(_dt.UTC).isoformat().replace("+00:00", "Z")


def canonical_json(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class PseudoGlobalStatus:
    schema: str = SCHEMA
    status: str = DEFAULT_STATUS
    outside_sot: bool = True
    sot_available: bool = False
    current_state_loaded: bool = False
    current_state_id: None = None
    canon_allowed: bool = False
    noema_writeback_performed: bool = False
    network_used: bool = False
    account_global_claimed: bool = False
    uncertainty_operator: str = "chyba"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PseudoGlobalInstance:
    instance_id: str
    role: str = "local_gpt_instance"
    namespace: str = "USERGPT_LOCAL"
    created_at: str = field(default_factory=utc_now)
    capabilities: list[str] = field(default_factory=lambda: [
        "append_only_packets",
        "local_manifest",
        "hash_commitment",
        "outside_sot_boundary",
    ])
    outside_sot: bool = True
    canon_allowed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PseudoGlobalPacket:
    packet_id: str
    src_instance_id: str
    dst: str
    payload: dict[str, Any]
    created_at: str = field(default_factory=utc_now)
    schema: str = "NOEMA_PSEUDOGLOBAL_PACKET_V0_1"
    outside_sot: bool = True
    canon_allowed: bool = False

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        payload_hash = sha256_text(canonical_json(data["payload"]))
        data["payload_sha256"] = payload_hash
        data["packet_sha256"] = sha256_text(canonical_json({k: v for k, v in data.items() if k != "packet_sha256"}))
        return data


class LocalNoemaPseudoGlobalNode:
    """Filesystem-backed local pseudo-global handoff node.

    The node is deliberately boring: JSON files, JSONL ledger, no sockets,
    no listeners, no external calls. Multiple local instances can agree on
    the same root path and exchange packets through inbox/outbox directories.
    """

    def __init__(self, root: str | Path | None = None):
        root_value = root or os.environ.get("NOEMA_PSEUDOGLOBAL_ROOT") or "state/noema_pseudoglobal"
        self.root = Path(root_value).resolve()

    @property
    def current_path(self) -> Path:
        return self.root / "CURRENT_PSEUDOGLOBAL.noema.json"

    @property
    def registry_path(self) -> Path:
        return self.root / "registry" / "instances.json"

    @property
    def ledger_path(self) -> Path:
        return self.root / "logs" / "events.jsonl"

    def bootstrap(self) -> dict[str, Any]:
        for rel in ["registry", "instances", "inbox", "outbox", "logs", "snapshots"]:
            (self.root / rel).mkdir(parents=True, exist_ok=True)
        status = PseudoGlobalStatus().to_dict()
        status.update({
            "created_at": utc_now(),
            "node_root": str(self.root),
            "entry_kind": "local_pseudoglobal_proxy_entry",
            "description": "Shared local NOEMA-like node for GPT-instance handoff; visible as an entry, outside SoT.",
        })
        status["status_sha256"] = sha256_text(canonical_json(status))
        self._write_json(self.current_path, status)
        if not self.registry_path.exists():
            self._write_json(self.registry_path, {"schema": SCHEMA, "instances": {}, "outside_sot": True})
        self._append_event("bootstrap", {"current": self.current_path.name, "status_sha256": status["status_sha256"]})
        return status

    def register_instance(self, instance_id: str | None = None, *, role: str = "local_gpt_instance", namespace: str = "USERGPT_LOCAL") -> dict[str, Any]:
        if not self.current_path.exists():
            self.bootstrap()
        instance_id = instance_id or f"inst_{uuid.uuid4().hex[:12]}"
        instance = PseudoGlobalInstance(instance_id=instance_id, role=role, namespace=namespace).to_dict()
        registry = self._read_json(self.registry_path)
        registry.setdefault("instances", {})[instance_id] = instance
        registry["updated_at"] = utc_now()
        registry["registry_sha256"] = sha256_text(canonical_json({k: v for k, v in registry.items() if k != "registry_sha256"}))
        self._write_json(self.registry_path, registry)
        self._write_json(self.root / "instances" / f"{instance_id}.json", instance)
        self._append_event("register_instance", {"instance_id": instance_id, "role": role, "namespace": namespace})
        return instance

    def create_packet(self, src_instance_id: str, payload: dict[str, Any], *, dst: str = "broadcast") -> dict[str, Any]:
        if not self.current_path.exists():
            self.bootstrap()
        packet_id = f"pkt_{utc_now().replace(':','').replace('-','').replace('.','_')}_{uuid.uuid4().hex[:8]}"
        packet = PseudoGlobalPacket(packet_id=packet_id, src_instance_id=src_instance_id, dst=dst, payload=payload).to_dict()
        rel_dir = "outbox" if dst != "local_inbox" else "inbox"
        self._write_json(self.root / rel_dir / f"{packet_id}.noema.json", packet)
        self._append_event("create_packet", {"packet_id": packet_id, "src_instance_id": src_instance_id, "dst": dst, "packet_sha256": packet["packet_sha256"]})
        return packet

    def discover(self) -> dict[str, Any]:
        status = self._read_json(self.current_path) if self.current_path.exists() else self.bootstrap()
        registry = self._read_json(self.registry_path) if self.registry_path.exists() else {"instances": {}}
        packets = sorted([p.name for p in (self.root / "outbox").glob("*.noema.json")]) if (self.root / "outbox").exists() else []
        return {
            "schema": SCHEMA,
            "entry_visible": True,
            "status": status,
            "registered_instances": sorted(registry.get("instances", {}).keys()),
            "outbox_packets": packets,
            "outside_sot": True,
            "canon_allowed": False,
        }

    def _write_json(self, path: Path, data: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def _read_json(self, path: Path) -> dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))

    def _append_event(self, event_type: str, payload: dict[str, Any]) -> None:
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        event = {
            "schema": "NOEMA_PSEUDOGLOBAL_EVENT_V0_1",
            "event_type": event_type,
            "created_at": utc_now(),
            "payload": payload,
            "outside_sot": True,
        }
        event["event_sha256"] = sha256_text(canonical_json(event))
        with self.ledger_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
