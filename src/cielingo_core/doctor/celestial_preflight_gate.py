
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

from cielingo_core.doctor.celestial_register_doctor import CelestialRegisterDoctor
from cielingo_core.doctor.test_holonomy_registry import TestHolonomyNode, route_for_region

@dataclass(frozen=True)
class CelestialPreflightDecision:
    subject_id: str
    subject_type: str
    region_or_import: str
    mapped_star: str
    star_exists: bool
    celestial_route_ok: bool
    decision: str
    repair_route: str
    phase_load: float
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class CelestialPreflightGate:
    """Mandatory preflight gate for TestHolonomyRegistry and ImportDoctor.

    The gate enforces the subsystem hierarchy introduced in 1.2X:
    satellite -> planet -> star -> attractor.

    It is deliberately non-mutating. It does not rewrite the register or promote
    any card. It returns routing decisions that can be written as append-only
    NOEMA updates by the caller.
    """

    def __init__(self, register: Dict[str, Any]):
        self.doctor = CelestialRegisterDoctor(register)
        self.validation = self.doctor.validate_register()

    def preflight_test_node(self, node: TestHolonomyNode | Mapping[str, Any]) -> CelestialPreflightDecision:
        if hasattr(node, 'nodeid'):
            nodeid = getattr(node, 'nodeid')
            region = getattr(node, 'region_id')
            phase_load = float(getattr(node, 'phase_load'))
        else:
            nodeid = str(node.get('nodeid') or node.get('file') or 'unknown_test')
            region = str(node.get('region') or node.get('region_id') or 'unknown')
            phase_load = float(node.get('phase_load', 0.5))

        finding = self.doctor.classify_test_node({'nodeid': nodeid, 'region': region, 'phase_load': phase_load})
        star = finding['mapped_star']
        star_exists = bool(finding['star_exists'])
        route = route_for_region(region)
        if not self.validation.get('valid'):
            decision = 'block_register_repair_required'
            repair_route = 'repair_celestial_register_first'
            reason = 'celestial_register_invalid'
            ok = False
        elif not star_exists:
            decision = 'manual_adapter_required'
            repair_route = 'register_missing_star_or_region_mapping'
            reason = 'mapped_star_missing'
            ok = False
        elif region == 'global_pass_heavy':
            decision = 'slow_lane_micro_run'
            repair_route = 'phase_load_scheduler'
            reason = 'heavy_region_requires_micro_run'
            ok = True
        else:
            decision = 'continue'
            repair_route = route
            reason = 'celestial_preflight_passed'
            ok = True
        return CelestialPreflightDecision(
            subject_id=nodeid,
            subject_type='test_node',
            region_or_import=region,
            mapped_star=star,
            star_exists=star_exists,
            celestial_route_ok=ok,
            decision=decision,
            repair_route=repair_route,
            phase_load=phase_load,
            reason=reason,
        )

    def preflight_import(self, import_path: str) -> CelestialPreflightDecision:
        finding = self.doctor.classify_import(import_path)
        star = finding['mapped_star']
        star_exists = bool(finding['star_exists'])
        if not self.validation.get('valid'):
            decision = 'block_register_repair_required'
            repair_route = 'repair_celestial_register_first'
            reason = 'celestial_register_invalid'
            ok = False
        elif not star_exists:
            decision = 'manual_adapter_required'
            repair_route = 'register_missing_import_star'
            reason = 'mapped_star_missing'
            ok = False
        else:
            decision = 'continue'
            repair_route = 'import_star_route_ok'
            reason = 'celestial_import_preflight_passed'
            ok = True
        return CelestialPreflightDecision(
            subject_id=import_path,
            subject_type='import',
            region_or_import=import_path,
            mapped_star=star,
            star_exists=star_exists,
            celestial_route_ok=ok,
            decision=decision,
            repair_route=repair_route,
            phase_load=0.5,
            reason=reason,
        )

    def preflight_tests(self, nodes: Iterable[TestHolonomyNode | Mapping[str, Any]]) -> List[Dict[str, Any]]:
        return [self.preflight_test_node(n).to_dict() for n in nodes]

    def preflight_imports(self, imports: Iterable[str]) -> List[Dict[str, Any]]:
        return [self.preflight_import(p).to_dict() for p in imports]

    def integrated_report(self, *, test_nodes: Sequence[TestHolonomyNode | Mapping[str, Any]] = (), imports: Sequence[str] = ()) -> Dict[str, Any]:
        test_decisions = self.preflight_tests(test_nodes)
        import_decisions = self.preflight_imports(imports)
        all_decisions = test_decisions + import_decisions
        blockers = [d for d in all_decisions if d['decision'].startswith('block') or d['decision'] == 'manual_adapter_required']
        slow_lane = [d for d in all_decisions if d['decision'] == 'slow_lane_micro_run']
        return {
            'schema': 'CELESTIAL_PREFLIGHT_GATE_REPORT_V1_2Z',
            'register_valid': bool(self.validation.get('valid')),
            'test_decisions': test_decisions,
            'import_decisions': import_decisions,
            'decision_counts': {
                'total': len(all_decisions),
                'continue': sum(1 for d in all_decisions if d['decision'] == 'continue'),
                'slow_lane_micro_run': len(slow_lane),
                'manual_or_block': len(blockers),
            },
            'doctor_decision': 'continue' if not blockers else 'repair_required',
            'preflight_enforced_for': ['TestHolonomyRegistry', 'ImportDoctor'],
        }
