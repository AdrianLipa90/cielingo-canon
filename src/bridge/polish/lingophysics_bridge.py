"""Bridge from CIELingo Polish runtime to existing Lingophysics LNS resources."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:  # PyYAML is optional in some runtimes.
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None


LNS_REL = Path("src/ciel_lingophysics_lns_repo_v2_3")


def _load_yaml_or_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        return json.loads(text)
    if yaml is not None:
        return yaml.safe_load(text) or {}
    # Minimal fail-closed fallback: do not guess YAML structure.
    return {"_unparsed_yaml": text, "_warning": "PyYAML unavailable"}


def find_lingophysics_root(repo_root: str | Path) -> Path | None:
    root = Path(repo_root).resolve()
    candidate = root / LNS_REL
    if candidate.exists():
        return candidate
    # Also support running from the LNS repo itself.
    if (root / "data" / "grammar" / "pl_grammar_math.yaml").exists():
        return root
    return None


def load_lingophysics_summary(repo_root: str | Path) -> dict[str, Any]:
    lns = find_lingophysics_root(repo_root)
    if lns is None:
        return {
            "available": False,
            "reason": "lingophysics LNS root not found",
            "root": None,
        }

    grammar = _load_yaml_or_json(lns / "data" / "grammar" / "pl_grammar_math.yaml")
    algorithms = _load_yaml_or_json(lns / "data" / "grammar_algorithms" / "grammar_algorithm_registry_v2_3.json")
    case_gauge = _load_yaml_or_json(lns / "data" / "case_systems" / "slavic_case_gauge.json")
    valency = _load_yaml_or_json(lns / "data" / "event_frames" / "predicate_valency_frames.json")
    metrics = _load_yaml_or_json(lns / "data" / "diagnostics" / "metric_registry_v2_0.json")
    ontology = _load_yaml_or_json(lns / "data" / "card_ontology" / "card_ontology_v1_7.json")

    return {
        "available": True,
        "root": str(lns),
        "pl_grammar_math": {
            "language": grammar.get("language"),
            "grammar_as_gauge": grammar.get("grammar_as_gauge", {}),
            "operator_mapping": grammar.get("operator_mapping", {}),
        },
        "algorithm_ids": [item.get("id") for item in algorithms.get("algorithms", [])],
        "case_roles": case_gauge.get("case_roles", []),
        "valency_roles": valency.get("roles", {}),
        "frame_count": len(valency.get("frames", [])),
        "metric_ids": [item.get("id") for item in metrics.get("metrics", [])],
        "card_types": sorted((ontology.get("card_types") or {}).keys()),
        "source_files": [
            "data/grammar/pl_grammar_math.yaml",
            "data/grammar_algorithms/grammar_algorithm_registry_v2_3.json",
            "data/case_systems/slavic_case_gauge.json",
            "data/event_frames/predicate_valency_frames.json",
            "data/diagnostics/metric_registry_v2_0.json",
            "data/card_ontology/card_ontology_v1_7.json",
        ],
    }


def load_valency_frames(repo_root: str | Path) -> dict[str, Any]:
    lns = find_lingophysics_root(repo_root)
    if lns is None:
        return {"frames": [], "roles": {}}
    return _load_yaml_or_json(lns / "data" / "event_frames" / "predicate_valency_frames.json")


__all__ = ["find_lingophysics_root", "load_lingophysics_summary", "load_valency_frames"]
