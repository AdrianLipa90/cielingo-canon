
"""GLOBAL codecs v1.1C: forward common-frame encode and reverse regional request."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Any

from cielingo_core.global_layer.common_functional_frame import CommonFunctionalFrame, build_common_functional_frame
from cielingo_core.global_layer.response_contract import AllowedResponseContract


@dataclass(frozen=True)
class GlobalEncodeReport:
    report_id: str
    input_ref: str
    frame: CommonFunctionalFrame
    confidence: float
    codec_direction: str = "surface_to_common_functional_frame"
    canon_allowed: bool = False
    source_promotion_allowed: bool = False
    noema_writeback_allowed: bool = False
    current_update_allowed: bool = False
    runtime_execution_allowed: bool = False

    def validate(self) -> list[str]:
        issues = []
        issues.extend(self.frame.validate())
        if not 0.0 <= self.confidence <= 1.0:
            issues.append("confidence must be in [0,1]")
        if self.codec_direction != "surface_to_common_functional_frame":
            issues.append("wrong codec_direction")
        for flag in [self.canon_allowed, self.source_promotion_allowed, self.noema_writeback_allowed, self.current_update_allowed, self.runtime_execution_allowed]:
            if flag:
                issues.append("GLOBAL encode report must not grant authority")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "input_ref": self.input_ref,
            "frame": self.frame.to_dict(),
            "confidence": self.confidence,
            "codec_direction": self.codec_direction,
            "canon_allowed": self.canon_allowed,
            "source_promotion_allowed": self.source_promotion_allowed,
            "noema_writeback_allowed": self.noema_writeback_allowed,
            "current_update_allowed": self.current_update_allowed,
            "runtime_execution_allowed": self.runtime_execution_allowed,
        }

    def stable_hash(self) -> str:
        return sha256(json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class RegionalRealizationRequest:
    request_id: str
    language_id: str
    answer_kind: str
    required_markers: list[str]
    forbidden_claims: list[str]
    severity: str
    codec_direction: str = "global_contract_to_regional_realization_request"
    canon_allowed: bool = False
    source_promotion_allowed: bool = False
    noema_writeback_allowed: bool = False
    current_update_allowed: bool = False
    runtime_execution_allowed: bool = False

    def validate(self) -> list[str]:
        issues = []
        if not self.language_id:
            issues.append("language_id is required")
        if not self.required_markers:
            issues.append("required_markers must not be empty")
        if self.codec_direction != "global_contract_to_regional_realization_request":
            issues.append("wrong codec_direction")
        for flag in [self.canon_allowed, self.source_promotion_allowed, self.noema_writeback_allowed, self.current_update_allowed, self.runtime_execution_allowed]:
            if flag:
                issues.append("RegionalRealizationRequest must not grant authority")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def stable_hash(self) -> str:
        return sha256(json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def encode_surface_to_common_frame(text: str, *, input_ref: str = "surface", language_hint: str = "pl") -> GlobalEncodeReport:
    frame = build_common_functional_frame(text, language_hint=language_hint)
    confidence = round(min(0.95, 0.50 + frame.functional_entropy * 0.20 + (1.0 - frame.operator_risk) * 0.25), 6)
    payload = json.dumps({"input_ref": input_ref, "frame": frame.frame_id, "confidence": confidence}, sort_keys=True)
    return GlobalEncodeReport(
        report_id="global_encode_" + sha256(payload.encode("utf-8")).hexdigest()[:16],
        input_ref=input_ref,
        frame=frame,
        confidence=confidence,
    )


def decode_contract_to_regional_request(contract: AllowedResponseContract, language_id: str = "pl") -> RegionalRealizationRequest:
    payload = json.dumps({"contract": contract.contract_id, "language": language_id}, sort_keys=True)
    return RegionalRealizationRequest(
        request_id="regional_request_" + sha256(payload.encode("utf-8")).hexdigest()[:16],
        language_id=language_id,
        answer_kind=contract.answer_kind,
        required_markers=list(contract.required_markers),
        forbidden_claims=list(contract.forbidden_claims),
        severity=contract.severity,
    )
