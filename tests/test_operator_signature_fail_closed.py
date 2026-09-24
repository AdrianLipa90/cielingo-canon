from __future__ import annotations

from dataclasses import replace

from cielingo_core.lingophysics import extract_polish_case_port_frames, type_case_port_frame


def _one(text: str):
    frames = extract_polish_case_port_frames(text)
    assert len(frames) == 1
    return frames[0]


def test_duplicate_operator_port_fails_closed() -> None:
    frame = _one("Daję Zosi książkę")
    duplicate = frame.ports[1]
    report = type_case_port_frame(replace(frame, ports=frame.ports + (duplicate,)))
    assert report.valid is False
    assert report.duplicate_ports == ("DAT:recipient",)
    assert report.universal_roles == ()


def test_invalid_case_frame_fails_closed_before_normalization() -> None:
    frame = _one("Daję Zosi książkę")
    report = type_case_port_frame(replace(frame, candidate_only=False))
    assert report.valid is False
    assert any("candidate-only" in issue for issue in report.frame_issues)
    assert report.universal_roles == ()


def test_typing_report_binds_signature_commitment() -> None:
    report = type_case_port_frame(_one("Daję Zosi książkę"))
    assert report.valid is True
    assert report.signature_id == "GIVES@0.1.0"
    assert report.signature_commitment is not None
    assert len(report.signature_commitment) == 64
    assert report.to_dict()["signature_commitment"] == report.signature_commitment
