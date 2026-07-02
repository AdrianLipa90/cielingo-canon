#!/usr/bin/env python3
"""Encode all NOEMA cards through phasenav geometry — v2."""
from __future__ import annotations

import hashlib, json, math, re, sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SURFACE = Path('/tmp/noema_surface_workspace/NOEMA_LOCAL_ROOT/head/NoemaSurface').resolve()
CARDS_PATH = SURFACE / 'canon' / 'cielingo' / 'cards' / 'CIELINGO_ALL_IMPORTED_CARDS.jsonl'
LATEST = SURFACE / 'runtime' / 'phasenav' / 'latest'
REPORTS = SURFACE / 'outbox' / 'reports'

# ── All 33 available operator names from imported cards ──
AVAILABLE_OPERATORS = {
    'above', 'after', 'and', 'anytime', 'anywhere', 'be', 'because',
    'before', 'contain', 'from', 'have', 'how', 'if_then', 'inside',
    'like_as', 'never', 'not', 'nowhere', 'on', 'or', 'outside',
    'somehow', 'sometime', 'somewhere', 'somewhere_from', 'somewhere_to',
    'through', 'to', 'under', 'when', 'where', 'with', 'without',
}

# Hook → operator name mapping (only to operators that exist)
HOOK_TO_OP: dict[str, str] = {}
_h2o = {
    'is': 'be', 'was': 'be', 'were': 'be', 'are': 'be', 'be': 'be',
    'has': 'have', 'have': 'have', 'had': 'have',
    'contains': 'contain', 'contain': 'contain', 'hold': 'contain',
    'inside': 'inside', 'in': 'inside',
    'outside': 'outside', 'out': 'outside',
    'not': 'not', 'no': 'not', 'never': 'never',
    'and': 'and', 'all': 'and', 'every': 'and',
    'or': 'or',
    'with': 'with', 'connection': 'with', 'link': 'with', 'mark': 'with',
    'without': 'without',
    'to': 'to', 'target': 'to',
    'from': 'from', 'source': 'from',
    'through': 'through', 'flow': 'through', 'access': 'through', 'bridge': 'through',
    'because': 'because',
    'before': 'before',
    'after': 'after', 'tick': 'after',
    'when': 'when',
    'where': 'where',
    'how': 'how',
    'if_then': 'if_then', 'if': 'if_then', 'then': 'if_then',
    'like_as': 'like_as', 'like': 'like_as', 'as': 'like_as',
    'on': 'on', 'onto': 'on',
    'under': 'under', 'below': 'under', 'limit': 'under', 'boundary': 'under',
    'above': 'above', 'over': 'above',
    'edge': 'outside', 'boundary': 'under',
    'anytime': 'anytime', 'any': 'anytime',
    'anywhere': 'anywhere',
    'nowhere': 'nowhere',
    'somehow': 'somehow',
    'sometime': 'sometime', 'some': 'sometime',
    'somewhere': 'somewhere',
    'somewhere_from': 'somewhere_from',
    'somewhere_to': 'somewhere_to',
    'check': 'contain', 'verify': 'contain', 'confirm': 'contain',
    'error': 'not', 'void': 'without', 'empty': 'without',
}
for hook, op in _h2o.items():
    if op in AVAILABLE_OPERATORS:
        HOOK_TO_OP[hook] = op

# ── Semantic axes per radical card ──
AXES_MAP: dict[str, list[str]] = {
    'rad_entity': ['being', 'object', 'participant'],
    'rad_action': ['act', 'directed', 'agent'],
    'rad_state': ['condition', 'configuration', 'static'],
    'rad_relation': ['binding', 'connection', 'between'],
    'rad_source': ['origin', 'provenance', 'source'],
    'rad_evidence': ['support', 'claim', 'weaker'],
    'rad_truth': ['correspondence', 'reality', 'verified'],
    'rad_hypothesis': ['unconfirmed', 'candidate', 'proposition'],
    'rad_simulation': ['hypothetical', 'execution', 'generated'],
    'rad_memory': ['stored', 'recallable', 'trace'],
    'rad_bridge': ['connection', 'between', 'link'],
    'rad_check': ['verify', 'validate', 'confirm'],
    'rad_review': ['examine', 'audit', 'inspect'],
    'rad_accept': ['receive', 'agree', 'allow'],
    'rad_reject': ['deny', 'refuse', 'dismiss'],
    'rad_mark': ['indicate', 'signal', 'label'],
    'rad_tick': ['increment', 'counter', 'evidence'],
    'rad_boundary': ['edge', 'limit', 'border'],
    'rad_access': ['entry', 'gate', 'permission'],
    'rad_hold': ['contain', 'keep', 'possess'],
    'rad_flow': ['movement', 'direction', 'current'],
    'rad_void': ['empty', 'absence', 'null'],
    'rad_error': ['mistake', 'fault', 'incorrect'],
    'rad_identity': ['self', 'persistence', 'invariant'],
    'rad_final': ['end', 'terminal', 'complete'],
}

# ── Operator hooks per radical card (all map to existing operators) ──
HOOKS_MAP: dict[str, list[str]] = {
    'rad_entity': ['is', 'has', 'contains', 'inside'],
    'rad_action': ['to', 'with', 'through', 'before'],
    'rad_state': ['is', 'was', 'not'],
    'rad_relation': ['and', 'or', 'because', 'is'],
    'rad_source': ['from', 'is', 'verify', 'check', 'through'],
    'rad_evidence': ['is', 'check', 'verify', 'from'],
    'rad_truth': ['is', 'was', 'verify', 'from'],
    'rad_hypothesis': ['if_then', 'or', 'not', 'is'],
    'rad_simulation': ['like_as', 'if_then', 'is', 'through'],
    'rad_memory': ['is', 'was', 'contains', 'when'],
    'rad_bridge': ['through', 'to', 'from', 'with'],
    'rad_check': ['verify', 'check', 'is', 'through'],
    'rad_review': ['check', 'verify', 'is', 'through'],
    'rad_accept': ['and', 'to', 'is', 'with'],
    'rad_reject': ['not', 'without', 'outside', 'never'],
    'rad_mark': ['is', 'has', 'with', 'on'],
    'rad_tick': ['after', 'when', 'is', 'with'],
    'rad_boundary': ['inside', 'outside', 'under', 'above'],
    'rad_access': ['through', 'to', 'from', 'with'],
    'rad_hold': ['contains', 'has', 'inside', 'with'],
    'rad_flow': ['through', 'to', 'from', 'before'],
    'rad_void': ['not', 'without', 'outside', 'never'],
    'rad_error': ['not', 'without', 'is', 'not'],
    'rad_final': ['after', 'before', 'when', 'to'],
}

# ── Concept name → hooks (for concept:* cards) ──
CONCEPT_HOOKS: dict[str, list[str]] = {
    'air': ['through', 'inside', 'with', 'without'],
    'answer': ['is', 'to', 'from', 'with'],
    'blood': ['through', 'inside', 'contain', 'from'],
    'body': ['has', 'inside', 'with', 'through'],
    'border': ['outside', 'inside', 'under', 'above'],
    'boundary': ['outside', 'inside', 'under', 'above'],
    'center': ['inside', 'is', 'with', 'on'],
    'chaos': ['without', 'not', 'outside', 'before'],
    'child': ['is', 'has', 'with', 'to'],
    'dark': ['without', 'not', 'inside', 'under'],
    'depth': ['under', 'inside', 'through', 'below'],
    'desire': ['to', 'for', 'have', 'with'],
    'edge': ['outside', 'inside', 'on', 'under'],
    'end': ['after', 'before', 'to', 'when'],
    'energy': ['through', 'from', 'to', 'have'],
    'fear': ['of', 'from', 'outside', 'not'],
    'fire': ['from', 'through', 'inside', 'without'],
    'flow': ['through', 'to', 'from', 'with'],
    'force': ['through', 'from', 'to', 'have'],
    'form': ['is', 'has', 'with', 'like_as'],
    'freedom': ['without', 'through', 'to', 'outside'],
    'glass': ['through', 'inside', 'outside', 'on'],
    'gravity': ['from', 'to', 'under', 'with'],
    'ground': ['on', 'under', 'from', 'is'],
    'growth': ['from', 'to', 'through', 'after'],
    'heart': ['inside', 'contain', 'is', 'with'],
    'heat': ['from', 'through', 'inside', 'without'],
    'home': ['inside', 'is', 'with', 'from'],
    'ice': ['from', 'inside', 'without', 'on'],
    'idea': ['from', 'is', 'to', 'through'],
    'identity': ['is', 'has', 'with', 'from'],
    'infinite': ['without', 'never', 'everywhere', 'always'],
    'intention': ['to', 'for', 'with', 'from'],
    'joy': ['is', 'with', 'inside', 'from'],
    'journey': ['from', 'to', 'through', 'with'],
    'justice': ['is', 'with', 'from', 'to'],
    'key': ['to', 'through', 'with', 'is'],
    'knowledge': ['from', 'is', 'contain', 'through'],
    'language': ['through', 'with', 'from', 'is'],
    'law': ['is', 'under', 'from', 'with'],
    'life': ['through', 'from', 'to', 'is'],
    'light': ['from', 'through', 'inside', 'on'],
    'limit': ['under', 'above', 'inside', 'outside'],
    'love': ['is', 'with', 'inside', 'to'],
    'machine': ['from', 'to', 'through', 'with'],
    'magic': ['through', 'with', 'without', 'like_as'],
    'mind': ['inside', 'contain', 'through', 'is'],
    'moon': ['on', 'above', 'from', 'with'],
    'mountain': ['on', 'above', 'from', 'to'],
    'music': ['through', 'with', 'like_as', 'from'],
    'name': ['is', 'has', 'with', 'from'],
    'ocean': ['inside', 'through', 'from', 'contain'],
    'order': ['with', 'and', 'from', 'is'],
    'pain': ['from', 'through', 'inside', 'without'],
    'path': ['to', 'from', 'through', 'with'],
    'pattern': ['is', 'like_as', 'with', 'from'],
    'peace': ['with', 'inside', 'without', 'is'],
    'point': ['on', 'is', 'from', 'to'],
    'power': ['from', 'through', 'to', 'have'],
    'purpose': ['to', 'for', 'is', 'from'],
    'question': ['is', 'to', 'from', 'how'],
    'reality': ['is', 'like_as', 'from', 'with'],
    'reason': ['because', 'is', 'from', 'for'],
    'relation': ['with', 'and', 'from', 'to'],
    'river': ['from', 'through', 'to', 'with'],
    'shadow': ['without', 'from', 'not', 'under'],
    'silence': ['without', 'inside', 'not', 'with'],
    'space': ['inside', 'through', 'with', 'without'],
    'star': ['above', 'from', 'on', 'through'],
    'storm': ['through', 'from', 'without', 'with'],
    'structure': ['has', 'is', 'with', 'from'],
    'sun': ['from', 'on', 'above', 'through'],
    'time': ['after', 'before', 'when', 'through'],
    'trust': ['is', 'with', 'from', 'because'],
    'truth': ['is', 'from', 'with', 'because'],
    'water': ['through', 'inside', 'from', 'contain'],
    'way': ['through', 'to', 'from', 'with'],
    'will': ['to', 'for', 'with', 'through'],
    'wisdom': ['from', 'is', 'through', 'with'],
    'word': ['is', 'with', 'through', 'from'],
}

# ── NOEMA card hooks ──
NOEMA_HOOKS = {
    'noema:case:slavic_role_gauge': ['is', 'with', 'from', 'to'],
    'noema:concept:glass': ['through', 'inside', 'outside', 'on'],
    'noema:concept:water': ['through', 'inside', 'from', 'contain'],
    'noema:deictic:unresolved': ['is', 'how', 'where', 'when'],
    'noema:event:containment': ['inside', 'contain', 'with', 'without'],
    'noema:scope:negation': ['not', 'without', 'never', 'nowhere'],
    'noema:tame:temporal': ['after', 'before', 'when', 'through'],
}


def utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def stamp() -> str:
    return datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')


def bounded(v: float) -> float:
    return max(0.0, min(1.0, float(v)))


def norm(text: str) -> str:
    return re.sub(r'[^a-z0-9]+', '', str(text).lower())


def angle_delta(a: float, b: float) -> float:
    return abs(math.atan2(math.sin(a - b), math.cos(a - b)))


def load_cards() -> list[dict[str, Any]]:
    cards = []
    with open(CARDS_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                cards.append(json.loads(line))
    return cards


def group_by_card_id(cards: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for card in cards:
        groups[card['card_id']].append(card)
    return dict(groups)


def classify_card(card_id: str) -> str:
    if card_id.startswith('op:') or card_id.startswith('operator:'):
        return 'operator'
    if card_id.startswith('rad_') or card_id.startswith('concept:') or card_id.startswith('noema:'):
        return 'concept'
    return 'word_candidate'


def get_hooks(card_id: str) -> list[str]:
    if card_id in HOOKS_MAP:
        return HOOKS_MAP[card_id]
    if card_id.startswith('concept:'):
        name = card_id.split(':', 1)[1]
        return CONCEPT_HOOKS.get(name, ['is', 'has', 'with', 'inside'])
    if card_id in NOEMA_HOOKS:
        return NOEMA_HOOKS[card_id]
    return ['is', 'has', 'with']


def get_axes(card_id: str, slot_id: int) -> list[str]:
    if card_id in AXES_MAP:
        return AXES_MAP[card_id]
    if slot_id <= 8:
        return ['entity', 'object', 'nominal']
    elif slot_id <= 16:
        return ['action', 'process', 'verbal']
    elif slot_id <= 24:
        return ['relation', 'modifier', 'abstract']
    return ['unknown', 'candidate', 'unresolved']


def resolve_hook_to_operator(hook: str) -> str | None:
    return HOOK_TO_OP.get(hook.lower())


def pick_bus_action(alignment: float, tension: float, j_bus: float) -> str:
    if alignment > 0.7:
        return 'run_on_shared_phase'
    if tension > 0.7 or j_bus > 0.3:
        return 'throttle_and_rephase_on_htri_bus'
    if tension > 0.5:
        return 'rephase_before_heavy_inference'
    if j_bus > 0.1:
        return 'run_with_j_cqcl_weighting'
    return 'run_on_shared_phase'


def pick_lane(alignment: float, tension: float) -> str:
    if alignment > 0.85:
        return 'phase_locked'
    if tension > 0.7:
        return 'phase_saturated'
    if tension > 0.5:
        return 'phase_tension'
    return 'phase_coupled'


def compute_viscosity(phase_delta_norm: float, tension: float, j_bus: float, vdist: float, mass_delta: float) -> float:
    raw = (
        0.30 * phase_delta_norm
        + 0.22 * tension
        + 0.18 * j_bus
        + 0.16 * vdist
        + 0.08 * mass_delta
    )
    # Spread to cover full [0,1] range: scale + base
    return bounded(0.04 + raw * 1.8)


def compute_affordance(mass_src: float, mass_tgt: float, viscosity: float, alignment: float) -> float:
    return bounded(((mass_src + mass_tgt) / 2.0) * (1.0 - viscosity) * (0.5 + 0.5 * alignment))


def build() -> dict[str, Any]:
    cards = load_cards()
    groups = group_by_card_id(cards)

    all_name_mass: list[dict[str, Any]] = []
    concept_phases: list[dict[str, Any]] = []
    operator_vectors: list[dict[str, Any]] = []
    all_edges: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    orbit_vectors: list[dict[str, Any]] = []

    # Phase 1: classify & extract unique info
    ui: dict[str, dict[str, Any]] = {}
    for cid, variants in groups.items():
        first = variants[0]
        kind = classify_card(cid)
        slot = first.get('slot_id', 999)
        mass = float(first.get('semantic_mass', 0.5))
        marker = first.get('runtime', {}).get('noema_holonomic_marker', {})
        phase = float(marker.get('operator_phase', 0.0)) % (2.0 * math.pi)
        sem_phase = float(marker.get('semantic_phase', 0.5))
        aff_charge = float(first.get('runtime', {}).get('affective_charge', 0.0))
        fn = first.get('function', '')
        lemma = first.get('lemma', cid)
        lang = first.get('language_id', 'universal')
        source = first.get('source_binding', 'ARTIFACT_GROUNDED')
        val = first.get('validation_status', 'draft')

        all_surfaces: list[str] = []
        for v in variants:
            all_surfaces.extend(v.get('surface_forms', []))
        seen: set[str] = set()
        unique_surfaces = [s for s in all_surfaces if not (s in seen or seen.add(s))]

        ui[cid] = {
            'variants': variants, 'kind': kind, 'slot': slot,
            'mass': mass, 'phase_rad': phase, 'semantic_phase': sem_phase,
            'affective_charge': aff_charge, 'function': fn,
            'lemma': lemma, 'language': lang, 'source': source,
            'validation': val, 'all_surfaces': unique_surfaces,
        }

    # Phase 2: alignment/tension from phase distribution
    all_phases = [v['phase_rad'] for v in ui.values()]
    mean_phase = sum(all_phases) / len(all_phases) if all_phases else 0.0
    for v in ui.values():
        d = angle_delta(v['phase_rad'], mean_phase)
        v['phase_alignment'] = round(math.cos(d), 9)
        v['phase_tension'] = round(math.sin(d) ** 2, 9)
        v['j_bus_total'] = round(bounded(v['phase_tension'] * 0.8 + v['affective_charge'] * 0.2), 9)

    # Phase 3: name_mass
    seen_names: set[str] = set()
    for cid, info in sorted(ui.items()):
        for idx, surface in enumerate(info['all_surfaces']):
            key = norm(surface)
            if not key or key in seen_names:
                continue
            seen_names.add(key)
            all_name_mass.append({
                'schema': 'NOEMA_CIELINGO_NAME_SEMANTIC_MASS_V0_1',
                'surface': surface, 'normalized': key,
                'language': info['language'],
                'role': 'lemma' if idx == 0 else 'surface_variant',
                'card_id': cid, 'card_kind': info['kind'],
                'canonical_label': cid,
                'semantic_mass': round(info['mass'], 9),
                'geometric_phase_rad': round(info['phase_rad'], 9),
                'geometric_phase_deg': round(info['phase_rad'] * 180.0 / math.pi, 6),
                'phase_alignment': info['phase_alignment'],
                'phase_tension': info['phase_tension'],
                'vector_digest': None, 'source_path': str(CARDS_PATH),
                'canon_allowed': False,
            })

    # Phase 4: concept_phases
    concept_ids = sorted([cid for cid, v in ui.items() if v['kind'] == 'concept'])
    operator_ids = sorted([cid for cid, v in ui.items() if v['kind'] == 'operator'])

    for cid in concept_ids:
        info = ui[cid]
        axes = get_axes(cid, info['slot'])
        raw_hooks = get_hooks(cid)

        # Only keep hooks that resolve to actual operators
        valid_hooks = []
        seen_ops: set[str] = set()
        for h in raw_hooks:
            op = resolve_hook_to_operator(h)
            if op and op not in seen_ops:
                seen_ops.add(op)
                valid_hooks.append(h)

        bus = pick_bus_action(info['phase_alignment'], info['phase_tension'], info['j_bus_total'])
        lane = pick_lane(info['phase_alignment'], info['phase_tension'])

        concept_phases.append({
            'schema': 'NOEMA_CIELINGO_CONCEPT_GEOMETRIC_PHASE_V0_1',
            'concept_card_id': cid, 'canonical_label': cid,
            'semantic_mass': round(info['mass'], 9),
            'semantic_axes': axes, 'operator_hooks': valid_hooks,
            'geometric_phase_rad': round(info['phase_rad'], 9),
            'geometric_phase_deg': round(info['phase_rad'] * 180.0 / math.pi, 6),
            'berry_fraction': round(info['phase_rad'] / (2.0 * math.pi), 9),
            'phase_alignment': info['phase_alignment'],
            'phase_tension': info['phase_tension'],
            'j_bus_total': info['j_bus_total'],
            'phase_lane': lane, 'bus_action': bus,
            'vector_digest': None, 'source_path': str(CARDS_PATH),
            'canon_allowed': False,
        })

    # Phase 5: operator_vectors
    op_name_map: dict[str, str] = {}
    for cid in operator_ids:
        name = cid.split(':')[-1]
        op_name_map[cid] = name

    for cid in operator_ids:
        info = ui[cid]
        op_name = op_name_map[cid]
        op_power = bounded(0.35 + 0.12 * info['mass'] + 0.08 * min(len(op_name), 8) / 8.0)
        visc = bounded(0.42 * info['phase_tension'] + 0.34 * info['j_bus_total'] + 0.24 * (1.0 - info['mass']))

        operator_vectors.append({
            'schema': 'NOEMA_CIELINGO_OPERATOR_VECTOR_V0_1',
            'operator_card_id': cid, 'operator_alias': op_name,
            'canonical_label': cid, 'family': op_name,
            'classes': [], 'arity': None, 'symbol': op_name,
            'vector_components': [], 'vector': None, 'vector_digest': None,
            'semantic_mass': round(info['mass'], 9),
            'geometric_phase_rad': round(info['phase_rad'], 9),
            'phase_alignment': info['phase_alignment'],
            'phase_tension': info['phase_tension'],
            'j_bus_total': info['j_bus_total'],
            'operator_power': round(op_power, 9),
            'holonomic_viscosity': round(visc, 9),
            'phasenav_role': 'operator_force_vector',
            'canon_allowed': False,
        })

    # Phase 6: transition edges (deduped by concept×operator)
    for cid in concept_ids:
        info = ui[cid]
        raw_hooks = get_hooks(cid)
        concept_phase = info['phase_rad']
        concept_mass = info['mass']
        seen_ops: set[str] = set()

        for h in raw_hooks:
            op_name = resolve_hook_to_operator(h)
            if not op_name or op_name in seen_ops:
                continue
            seen_ops.add(op_name)

            # Find operator card_id by name
            matching_ops = [oid for oid in operator_ids if op_name_map.get(oid) == op_name]
            if not matching_ops:
                continue
            oid = matching_ops[0]
            o_info = ui[oid]

            phase_delta_norm = angle_delta(concept_phase, o_info['phase_rad']) / math.pi
            mass_delta = abs(concept_mass - o_info['mass'])
            vdist = bounded(0.3 + 0.5 * phase_delta_norm)

            viscosity = compute_viscosity(
                phase_delta_norm, info['phase_tension'],
                info['j_bus_total'], vdist, mass_delta
            )
            affordance = compute_affordance(
                concept_mass, o_info['mass'], viscosity, info['phase_alignment']
            )
            lane = ('low_viscosity_direct' if viscosity < 0.33
                    else 'viscous_rephase' if viscosity < 0.66
                    else 'high_resistance_review')

            all_edges.append({
                'schema': 'NOEMA_CIELINGO_PHASENAV_TRANSITION_EDGE_V0_1',
                'concept_id': cid, 'concept_label': cid,
                'operator_hook': op_name,
                'operator_card_id': oid, 'operator_label': oid,
                'resolved_operator': True,
                'source_path': str(CARDS_PATH), 'link_type': 'semantic_hook',
                'status': 'derived',
                'phase_delta_norm': round(phase_delta_norm, 9),
                'vector_distance': round(vdist, 9),
                'mass_delta': round(mass_delta, 9),
                'holonomic_viscosity': round(viscosity, 9),
                'phasenav_affordance': round(affordance, 9),
                'transition_lane': lane,
                'canon_allowed': False,
            })

    all_edges.sort(key=lambda e: (-float(e['phasenav_affordance']), float(e['holonomic_viscosity'])))

    # Phase 7: candidates (word_candidate cards)
    # Precompute mean visc/aff per concept for candidate propagation
    concept_edge_stats: dict[str, tuple[float, float]] = {}
    for cid in concept_ids:
        related = [e for e in all_edges if e['concept_id'] == cid]
        mean_v = sum(float(e['holonomic_viscosity']) for e in related) / len(related) if related else 0.5
        max_a = max((float(e['phasenav_affordance']) for e in related), default=0.3)
        concept_edge_stats[cid] = (mean_v, max_a)

    for cid, info in sorted(ui.items()):
        if info['kind'] != 'word_candidate':
            continue

        conf = bounded(0.50 * info['semantic_phase'] + 0.20 * info['mass'] + 0.20 * (1.0 - 0.5) + 0.10 * 0.3)

        candidates.append({
            'schema': 'NOEMA_CIELINGO_PHASENAV_WORD_CARD_CANDIDATE_V0_1',
            'promotion_status': 'candidate_only_not_canon',
            'candidate_confidence': round(conf, 9),
            'base_knowledge_confidence': round(info['semantic_phase'], 9),
            'semantic_mass': round(info['mass'], 9),
            'mean_holonomic_viscosity': 0.0,
            'mean_phasenav_affordance': 0.0,
            'surface': info['all_surfaces'][0] if info['all_surfaces'] else info['lemma'],
            'lemma': info['lemma'], 'language': info['language'],
            'card_id': cid, 'lexical_id': cid,
            'phase_rad': round(info['phase_rad'], 9),
            'semantic_axes': [], 'verification_state': info['validation'],
            'review_note': 'chyba: phasenav candidate from imported CIELingo cards; no canon promotion',
            'canon_allowed': False,
        })

    candidates.sort(key=lambda r: (-float(r['candidate_confidence']), r['language'], r['surface']))

    # Compute overall edge stats for word_candidate propagation
    all_viscs = [float(e['holonomic_viscosity']) for e in all_edges]
    all_affs = [float(e['phasenav_affordance']) for e in all_edges]
    overall_mean_visc = sum(all_viscs) / len(all_viscs) if all_viscs else 0.5
    overall_mean_aff = sum(all_affs) / len(all_affs) if all_affs else 0.3

    # Phase 8: orbit vectors for ALL unique cards
    for cid, info in sorted(ui.items()):
        sin_p = math.sin(info['phase_rad'])
        cos_p = math.cos(info['phase_rad'])
        j_bus = info['j_bus_total']

        if info['kind'] == 'concept':
            related = [e for e in all_edges if e['concept_id'] == cid]
            mean_v = (sum(float(e['holonomic_viscosity']) for e in related) / len(related)
                      if related else 0.5)
            max_a = max((float(e['phasenav_affordance']) for e in related), default=0.3)
        elif info['kind'] == 'operator':
            related = [e for e in all_edges if e['operator_card_id'] == cid]
            mean_v = (sum(float(e['holonomic_viscosity']) for e in related) / len(related)
                      if related else 0.5)
            max_a = max((float(e['phasenav_affordance']) for e in related), default=0.3)
        else:
            mean_v = overall_mean_visc
            max_a = overall_mean_aff

        orbit_vectors.append({
            'schema': 'NOEMA_CIELINGO_ORBIT_VECTOR_V0_1',
            'card_id': cid, 'card_kind': info['kind'],
            'lemma': info['lemma'],
            'orbit_vector': [
                round(info['mass'], 9),
                round(sin_p, 9),
                round(cos_p, 9),
                round(info['phase_alignment'], 9),
                round(info['phase_tension'], 9),
                round(j_bus, 9),
                round(mean_v, 9),
                round(max_a, 9),
                round(bounded(len(info['all_surfaces']) / 10.0), 9),
                round(bounded(1.0 / (1.0 + len(info['variants']) / 10.0)), 9),
                round(bounded(info['phase_alignment'] * 0.7 + info['mass'] * 0.3), 9),
            ],
            'canon_allowed': False,
        })

    summary = {
        'schema': 'NOEMA_CIELINGO_PHASENAV_ENCODE_SUMMARY_V0_1',
        'total_cards': len(cards),
        'unique_concepts': len(concept_ids),
        'unique_operators': len(operator_ids),
        'unique_word_candidates': sum(1 for v in ui.values() if v['kind'] == 'word_candidate'),
        'name_mass_count': len(all_name_mass),
        'concept_phase_count': len(concept_phases),
        'operator_vector_count': len(operator_vectors),
        'transition_edge_count': len(all_edges),
        'candidate_count': len(candidates),
        'orbit_vector_count': len(orbit_vectors),
        'canon_allowed': False,
        'review_note': 'chyba: v2 — properly mapped hooks to 33 available operators; edges use real phase deltas',
    }

    return {
        'all_name_mass': all_name_mass, 'concept_phases': concept_phases,
        'operator_vectors': operator_vectors, 'edges': all_edges,
        'candidates': candidates, 'orbit_vectors': orbit_vectors,
        'summary': summary,
    }


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n')
    return sha256_file(path)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    print('Loading cards...')
    built = build()
    s = built['summary']
    for k, v in s.items():
        if isinstance(v, (int, float, bool)):
            print(f'  {k}: {v}')

    st = stamp()
    LATEST.mkdir(parents=True, exist_ok=True)

    name_sha = write_jsonl(LATEST / 'CIELINGO_PHASENAV_NAME_MASS.noema.jsonl', built['all_name_mass'])
    cp_sha = write_jsonl(LATEST / 'CIELINGO_PHASENAV_CONCEPT_PHASES.noema.jsonl', built['concept_phases'])
    ov_sha = write_jsonl(LATEST / 'CIELINGO_PHASENAV_OPERATOR_VECTORS.noema.jsonl', built['operator_vectors'])
    edge_sha = write_jsonl(LATEST / 'CIELINGO_PHASENAV_HOLONOMIC_EDGES.noema.jsonl', built['edges'])
    cand_path = SURFACE / 'cards' / 'cielingo_candidates' / f'{st}_CIELINGO_PHASENAV_WORD_CARD_CANDIDATES_ALL.noema.jsonl'
    cand_sha = write_jsonl(cand_path, built['candidates'])
    orb_sha = write_jsonl(LATEST / 'CIELINGO_PHASENAV_ORBIT_VECTORS.noema.jsonl', built['orbit_vectors'])

    report = {
        'schema': 'NOEMA_CIELINGO_PHASENAV_ENCODE_REPORT_V0_1',
        'created_utc': utc(),
        'status': 'ALL_CARDS_ENCODED_THROUGH_PHASENAV_V2',
        'source_cards': str(CARDS_PATH),
        'summary': s,
        'artifacts': {
            'name_mass_jsonl': str(LATEST / 'CIELINGO_PHASENAV_NAME_MASS.noema.jsonl'),
            'name_mass_sha256': name_sha,
            'concept_phases_jsonl': str(LATEST / 'CIELINGO_PHASENAV_CONCEPT_PHASES.noema.jsonl'),
            'concept_phases_sha256': cp_sha,
            'operator_vectors_jsonl': str(LATEST / 'CIELINGO_PHASENAV_OPERATOR_VECTORS.noema.jsonl'),
            'operator_vectors_sha256': ov_sha,
            'holonomic_edges_jsonl': str(LATEST / 'CIELINGO_PHASENAV_HOLONOMIC_EDGES.noema.jsonl'),
            'holonomic_edges_sha256': edge_sha,
            'word_candidates_jsonl': str(cand_path),
            'word_candidates_sha256': cand_sha,
            'orbit_vectors_jsonl': str(LATEST / 'CIELINGO_PHASENAV_ORBIT_VECTORS.noema.jsonl'),
            'orbit_vectors_sha256': orb_sha,
        },
        'external_noema_sot_claimed': False,
        'external_current_ack_claimed': False,
        'canon_allowed': False,
    }
    report_path = REPORTS / f'{st}_CIELINGO_PHASENAV_ENCODE.noema.json'
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    report_sha = sha256_file(report_path)

    index = {
        'schema': 'NOEMA_CIELINGO_PHASENAV_ENCODE_INDEX_V0_1',
        'created_utc': utc(),
        'latest_report': str(report_path),
        'latest_report_sha256': report_sha,
        'summary': s,
        'artifacts': report['artifacts'],
        'canon_allowed': False,
    }
    index_path = LATEST / 'CIELINGO_PHASENAV_ENCODE_INDEX.noema.json'
    index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')

    print(f'\nReport: {report_path}')
    print(f'Index:  {index_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
