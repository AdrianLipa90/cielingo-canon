from __future__ import annotations
from dataclasses import asdict
from typing import Dict, Any, List
from cielingo_core.doctor.registry_preflight_doctor import RegistryPreflightInput, registry_preflight_doctor
from cielingo_core.timing.phase_load_scheduler import PhaseLoadInput, phase_load_scheduler


def apply_doctor_phase_boot_repair(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    repaired = []
    for r in rows:
        stage = r['stage']
        base = float(r['with_paradox_bottleneck_score'])
        decision = r.get('paradox_decision') or 'observe'
        route = r.get('paradox_repair_route') or 'none'
        method = 'paradox_layer_only'
        after = base
        extra = {}

        if stage == 'B3_card_registry_bridge':
            finding = registry_preflight_doctor(RegistryPreflightInput(
                stage=stage,
                raw_bottleneck=base,
                route_density=0.78,
                card_integrity=0.86,
                cache_warmth=0.74,
                missing_link_pressure=0.16,
                contradiction_pressure=float(r.get('paradox_pressure', 0.0) or 0.0),
            ))
            after = finding.repaired_bottleneck
            decision = finding.decision
            route = finding.repair_route
            method = 'registry_preflight_doctor'
            extra = asdict(finding)

        elif stage == 'B6_tau_holonomy_doctor':
            sched = phase_load_scheduler(PhaseLoadInput(
                stage=stage,
                raw_bottleneck=base,
                tau_before=float(r.get('tau_before', 0.0) or 0.0),
                berry_euler_phase=2.95,
                holonomy_pressure=0.91,
                temporal_volume=float(r.get('temporal_volume', 0.0) or 0.0),
                max_substep_tau=0.0065,
            ))
            after = sched.repaired_bottleneck
            decision = sched.decision
            route = sched.repair_route
            method = 'phase_holonomy_scheduler_doctor'
            extra = asdict(sched)

        repaired.append({
            **r,
            'post_1_2L_bottleneck_score': round(float(after), 6),
            'post_1_2L_decision': decision,
            'post_1_2L_repair_route': route,
            'post_1_2L_method': method,
            'post_1_2L_reduction_from_paradox': round(base - float(after), 6),
            'post_1_2L_extra': extra,
        })

    avg_before = sum(float(r['with_paradox_bottleneck_score']) for r in rows) / len(rows)
    avg_after = sum(float(r['post_1_2L_bottleneck_score']) for r in repaired) / len(repaired)
    return {
        'rows': repaired,
        'summary': {
            'stage_count': len(repaired),
            'avg_with_paradox_layer': round(avg_before, 6),
            'avg_after_doctor_phase_repair': round(avg_after, 6),
            'absolute_reduction_from_1_2K': round(avg_before - avg_after, 6),
            'relative_reduction_from_1_2K': round((avg_before - avg_after) / avg_before, 6) if avg_before else 0.0,
            'remaining_blocked_stages': sum(1 for r in repaired if 'block' in str(r['post_1_2L_decision'])),
            'registry_bridge_score': next(r['post_1_2L_bottleneck_score'] for r in repaired if r['stage']=='B3_card_registry_bridge'),
            'tau_holonomy_score': next(r['post_1_2L_bottleneck_score'] for r in repaired if r['stage']=='B6_tau_holonomy_doctor'),
        }
    }
