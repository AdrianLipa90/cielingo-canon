"""CIELingo bridge — external and NOEMA surface integration."""
from __future__ import annotations
from .filesense_boundary import FileSenseBoundaryReport
from .filesense_surface import FileSenseHit, FileSenseReport, FileSenseSurface
from .global_filesense_adapter import FileSenseGlobalResult
from .gremlin_full_bridge import (
    ConsequenceClass,
    GremlinAuthorization,
    GremlinCapabilitySnapshot,
    GremlinFullBridge,
    GremlinTransport,
    MCPClientTransport,
    classify_consequence,
)
from .noema_marker_boundary import NoemaMarkerBoundaryReport

__all__ = [
    "FileSenseBoundaryReport",
    "FileSenseHit",
    "FileSenseReport",
    "FileSenseSurface",
    "FileSenseGlobalResult",
    "ConsequenceClass",
    "GremlinAuthorization",
    "GremlinCapabilitySnapshot",
    "GremlinFullBridge",
    "GremlinTransport",
    "MCPClientTransport",
    "classify_consequence",
    "NoemaMarkerBoundaryReport",
]
