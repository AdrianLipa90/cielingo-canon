from __future__ import annotations

import asyncio
import pytest

from cielingo_core.bridge.gremlin_full_bridge import (
    GremlinAuthorization, GremlinFullBridge, REQUIRED_CORE_TOOLS,
)


class FakeTransport:
    def __init__(self, tools):
        self.tools = list(tools)
        self.calls = []

    async def list_tools(self):
        return [{"name": name} for name in self.tools]

    async def call_tool(self, name, arguments):
        self.calls.append((name, dict(arguments)))
        return {"ok": True, "name": name}


def run(coro):
    return asyncio.run(coro)


def test_discovers_full_dynamic_surface_without_truncating_extensions():
    tools = set(REQUIRED_CORE_TOOLS) | {
        "gremlin_hive_status", "gremlin_hive_place", "gremlin_raphael_future_extension",
    }
    bridge = GremlinFullBridge(FakeTransport(tools))
    snapshot = run(bridge.discover())
    assert snapshot.required_core_present is True
    assert set(snapshot.tools) == tools
    assert snapshot.authority["gremlin_output_is_advisory"] is True


def test_missing_invariant_core_fails_closed():
    tools = set(REQUIRED_CORE_TOOLS) - {"gremlin_route"}
    bridge = GremlinFullBridge(FakeTransport(tools))
    with pytest.raises(RuntimeError, match="gremlin_route"):
        run(bridge.discover())


def test_read_only_tool_is_callable_without_mutation_grant():
    bridge = GremlinFullBridge(FakeTransport(REQUIRED_CORE_TOOLS))
    out = run(bridge.invoke("gremlin_plan", {"route_counts": {"SPIDER": 1}}))
    assert out["consequence_class"] == "READ_ONLY"
    assert out["authority"]["canon_allowed"] is False


def test_mutating_and_unknown_tools_require_explicit_per_tool_grant():
    tools = set(REQUIRED_CORE_TOOLS) | {
        "gremlin_hive_place", "gremlin_fanout", "gremlin_product_status",
        "gremlin_raphael_future_extension",
    }
    bridge = GremlinFullBridge(FakeTransport(tools))
    run(bridge.discover())

    for tool, args in [
        ("gremlin_hive_place", {"subject_id": "x"}),
        ("gremlin_auto_fanout", {"payload": {}}),
        ("gremlin_fanout", {"payload": {}, "species": ["SPIDER"]}),
        ("gremlin_raphael_future_extension", {}),
    ]:
        with pytest.raises(PermissionError):
            run(bridge.invoke(tool, args))

    status = run(bridge.invoke("gremlin_product_status", {}))
    assert status["consequence_class"] == "READ_ONLY"

    auth = GremlinAuthorization(True, frozenset({"gremlin_hive_place"}))
    out = run(bridge.invoke("gremlin_hive_place", {"subject_id": "x"}, authorization=auth))
    assert out["consequence_class"] == "MUTATING"


def test_mcp_client_transport_normalizes_structured_content():
    from cielingo_core.bridge.gremlin_full_bridge import MCPClientTransport

    class Result:
        is_error = False
        structured_content = {"status": "ok"}
        content = ()

    class Client:
        async def call_tool(self, name, arguments):
            return Result()

    transport = MCPClientTransport(Client())
    assert run(transport.call_tool("gremlin_status", {})) == {"status": "ok"}
