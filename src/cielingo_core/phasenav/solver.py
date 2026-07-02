"""Phasenav solver — find operator paths between concepts."""
from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Any

from .loader import PhasenavData, load_phasenav

ORBIT_DIMS = ["mass", "sin", "cos", "align", "tension", "j_bus", "visc", "afford", "word_int", "file_int", "tele_ctrl"]

@dataclass
class PhasenavStep:
    source_card_id: str
    target_card_id: str
    operator_hook: str
    operator_card_id: str
    phase_start: float
    phase_end: float
    phase_delta: float
    holonomic_viscosity: float
    phasenav_affordance: float
    transition_lane: str
    path_integral: float = 0.0

@dataclass
class PhasenavTrace:
    steps: list[PhasenavStep] = field(default_factory=list)
    total_path_integral: float = 0.0
    mean_viscosity: float = 0.0
    mean_affordance: float = 0.0
    card_sequence: list[str] = field(default_factory=list)

@dataclass
class PhasenavSolver:
    data: PhasenavData

    @classmethod
    def load(cls, base_path=None) -> PhasenavSolver:
        return cls(data=load_phasenav(base_path))

    def get_phase(self, card_id: str) -> float:
        cp = self.data.concept_phases.get(card_id)
        if cp:
            return float(cp.get("geometric_phase_rad", 0.0))
        nm = self.data.name_mass_by_card_id.get(card_id)
        if nm:
            return float(nm.get("geometric_phase_rad", 0.0))
        return 0.0

    def get_orbit(self, card_id: str) -> list[float]:
        o = self.data.orbits.get(card_id, [0.0] * 11)
        return [float(x) for x in o]

    def best_edge_from(self, concept_id: str) -> dict | None:
        edges = self.data.edges_by_concept.get(concept_id)
        if not edges:
            return None
        return max(edges, key=lambda e: float(e.get("phasenav_affordance", 0)))

    def trace(self, card_ids: list[str]) -> PhasenavTrace:
        trace = PhasenavTrace(card_sequence=list(card_ids))
        for i in range(len(card_ids) - 1):
            src = card_ids[i]
            tgt = card_ids[i + 1]
            step = self._step_between(src, tgt)
            if step:
                trace.steps.append(step)
        if trace.steps:
            trace.total_path_integral = sum(s.path_integral for s in trace.steps)
            trace.mean_viscosity = sum(s.holonomic_viscosity for s in trace.steps) / len(trace.steps)
            trace.mean_affordance = sum(s.phasenav_affordance for s in trace.steps) / len(trace.steps)
        return trace

    def _step_between(self, src_card_id: str, tgt_card_id: str) -> PhasenavStep | None:
        src_phase = self.get_phase(src_card_id)
        tgt_phase = self.get_phase(tgt_card_id)

        edge = self.best_edge_from(src_card_id)
        if edge is None:
            return None

        op_card_id = edge.get("operator_card_id", "")
        op_hook = edge.get("operator_hook", "")
        visc = float(edge.get("holonomic_viscosity", 0))
        afford = float(edge.get("phasenav_affordance", 0))
        lane = edge.get("transition_lane", "unknown")

        phase_delta = tgt_phase - src_phase
        path_contrib = visc * abs(phase_delta)

        return PhasenavStep(
            source_card_id=src_card_id,
            target_card_id=tgt_card_id,
            operator_hook=op_hook,
            operator_card_id=op_card_id,
            phase_start=src_phase,
            phase_end=tgt_phase,
            phase_delta=phase_delta,
            holonomic_viscosity=visc,
            phasenav_affordance=afford,
            transition_lane=lane,
            path_integral=path_contrib,
        )
