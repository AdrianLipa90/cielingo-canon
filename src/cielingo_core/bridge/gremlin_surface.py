"""Transport-agnostic bridge from CIELingo to a live GREMLIN MCP surface.

The bridge deliberately does not vendor GREMLIN and does not depend on the mcp
package. A caller injects any client object exposing async list_tools() and
call_tool(). This keeps the CIELingo ABI stable while allowing the complete
runtime GREMLIN registry to be discovered dynamically.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable, Mapping

SCHEMA = "CIELINGO_GREMLIN_SURFACE_BRIDGE_V0_1"

MINIMUM_GREMLIN_CORE = frozenset(
    {
        "gremlin_status",
        "gremlin_bestiary",
        "gremlin_species",
        "gremlin_plan",
        "gremlin_route",
        "gremlin_collect",
        "gremlin_synthesize",
        "gremlin_prototype",
    }
)

_MUTATION_TOKENS = frozenset(
    {
        "place",
        "gates",
        "dispute",
        "latch",
        "ingest",
        "apply",
        "register",
        "heartbeat",
        "enqueue",
        "claim",
        "submit",
    }
)


class GremlinConsequence(str, Enum):
    READ_ONLY = "READ_ONLY"
    CONTROLLED_MUTATION = "CONTROLLED_MUTATION"


@dataclass(frozen=True)
class GremlinToolDescriptor:
    name: str
    description: str = ""

    @classmethod
    def from_object(cls, tool: Any) -> "GremlinToolDescriptor":
        if isinstance(tool, Mapping):
            name = tool.get("name")
            description = tool.get("description", "")
        else:
            name = getattr(tool, "name", None)
            description = getattr(tool, "description", "")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("GREMLIN tool descriptor requires a non-empty name")
        return cls(name=name.strip(), description=str(description or ""))


@dataclass(frozen=True)
class GremlinSurfaceSnapshot:
    schema: str
    tool_names: tuple[str, ...]
    missing_core: tuple[str, ...]
    complete_core: bool
    authority: Mapping[str, bool]

    @property
    def tool_count(self) -> int:
        return len(self.tool_names)

    def has(self, name: str) -> bool:
        return name in self.tool_names


def classify_consequence(tool_name: str) -> GremlinConsequence:
    """Conservatively classify whether invoking a tool can mutate GREMLIN state."""
    tokens = {part for part in tool_name.lower().replace("-", "_").split("_") if part}
    if tokens & _MUTATION_TOKENS:
        return GremlinConsequence.CONTROLLED_MUTATION
    return GremlinConsequence.READ_ONLY


class GremlinSurfaceBridge:
    """Discover and gate the complete live GREMLIN tool registry.

    "Complete" here means every tool advertised by the connected MCP server is
    preserved in the snapshot. CIELingo does not maintain a copied allow-list,
    so newly added GREMLIN/Bestiary tools become visible automatically.

    The bridge never grants canon, NOEMA writeback, or production-runtime
    authority. Known mutation-shaped calls require explicit authorization.
    """

    def __init__(self, required_core: Iterable[str] = MINIMUM_GREMLIN_CORE):
        core = {str(name).strip() for name in required_core if str(name).strip()}
        if not core:
            raise ValueError("required_core must not be empty")
        self._required_core = frozenset(core)
        self._snapshot: GremlinSurfaceSnapshot | None = None

    @property
    def snapshot(self) -> GremlinSurfaceSnapshot | None:
        return self._snapshot

    def discover(self, tools: Iterable[Any]) -> GremlinSurfaceSnapshot:
        descriptors = [GremlinToolDescriptor.from_object(tool) for tool in tools]
        names = tuple(sorted({tool.name for tool in descriptors}))
        if not names:
            raise ValueError("GREMLIN surface advertised no tools")
        missing = tuple(sorted(self._required_core - set(names)))
        self._snapshot = GremlinSurfaceSnapshot(
            schema=SCHEMA,
            tool_names=names,
            missing_core=missing,
            complete_core=not missing,
            authority={
                "canon_allowed": False,
                "noema_writeback_allowed": False,
                "production_runtime_write": False,
            },
        )
        return self._snapshot

    async def discover_from_client(self, client: Any) -> GremlinSurfaceSnapshot:
        listed = await client.list_tools()
        tools = getattr(listed, "tools", listed)
        return self.discover(tools)

    def require_ready(self) -> GremlinSurfaceSnapshot:
        if self._snapshot is None:
            raise RuntimeError("GREMLIN surface has not been discovered")
        if not self._snapshot.complete_core:
            missing = ", ".join(self._snapshot.missing_core)
            raise RuntimeError(f"GREMLIN core surface incomplete: {missing}")
        return self._snapshot

    def admit_call(self, tool_name: str, *, explicit_authorization: bool = False) -> None:
        snapshot = self.require_ready()
        if tool_name not in snapshot.tool_names:
            raise ValueError(f"tool is not present on discovered GREMLIN surface: {tool_name}")
        if (
            classify_consequence(tool_name) is GremlinConsequence.CONTROLLED_MUTATION
            and not explicit_authorization
        ):
            raise PermissionError(
                f"GREMLIN mutation-shaped tool requires explicit authorization: {tool_name}"
            )

    async def invoke(
        self,
        client: Any,
        tool_name: str,
        arguments: Mapping[str, Any] | None = None,
        *,
        explicit_authorization: bool = False,
    ) -> Any:
        self.admit_call(tool_name, explicit_authorization=explicit_authorization)
        return await client.call_tool(tool_name, dict(arguments or {}))

    def manifest(self) -> dict[str, Any]:
        snapshot = self.require_ready()
        return {
            "schema": snapshot.schema,
            "tool_count": snapshot.tool_count,
            "tools": list(snapshot.tool_names),
            "missing_core": list(snapshot.missing_core),
            "complete_core": snapshot.complete_core,
            "authority": dict(snapshot.authority),
            "discovery_mode": "DYNAMIC_FULL_MCP_SURFACE",
            "vendored_gremlin": False,
        }
