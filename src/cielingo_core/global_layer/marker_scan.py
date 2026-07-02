
from __future__ import annotations

def forbidden_claims_after_required_markers(text: str, required_markers: list[str], forbidden_claims: list[str]) -> list[str]:
    """Scan forbidden claims after masking required safety markers.

    Example: 'nie SOURCE' is a required marker and must not be counted as a
    positive SOURCE claim.
    """
    surface = text.lower()
    for marker in sorted(required_markers, key=len, reverse=True):
        surface = surface.replace(marker.lower(), " ")
    return [claim for claim in forbidden_claims if claim.lower() in surface]
