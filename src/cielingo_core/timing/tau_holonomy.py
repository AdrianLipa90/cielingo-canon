#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CIELingo / ApocalypOS tau-holonomy timing model v1.2F.

This module implements the internal NOEMA phase-time update used by the
ApocalypOS<=>CIELingo emulated server process. It is not an OS daemon. It
updates a serializable server-state dictionary by a holonomic phase-time tick.

Core rule:
    delta_tau = (ln(2) / (24*pi)) * phase_fraction * Phi_BE
with phase_fraction = 1/2 by default, so:
    delta_tau = (ln(2) / (48*pi)) * Phi_BE

Phi_BE is the Berry-Euler phase accumulated from W_ij influence weights,
A_ij connection values, spin-1/2 transport, epsilon oscillation, D_Lambda drift,
and a route holonomy term.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from math import log, pi, sin, atan2, isfinite
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

NumberMatrix = Sequence[Sequence[float]]


def _matrix_sum_product(W_ij: NumberMatrix, A_ij: NumberMatrix) -> float:
    """Return sum_ij W_ij * A_ij with shape checks."""
    if len(W_ij) != len(A_ij):
        raise ValueError("W_ij and A_ij row counts differ")
    total = 0.0
    for w_row, a_row in zip(W_ij, A_ij):
        if len(w_row) != len(a_row):
            raise ValueError("W_ij and A_ij column counts differ")
        for w, a in zip(w_row, a_row):
            total += float(w) * float(a)
    if not isfinite(total):
        raise ValueError("non-finite holonomy coupling")
    return total


@dataclass(frozen=True)
class TauHolonomyConfig:
    """Configuration for NOEMA internal phase-time."""

    tau_scale: float = log(2.0) / (24.0 * pi)
    phase_fraction: float = 0.5
    spin_half_factor: float = 0.5
    epsilon_weight: float = 1.0
    d_lambda_weight: float = 1.0
    holonomy_weight: float = 1.0
    model_name: str = "berry_euler_holonomic_phase_time_v1_2F"

    @property
    def effective_tau_scale(self) -> float:
        return self.tau_scale * self.phase_fraction


@dataclass(frozen=True)
class TauHolonomyInput:
    """Input packet used to compute a single phase-time tick."""

    W_ij: NumberMatrix
    A_ij: NumberMatrix
    epsilon_phase: float = 0.0
    d_lambda_phase: float = 0.0
    route_phase: float = 0.0
    semantic_load: float = 0.0
    contradiction_pressure: float = 0.0
    holonomy_pressure: float = 0.0


def berry_euler_phase(packet: TauHolonomyInput, cfg: TauHolonomyConfig = TauHolonomyConfig()) -> float:
    """Compute bounded Berry-Euler phase for one NOEMA route.

    The raw W*A coupling is compressed with atan2 so extreme weights cannot
    explode the local server time. Epsilon and D_Lambda are explicit phase
    sources, while route_phase carries path-dependent holonomy.
    """
    coupling = _matrix_sum_product(packet.W_ij, packet.A_ij)
    holonomy_component = atan2(coupling, 1.0)
    pressure_component = atan2(
        float(packet.semantic_load) + float(packet.contradiction_pressure) + float(packet.holonomy_pressure),
        3.0,
    )
    phi = (
        cfg.spin_half_factor * pi
        + cfg.holonomy_weight * holonomy_component
        + cfg.epsilon_weight * float(packet.epsilon_phase)
        + cfg.d_lambda_weight * float(packet.d_lambda_phase)
        + float(packet.route_phase)
        + pressure_component
    )
    if not isfinite(phi):
        raise ValueError("non-finite Berry-Euler phase")
    return phi


def delta_tau(packet: TauHolonomyInput, cfg: TauHolonomyConfig = TauHolonomyConfig()) -> float:
    """Return delta_tau = ln(2)/(48*pi) * Phi_BE by default."""
    return cfg.effective_tau_scale * berry_euler_phase(packet, cfg)


def tick_server_state(state: Mapping[str, Any], packet: TauHolonomyInput,
                      cfg: TauHolonomyConfig = TauHolonomyConfig()) -> Dict[str, Any]:
    """Return a new server-state dictionary after one tau-holonomy tick."""
    old_tau = float(state.get("tau", state.get("phase_time", 0.0)))
    old_tick = int(state.get("tick", 0))
    phi = berry_euler_phase(packet, cfg)
    d_tau = cfg.effective_tau_scale * phi
    new_tau = old_tau + d_tau
    repair_bias = max(0.0, min(1.0, 0.4 * packet.contradiction_pressure + 0.35 * packet.holonomy_pressure + 0.25 * packet.semantic_load))
    if repair_bias >= 0.75:
        decision = "block_and_quarantine"
    elif repair_bias >= 0.50:
        decision = "repair_bias"
    else:
        decision = "observe"
    out = dict(state)
    out.update({
        "schema": "APOCALYPOS_CIELINGO_NOEMA_SERVER_STATE_V1_2F",
        "tau_model": asdict(cfg),
        "tick": old_tick + 1,
        "tau": new_tau,
        "phase_time": new_tau,
        "last_delta_tau": d_tau,
        "last_berry_euler_phase": phi,
        "last_phase_sources": {
            "spin_half_factor": cfg.spin_half_factor,
            "epsilon_phase": packet.epsilon_phase,
            "d_lambda_phase": packet.d_lambda_phase,
            "route_phase": packet.route_phase,
            "W_ij_A_ij_coupling": _matrix_sum_product(packet.W_ij, packet.A_ij),
        },
        "semantic_load": packet.semantic_load,
        "contradiction_pressure": packet.contradiction_pressure,
        "holonomy_pressure": packet.holonomy_pressure,
        "repair_bias": repair_bias,
        "decision": decision,
        "external_current_ack_claimed": False,
        "os_process_spawned": False,
        "network_used": False,
    })
    return out
