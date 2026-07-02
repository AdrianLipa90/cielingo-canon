"""Tests for CIELingo phasenav — geometric programming model."""
from __future__ import annotations
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from cielingo_core.phasenav import PhasenavData, load_phasenav, PhasenavSolver

PHASENAV_LATEST = (
    Path(__file__).resolve().parents[5]
    / "runtime" / "phasenav" / "latest"
)


def test_loader_loads_all_artifacts():
    data = load_phasenav(PHASENAV_LATEST)
    assert isinstance(data, PhasenavData)
    assert len(data.name_mass) == 2922
    assert len(data.name_mass_by_card_id) == 1685
    assert len(data.concept_phases) == 105
    assert len(data.edges) == 394
    assert len(data.orbits) == 1732
    assert len(data.edges_by_concept) == 105


def test_loader_index_by_card_id():
    data = load_phasenav(PHASENAV_LATEST)
    assert len(data.name_mass_by_card_id) > 0
    first = next(iter(data.name_mass_by_card_id.values()))
    assert "geometric_phase_rad" in first
    assert "semantic_mass" in first


def test_loader_concept_phases_have_hooks():
    data = load_phasenav(PHASENAV_LATEST)
    for cid, cp in data.concept_phases.items():
        assert "operator_hooks" in cp, f"Missing hooks for {cid}"
        assert "bus_action" in cp, f"Missing bus_action for {cid}"
        assert "geometric_phase_rad" in cp, f"Missing phase for {cid}"


def test_loader_edges_have_quantities():
    data = load_phasenav(PHASENAV_LATEST)
    for e in data.edges:
        assert "holonomic_viscosity" in e
        assert "phasenav_affordance" in e
        assert "transition_lane" in e
        assert "concept_id" in e
        assert "operator_hook" in e


def test_loader_edges_by_concept():
    data = load_phasenav(PHASENAV_LATEST)
    assert len(data.edges_by_concept) > 0
    for cid, edges in data.edges_by_concept.items():
        assert len(edges) >= 1
        for e in edges:
            assert e["concept_id"] == cid


def test_loader_orbit_vectors_11d():
    data = load_phasenav(PHASENAV_LATEST)
    for cid, orb in data.orbits.items():
        assert len(orb) == 11, f"Orbit for {cid} has {len(orb)} dims, expected 11"
        assert all(isinstance(v, float) for v in orb)


def test_solver_load():
    solver = PhasenavSolver.load(PHASENAV_LATEST)
    assert isinstance(solver, PhasenavSolver)
    assert isinstance(solver.data, PhasenavData)


def test_solver_get_phase_concept():
    solver = PhasenavSolver.load(PHASENAV_LATEST)
    phase = solver.get_phase("concept:air")
    assert isinstance(phase, float)
    assert 0 <= phase < 2 * 3.14159


def test_solver_get_phase_word_candidate():
    solver = PhasenavSolver.load(PHASENAV_LATEST)
    first_cid = next(iter(solver.data.name_mass_by_card_id.keys()))
    phase = solver.get_phase(first_cid)
    assert isinstance(phase, float)


def test_solver_get_phase_unknown():
    solver = PhasenavSolver.load(PHASENAV_LATEST)
    phase = solver.get_phase("nonexistent_card_id")
    assert phase == 0.0


def test_solver_get_orbit():
    solver = PhasenavSolver.load(PHASENAV_LATEST)
    orb = solver.get_orbit("concept:air")
    assert len(orb) == 11
    assert all(isinstance(v, float) for v in orb)


def test_solver_get_orbit_unknown():
    solver = PhasenavSolver.load(PHASENAV_LATEST)
    orb = solver.get_orbit("nonexistent")
    assert len(orb) == 11
    assert all(v == 0.0 for v in orb)


def test_solver_best_edge_from():
    solver = PhasenavSolver.load(PHASENAV_LATEST)
    edge = solver.best_edge_from("concept:air")
    assert edge is not None
    assert "holonomic_viscosity" in edge
    assert "phasenav_affordance" in edge
    assert edge["concept_id"] == "concept:air"


def test_solver_best_edge_from_nonexistent():
    solver = PhasenavSolver.load(PHASENAV_LATEST)
    edge = solver.best_edge_from("nonexistent")
    assert edge is None


def test_solver_trace_two_concepts():
    solver = PhasenavSolver.load(PHASENAV_LATEST)
    trace = solver.trace(["concept:air", "concept:fire"])
    assert len(trace.steps) >= 1
    assert trace.card_sequence == ["concept:air", "concept:fire"]
    assert trace.total_path_integral >= 0
    assert 0 <= trace.mean_viscosity <= 1
    assert 0 <= trace.mean_affordance <= 1


def test_solver_trace_single_card():
    solver = PhasenavSolver.load(PHASENAV_LATEST)
    trace = solver.trace(["concept:air"])
    assert len(trace.steps) == 0
    assert trace.total_path_integral == 0.0


def test_solver_trace_three_concepts():
    solver = PhasenavSolver.load(PHASENAV_LATEST)
    trace = solver.trace(["concept:air", "concept:fire", "concept:water"])
    assert len(trace.steps) == 2
    assert len(trace.card_sequence) == 3
    for step in trace.steps:
        assert step.holonomic_viscosity >= 0
        assert step.phasenav_affordance >= 0
        assert step.transition_lane in ("low_viscosity_direct", "viscous_rephase")


def test_solver_step_has_all_fields():
    solver = PhasenavSolver.load(PHASENAV_LATEST)
    step = solver._step_between("concept:air", "concept:fire")
    assert step is not None
    assert step.source_card_id == "concept:air"
    assert step.target_card_id == "concept:fire"
    assert isinstance(step.operator_hook, str)
    assert isinstance(step.operator_card_id, str)
    assert isinstance(step.phase_start, float)
    assert isinstance(step.phase_end, float)
    assert isinstance(step.phase_delta, float)
    assert isinstance(step.path_integral, float)
    assert step.path_integral >= 0


def test_solver_edge_lane_distribution():
    data = load_phasenav(PHASENAV_LATEST)
    lanes = {}
    for e in data.edges:
        lane = e.get("transition_lane", "unknown")
        lanes[lane] = lanes.get(lane, 0) + 1
    total = sum(lanes.values())
    assert total == 394
    assert "low_viscosity_direct" in lanes
    assert "viscous_rephase" in lanes
    low_pct = lanes.get("low_viscosity_direct", 0) / total
    visc_pct = lanes.get("viscous_rephase", 0) / total
    assert low_pct == 84.5 / 100 or abs(low_pct - 0.845) < 0.01
    assert visc_pct == 15.5 / 100 or abs(visc_pct - 0.155) < 0.01


def test_solver_viscosity_range():
    data = load_phasenav(PHASENAV_LATEST)
    viscosities = [e["holonomic_viscosity"] for e in data.edges]
    assert min(viscosities) >= 0.0
    assert max(viscosities) <= 1.0


def test_solver_affordance_range():
    data = load_phasenav(PHASENAV_LATEST)
    affordances = [e["phasenav_affordance"] for e in data.edges]
    assert min(affordances) >= 0.0
    assert max(affordances) <= 1.0


def test_solver_all_concepts_connected():
    data = load_phasenav(PHASENAV_LATEST)
    concepts_with_edges = set(data.edges_by_concept.keys())
    for cid in data.concept_phases:
        assert cid in concepts_with_edges, f"Concept {cid} has no edges"


if __name__ == "__main__":
    tests = [
        test_loader_loads_all_artifacts,
        test_loader_index_by_card_id,
        test_loader_concept_phases_have_hooks,
        test_loader_edges_have_quantities,
        test_loader_edges_by_concept,
        test_loader_orbit_vectors_11d,
        test_solver_load,
        test_solver_get_phase_concept,
        test_solver_get_phase_word_candidate,
        test_solver_get_phase_unknown,
        test_solver_get_orbit,
        test_solver_get_orbit_unknown,
        test_solver_best_edge_from,
        test_solver_best_edge_from_nonexistent,
        test_solver_trace_two_concepts,
        test_solver_trace_single_card,
        test_solver_trace_three_concepts,
        test_solver_step_has_all_fields,
        test_solver_edge_lane_distribution,
        test_solver_viscosity_range,
        test_solver_affordance_range,
        test_solver_all_concepts_connected,
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
