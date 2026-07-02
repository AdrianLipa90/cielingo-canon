
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, Iterable, List, Mapping, Optional

@dataclass(frozen=True)
class TestHolonomyRegion:
    region_id: str
    label: str
    phase_axis: str
    default_timeout_s: float
    phase_load: float
    stress_weight: float
    description: str

@dataclass(frozen=True)
class TestHolonomyNode:
    nodeid: str
    region_id: str
    dependencies: tuple[str, ...]
    phase_load: float
    expected_route: str
    timeout_s: float

REGIONS: Dict[str, TestHolonomyRegion] = {
    'global_pass_heavy': TestHolonomyRegion('global_pass_heavy', 'Global Pass / R_H / Lambda / closure', 'global_holonomy', 10.0, 0.95, 1.00, 'Heavy global pass tests; require micro-run or slow lane.'),
    'bridge_runtime': TestHolonomyRegion('bridge_runtime', 'Orbital Bridge / Registry Runtime', 'bridge_registry', 8.0, 0.75, 0.80, 'Bridge and registry tests; require preflight Doctor.'),
    'memory_consolidator': TestHolonomyRegion('memory_consolidator', 'Memory Consolidator', 'episodic_memory', 6.0, 0.55, 0.60, 'Memory consolidation and failure triage tests.'),
    'orbital_semantics_shell': TestHolonomyRegion('orbital_semantics_shell', 'Orbital Semantics / Shell / Cards', 'orbital_semantic_shell', 5.0, 0.45, 0.50, 'Orbital shell, object cards and semantics tests.'),
    'runtime_smoke': TestHolonomyRegion('runtime_smoke', 'Runtime Smoke / Fast Defaults', 'runtime_smoke', 4.0, 0.30, 0.35, 'Fast runtime and default-manifest tests.'),
    'unknown': TestHolonomyRegion('unknown', 'Unknown / Unclassified', 'unclassified', 4.0, 0.50, 0.50, 'Fallback region for new tests.'),
}

KEYWORDS = (
    ('global_pass_heavy', ('run_global_pass', 'globalpass', 'global_pass', 'r_h_', 'closure_penalty', 'lambda_glob', 'history_')),
    ('bridge_runtime', ('bridge', 'registry_verifier', 'registry')),
    ('memory_consolidator', ('memory_consolidator', 'consolidator', 'triage', 'reconsolidation')),
    ('orbital_semantics_shell', ('orbital_semantics', 'orbital_shell', 'object_cards', 'phase4', 'shellindex')),
)

def classify_nodeid(nodeid: str) -> str:
    low = nodeid.lower()
    for region, keys in KEYWORDS:
        if any(k in low for k in keys):
            return region
    if 'orbital_runtime' in low:
        return 'runtime_smoke'
    return 'unknown'

def infer_dependencies(region_id: str) -> tuple[str, ...]:
    deps = {
        'global_pass_heavy': ('ciel_sot_agent', 'orbital_bridge', 'global_pass_state'),
        'bridge_runtime': ('registry_preflight_doctor', 'orbital_bridge', 'noema_surface'),
        'memory_consolidator': ('memory_store', 'failure_triage', 'episodic_snap'),
        'orbital_semantics_shell': ('orbital_shell', 'object_cards', 'phase_index'),
        'runtime_smoke': ('runtime_defaults',),
        'unknown': ('manual_review',),
    }
    return deps.get(region_id, ('manual_review',))

def route_for_region(region_id: str) -> str:
    if region_id == 'global_pass_heavy': return 'slow_lane_micro_run'
    if region_id == 'bridge_runtime': return 'doctor_registry_preflight'
    if region_id == 'memory_consolidator': return 'memory_doctor_triage'
    if region_id == 'orbital_semantics_shell': return 'keep_fast_orbital_region'
    if region_id == 'runtime_smoke': return 'keep_fast_runtime_smoke'
    return 'manual_adapter_required'

def build_nodes(nodeids: Iterable[str]) -> List[TestHolonomyNode]:
    nodes: List[TestHolonomyNode] = []
    for nodeid in nodeids:
        region = classify_nodeid(nodeid)
        r = REGIONS[region]
        nodes.append(TestHolonomyNode(
            nodeid=nodeid,
            region_id=region,
            dependencies=infer_dependencies(region),
            phase_load=r.phase_load,
            expected_route=route_for_region(region),
            timeout_s=r.default_timeout_s,
        ))
    return nodes

def group_nodes(nodes: Iterable[TestHolonomyNode]) -> Dict[str, List[TestHolonomyNode]]:
    grouped: Dict[str, List[TestHolonomyNode]] = {}
    for n in nodes:
        grouped.setdefault(n.region_id, []).append(n)
    return grouped

def dependency_edges(nodes: Iterable[TestHolonomyNode]) -> List[dict]:
    edges = []
    for n in nodes:
        for dep in n.dependencies:
            edges.append({'nodeid': n.nodeid, 'depends_on': dep, 'region_id': n.region_id})
    return edges

def region_summary(nodes: Iterable[TestHolonomyNode]) -> Dict[str, dict]:
    grouped = group_nodes(nodes)
    out: Dict[str, dict] = {}
    for region_id, group in grouped.items():
        r = REGIONS.get(region_id, REGIONS['unknown'])
        out[region_id] = {
            'label': r.label,
            'count': len(group),
            'phase_axis': r.phase_axis,
            'mean_phase_load': sum(n.phase_load for n in group) / max(1, len(group)),
            'stress_weight': r.stress_weight,
            'route': route_for_region(region_id),
            'timeout_s': r.default_timeout_s,
        }
    return out
