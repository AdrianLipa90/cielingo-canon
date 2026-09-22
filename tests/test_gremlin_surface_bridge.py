from __future__ import annotations

import asyncio

import pytest

from cielingo_core.bridge.gremlin_surface import (
    GremlinConsequence,
    GremlinSurfaceBridge,
    MINIMUM_GREMLIN_CORE,
    classify_consequence,
)


class Tool:
    def __init__(self, name: str):
        self.name = name
        self.description = name


class Listing:
    def __init__(self, tools):
        self.tools = tools


class FakeClient:
    def __init__(self, names):
        self.names = names
        self.calls = []

    async def list_tools(self):
        return Listing([Tool(name) for name in self.names])

    async def call_tool(self, name, arguments):
        self.calls.append((name, arguments))
        return {"name": name, "arguments": arguments}


def test_dynamic_surface_preserves_every_advertised_tool() -> None:
    names = set(MINIMUM_GREMLIN_CORE) | {
        "gremlin_hive_status",
        "gremlin_hive_place",
        "gremlin_raphael_review",
        "gremlin_future_species_tool",
    }
    bridge = GremlinSurfaceBridge()
    snapshot = bridge.discover(Tool(name) for name in names)

    assert snapshot.complete_core
    assert set(snapshot.tool_names) == names
    assert bridge.manifest()["discovery_mode"] == "DYNAMIC_FULL_MCP_SURFACE"
    assert bridge.manifest()["authority"]["canon_allowed"] is False


def test_incomplete_gremlin_core_fails_closed() -> None:
    bridge = GremlinSurfaceBridge()
    bridge.discover([Tool("gremlin_status")])
    with pytest.raises(RuntimeError, match="core surface incomplete"):
        bridge.require_ready()


def test_mutation_classification_is_conservative() -> None:
    assert classify_consequence("gremlin_hive_place") is GremlinConsequence.CONTROLLED_MUTATION
    assert classify_consequence("gremlin_worker_enqueue") is GremlinConsequence.CONTROLLED_MUTATION
    assert classify_consequence("gremlin_status") is GremlinConsequence.READ_ONLY


def test_mutation_requires_explicit_authorization() -> None:
    names = set(MINIMUM_GREMLIN_CORE) | {"gremlin_hive_place"}
    bridge = GremlinSurfaceBridge()
    bridge.discover(Tool(name) for name in names)

    with pytest.raises(PermissionError, match="explicit authorization"):
        bridge.admit_call("gremlin_hive_place")

    bridge.admit_call("gremlin_hive_place", explicit_authorization=True)


def test_async_client_discovery_and_invocation() -> None:
    names = set(MINIMUM_GREMLIN_CORE) | {"gremlin_hive_status"}
    client = FakeClient(names)
    bridge = GremlinSurfaceBridge()

    async def exercise():
        snapshot = await bridge.discover_from_client(client)
        assert snapshot.complete_core
        result = await bridge.invoke(client, "gremlin_hive_status", {})
        assert result["name"] == "gremlin_hive_status"

    asyncio.run(exercise())
