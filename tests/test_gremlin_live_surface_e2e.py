from __future__ import annotations

import os

import pytest

from cielingo_core.bridge.gremlin_full_bridge import GremlinFullBridge, REQUIRED_CORE_TOOLS
from cielingo_core.bridge.gremlin_stdio_transport import GremlinStdioTransport


pytestmark = pytest.mark.skipif(
    os.environ.get("CIELINGO_GREMLIN_E2E") != "1",
    reason="real GREMLIN MCP E2E is enabled only in the dedicated CI job",
)


def test_real_server_with_hive_full_surface_and_fail_closed_actuation(tmp_path) -> None:
    env = {
        "GREMLIN_MCP_STATE_PATH": str(tmp_path / "worker.sqlite3"),
        "GREMLIN_HIVE_STATE_PATH": str(tmp_path / "hive.sqlite3"),
    }
    transport = GremlinStdioTransport(env=env)
    bridge = GremlinFullBridge(transport)

    snapshot = bridge.discover()

    assert REQUIRED_CORE_TOOLS <= snapshot.tools
    assert len(snapshot.tools) > len(REQUIRED_CORE_TOOLS)
    assert "gremlin_hive_status" in snapshot.extra_tools
    assert "gremlin_hive_place" in snapshot.extra_tools
    assert snapshot.status["authority"]["canon_allowed"] is False
    assert "RAPHAEL" in set(snapshot.bestiary["governance_topology"])

    hive = bridge.dispatch("gremlin_hive_status", {})
    assert hive["principal_boundary"]["bestiary_species_authority"] is False
    assert hive["memory_information_exchange"]["automatic_latch"] is False

    with pytest.raises(PermissionError, match="explicit actuation grant"):
        bridge.dispatch(
            "gremlin_hive_place",
            {
                "subject_id": "cielingo-genomic-e2e",
                "payload": {"status": "must-not-be-written"},
                "priority": 0.5,
                "semantic_key": "genomic-e2e",
                "relation_phase": 0.0,
            },
        )
