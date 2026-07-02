"""Local pseudo-global NOEMA node.

This package provides a bounded filesystem node for local GPT-instance handoff.
It is outside NOEMA SoT and must not be treated as CURRENT, ACK, or canon.
"""

from .node import (
    LocalNoemaPseudoGlobalNode,
    PseudoGlobalInstance,
    PseudoGlobalPacket,
    PseudoGlobalStatus,
)

__all__ = [
    "LocalNoemaPseudoGlobalNode",
    "PseudoGlobalInstance",
    "PseudoGlobalPacket",
    "PseudoGlobalStatus",
]

from cielingo_core.noema_pseudoglobal.lifecycle import audit_pseudoglobal_lifecycle, install_default_noema_global_gadgets

__all__ = ["LocalNoemaPseudoGlobalNode", "audit_pseudoglobal_lifecycle", "install_default_noema_global_gadgets"]
