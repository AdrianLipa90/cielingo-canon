from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence
import re
import time

@dataclass(frozen=True)
class VectorRequest:
    method: str
    path: str
    payload: Dict[str, Any]
    headers: Dict[str, str]
    earth_time_utc: str = "orientation_anchor_only"

@dataclass(frozen=True)
class VectorResponse:
    status: int
    route: str
    decision: str
    payload: Dict[str, Any]
    notes: str

@dataclass(frozen=True)
class RouteSpec:
    path: str
    methods: Sequence[str]
    handler_name: str
    vector_axes: Sequence[str]
    doctor_required: bool = True

class VectorizedNoemaApp:
    """A vectorized Flask analogue for NOEMA/ITP runtime.

    It is deliberately not a web server.  It models the useful part of Flask for
    this project: route registration, request dispatch, typed request/response
    envelopes and Doctor-compatible batch/vector execution.  Time is carried as
    NOEMA/ITP metadata, not as an OS daemon claim.
    """

    def __init__(self, name: str = "noema_vector_app"):
        self.name = name
        self._routes: Dict[str, RouteSpec] = {}
        self._handlers: Dict[str, Callable[[VectorRequest], VectorResponse]] = {}

    def route(self, path: str, methods: Sequence[str] = ("GET",), *, vector_axes: Sequence[str] = ("semantic_load",)):
        def decorator(fn: Callable[[VectorRequest], VectorResponse]):
            spec = RouteSpec(path=path, methods=tuple(m.upper() for m in methods), handler_name=fn.__name__, vector_axes=tuple(vector_axes))
            self._routes[path] = spec
            self._handlers[fn.__name__] = fn
            return fn
        return decorator

    @property
    def routes(self) -> Dict[str, RouteSpec]:
        return dict(self._routes)

    def dispatch(self, req: VectorRequest) -> VectorResponse:
        spec = self._routes.get(req.path)
        if not spec:
            return VectorResponse(404, req.path, "route_not_found", {"path": req.path}, "no matching NOEMA route")
        if req.method.upper() not in spec.methods:
            return VectorResponse(405, req.path, "method_not_allowed", {"method": req.method, "allowed": list(spec.methods)}, "method rejected by vectorized route contract")
        return self._handlers[spec.handler_name](req)

    def dispatch_many(self, requests: Iterable[VectorRequest]) -> List[VectorResponse]:
        return [self.dispatch(r) for r in requests]

    def route_matrix(self) -> List[Dict[str, Any]]:
        return [asdict(spec) for spec in self._routes.values()]


def _pressure(payload: Mapping[str, Any], key: str, default: float = 0.0) -> float:
    try:
        return max(0.0, min(1.0, float(payload.get(key, default))))
    except Exception:
        return default


def build_default_noema_vector_app() -> VectorizedNoemaApp:
    app = VectorizedNoemaApp("apocalypos_cielingo_noema_vectorized_app")

    @app.route("/itp/tick", methods=("POST",), vector_axes=("semantic_load", "holonomy_pressure", "contradiction_pressure"))
    def itp_tick(req: VectorRequest) -> VectorResponse:
        semantic = _pressure(req.payload, "semantic_load")
        hol = _pressure(req.payload, "holonomy_pressure")
        contradiction = _pressure(req.payload, "contradiction_pressure")
        energy_pressure = round(0.40 * semantic + 0.35 * hol + 0.25 * contradiction, 6)
        decision = "observe" if energy_pressure < 0.35 else "repair_bias" if energy_pressure < 0.75 else "block_and_quarantine"
        return VectorResponse(200, req.path, decision, {"energy_pressure": energy_pressure, "continuum": "D<=>epsilon"}, "ITP tick routed through vectorized NOEMA app")

    @app.route("/doctor/imports", methods=("POST",), vector_axes=("missing_imports", "shim_pressure", "runtime_pressure"))
    def doctor_imports(req: VectorRequest) -> VectorResponse:
        missing = req.payload.get("missing_imports", [])
        shim_pressure = _pressure(req.payload, "shim_pressure")
        runtime_pressure = _pressure(req.payload, "runtime_pressure")
        pressure = round(min(1.0, 0.2 * len(missing) + 0.35 * shim_pressure + 0.45 * runtime_pressure), 6)
        decision = "clean" if pressure < 0.25 else "repair_bias" if pressure < 0.85 else "import_block"
        return VectorResponse(200, req.path, decision, {"import_pressure": pressure, "missing_imports": list(missing)}, "Import Doctor route")

    @app.route("/registry/preflight", methods=("POST",), vector_axes=("route_density", "card_integrity", "cache_warmth"))
    def registry_preflight(req: VectorRequest) -> VectorResponse:
        route_density = _pressure(req.payload, "route_density")
        card_integrity = _pressure(req.payload, "card_integrity")
        cache_warmth = _pressure(req.payload, "cache_warmth")
        readiness = round(0.34 * route_density + 0.43 * card_integrity + 0.23 * cache_warmth, 6)
        decision = "boot_continue" if readiness >= 0.70 else "repair_bias" if readiness >= 0.40 else "preflight_block"
        return VectorResponse(200, req.path, decision, {"registry_readiness": readiness}, "Registry preflight route")

    return app
