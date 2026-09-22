"""Dynamic, fail-closed bridge from CIELingo into the GREMLIN MCP surface.

The bridge deliberately does not hard-code the complete GREMLIN registry. It
requires a small invariant core, discovers every additional tool exposed by the
connected GREMLIN runtime, and preserves CIELingo's authority boundary.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import json
from typing import Any, Mapping, Protocol, Sequence

SCHEMA = "CIELINGO_GREMLIN_FULL_BRIDGE_V0_1"

REQUIRED_CORE_TOOLS = frozenset({
    "gremlin_status", "gremlin_bestiary", "gremlin_species", "gremlin_plan",
    "gremlin_route", "gremlin_auto_fanout", "gremlin_collect",
    "gremlin_synthesize", "gremlin_prototype",
})

READ_ONLY_EXACT = frozenset({
    "gremlin_product_status", "gremlin_license_status", "gremlin_status",
    "gremlin_bestiary", "gremlin_species", "gremlin_plan", "gremlin_route",
    "gremlin_relation_parse", "gremlin_relation_signature", "gremlin_collect",
    "gremlin_prototype", "gremlin_phasenav_status",
    "gremlin_phasenav_reference_sweep", "gremlin_phasenav_threeway",
    "gremlin_phasenav_analog_invariants", "gremlin_phasenav_live_replay",
    "gremlin_phasenav_spectroscopic_holonomy", "gremlin_worker_list",
    "gremlin_worker_result", "gremlin_worker_queue", "gremlin_web_fetch",
    "gremlin_web_search", "gremlin_research", "gremlin_research_execute",
    "gremlin_research_hound_provenance", "gremlin_research_guarded",
    "gremlin_research_relational",
})

MUTATING_EXACT = frozenset({
    "gremlin_auto_fanout", "gremlin_fanout", "gremlin_synthesize",
    "gremlin_worker_register", "gremlin_worker_heartbeat",
    "gremlin_worker_enqueue", "gremlin_worker_claim", "gremlin_worker_submit",
    "gremlin_hive_place", "gremlin_hive_gates", "gremlin_hive_dispute",
    "gremlin_hive_latch", "gremlin_hive_exchange_ingest",
    "gremlin_hive_exchange_bundle_ingest", "gremlin_hive_sync_apply",
    "gremlin_hive_research_execute",
})

MUTATING_PREFIXES = ("gremlin_ferret_",)

READ_ONLY_PREFIXES = (
    "gremlin_hive_status", "gremlin_hive_head", "gremlin_hive_table",
    "gremlin_hive_history", "gremlin_hive_persisted",
    "gremlin_hive_sync_inventory", "gremlin_hive_sync_manifest",
    "gremlin_hive_sync_delta", "gremlin_hive_consolidation_route",
)


class ConsequenceClass(str, Enum):
    READ_ONLY = "READ_ONLY"
    MUTATING = "MUTATING"
    GOVERNED = "GOVERNED"


class GremlinTransport(Protocol):
    async def list_tools(self) -> Sequence[Any]: ...
    async def call_tool(self, name: str, arguments: Mapping[str, Any]) -> Any: ...


@dataclass(frozen=True)
class GremlinAuthorization:
    allow_mutation: bool = False
    allowed_tools: frozenset[str] = field(default_factory=frozenset)

    def permits(self, tool_name: str) -> bool:
        return self.allow_mutation and tool_name in self.allowed_tools


@dataclass(frozen=True)
class GremlinCapabilitySnapshot:
    schema: str
    tools: tuple[str, ...]
    required_core_present: bool
    missing_core_tools: tuple[str, ...]
    authority: Mapping[str, bool]

    @property
    def tool_count(self) -> int:
        return len(self.tools)


class MCPClientTransport:
    """Adapter for an already-open MCP client."""

    def __init__(self, client: Any):
        self.client = client

    async def list_tools(self) -> Sequence[Any]:
        listed = await self.client.list_tools()
        return tuple(getattr(listed, "tools", listed))

    async def call_tool(self, name: str, arguments: Mapping[str, Any]) -> Any:
        result = await self.client.call_tool(name, dict(arguments))
        if getattr(result, "is_error", False):
            raise RuntimeError(f"GREMLIN MCP tool call failed: {name}")
        structured = getattr(result, "structured_content", None)
        if isinstance(structured, Mapping):
            return dict(structured)
        for block in getattr(result, "content", ()):
            text = getattr(block, "text", None)
            if not isinstance(text, str):
                continue
            try:
                value = json.loads(text)
            except json.JSONDecodeError:
                continue
            if isinstance(value, Mapping):
                return dict(value)
        raise RuntimeError(f"GREMLIN MCP tool result is not a structured mapping: {name}")


def _tool_name(tool: Any) -> str:
    if isinstance(tool, str):
        name = tool
    elif isinstance(tool, Mapping):
        name = tool.get("name")
    else:
        name = getattr(tool, "name", None)
    if not isinstance(name, str) or not name.strip():
        raise ValueError("GREMLIN tool registry contains an invalid tool name")
    return name.strip()


def classify_consequence(tool_name: str) -> ConsequenceClass:
    if tool_name in MUTATING_EXACT or tool_name.startswith(MUTATING_PREFIXES):
        return ConsequenceClass.MUTATING
    if tool_name in READ_ONLY_EXACT or tool_name.startswith(READ_ONLY_PREFIXES):
        return ConsequenceClass.READ_ONLY
    return ConsequenceClass.GOVERNED


class GremlinFullBridge:
    def __init__(self, transport: GremlinTransport):
        self.transport = transport
        self._snapshot: GremlinCapabilitySnapshot | None = None

    async def discover(self) -> GremlinCapabilitySnapshot:
        names = tuple(sorted({_tool_name(tool) for tool in await self.transport.list_tools()}))
        missing = tuple(sorted(REQUIRED_CORE_TOOLS.difference(names)))
        snapshot = GremlinCapabilitySnapshot(
            schema=SCHEMA,
            tools=names,
            required_core_present=not missing,
            missing_core_tools=missing,
            authority={
                "cielingo_canon_allowed": False,
                "noema_writeback_allowed": False,
                "production_runtime_write": False,
                "gremlin_output_is_advisory": True,
            },
        )
        self._snapshot = snapshot
        if missing:
            raise RuntimeError(
                "GREMLIN capability surface is incomplete; missing core tools: "
                + ", ".join(missing)
            )
        return snapshot

    @property
    def snapshot(self) -> GremlinCapabilitySnapshot:
        if self._snapshot is None:
            raise RuntimeError("GREMLIN surface has not been discovered")
        return self._snapshot

    async def invoke(
        self,
        tool_name: str,
        arguments: Mapping[str, Any] | None = None,
        *,
        authorization: GremlinAuthorization | None = None,
    ) -> dict[str, Any]:
        if self._snapshot is None:
            await self.discover()
        if tool_name not in self.snapshot.tools:
            raise KeyError(f"GREMLIN tool not advertised by connected runtime: {tool_name}")

        consequence = classify_consequence(tool_name)
        if consequence is not ConsequenceClass.READ_ONLY:
            if authorization is None or not authorization.permits(tool_name):
                raise PermissionError(
                    f"{tool_name} is {consequence.value}; explicit per-tool mutation authorization required"
                )

        result = await self.transport.call_tool(tool_name, arguments or {})
        return {
            "schema": SCHEMA,
            "tool": tool_name,
            "consequence_class": consequence.value,
            "result": result,
            "authority": {
                "advisory_only": True,
                "canon_allowed": False,
                "noema_writeback_allowed": False,
            },
        }
