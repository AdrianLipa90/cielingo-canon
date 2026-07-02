"""Thin ApocalypOS bridge for CIELingo.

This package is deliberately observational. It binds CIELingo to an
ApocalypOS working artifact without importing ApocalypOS runtime modules,
starting listeners, writing NOEMA, updating CURRENT, or promoting SOURCE/canon.
"""

from .thin_wrapper import (
    ApocalypOSArtifactRef,
    ApocalypOSWorkingState,
    ApocalypOSThinWrapper,
    build_working_state,
)

__all__ = [
    "ApocalypOSArtifactRef",
    "ApocalypOSWorkingState",
    "ApocalypOSThinWrapper",
    "build_working_state",
]
