from __future__ import annotations

from tests.test_canonical_lingophysics_adapter import _endpoint, _request


def test_canonical_response_semantic_diagnostic() -> None:
    response = _endpoint().handle(_request())
    assert response["status"] == "ACK", response
