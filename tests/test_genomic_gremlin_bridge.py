from __future__ import annotations

from math import isclose, pi

import pytest

from cielingo_core.bridge.gremlin_full_bridge import (
    ActuationGrant, BridgeMode, GremlinFullBridge, REQUIRED_CORE_TOOLS,
)
from cielingo_core.lingophysics.genomic_grammar import (
    EvidenceClass, GenomicGrammarPacket, GenomicNode, GenomicRelation, GenomicTier,
)


class FakeTransport:
    def __init__(self, tools=None):
        self.tools = set(tools or REQUIRED_CORE_TOOLS)
        self.tools.update({"gremlin_hive_status", "gremlin_hive_place", "gremlin_ferret_execute"})
        self.calls = []

    def list_tools(self):
        return sorted(self.tools)

    def call_tool(self, name, arguments):
        self.calls.append((name, dict(arguments)))
        if name == "gremlin_status":
            return {"authority": {"canon_allowed": False}}
        if name == "gremlin_bestiary":
            return {"governance_topology": ["GREMLIN", "RAPHAEL"]}
        return {"tool": name, "arguments": dict(arguments)}


def test_phase_geometry_is_periodic():
    a = GenomicRelation("m1", "m2", spacing_bp=10.5)
    b = GenomicRelation("m1", "m2", spacing_bp=5.25)
    assert isclose(a.phase_rad, 0.0, abs_tol=1e-12)
    assert isclose(b.phase_rad, pi, abs_tol=1e-12)


def test_packet_preserves_cielingo_hierarchy_and_epistemic_boundary():
    nodes = (
        GenomicNode("k1", GenomicTier.KAKU, "base/relation primitive", evidence=EvidenceClass.OBSERVED),
        GenomicNode("r1", GenomicTier.RADICAL, "motif", evidence=EvidenceClass.HYPOTHESIS),
    )
    packet = GenomicGrammarPacket(
        "enhancer-demo",
        nodes,
        (GenomicRelation("k1", "r1", spacing_bp=7.0),),
    )
    task = packet.to_gremlin_task()
    assert task["hierarchy"] == ["KAKU", "RADYKAŁ", "KONCEPT", "ZDANIE", "AKAPIT", "ROZDZIAŁ", "KSIĄŻKA"]
    assert task["guardrails"]["claim_phase_code_proven"] is False


def test_full_surface_discovery_keeps_extra_gremlin_tools():
    bridge = GremlinFullBridge(FakeTransport())
    snap = bridge.discover()
    assert "gremlin_hive_place" in snap.extra_tools
    assert "gremlin_ferret_execute" in snap.extra_tools
    assert len(REQUIRED_CORE_TOOLS) == 33


def test_incomplete_core_fails_closed():
    tools = set(REQUIRED_CORE_TOOLS)
    tools.remove("gremlin_route")
    with pytest.raises(RuntimeError, match="incomplete GREMLIN core surface"):
        GremlinFullBridge(FakeTransport(tools)).discover()


def test_mutation_requires_explicit_grant():
    transport = FakeTransport()
    bridge = GremlinFullBridge(transport)
    bridge.discover()
    with pytest.raises(PermissionError):
        bridge.dispatch("gremlin_hive_place", {"subject_id": "x"})


def test_authorized_actuation_is_narrowly_scoped():
    transport = FakeTransport()
    bridge = GremlinFullBridge(transport, mode=BridgeMode.AUTHORIZED_ACTUATION)
    bridge.discover()
    grant = ActuationGrant(frozenset({"gremlin_hive_place"}), reason="test-only explicit grant")
    out = bridge.dispatch("gremlin_hive_place", {"subject_id": "x"}, grant=grant)
    assert out["tool"] == "gremlin_hive_place"
    with pytest.raises(PermissionError):
        bridge.dispatch("gremlin_ferret_execute", {}, grant=grant)


def test_compile_genomic_project_routes_to_bestiary_without_claiming_authority():
    packet = GenomicGrammarPacket(
        "demo",
        (
            GenomicNode("m1", GenomicTier.RADICAL, "motif A"),
            GenomicNode("m2", GenomicTier.RADICAL, "motif B"),
        ),
        (GenomicRelation("m1", "m2", spacing_bp=10.5),),
    )
    envelope = GremlinFullBridge(FakeTransport()).compile_genomic_project(packet)
    assert "SPIDER" in envelope["recommended_bestiary"]
    assert "RAPHAEL" in envelope["recommended_bestiary"]
    assert envelope["actuation"]["default"] == "DENY"
