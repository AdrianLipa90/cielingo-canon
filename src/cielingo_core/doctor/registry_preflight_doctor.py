from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, Any

@dataclass(frozen=True)
class RegistryPreflightInput:
    stage: str
    raw_bottleneck: float
    route_density: float
    card_integrity: float
    cache_warmth: float
    missing_link_pressure: float
    contradiction_pressure: float = 0.0

@dataclass(frozen=True)
class RegistryPreflightFinding:
    stage: str
    preflight_score: float
    relief: float
    repaired_bottleneck: float
    decision: str
    repair_route: str
    notes: str


def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, float(x)))


def registry_preflight_doctor(inp: RegistryPreflightInput) -> RegistryPreflightFinding:
    """Doctor pass for ApocalypOS card/registry boot bridge.

    The Doctor does not claim external ACK. It checks local surface readiness:
    route density, card integrity, cache warmth and missing-link pressure.
    The output is a repaired bottleneck score for the local boot sequence.
    """
    route_density = clamp(inp.route_density)
    card_integrity = clamp(inp.card_integrity)
    cache_warmth = clamp(inp.cache_warmth)
    missing = clamp(inp.missing_link_pressure)
    contradiction = clamp(inp.contradiction_pressure)

    readiness = (0.30 * route_density + 0.35 * card_integrity + 0.25 * cache_warmth + 0.10 * (1.0 - missing))
    # paradox layer helps with contradiction, but registry bridge still needs concrete readiness
    contradiction_penalty = 0.18 * contradiction
    preflight_score = clamp(readiness - contradiction_penalty)

    # relief is not allowed to erase the bottleneck entirely: bridge still costs time/load
    relief = clamp(0.62 * preflight_score + 0.18 * (1.0 - missing), 0.0, 0.72)
    repaired = clamp(inp.raw_bottleneck * (1.0 - relief) + 0.08 * missing)

    if repaired >= 0.70:
        decision = 'preflight_block'
        route = 'doctor_registry_preflight_block'
    elif repaired >= 0.40:
        decision = 'repair_bias'
        route = 'doctor_registry_preflight_repair_bias'
    else:
        decision = 'boot_continue'
        route = 'doctor_registry_preflight_continue'

    return RegistryPreflightFinding(
        stage=inp.stage,
        preflight_score=round(preflight_score, 6),
        relief=round(relief, 6),
        repaired_bottleneck=round(repaired, 6),
        decision=decision,
        repair_route=route,
        notes='local card/registry surface preflight; no external CURRENT/ACK claimed',
    )
