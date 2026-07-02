
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List

@dataclass(frozen=True)
class CelestialNode:
    node_id: str
    level: str
    parent_id: str
    name: str
    binding_strength: float
    phase_load: float


def validate_celestial_register(register: Dict) -> Dict[str, object]:
    nodes = register.get("nodes", [])
    bridges = register.get("bridges", [])
    levels = {n.get("level") for n in nodes}
    parent_ids = {n.get("parent_id") for n in nodes}
    node_ids = {n.get("node_id") for n in nodes}
    orphan_nodes = [n.get("node_id") for n in nodes if n.get("level") != "star" and n.get("parent_id") not in node_ids]
    bridge_missing = [b for b in bridges if b.get("from_star") not in node_ids or b.get("to_star") not in node_ids]
    return {
        "schema_ok": register.get("schema") == "CARD_NONLOCAL_CELESTIAL_REGISTER_V1_2X",
        "has_required_levels": {"star", "planet", "satellite"}.issubset(levels),
        "orphan_nodes": orphan_nodes,
        "bridge_missing_count": len(bridge_missing),
        "valid": register.get("schema") == "CARD_NONLOCAL_CELESTIAL_REGISTER_V1_2X" and not orphan_nodes and not bridge_missing,
    }


def correction_direction(level: str) -> str:
    if level == "satellite":
        return "satellite→planet→star→attractor"
    if level == "planet":
        return "planet→star→attractor"
    if level == "star":
        return "star→attractor"
    return "attractor"
