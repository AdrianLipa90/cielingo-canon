"""Fail-closed full-surface GREMLIN bridge for CIELingo."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Protocol, Sequence

from cielingo_core.lingophysics.genomic_grammar import GenomicGrammarPacket

SCHEMA = "CIELINGO_GREMLIN_FULL_BRIDGE_V0_1"
GREMLIN_REPOSITORY = "AdrianLipa90/GREMLIN"
GREMLIN_BASELINE_SHA = "86059ead6177fbb5bf33211f674781883a149a57"

REQUIRED_CORE_TOOLS = frozenset({
    "gremlin_status", "gremlin_bestiary", "gremlin_species",
    "gremlin_plan", "gremlin_route", "gremlin_relation_parse", "gremlin_relation_signature",
    "gremlin_web_fetch", "gremlin_web_search", "gremlin_research", "gremlin_research_execute",
    "gremlin_research_hound_provenance", "gremlin_research_guarded", "gremlin_research_relational",
    "gremlin_auto_fanout", "gremlin_fanout", "gremlin_collect", "gremlin_synthesize", "gremlin_prototype",
    "gremlin_phasenav_status", "gremlin_phasenav_reference_sweep", "gremlin_phasenav_threeway",
    "gremlin_phasenav_analog_invariants", "gremlin_phasenav_live_replay",
    "gremlin_phasenav_spectroscopic_holonomy",
    "gremlin_worker_register", "gremlin_worker_heartbeat", "gremlin_worker_list",
    "gremlin_worker_enqueue", "gremlin_worker_claim", "gremlin_worker_submit",
    "gremlin_worker_result", "gremlin_worker_queue",
})

READ_ONLY_OR_ADVISORY = frozenset({
    "gremlin_status", "gremlin_bestiary", "gremlin_species",
    "gremlin_plan", "gremlin_route", "gremlin_relation_parse", "gremlin_relation_signature",
    "gremlin_web_fetch", "gremlin_web_search", "gremlin_research",
    "gremlin_research_hound_provenance", "gremlin_research_guarded", "gremlin_research_relational",
    "gremlin_collect", "gremlin_prototype",
    "gremlin_phasenav_status", "gremlin_phasenav_reference_sweep", "gremlin_phasenav_threeway",
    "gremlin_phasenav_analog_invariants", "gremlin_phasenav_live_replay",
    "gremlin_phasenav_spectroscopic_holonomy",
    "gremlin_worker_list", "gremlin_worker_result", "gremlin_worker_queue",
    "gremlin_hive_status", "gremlin_hive_head", "gremlin_hive_table",
    "gremlin_hive_history", "gremlin_hive_persisted",
    "gremlin_hive_sync_inventory", "gremlin_hive_sync_manifest",
    "gremlin_hive_consolidation_route",
})


class BridgeMode(str, Enum):
    ADVISORY = "ADVISORY"
    AUTHORIZED_ACTUATION = "AUTHORIZED_ACTUATION"


class GremlinTransport(Protocol):
    def list_tools(self) -> Sequence[str]: ...
    def call_tool(self, name: str, arguments: Mapping[str, Any]) -> Mapping[str, Any]: ...


@dataclass(frozen=True)
class ActuationGrant:
    tool_names: frozenset[str]
    reason: str
    issued_by: str = "USER"

    def __post_init__(self) -> None:
        if not self.reason.strip():
            raise ValueError("authorization reason must be non-empty")


@dataclass(frozen=True)
class CapabilitySnapshot:
    tools: frozenset[str]
    extra_tools: frozenset[str]
    status: Mapping[str, Any]
    bestiary: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "gremlin_repository": GREMLIN_REPOSITORY,
            "gremlin_baseline_sha": GREMLIN_BASELINE_SHA,
            "tool_count": len(self.tools),
            "tools": sorted(self.tools),
            "extra_tools": sorted(self.extra_tools),
            "authority": {
                "cielingo_semantic_authority_preserved": True,
                "gremlin_grants_canon": False,
                "gremlin_grants_noema_writeback": False,
            },
        }


class GremlinFullBridge:
    def __init__(self, transport: GremlinTransport, *, mode: BridgeMode = BridgeMode.ADVISORY):
        self.transport = transport
        self.mode = mode
        self._snapshot: CapabilitySnapshot | None = None

    def discover(self) -> CapabilitySnapshot:
        tools = frozenset(str(x) for x in self.transport.list_tools())
        missing = sorted(REQUIRED_CORE_TOOLS - tools)
        if missing:
            raise RuntimeError(f"incomplete GREMLIN core surface: {missing}")
        status = dict(self.transport.call_tool("gremlin_status", {}))
        bestiary = dict(self.transport.call_tool("gremlin_bestiary", {}))
        if status.get("authority", {}).get("canon_allowed") is not False:
            raise RuntimeError("GREMLIN authority boundary is not fail-closed")
        governance = set(bestiary.get("governance_topology", ()))
        if "RAPHAEL" not in governance:
            raise RuntimeError("RAPHAEL governance surface missing")
        self._snapshot = CapabilitySnapshot(
            tools=tools,
            extra_tools=tools - REQUIRED_CORE_TOOLS,
            status=status,
            bestiary=bestiary,
        )
        return self._snapshot

    @property
    def snapshot(self) -> CapabilitySnapshot:
        if self._snapshot is None:
            return self.discover()
        return self._snapshot

    def dispatch(
        self,
        tool_name: str,
        arguments: Mapping[str, Any],
        *,
        grant: ActuationGrant | None = None,
    ) -> Mapping[str, Any]:
        if tool_name not in self.snapshot.tools:
            raise KeyError(f"GREMLIN tool not present: {tool_name}")
        safe = tool_name in READ_ONLY_OR_ADVISORY
        authorized = (
            self.mode is BridgeMode.AUTHORIZED_ACTUATION
            and grant is not None
            and tool_name in grant.tool_names
        )
        if not safe and not authorized:
            raise PermissionError(f"GREMLIN tool requires explicit actuation grant: {tool_name}")
        return self.transport.call_tool(tool_name, dict(arguments))

    def compile_genomic_project(self, packet: GenomicGrammarPacket) -> dict[str, Any]:
        snap = self.snapshot
        return {
            "schema": "CIELINGO_GREMLIN_GENOMIC_PROJECT_ENVELOPE_V0_1",
            "bridge": snap.to_dict(),
            "task": packet.to_gremlin_task(),
            "recommended_bestiary": [
                "OCTOPUS", "SPIDER", "BAT", "HOUND", "MOLE", "OWL",
                "FOX", "BEAVER", "BELZEBUB", "GREMLIN", "RAPHAEL",
            ],
            "phase_1": {
                "mode": "ADVISORY",
                "tools": [
                    "gremlin_route",
                    "gremlin_research_guarded",
                    "gremlin_research_relational",
                    "gremlin_phasenav_analog_invariants",
                ],
            },
            "actuation": {
                "default": "DENY",
                "requires_explicit_grant": True,
                "ferret_default": "DISABLED",
                "hive_mutation_default": "DISABLED",
            },
        }
