from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable, Mapping

@dataclass(frozen=True)
class BiasFinding:
    bias_id: str
    pressure: float
    remedy: str
    decision: str

class CIELingoBiasDoctor:
    def __init__(self, registry: Mapping):
        self.registry = registry

    def diagnose(self, runtime_signals: Mapping[str, float]) -> list[BiasFinding]:
        findings: list[BiasFinding] = []
        for item in self.registry.get("bias_surfaces", []):
            base = float(item.get("initial_pressure", 0.0))
            target = float(item.get("target_pressure", 0.0))
            signal_key = item["id"].lower()
            modifier = float(runtime_signals.get(signal_key, 0.0))
            pressure = max(0.0, min(1.0, 0.7 * base + 0.3 * modifier))
            decision = "observe" if pressure <= 0.25 else ("repair_bias" if pressure <= 0.6 else "quarantine_candidate")
            findings.append(BiasFinding(item["id"], pressure, item.get("doctor_remedy", "review"), decision))
        return findings

    @staticmethod
    def mean_pressure(findings: Iterable[BiasFinding]) -> float:
        fs = list(findings)
        return sum(f.pressure for f in fs) / len(fs) if fs else 0.0
