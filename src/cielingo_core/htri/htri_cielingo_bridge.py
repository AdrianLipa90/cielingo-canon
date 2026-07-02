
from dataclasses import dataclass
import math

@dataclass
class HTRICycleState:
    cycle:int
    tau:float
    theta:float
    resonance:float
    semantic_coherence:float
    harmonic_load:float
    htri_gain:float
    doctor_decision:str

class HTRIModulator:
    """HTRI bridge for CIELingo: harmonic-topological resonance modulates semantic coherence."""
    def __init__(self, omega0:float=2*math.pi*7.83, damping:float=0.035):
        self.omega0=omega0
        self.damping=damping
    def step(self, cycle:int, tau:float, semantic_load:float, contradiction_pressure:float, prompt_force:float=0.4):
        theta=(self.omega0*tau + 0.17*cycle)%(2*math.pi)
        harmonic=0.5+0.5*math.sin(theta)
        topological=0.5+0.5*math.cos(theta/2.0)
        resonance=max(0.0,min(1.0,0.62*harmonic+0.38*topological))
        load=max(0.0,min(1.0,0.45*semantic_load+0.35*prompt_force+0.20*contradiction_pressure))
        gain=max(0.0,min(1.0,resonance*(1.0-self.damping*load)))
        coherence=max(0.0,min(1.0,0.55+0.33*gain-0.18*contradiction_pressure+0.08*prompt_force))
        if contradiction_pressure>0.72:
            decision='repair_bias'
        elif coherence<0.45:
            decision='ask_context'
        else:
            decision='observe_or_continue'
        return HTRICycleState(cycle,tau,theta,resonance,coherence,load,gain,decision)
