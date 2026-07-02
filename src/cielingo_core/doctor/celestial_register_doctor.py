
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

REQUIRED_PATHS = {
    "satellite": ("satellite", "planet", "star", "attractor"),
    "planet": ("planet", "star", "attractor"),
    "star": ("star", "attractor"),
}

@dataclass(frozen=True)
class CelestialDoctorFinding:
    severity: str
    code: str
    message: str
    node_id: Optional[str] = None
    subsystem_star: Optional[str] = None
    repair_route: str = "observe"
    phase_load: float = 0.0
    holonomic_correction_required: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class CelestialRegisterDoctor:
    """Doctor for enforcing attractor-star-planet-satellite registry discipline.

    It is intentionally small: it validates that operational cards, imports and
    test nodes can be routed through an explicit celestial subsystem hierarchy.
    It does not mutate an immutable historical register; it emits findings and
    repair candidates for append-only NOEMA updates.
    """

    def __init__(self, register: Dict[str, Any]):
        self.register = register
        self.nodes: List[Dict[str, Any]] = list(register.get("nodes", []))
        self.bridges: List[Dict[str, Any]] = list(register.get("bridges", []))
        self.corrections: List[Dict[str, Any]] = list(register.get("holonomic_corrections", []))
        self.by_id: Dict[str, Dict[str, Any]] = {n.get("node_id"): n for n in self.nodes if n.get("node_id")}
        self.stars: List[Dict[str, Any]] = [n for n in self.nodes if n.get("level") == "star"]
        self.planets: List[Dict[str, Any]] = [n for n in self.nodes if n.get("level") == "planet"]
        self.satellites: List[Dict[str, Any]] = [n for n in self.nodes if n.get("level") == "satellite"]

    def validate_register(self) -> Dict[str, Any]:
        findings: List[CelestialDoctorFinding] = []
        schema_ok = self.register.get("schema") == "CARD_NONLOCAL_CELESTIAL_REGISTER_V1_2X"
        if not schema_ok:
            findings.append(CelestialDoctorFinding("blocker", "bad_schema", "Unexpected celestial register schema", repair_route="manual_adapter_required"))
        if not self.stars:
            findings.append(CelestialDoctorFinding("blocker", "missing_stars", "No subsystem stars registered", repair_route="manual_adapter_required"))
        if not self.planets:
            findings.append(CelestialDoctorFinding("blocker", "missing_planets", "No planet modules registered", repair_route="manual_adapter_required"))
        if not self.satellites:
            findings.append(CelestialDoctorFinding("warning", "missing_satellites", "No satellite hooks registered", repair_route="repair_bias"))
        for n in self.nodes:
            level = n.get("level")
            pid = n.get("parent_id")
            nid = n.get("node_id")
            if level in ("planet", "satellite") and pid not in self.by_id:
                findings.append(CelestialDoctorFinding("blocker", "orphan_node", "Node parent is missing", node_id=nid, repair_route="manual_adapter_required", holonomic_correction_required=True))
        for b in self.bridges:
            if b.get("from_star") not in self.by_id or b.get("to_star") not in self.by_id:
                findings.append(CelestialDoctorFinding("blocker", "broken_bridge", "n_holonomic_bridge references missing star", repair_route="manual_adapter_required", holonomic_correction_required=True))
        return {
            "valid": not any(f.severity == "blocker" for f in findings),
            "findings": [f.to_dict() for f in findings],
            "counts": {
                "stars": len(self.stars),
                "planets": len(self.planets),
                "satellites": len(self.satellites),
                "bridges": len(self.bridges),
                "corrections": len(self.corrections),
            },
        }

    def ancestry(self, node_id: str) -> List[str]:
        path: List[str] = []
        current = self.by_id.get(node_id)
        seen = set()
        while current and current.get("node_id") not in seen:
            nid = current.get("node_id")
            seen.add(nid)
            path.append(nid)
            pid = current.get("parent_id")
            current = self.by_id.get(pid) if pid else None
        path.append("ATTRACTOR_CIELINGO_APOCALYPOS_NOEMA")
        return path

    def check_node_route(self, node_id: str) -> CelestialDoctorFinding:
        node = self.by_id.get(node_id)
        if not node:
            return CelestialDoctorFinding("blocker", "unknown_card", "Card is not present in celestial register", node_id=node_id, repair_route="register_card_required", holonomic_correction_required=True)
        level = node.get("level")
        path = self.ancestry(node_id)
        if level == "satellite" and len(path) < 4:
            return CelestialDoctorFinding("blocker", "incomplete_satellite_route", "Satellite must route through planet and star", node_id=node_id, repair_route="repair_celestial_parentage", phase_load=float(node.get("phase_load", 0.0)), holonomic_correction_required=True)
        if level == "planet" and len(path) < 3:
            return CelestialDoctorFinding("blocker", "incomplete_planet_route", "Planet must route through star", node_id=node_id, repair_route="repair_celestial_parentage", phase_load=float(node.get("phase_load", 0.0)), holonomic_correction_required=True)
        return CelestialDoctorFinding("info", "route_ok", "Celestial route is valid", node_id=node_id, subsystem_star=self._star_for(node_id), repair_route="observe", phase_load=float(node.get("phase_load", 0.0)))

    def _star_for(self, node_id: str) -> Optional[str]:
        for nid in self.ancestry(node_id):
            n = self.by_id.get(nid)
            if n and n.get("level") == "star":
                return nid
        return None

    def classify_test_node(self, test_node: Dict[str, Any]) -> Dict[str, Any]:
        region = test_node.get("region", "unknown")
        # Region-to-star mapping deliberately mirrors 1.2V regions.
        region_star = {
            "runtime_smoke": "STAR_RUNTIME_GATEWAY",
            "orbital_semantics_shell": "STAR_MEMORY_ORBITAL",
            "memory_consolidator": "STAR_MEMORY_ORBITAL",
            "bridge_runtime": "STAR_APOCALYPOS_WRAPPER",
            "global_pass_heavy": "STAR_TEST_HOLONOMY",
            "unknown": "STAR_TEST_HOLONOMY",
        }.get(region, "STAR_TEST_HOLONOMY")
        star_exists = region_star in self.by_id
        severity = "info" if star_exists else "warning"
        route = "test_holonomy_region_ok" if star_exists else "manual_adapter_required"
        return {
            "test_id": test_node.get("nodeid") or test_node.get("file") or "unknown_test",
            "region": region,
            "mapped_star": region_star,
            "star_exists": star_exists,
            "severity": severity,
            "repair_route": route,
            "phase_load": float(test_node.get("phase_load", 0.5)),
        }

    def classify_import(self, import_path: str) -> Dict[str, Any]:
        # Minimal deterministic mapping: import path prefixes to subsystem stars.
        mapping = [
            ("cielingo_core.runtime", "STAR_RUNTIME_GATEWAY"),
            ("cielingo_core.doctor", "STAR_DOCTOR_STACK"),
            ("cielingo_core.timing", "STAR_ITP_TAU"),
            ("cielingo_core.logic", "STAR_CIELINGO_SURFACE"),
            ("cielingo_core.registers", "STAR_TEST_HOLONOMY"),
            ("ciel_omega", "STAR_APOCALYPOS_WRAPPER"),
            ("integration", "STAR_APOCALYPOS_WRAPPER"),
            ("flask", "STAR_RUNTIME_GATEWAY"),
        ]
        star = None
        for prefix, candidate in mapping:
            if import_path.startswith(prefix):
                star = candidate
                break
        if star is None:
            star = "STAR_TEST_HOLONOMY"
        exists = star in self.by_id
        return {
            "import_path": import_path,
            "mapped_star": star,
            "star_exists": exists,
            "severity": "info" if exists else "warning",
            "repair_route": "import_star_route_ok" if exists else "manual_adapter_required",
        }

    def doctor_report(self, test_nodes: Sequence[Dict[str, Any]] = (), imports: Sequence[str] = ()) -> Dict[str, Any]:
        validation = self.validate_register()
        test_findings = [self.classify_test_node(t) for t in test_nodes]
        import_findings = [self.classify_import(i) for i in imports]
        blockers = [f for f in validation["findings"] if f.get("severity") == "blocker"]
        warnings = [f for f in validation["findings"] if f.get("severity") == "warning"]
        return {
            "schema": "CELESTIAL_REGISTER_DOCTOR_REPORT_V1_2Y",
            "register_valid": validation["valid"],
            "register_counts": validation["counts"],
            "validation_findings": validation["findings"],
            "test_node_findings": test_findings,
            "import_findings": import_findings,
            "blocker_count": len(blockers),
            "warning_count": len(warnings),
            "doctor_decision": "continue" if validation["valid"] else "repair_required",
        }
