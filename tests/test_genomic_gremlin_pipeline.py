from __future__ import annotations

import asyncio

import pytest

from cielingo_core.bridge.gremlin_full_bridge import (
    GremlinAuthorization,
    GremlinFullBridge,
    REQUIRED_CORE_TOOLS,
)
from cielingo_core.genomics.grammar import GenomicLevel, GenomicUnit
from cielingo_core.genomics.gremlin_pipeline import (
    FULL_AUDIT_SPECIALISTS,
    GenomicGremlinPipeline,
    GenomicPipelineMode,
)


class FakeTransport:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []
        self.tools = set(REQUIRED_CORE_TOOLS) | {"gremlin_fanout"}

    async def list_tools(self):
        return [{"name": name} for name in self.tools]

    async def call_tool(self, name, arguments):
        self.calls.append((name, dict(arguments)))
        value = self.responses[name]
        if callable(value):
            value = value(arguments)
        return value


def run(coro):
    return asyncio.run(coro)


def unit():
    return GenomicUnit("k1", GenomicLevel.KAKU, {"symbol": "A", "position_bp": 0})


def mutation_auth(*tools):
    return GremlinAuthorization(True, frozenset(tools))


def test_preview_route_is_read_only_and_carries_relational_signature():
    transport = FakeTransport({"gremlin_route": {"route_mask": ["SPIDER", "OWL"]}})
    pipeline = GenomicGremlinPipeline(GremlinFullBridge(transport))
    out = run(pipeline.preview_route(unit(), "test spacing-phase grammar"))
    assert out["consequence_class"] == "READ_ONLY"
    payload = transport.calls[0][1]["payload"]
    assert len(payload["semantic_signature"]) == 64
    assert payload["canon_allowed"] is False


def test_auto_route_requires_explicit_local_mutation_grant():
    transport = FakeTransport({"gremlin_auto_fanout": {"tasks": [{"task_id": "t1"}]}})
    pipeline = GenomicGremlinPipeline(GremlinFullBridge(transport))
    with pytest.raises(PermissionError):
        run(pipeline.dispatch(unit(), "test", authorization=mutation_auth()))
    dispatched = run(
        pipeline.dispatch(
            unit(),
            "test",
            authorization=mutation_auth("gremlin_auto_fanout"),
            request_id="g1",
        )
    )
    assert dispatched.task_ids == ("t1",)


def test_full_audit_uses_exact_gremlin_specialist_contract():
    transport = FakeTransport({
        "gremlin_fanout": lambda args: {
            "tasks": [{"task_id": f"t-{species}"} for species in args["species"]]
        }
    })
    pipeline = GenomicGremlinPipeline(GremlinFullBridge(transport))
    dispatched = run(
        pipeline.dispatch(
            unit(),
            "full audit",
            mode=GenomicPipelineMode.FULL_AUDIT,
            authorization=mutation_auth("gremlin_fanout"),
        )
    )
    assert len(dispatched.task_ids) == 7
    assert transport.calls[-1][1]["species"] == list(FULL_AUDIT_SPECIALISTS)


def test_synthesis_waits_until_all_specialists_are_complete():
    transport = FakeTransport({"gremlin_collect": {"complete": False, "done_count": 1}})
    pipeline = GenomicGremlinPipeline(GremlinFullBridge(transport))
    out = run(
        pipeline.synthesize_if_complete(
            ["t1", "t2"],
            authorization=mutation_auth("gremlin_synthesize"),
        )
    )
    assert out["status"] == "WAITING_SPECIALISTS"
    assert [name for name, _ in transport.calls] == ["gremlin_collect"]


def test_synthesis_queues_belzebub_only_after_complete_collection():
    transport = FakeTransport({
        "gremlin_collect": {"complete": True, "done_count": 2},
        "gremlin_synthesize": {"status": "BELZEBUB_QUEUED", "task_id": "bz1"},
    })
    pipeline = GenomicGremlinPipeline(GremlinFullBridge(transport))
    out = run(
        pipeline.synthesize_if_complete(
            ["t1", "t2"],
            authorization=mutation_auth("gremlin_synthesize"),
            request_id="g2",
        )
    )
    assert out["status"] == "SYNTHESIS_QUEUED"
    assert out["synthesis"]["status"] == "BELZEBUB_QUEUED"
