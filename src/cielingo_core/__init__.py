"""CIELingo core — language-semantic engine."""
from __future__ import annotations

from importlib import import_module

_SUBMODULES = (
    "alignment",
    "doctor",
    "expressive",
    "global_layer",
    "lingophysics",
    "meaning",
    "regional",
    "semantic_neural",
    "timing",
    "io",
    "bridge",
    "noema_surface",
    "noema_local_sot_agent",
    "noema_pseudoglobal",
    "apocalypos_bridge",
    "architecture",
    "language_spaces",
    "phasenav",
)

__all__ = list(_SUBMODULES)


def __getattr__(name: str):
    """Load public subpackages on first access instead of at package import time."""
    if name in _SUBMODULES:
        module = import_module(f"{__name__}.{name}")
        globals()[name] = module
        return module
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
