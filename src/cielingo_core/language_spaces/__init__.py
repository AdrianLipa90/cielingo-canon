"""CIELingo language spaces — multilingual grammar engines."""
from __future__ import annotations

from importlib import import_module

__all__ = ["LanguageTrajectory", "pl", "en", "ja"]

_EXPORTS = {
    "LanguageTrajectory": (".policy", "LanguageTrajectory"),
    "pl": (".pl", None),
    "en": (".en", None),
    "ja": (".ja", None),
}


def __getattr__(name: str):
    target = _EXPORTS.get(name)
    if target is None:
        raise AttributeError(name)
    module_name, attr = target
    module = import_module(module_name, __name__)
    value = module if attr is None else getattr(module, attr)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
