from __future__ import annotations
from dataclasses import dataclass
from typing import List
import math

ZETA_ZEROS = [14.134725, 21.022040, 25.010858, 30.424876, 32.935062]
TAU_SCALE = math.log(2.0) / (48.0 * math.pi)

@dataclass(frozen=True)
class PhaseLoadInput:
    stage: str
    raw_bottleneck: float
    tau_before: float
    berry_euler_phase: float
    holonomy_pressure: float
    temporal_volume: float
    max_substep_tau: float = 0.0065

@dataclass(frozen=True)
class PhaseLoadSchedule:
    stage: str
    raw_delta_tau: float
    substep_count: int
    safe_delta_tau: float
    phase_load_reduction: float
    repaired_bottleneck: float
    decision: str
    repair_route: str
    substeps: List[float]


def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, float(x)))


def softclip_hs(x: float, bound: float, hbar_like: float = 1.0) -> float:
    denom = max(bound * hbar_like, 1e-12)
    return bound * math.tanh(x / denom)


def zeta_zero_guard(tau: float, width: float = 0.08) -> float:
    guard = 1.0
    for z in ZETA_ZEROS:
        nearest = min(abs((tau % z)), abs(z - (tau % z)))
        window = math.exp(-(nearest * nearest) / max(width * width, 1e-12))
        guard *= (1.0 - 0.25 * window)
    return clamp(guard, 0.05, 1.0)


def phase_load_scheduler(inp: PhaseLoadInput) -> PhaseLoadSchedule:
    raw_delta = TAU_SCALE * float(inp.berry_euler_phase)
    guard = zeta_zero_guard(inp.tau_before)
    protected_delta = raw_delta * guard
    soft_delta = softclip_hs(protected_delta, bound=max(inp.max_substep_tau * 2.0, 1e-9), hbar_like=1.0)

    substeps_n = max(1, math.ceil(abs(soft_delta) / max(inp.max_substep_tau, 1e-12)))
    each = soft_delta / substeps_n
    substeps = [round(each, 12) for _ in range(substeps_n)]

    hol = clamp(inp.holonomy_pressure)
    vol_norm = clamp(inp.temporal_volume / 4.0)
    load = clamp(0.55 * hol + 0.45 * vol_norm)
    scheduling_relief = clamp(0.20 + 0.18 * substeps_n + 0.22 * (1.0 - load), 0.0, 0.68)
    repaired = clamp(inp.raw_bottleneck * (1.0 - scheduling_relief) + 0.04 * load)

    if repaired >= 0.70:
        decision = 'phase_load_block'
        route = 'doctor_phase_load_block'
    elif repaired >= 0.40:
        decision = 'repair_bias'
        route = 'doctor_phase_load_scheduler_repair_bias'
    else:
        decision = 'boot_continue'
        route = 'doctor_phase_load_scheduler_continue'

    return PhaseLoadSchedule(
        stage=inp.stage,
        raw_delta_tau=round(raw_delta, 12),
        substep_count=substeps_n,
        safe_delta_tau=round(soft_delta, 12),
        phase_load_reduction=round(scheduling_relief, 6),
        repaired_bottleneck=round(repaired, 6),
        decision=decision,
        repair_route=route,
        substeps=substeps,
    )
