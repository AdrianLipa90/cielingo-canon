"""Fail-closed negation/condition scope receipts bound to ActionIntentBundle."""
from __future__ import annotations
from dataclasses import dataclass, replace
from hashlib import sha256
import json, re
from typing import Any
from .action_intent_bundle import ActionIntentBundle, build_polish_action_intent_bundle

ACTION_SCOPE_RECEIPT_SCHEMA = "CIEL_ACTION_SCOPE_RECEIPT_V0_1"
ACTION_SCOPE_BINDING_SCHEMA = "CIEL_ACTION_SCOPE_BINDING_V0_1"
_PUNCT = ".,?!:;\"'()[]{}"
_NEG = "nie"
_COND = frozenset({"jeśli","jeżeli","dopóki","gdy","kiedy","tylko","dopiero"})
_VERBS = {
    "SENDS": frozenset({"wyślij","wyslij","wyślijcie","wysyłaj","wysylaj"}),
    "ARCHIVES": frozenset({"zarchiwizuj","archiwizuj"}),
    "DELETES": frozenset({"usuń","usun","usuwaj"}),
    "SETS_STATUS": frozenset({"zmień","zmien","ustaw"}),
    "APPROVES_SUPPLIER": frozenset({"zatwierdź","zatwierdz","zatwierdzaj"}),
    "CREATES_CONTRACT": frozenset({"utwórz","utworz","stwórz","stworz","twórz","tworz"}),
}

def _digest(payload: Any) -> str:
    return sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
def _norm(token:str)->str: return str(token).strip(_PUNCT).casefold()
def _tokens(text:str)->list[str]: return [t for t in re.split(r"\s+",str(text).strip()) if t]

@dataclass(frozen=True)
class ActionScopeBinding:
    frame_commitment: str
    operator: str
    trigger_token_index: int
    trigger_surface: str
    negated_action: bool
    conditional_action: bool
    post_action_negation_review: bool
    condition_marker_indices: tuple[int,...]
    status: str
    commitment: str
    candidate_only: bool=True
    schema: str=ACTION_SCOPE_BINDING_SCHEMA
    @classmethod
    def create(cls, **kwargs):
        body={"schema":ACTION_SCOPE_BINDING_SCHEMA,**kwargs,"condition_marker_indices":list(kwargs.get("condition_marker_indices",())),"candidate_only":True}
        c=_digest(body)
        obj=cls(
            frame_commitment=str(kwargs["frame_commitment"]),operator=str(kwargs["operator"]),
            trigger_token_index=int(kwargs["trigger_token_index"]),trigger_surface=str(kwargs["trigger_surface"]),
            negated_action=bool(kwargs["negated_action"]),conditional_action=bool(kwargs["conditional_action"]),
            post_action_negation_review=bool(kwargs["post_action_negation_review"]),
            condition_marker_indices=tuple(int(i) for i in kwargs.get("condition_marker_indices",())),
            status=str(kwargs["status"]),commitment=c,
        )
        issues=obj.validate()
        if issues: raise ValueError("; ".join(issues))
        return obj
    def validate(self)->list[str]:
        issues=[]
        if not self.frame_commitment or len(self.frame_commitment)!=64: issues.append("action scope frame commitment must be SHA-256")
        if self.operator not in _VERBS: issues.append("action scope operator unsupported")
        if self.trigger_token_index < 0 or not self.trigger_surface: issues.append("action scope trigger provenance invalid")
        allowed={"CLEAR","NEGATED_ACTION","CONDITIONAL_ACTION","NEGATED_CONDITIONAL_ACTION","POST_ACTION_NEGATION_REVIEW","AMBIGUOUS_SCOPE"}
        if self.status not in allowed: issues.append("action scope status invalid")
        if self.status=="CLEAR" and (self.negated_action or self.conditional_action or self.post_action_negation_review): issues.append("CLEAR scope cannot carry blockers")
        if not self.candidate_only: issues.append("action scope binding must remain candidate-only")
        body={"schema":self.schema,"frame_commitment":self.frame_commitment,"operator":self.operator,"trigger_token_index":self.trigger_token_index,"trigger_surface":self.trigger_surface,"negated_action":self.negated_action,"conditional_action":self.conditional_action,"post_action_negation_review":self.post_action_negation_review,"condition_marker_indices":list(self.condition_marker_indices),"status":self.status,"candidate_only":self.candidate_only}
        if self.commitment != _digest(body): issues.append("action scope binding commitment mismatch")
        return issues
    def to_dict(self):
        return {"schema":self.schema,"frame_commitment":self.frame_commitment,"operator":self.operator,"trigger_token_index":self.trigger_token_index,"trigger_surface":self.trigger_surface,"negated_action":self.negated_action,"conditional_action":self.conditional_action,"post_action_negation_review":self.post_action_negation_review,"condition_marker_indices":list(self.condition_marker_indices),"status":self.status,"candidate_only":self.candidate_only,"commitment":self.commitment}

@dataclass(frozen=True)
class ActionScopeReceipt:
    language_id: str
    surface_text: str
    action_bundle_commitment: str
    bindings: tuple[ActionScopeBinding,...]
    status: str
    commitment: str
    candidate_only: bool=True
    schema: str=ACTION_SCOPE_RECEIPT_SCHEMA
    @classmethod
    def create(cls, *, language_id:str,surface_text:str,action_bundle_commitment:str,bindings:tuple[ActionScopeBinding,...]|list[ActionScopeBinding],status:str):
        packed=tuple(bindings); body={"schema":ACTION_SCOPE_RECEIPT_SCHEMA,"language_id":language_id,"surface_text":surface_text,"action_bundle_commitment":action_bundle_commitment,"bindings":[b.to_dict() for b in packed],"status":status,"candidate_only":True}; c=_digest(body)
        obj=cls(language_id,surface_text,action_bundle_commitment,packed,status,c)
        issues=obj.validate()
        if issues: raise ValueError("; ".join(issues))
        return obj
    @property
    def scope_clear(self)->bool: return self.status=="CLEAR"
    @property
    def execution_authorized(self)->bool: return False
    def validate(self)->list[str]:
        issues=[]
        if self.language_id!="pl": issues.append("ActionScopeReceipt v0.1 expects language_id=pl")
        if len(self.action_bundle_commitment)!=64: issues.append("action scope bundle commitment must be SHA-256")
        for b in self.bindings: issues.extend(b.validate())
        allowed={"NO_ACTION","CLEAR","SCOPE_REVIEW","MULTI_ACTION_REVIEW","COORDINATION_REVIEW","INCOMPLETE_ARGUMENTS","AMBIGUOUS_SCOPE"}
        if self.status not in allowed: issues.append("action scope receipt status invalid")
        if not self.candidate_only: issues.append("action scope receipt must remain candidate-only")
        body={"schema":self.schema,"language_id":self.language_id,"surface_text":self.surface_text,"action_bundle_commitment":self.action_bundle_commitment,"bindings":[b.to_dict() for b in self.bindings],"status":self.status,"candidate_only":self.candidate_only}
        if self.commitment != _digest(body): issues.append("action scope receipt commitment mismatch")
        return issues
    def to_dict(self):
        return {"schema":self.schema,"language_id":self.language_id,"surface_text":self.surface_text,"action_bundle_commitment":self.action_bundle_commitment,"bindings":[b.to_dict() for b in self.bindings],"status":self.status,"scope_clear":self.scope_clear,"execution_authorized":False,"candidate_only":self.candidate_only,"commitment":self.commitment}

def _trigger_candidates(tokens:list[str]):
    low=[_norm(t) for t in tokens]; out=[]
    for i,w in enumerate(low):
        for op,forms in _VERBS.items():
            if w in forms: out.append((i,op,tokens[i])); break
    return out

def build_polish_action_scope_receipt(text:str, bundle:ActionIntentBundle|None=None)->ActionScopeReceipt:
    bundle=bundle or build_polish_action_intent_bundle(text)
    if bundle.surface_text != text: raise ValueError("action scope text/bundle mismatch")
    tokens=_tokens(text); low=[_norm(t) for t in tokens]; triggers=_trigger_candidates(tokens)
    if len(triggers)!=len(bundle.frames):
        status="NO_ACTION" if not bundle.frames and not triggers else "AMBIGUOUS_SCOPE"
        return ActionScopeReceipt.create(language_id="pl",surface_text=text,action_bundle_commitment=bundle.commitment,bindings=(),status=status)
    cond_indices=tuple(i for i,w in enumerate(low) if w in _COND)
    neg_indices=tuple(i for i,w in enumerate(low) if w==_NEG)
    bindings=[]
    for frame,(trigger_i,op,trigger_surface) in zip(bundle.frames,triggers):
        if op != frame.operator:
            return ActionScopeReceipt.create(language_id="pl",surface_text=text,action_bundle_commitment=bundle.commitment,bindings=(),status="AMBIGUOUS_SCOPE")
        immediate_negated=trigger_i>0 and low[trigger_i-1]==_NEG
        next_trigger=min((i for i,_,_ in triggers if i>trigger_i),default=len(tokens))
        later_neg=[i for i in neg_indices if trigger_i < i < next_trigger]
        post_review=bool(later_neg) and not immediate_negated
        conditional=bool(cond_indices)
        if immediate_negated and conditional: bstatus="NEGATED_CONDITIONAL_ACTION"
        elif immediate_negated: bstatus="NEGATED_ACTION"
        elif post_review: bstatus="POST_ACTION_NEGATION_REVIEW"
        elif conditional: bstatus="CONDITIONAL_ACTION"
        else: bstatus="CLEAR"
        bindings.append(ActionScopeBinding.create(frame_commitment=frame.commitment,operator=frame.operator,trigger_token_index=trigger_i,trigger_surface=trigger_surface,negated_action=immediate_negated,conditional_action=conditional,post_action_negation_review=post_review,condition_marker_indices=cond_indices,status=bstatus))
    if bundle.gate_status=="MULTI_ACTION_REVIEW": status="MULTI_ACTION_REVIEW"
    elif bundle.gate_status=="COORDINATION_REVIEW": status="COORDINATION_REVIEW"
    elif bundle.gate_status=="INCOMPLETE_ARGUMENTS": status="INCOMPLETE_ARGUMENTS"
    elif any(b.status!="CLEAR" for b in bindings): status="SCOPE_REVIEW"
    elif bundle.gate_status=="NO_ACTION": status="NO_ACTION"
    else: status="CLEAR"
    return ActionScopeReceipt.create(language_id="pl",surface_text=text,action_bundle_commitment=bundle.commitment,bindings=bindings,status=status)

__all__=["ACTION_SCOPE_RECEIPT_SCHEMA","ACTION_SCOPE_BINDING_SCHEMA","ActionScopeBinding","ActionScopeReceipt","build_polish_action_scope_receipt"]
