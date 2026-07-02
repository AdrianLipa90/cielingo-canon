"""CIELingo language spaces — multilingual grammar engines."""
from __future__ import annotations
from .policy import LanguageTrajectory
from . import pl, en, ja
__all__ = ["LanguageTrajectory", "pl", "en", "ja"]
