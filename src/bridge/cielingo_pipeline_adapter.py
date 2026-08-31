"""CIELingo pipeline adapter — connects CielEngine step() output to CIELingoBridge.

Sits between CielEngine.step() and LanguageBackend.generate_reply().

The adapter:
  1. Receives the raw Dict[str, Any] from CielEngine.step()
  2. Passes relevant fields to CIELingoBridge.process()
  3. Enriches the state dict with 'cielingo' key containing loop_state, style, notes
  4. If needed, also populates 'lingo_frame' for backward compat with build_semantic_speech_context()

Usage:
    adapter = CIELingoPipelineAdapter(repo_root="/path/to/repo")
    enriched = adapter.enrich(engine_state, turn_id="turn_001", intention_text="hello")
    # enriched now has "cielingo" key with bridge output
"""

from __future__ import annotations
from hashlib import sha256
from typing import Any


def _extract_intention(engine_state: dict[str, Any], intention_text: str) -> str:
    """Extract or infer intention text from engine state."""
    if intention_text:
        return intention_text
    return engine_state.get("text", engine_state.get("cqcl_input", ""))


def _detect_intention_type(engine_state: dict[str, Any]) -> str:
    """Map engine state to an intention type string."""
    ethical_score = engine_state.get("ethical_score", 0.5)
    dominant_emotion = engine_state.get("dominant_emotion", "neutral")
    if ethical_score < 0.2:
        return "command"
    if dominant_emotion in ("awe", "curiosity"):
        return "query"
    if dominant_emotion in ("doubt", "confusion"):
        return "verify"
    return "query"


def _extract_emotion(engine_state: dict[str, Any]) -> dict[str, float] | None:
    """Extract emotion vector from engine state."""
    ep = engine_state.get("emotional_profile")
    if isinstance(ep, dict):
        return ep
    emotion = engine_state.get("emotion_state")
    if isinstance(emotion, dict):
        return emotion
    mood = engine_state.get("mood")
    if isinstance(mood, (int, float)):
        return {"mood": float(mood)}
    return None


def _extract_collatz_phase(engine_state: dict[str, Any]) -> float | None:
    """Extract Collatz phase value from engine state."""
    cr = engine_state.get("collatz_runtime")
    if isinstance(cr, dict):
        phase = cr.get("phase")
        if isinstance(phase, dict):
            return phase.get("R_H")
        if isinstance(phase, (int, float)):
            return float(phase)
    return None


def _extract_ethics(engine_state: dict[str, Any]) -> list[str] | None:
    """Extract ethics flags from engine state."""
    score = engine_state.get("ethical_score", 0.5)
    flags: list[str] = []
    if score > 0.7:
        flags.append("high_ethics")
    elif score > 0.3:
        flags.append("moderate_ethics")
    else:
        flags.append("low_ethics")
    if engine_state.get("memorised"):
        flags.append("memory_promoted")
    return flags if flags else None


def _extract_memory(engine_state: dict[str, Any]) -> dict[str, Any] | None:
    """Extract memory state from engine state."""
    mem: dict[str, Any] = {}
    if engine_state.get("memorised"):
        mem["memorised"] = engine_state["memorised"]
    if engine_state.get("euler_bridge"):
        mem["euler"] = engine_state["euler_bridge"]
    return mem if mem else None


class CIELingoPipelineAdapter:
    """Adapter that enriches CielEngine step() output with CIELingo bridge state."""

    def __init__(self, repo_root: str = "."):
        # Import the heavy bridge only when an adapter instance is constructed.
        # Importing this module alone stays a narrow, provenance-verifiable bind.
        from bridge.cielingo_bridge import CIELingoBridge

        self.bridge = CIELingoBridge(repo_root=repo_root)
        self.processed_count = 0

    def enrich(
        self,
        engine_state: dict[str, Any],
        turn_id: str | None = None,
        intention_text: str = "",
    ) -> dict[str, Any]:
        """Enrich engine state dict with CIELingo bridge output.

        Args:
            engine_state: Raw output from CielEngine.step()
            turn_id: Optional turn identifier (auto-generated if missing)
            intention_text: The original user/text input

        Returns:
            Same dict with added "cielingo" key
        """
        if turn_id is None:
            seed = engine_state.get("collatz_runtime", {}).get("seed", str(self.processed_count))
            turn_id = f"omega_{sha256(str(seed).encode()).hexdigest()[:12]}"

        text = _extract_intention(engine_state, intention_text)
        itype = _detect_intention_type(engine_state)
        emotion = _extract_emotion(engine_state)
        phase = _extract_collatz_phase(engine_state)
        ethics = _extract_ethics(engine_state)
        memory = _extract_memory(engine_state)

        # Run through CIELingo bridge
        bridge_state = self.bridge.process(
            engine_turn_id=turn_id,
            intention_text=text,
            intention_type=itype,
            engine_emotion=emotion,
            collatz_phase=phase,
            ethics_flags=ethics,
            memory_state=memory,
        )
        self.processed_count += 1

        # Build CIELingo output
        cielo_out = {
            "turn_id": turn_id,
            "loop_state": bridge_state.loop_state.value,
            "style": bridge_state.style.value,
            "intention_type": bridge_state.intention.intention_type.value if bridge_state.intention else None,
            "language": type(bridge_state.regional_solver).__name__.replace("RegionalSolver", "").lower() if bridge_state.regional_solver else "pl",
            "immune_pressure": bridge_state.immune_signal.pressure_type.value if bridge_state.immune_signal else None,
            "notes": bridge_state.notes,
        }
        if bridge_state.response_draft:
            cielo_out["draft_id"] = bridge_state.response_draft.expressive_id

        # Enrich the state dict
        enriched = dict(engine_state)
        enriched["cielingo"] = cielo_out

        # Also populate lingo_frame for backward compat with build_semantic_speech_context()
        enriched["lingo_frame"] = {
            "summary": f"CIELingo|loop={cielo_out['loop_state']}|style={cielo_out['style']}|lang={cielo_out['language']}",
            "loop_state": cielo_out["loop_state"],
            "style": cielo_out["style"],
            "intention_type": cielo_out["intention_type"],
            "notes": cielo_out["notes"],
        }

        return enriched

    def summary(self) -> dict[str, Any]:
        return {
            "processed_count": self.processed_count,
            "bridge_turns": len(self.bridge.turns),
        }
