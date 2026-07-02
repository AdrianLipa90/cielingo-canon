"""Tests for CIELingo bridge and pipeline adapter."""
from __future__ import annotations
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bridge.cielingo_bridge import CIELingoBridge, detect_language, CielingoBridgeState
from bridge.cielingo_pipeline_adapter import CIELingoPipelineAdapter


CANON_SRC = str(Path(__file__).resolve().parent.parent)


def test_detect_language():
    assert detect_language("polish text") == "pl"
    assert detect_language("english text") == "en"
    assert detect_language("japanese content") == "ja"
    assert detect_language("default intent") == "pl"


def test_bridge_create():
    bridge = CIELingoBridge(repo_root=CANON_SRC)
    assert bridge is not None
    assert len(bridge.turns) == 0


def test_bridge_process_detault():
    bridge = CIELingoBridge(repo_root=CANON_SRC)
    result = bridge.process(
        engine_turn_id="test_001",
        intention_text="hello world",
        intention_type="query",
    )
    assert isinstance(result, CielingoBridgeState)
    assert result.engine_turn_id == "test_001"
    assert result.loop_state.value == "open"
    assert result.style.value == "plain"
    assert result.response_draft is not None


def test_bridge_process_with_emotion():
    bridge = CIELingoBridge(repo_root=CANON_SRC)
    result = bridge.process(
        engine_turn_id="test_002",
        intention_text="formal request",
        intention_type="formal",
        engine_emotion={"awe": 0.9},
    )
    assert result.immune_signal is not None
    assert result.immune_signal.pressure_detected


def test_bridge_process_with_ethics():
    bridge = CIELingoBridge(repo_root=CANON_SRC)
    result = bridge.process(
        engine_turn_id="test_003",
        intention_text="do something",
        intention_type="command",
        ethics_flags=["no_harm"],
        collatz_phase=0.9,
    )
    assert result.style.value == "relational_formal"
    assert len(result.notes) > 0


def test_bridge_multiple_turns():
    bridge = CIELingoBridge(repo_root=CANON_SRC)
    bridge.process("t1", "first", "query")
    bridge.process("t2", "second", "command")
    assert len(bridge.turns) == 2
    assert bridge.turns[0].engine_turn_id == "t1"
    assert bridge.turns[1].engine_turn_id == "t2"


def test_adapter_create():
    adapter = CIELingoPipelineAdapter(repo_root=CANON_SRC)
    assert adapter is not None
    assert adapter.processed_count == 0


def test_adapter_enrich():
    adapter = CIELingoPipelineAdapter(repo_root=CANON_SRC)
    engine_state = {
        "intention_vector": [0.1] * 12,
        "emotional_profile": {"curiosity": 0.8},
        "dominant_emotion": "curiosity",
        "mood": 0.7,
        "ethical_score": 0.6,
        "collatz_runtime": {"seed": 42, "phase": {"R_H": 0.3}},
        "status": "ok",
    }
    enriched = adapter.enrich(engine_state, turn_id="omega_test", intention_text="test query")
    assert "cielingo" in enriched
    assert enriched["cielingo"]["loop_state"] == "open"
    assert enriched["cielingo"]["intention_type"] == "ask"
    assert "lingo_frame" in enriched
    assert "CIELingo|loop=" in enriched["lingo_frame"]["summary"]


def test_adapter_enrich_missing_fields():
    adapter = CIELingoPipelineAdapter(repo_root=CANON_SRC)
    engine_state = {"dominant_emotion": "neutral", "ethical_score": 0.8}
    enriched = adapter.enrich(engine_state)
    assert "cielingo" in enriched
    assert enriched["cielingo"]["loop_state"] == "open"


def test_adapter_multiple():
    adapter = CIELingoPipelineAdapter(repo_root=CANON_SRC)
    adapter.enrich({"ethical_score": 0.5, "dominant_emotion": "neutral"})
    adapter.enrich({"ethical_score": 0.5, "dominant_emotion": "neutral"})
    assert adapter.processed_count == 2


if __name__ == "__main__":
    tests = [
        test_detect_language,
        test_bridge_create,
        test_bridge_process_detault,
        test_bridge_process_with_emotion,
        test_bridge_process_with_ethics,
        test_bridge_multiple_turns,
        test_adapter_create,
        test_adapter_enrich,
        test_adapter_enrich_missing_fields,
        test_adapter_multiple,
    ]
    passed = 0
    failed = []
    for t in tests:
        try:
            t()
            print(f"  ✓ {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"  ✗ {t.__name__}: {e}")
            failed.append(t.__name__)
    print(f"\n{passed}/{len(tests)} passed")
    if failed:
        print(f"Failed: {failed}")
