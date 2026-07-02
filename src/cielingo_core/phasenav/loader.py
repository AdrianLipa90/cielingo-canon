"""Load phasenav encoded data from the latest runtime output."""
from __future__ import annotations
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

PHASENAV_LATEST = (
    Path(__file__).resolve().parents[3]
    / "runtime" / "phasenav" / "latest"
)

@dataclass
class PhasenavData:
    name_mass: dict[str, dict[str, Any]] = field(default_factory=dict)
    name_mass_by_card_id: dict[str, dict[str, Any]] = field(default_factory=dict)
    concept_phases: dict[str, dict[str, Any]] = field(default_factory=dict)
    operator_vectors: dict[str, list[float]] = field(default_factory=dict)
    edges: list[dict[str, Any]] = field(default_factory=list)
    orbits: dict[str, list[float]] = field(default_factory=dict)
    edges_by_concept: dict[str, list[dict[str, Any]]] = field(default_factory=dict)

def load_phasenav(base_path: Path | None = None) -> PhasenavData:
    base = base_path or PHASENAV_LATEST
    data = PhasenavData()

    data.name_mass = _load_jsonl_map(base / "CIELINGO_PHASENAV_NAME_MASS.noema.jsonl", "normalized")
    for nm in data.name_mass.values():
        cid = nm.get("card_id", "")
        if cid:
            data.name_mass_by_card_id[cid] = nm

    data.concept_phases = _load_jsonl_map(base / "CIELINGO_PHASENAV_CONCEPT_PHASES.noema.jsonl", "concept_card_id")
    data.operator_vectors = _load_orbit_map(base / "CIELINGO_PHASENAV_OPERATOR_VECTORS.noema.jsonl")

    data.edges = [json.loads(line) for line in _lines(base / "CIELINGO_PHASENAV_HOLONOMIC_EDGES.noema.jsonl")]

    data.orbits = _load_orbit_map(base / "CIELINGO_PHASENAV_ORBIT_VECTORS.noema.jsonl")

    data.edges_by_concept = {}
    for e in data.edges:
        cid = e["concept_id"]
        data.edges_by_concept.setdefault(cid, []).append(e)

    return data

def _lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [l for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]

def _load_jsonl_map(path: Path, key_field: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for line in _lines(path):
        obj = json.loads(line)
        out[str(obj.get(key_field, ""))] = obj
    return out

def _load_orbit_map(path: Path) -> dict[str, list[float]]:
    out: dict[str, list[float]] = {}
    for line in _lines(path):
        obj = json.loads(line)
        vec = obj.get("orbit_vector") or obj.get("vector") or obj.get("orbital_11dim_vector")
        if vec:
            out[obj["card_id"]] = [float(x) for x in vec]
    return out
