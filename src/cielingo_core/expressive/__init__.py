"""CIELingo expressive package."""
from __future__ import annotations

from importlib import import_module

_EXPORTS = {
    "ExpressiveSurfacePlan": "expressive_codecs",
    "ExpressivePriority": "expressive_contract",
    "ExpressiveMove": "expressive_contract",
    "ExpressiveContract": "expressive_contract",
    "ExpressiveStyle": "style_renderer",
    "ExpressiveResponseDraft": "style_renderer",
}

__all__ = list(_EXPORTS)


def __getattr__(name: str):
    module_name = _EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = import_module(f"{__name__}.{module_name}")
    value = getattr(module, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
