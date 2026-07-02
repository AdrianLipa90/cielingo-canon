from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Literal

Decision = Literal["observe", "assist", "advise_pause", "clean_shutdown", "quarantine_trace"]

@dataclass(frozen=True)
class GuardianAngelFinding:
    tick: int
    tau: float
    heartbeat_age_s: float
    residual_bottleneck: float
    energy_pressure: float
    phase_load: float
    stale_lock: bool
    decision: Decision
    reason: str

class TheGuardianAngel:
    """Assistive lifecycle doctor for NOEMA/ApocalypOS daemon processes.

    Not a cage and not a punitive guard. It observes heartbeat, bottleneck,
    energy pressure, phase load and stale-lock state, then routes to an
    assistive lifecycle decision.
    """
    def __init__(self, *, bottleneck_warn: float = 0.25, energy_warn: float = 0.02,
                 stale_after_s: float = 3.0, phase_warn: float = 0.72):
        self.bottleneck_warn = bottleneck_warn
        self.energy_warn = energy_warn
        self.stale_after_s = stale_after_s
        self.phase_warn = phase_warn

    def inspect(self, *, tick: int, tau: float, heartbeat_age_s: float,
                residual_bottleneck: float, energy_pressure: float,
                phase_load: float, stale_lock: bool = False) -> GuardianAngelFinding:
        if stale_lock or heartbeat_age_s > self.stale_after_s:
            return GuardianAngelFinding(tick, tau, heartbeat_age_s, residual_bottleneck,
                                        energy_pressure, phase_load, stale_lock,
                                        "clean_shutdown", "stale heartbeat or lock detected")
        if residual_bottleneck >= self.bottleneck_warn or energy_pressure >= self.energy_warn:
            return GuardianAngelFinding(tick, tau, heartbeat_age_s, residual_bottleneck,
                                        energy_pressure, phase_load, stale_lock,
                                        "advise_pause", "bottleneck or energy threshold exceeded")
        if phase_load >= self.phase_warn:
            return GuardianAngelFinding(tick, tau, heartbeat_age_s, residual_bottleneck,
                                        energy_pressure, phase_load, stale_lock,
                                        "assist", "phase load approaching assist band")
        return GuardianAngelFinding(tick, tau, heartbeat_age_s, residual_bottleneck,
                                    energy_pressure, phase_load, stale_lock,
                                    "observe", "stable lifecycle pulse")

    @staticmethod
    def asdict(finding: GuardianAngelFinding) -> dict:
        return asdict(finding)
