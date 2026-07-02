#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CIELingo / ApocalypOS temporal-fluid calibration v1.2G.

This module keeps the ITP server's time model inside the NOEMA surface.
It does not use OS wall-clock time as runtime. Earth time is stored only
as an orientation anchor for timeline reading.

Core terms:
    tau: local phase-time accumulated by tau_holonomy.py
    cosmic_time: dimensionless Berry-Euler phase count, tau / (ln2/(48*pi))
    temporal_density: local scalar load of semantic, contradiction, holonomy,
        epsilon and D_Lambda components
    temporal_fluid_volume: integral/sum of temporal_density over a process grid
    motion_gradients: finite-difference gradients of tau over local phase nodes
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from math import log, pi, sqrt, isfinite
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

from .tau_holonomy import TauHolonomyConfig

Number = float
Vector = Sequence[float]
Matrix = Sequence[Sequence[float]]


@dataclass(frozen=True)
class TemporalFluidConfig:
    """Configuration for ITP temporal fluid calibration."""

    tau_quantum: float = log(2.0) / (48.0 * pi)
    earth_time_role: str = "orientation_anchor_only"
    cosmic_time_role: str = "dimensionless_phase_count"
    local_time_role: str = "NOEMA_tau_phase_time"
    schema: str = "ITP_TEMPORAL_FLUID_CONFIG_V1_2G"


@dataclass(frozen=True)
class TemporalNode:
    """One local node in the temporal-fluid phase surface."""

    node_id: str
    tau: float
    semantic_load: float = 0.0
    contradiction_pressure: float = 0.0
    holonomy_pressure: float = 0.0
    epsilon_phase: float = 0.0
    d_lambda_phase: float = 0.0
    route_phase: float = 0.0

    def density(self) -> float:
        vals = [
            self.semantic_load,
            self.contradiction_pressure,
            self.holonomy_pressure,
            self.epsilon_phase,
            self.d_lambda_phase,
            self.route_phase,
        ]
        rho = sqrt(sum(float(v) * float(v) for v in vals))
        if not isfinite(rho):
            raise ValueError(f"non-finite temporal density for {self.node_id}")
        return rho


def temporal_fluid_volume(nodes: Sequence[TemporalNode], cell_volume: float = 1.0) -> float:
    """Return V_tau = sum_i rho_tau(i) * dV.

    This is a NOEMA-internal process volume: it measures occupied phase-load,
    not physical litres/metres.
    """
    if cell_volume <= 0:
        raise ValueError("cell_volume must be positive")
    return float(sum(n.density() * cell_volume for n in nodes))


def temporal_gradient(nodes: Sequence[TemporalNode]) -> List[Dict[str, float]]:
    """Finite-difference tau gradients along the ordered local route."""
    if len(nodes) < 2:
        return []
    out = []
    for i, (a, b) in enumerate(zip(nodes, nodes[1:])):
        dtau = float(b.tau) - float(a.tau)
        drho = b.density() - a.density()
        out.append({
            "edge_index": i,
            "from": a.node_id,
            "to": b.node_id,
            "delta_tau": dtau,
            "delta_density": drho,
            "velocity_density_per_tau": drho / dtau if abs(dtau) > 1e-12 else 0.0,
        })
    return out


def cosmic_time_from_tau(tau: float, cfg: TemporalFluidConfig = TemporalFluidConfig()) -> float:
    """Return dimensionless cosmic phase-count from local tau."""
    return float(tau) / cfg.tau_quantum


def synchronize_earth_orientation(state: Mapping[str, Any], *,
                                  earth_iso: str | None = None,
                                  cfg: TemporalFluidConfig = TemporalFluidConfig()) -> Dict[str, Any]:
    """Attach cosmic/local/Earth orientation fields to a server-state.

    Earth time is not used as the process clock. It is an orientation anchor
    for reading timelines and comparing logs.
    """
    tau = float(state.get("tau", state.get("phase_time", 0.0)))
    if earth_iso is None:
        earth_iso = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    out = dict(state)
    out["time_orientation"] = {
        "schema": "ITP_TIME_ORIENTATION_V1_2G",
        "local_tau": tau,
        "cosmic_time_phase_count": cosmic_time_from_tau(tau, cfg),
        "earth_time_utc_anchor": earth_iso,
        "earth_time_role": cfg.earth_time_role,
        "tau_quantum": cfg.tau_quantum,
    }
    return out


def calibrate_temporal_fluid(state: Mapping[str, Any], nodes: Sequence[TemporalNode], *,
                             earth_iso: str | None = None,
                             cfg: TemporalFluidConfig = TemporalFluidConfig()) -> Dict[str, Any]:
    """Return updated ITP server-state with temporal fluid diagnostics."""
    oriented = synchronize_earth_orientation(state, earth_iso=earth_iso, cfg=cfg)
    volume = temporal_fluid_volume(nodes)
    gradients = temporal_gradient(nodes)
    mean_density = volume / max(1, len(nodes))
    oriented["temporal_fluid"] = {
        "schema": "ITP_TEMPORAL_FLUID_STATE_V1_2G",
        "config": asdict(cfg),
        "node_count": len(nodes),
        "volume": volume,
        "mean_density": mean_density,
        "nodes": [asdict(n) | {"density": n.density()} for n in nodes],
        "motion_gradients": gradients,
        "gradient_count": len(gradients),
        "interpretation": "NOEMA phase-fluid volume and gradients for ApocalypOS/CIELingo ITP timelines",
    }
    oriented["schema"] = "APOCALYPOS_CIELINGO_NOEMA_SERVER_STATE_V1_2G"
    return oriented


def default_nodes_from_state(state: Mapping[str, Any]) -> List[TemporalNode]:
    """Build a compact three-node temporal route from a server state."""
    tau = float(state.get("tau", state.get("phase_time", 0.0)))
    last_delta = float(state.get("last_delta_tau", 0.0))
    return [
        TemporalNode(
            node_id="source_state",
            tau=tau - last_delta,
            semantic_load=float(state.get("semantic_load", 0.0)) * 0.5,
            contradiction_pressure=float(state.get("contradiction_pressure", 0.0)) * 0.5,
            holonomy_pressure=float(state.get("holonomy_pressure", 0.0)) * 0.5,
            epsilon_phase=0.25,
            d_lambda_phase=0.10,
        ),
        TemporalNode(
            node_id="berry_euler_transport",
            tau=tau - 0.5 * last_delta,
            semantic_load=float(state.get("semantic_load", 0.0)),
            contradiction_pressure=float(state.get("contradiction_pressure", 0.0)),
            holonomy_pressure=float(state.get("holonomy_pressure", 0.0)),
            epsilon_phase=float(state.get("last_phase_sources", {}).get("epsilon_phase", 0.4)),
            d_lambda_phase=float(state.get("last_phase_sources", {}).get("d_lambda_phase", 0.2)),
            route_phase=float(state.get("last_phase_sources", {}).get("route_phase", 0.1)),
        ),
        TemporalNode(
            node_id="d_epsilon_continuum",
            tau=tau,
            semantic_load=float(state.get("semantic_load", 0.0)) + 0.05,
            contradiction_pressure=float(state.get("contradiction_pressure", 0.0)),
            holonomy_pressure=float(state.get("holonomy_pressure", 0.0)) + 0.05,
            epsilon_phase=float(state.get("last_phase_sources", {}).get("epsilon_phase", 0.4)),
            d_lambda_phase=float(state.get("last_phase_sources", {}).get("d_lambda_phase", 0.2)),
            route_phase=float(state.get("last_phase_sources", {}).get("route_phase", 0.1)),
        ),
    ]
