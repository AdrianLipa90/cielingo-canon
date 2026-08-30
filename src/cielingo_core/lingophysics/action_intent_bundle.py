"""Bundle-level admission state for candidate ActionIntentFrames."""
from __future__ import annotations
from dataclasses import dataclass, replace
from hashlib import sha256
import json, re
from typing import Any
from .action_intent_frame import ActionIntentFrame, extract_polish_action_intent_frames

ACTION_INTENT_BUNDLE_SCHEMA = "CIEL_ACTION_INTENT_BUNDLE_V0_1"
_COORDINATION = frozenset({"a", "ale", "oraz", "i"})
_PUNCT = ".,?!:;\"'()[]{}"

def _digest(payload: Any) -> str:
    return sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
def _norm(token: str) -> str: return str(token).strip(_PUNCT).casefold()

@dataclass(frozen=True)
class ActionIntentBundle:
    language_id: str
    surface_text: str
    frames: tuple[ActionIntentFrame, ...]
    coordination_detected: bool
    commitment: str
    candidate_only: bool = True
    schema: str = ACTION_INTENT_BUNDLE_SCHEMA

    @classmethod
    def create(cls, *, language_id: str, surface_text: str, frames: tuple[ActionIntentFrame,...] | list[ActionIntentFrame], coordination_detected: bool):
        packed=tuple(frames)
        body={"schema":ACTION_INTENT_BUNDLE_SCHEMA,"language_id":language_id,"surface_text":surface_text,"frames":[f.to_dict() for f in packed],"coordination_detected":bool(coordination_detected),"candidate_only":True}
        c=_digest(body)
        obj=cls(language_id,surface_text,packed,bool(coordination_detected),c)
        issues=obj.validate()
        if issues: raise ValueError("; ".join(issues))
        return obj

    @property
    def multi_action_detected(self) -> bool: return len(self.frames) > 1
    @property
    def structurally_complete(self) -> bool: return bool(self.frames) and all(f.structurally_complete for f in self.frames)
    @property
    def scope_review_required(self) -> bool: return any(f.negation_detected or f.condition_detected for f in self.frames)
    @property
    def gate_status(self) -> str:
        if not self.frames: return "NO_ACTION"
        if self.multi_action_detected: return "MULTI_ACTION_REVIEW"
        if not self.structurally_complete: return "INCOMPLETE_ARGUMENTS"
        if self.scope_review_required: return "SCOPE_REVIEW"
        if self.coordination_detected: return "COORDINATION_REVIEW"
        return "CANDIDATE_SINGLE_ACTION"
    @property
    def execution_authorized(self) -> bool:
        # ActionIntent is semantic evidence only. Policy/execution authority lives downstream.
        return False

    def validate(self) -> list[str]:
        issues=[]
        if self.schema != ACTION_INTENT_BUNDLE_SCHEMA: issues.append("action intent bundle schema mismatch")
        if self.language_id != "pl": issues.append("ActionIntentBundle v0.1 expects language_id=pl")
        if not self.surface_text: issues.append("action intent bundle surface_text is required")
        if not self.candidate_only: issues.append("action intent bundle must remain candidate-only")
        for frame in self.frames: issues.extend(frame.validate())
        body={"schema":self.schema,"language_id":self.language_id,"surface_text":self.surface_text,"frames":[f.to_dict() for f in self.frames],"coordination_detected":self.coordination_detected,"candidate_only":self.candidate_only}
        if self.commitment != _digest(body): issues.append("action intent bundle commitment mismatch")
        return issues

    def to_dict(self) -> dict[str,Any]:
        return {"schema":self.schema,"language_id":self.language_id,"surface_text":self.surface_text,"frames":[f.to_dict() for f in self.frames],"coordination_detected":self.coordination_detected,"multi_action_detected":self.multi_action_detected,"structurally_complete":self.structurally_complete,"scope_review_required":self.scope_review_required,"gate_status":self.gate_status,"execution_authorized":False,"candidate_only":self.candidate_only,"commitment":self.commitment}

def build_polish_action_intent_bundle(text: str) -> ActionIntentBundle:
    tokens=[t for t in re.split(r"\s+", str(text).strip()) if t]
    coordination=any(_norm(t) in _COORDINATION for t in tokens)
    return ActionIntentBundle.create(language_id="pl",surface_text=text,frames=extract_polish_action_intent_frames(text),coordination_detected=coordination)

__all__=["ACTION_INTENT_BUNDLE_SCHEMA","ActionIntentBundle","build_polish_action_intent_bundle"]
