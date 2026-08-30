"""Bounded operational action-intent frames for CIELingo.

Action recognition is candidate-only. Negation and condition markers are
retained as blockers for downstream scope/policy admission; this module never
grants execution authority.
"""
from __future__ import annotations
from dataclasses import dataclass, replace
from hashlib import sha256
import json, re
from typing import Any, Iterable

ACTION_INTENT_FRAME_SCHEMA = "CIEL_ACTION_INTENT_FRAME_V0_1"
_ACTION_REQUIREMENTS = {
    "SENDS": ("object", "recipient"), "ARCHIVES": ("object",),
    "DELETES": ("object",), "SETS_STATUS": ("record", "status"),
    "APPROVES_SUPPLIER": ("supplier",), "CREATES_CONTRACT": ("counterparty",),
}
_NEGATION = frozenset({"nie"})
_CONDITIONS = frozenset({"jeśli", "jeżeli", "dopóki", "gdy", "kiedy", "tylko", "dopiero"})
_CLAUSE = frozenset({"a", "ale", "oraz", "i"})
_DATIVE_PRONOUNS = frozenset({"mu", "jej", "im", "ci", "tobie", "wam", "panu", "pani"})
_PUNCT = ".,?!:;\"'()[]{}"

def _digest(payload: Any) -> str:
    return sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def _clean(token: str) -> str: return str(token).strip(_PUNCT)
def _norm(token: str) -> str: return _clean(token).casefold()
def _tokens(text: str) -> list[str]: return [t for t in re.split(r"\s+", str(text).strip()) if t]

def _scope_flags(tokens: list[str]) -> tuple[bool, bool]:
    low = [_norm(t) for t in tokens]
    return any(t in _NEGATION for t in low), any(t in _CONDITIONS for t in low) or ("dopiero" in low and "po" in low)

def _clause_end(tokens: list[str], start: int) -> int:
    for i in range(start, len(tokens)):
        if _norm(tokens[i]) in _CLAUSE | _CONDITIONS: return i
        if i >= start and str(tokens[i]).rstrip().endswith((",", ";")): return i + 1
    return len(tokens)

def _indices(tokens: list[str], start: int, end: int, max_tokens: int = 4) -> tuple[int, ...]:
    return tuple(range(start, min(end, start + max_tokens)))

def _looks_dative_first(token: str) -> bool:
    raw, low = _clean(token), _norm(token)
    if low in _DATIVE_PRONOUNS: return True
    if not raw or not raw[0].isupper(): return False
    return low.endswith(("owi", "emu", "i", "ie", "u"))

@dataclass(frozen=True)
class ActionIntentPort:
    operator_role: str; entity: str; token_indices: tuple[int, ...]; surface_form: str
    grammatical_case: str | None = None; adposition: str | None = None
    basis: str = "BOUNDED_ACTION_PATTERN"; confidence: float = 0.82; candidate_only: bool = True
    def validate(self) -> list[str]:
        issues=[]
        if not self.operator_role: issues.append("action port operator_role is required")
        if not self.entity: issues.append("action port entity is required")
        if not self.token_indices: issues.append("action port token_indices must be non-empty")
        if any(i < 0 for i in self.token_indices): issues.append("action port token_indices must be non-negative")
        if not 0 <= float(self.confidence) <= 1: issues.append("action port confidence must be in [0,1]")
        if not self.candidate_only: issues.append("action port must remain candidate-only")
        return issues
    def to_dict(self) -> dict[str, Any]:
        return {"operator_role":self.operator_role,"entity":self.entity,"token_indices":list(self.token_indices),"surface_form":self.surface_form,"grammatical_case":self.grammatical_case,"adposition":self.adposition,"basis":self.basis,"confidence":self.confidence,"candidate_only":self.candidate_only}

@dataclass(frozen=True)
class ActionIntentFrame:
    frame_id: str; language_id: str; operator: str; ports: tuple[ActionIntentPort,...]; surface_text: str
    negation_detected: bool; condition_detected: bool; commitment: str
    evidence_basis: str="BOUNDED_POLISH_ACTION_PATTERN"; candidate_only: bool=True; confidence: float=0.82
    schema: str=ACTION_INTENT_FRAME_SCHEMA
    @classmethod
    def create(cls, *, language_id:str, operator:str, ports:Iterable[ActionIntentPort], surface_text:str, negation_detected:bool, condition_detected:bool):
        packed=tuple(ports)
        body={"schema":ACTION_INTENT_FRAME_SCHEMA,"language_id":language_id,"operator":operator,"ports":[p.to_dict() for p in packed],"surface_text":surface_text,"negation_detected":bool(negation_detected),"condition_detected":bool(condition_detected),"evidence_basis":"BOUNDED_POLISH_ACTION_PATTERN","candidate_only":True}
        c=_digest(body)
        obj=cls("actionframe:"+c[:24],language_id,operator,packed,surface_text,bool(negation_detected),bool(condition_detected),c,confidence=min((p.confidence for p in packed),default=0.0))
        issues=obj.validate()
        if issues: raise ValueError("; ".join(issues))
        return obj
    @property
    def required_roles(self): return _ACTION_REQUIREMENTS.get(self.operator,())
    @property
    def missing_required_roles(self):
        present={p.operator_role for p in self.ports}; return tuple(r for r in self.required_roles if r not in present)
    @property
    def structurally_complete(self): return not self.missing_required_roles
    @property
    def scope_clear_for_execution(self): return self.structurally_complete and not self.negation_detected and not self.condition_detected
    def validate(self) -> list[str]:
        issues=[]
        if self.schema != ACTION_INTENT_FRAME_SCHEMA: issues.append("action intent frame schema mismatch")
        if self.language_id != "pl": issues.append("ActionIntentFrame v0.1 expects language_id=pl")
        if self.operator not in _ACTION_REQUIREMENTS: issues.append("unknown action intent operator")
        if not self.frame_id or not self.surface_text: issues.append("action intent frame id/surface_text are required")
        if not self.ports: issues.append("action intent frame requires at least one port")
        keys=[]
        for p in self.ports: issues.extend(p.validate()); keys.append((p.operator_role,p.token_indices))
        if len(set(keys)) != len(keys): issues.append("action intent frame contains duplicate role/span")
        if not self.candidate_only: issues.append("action intent frame must remain candidate-only")
        body={"schema":self.schema,"language_id":self.language_id,"operator":self.operator,"ports":[p.to_dict() for p in self.ports],"surface_text":self.surface_text,"negation_detected":self.negation_detected,"condition_detected":self.condition_detected,"evidence_basis":self.evidence_basis,"candidate_only":self.candidate_only}
        if self.commitment != _digest(body): issues.append("action intent frame commitment mismatch")
        if self.frame_id != "actionframe:"+self.commitment[:24]: issues.append("action intent frame id/commitment mismatch")
        return issues
    def to_dict(self):
        return {"schema":self.schema,"frame_id":self.frame_id,"language_id":self.language_id,"operator":self.operator,"ports":[p.to_dict() for p in self.ports],"surface_text":self.surface_text,"negation_detected":self.negation_detected,"condition_detected":self.condition_detected,"structurally_complete":self.structurally_complete,"missing_required_roles":list(self.missing_required_roles),"scope_clear_for_execution":self.scope_clear_for_execution,"candidate_only":self.candidate_only,"confidence":self.confidence,"commitment":self.commitment}

def _port(role:str,tokens:list[str],idx:Iterable[int],case:str|None=None,adposition:str|None=None):
    packed=tuple(i for i in idx if 0<=i<len(tokens))
    if not packed: return None
    entity=" ".join(_clean(tokens[i]) for i in packed).strip()
    if not entity: return None
    return ActionIntentPort(role,entity,packed," ".join(tokens[i] for i in packed),case,adposition)

def _make(op:str,text:str,tokens:list[str],ports:Iterable[ActionIntentPort|None]):
    packed=tuple(p for p in ports if p is not None)
    if not packed: return None
    neg,cond=_scope_flags(tokens)
    return ActionIntentFrame.create(language_id="pl",operator=op,ports=packed,surface_text=text,negation_detected=neg,condition_detected=cond)

def _send(text,tokens,low,v):
    end=_clause_end(tokens,v+1)
    if v+1>=end: return None
    tail=low[v+1:end]
    if "do" in tail:
        d=low.index("do",v+1,end)
        return _make("SENDS",text,tokens,(_port("object",tokens,range(v+1,d),"ACC"),_port("recipient",tokens,_indices(tokens,d+1,end,4),"GEN","do")))
    idx=tuple(range(v+1,end))
    if len(idx)<2: return _make("SENDS",text,tokens,(_port("object",tokens,idx[:1],"ACC"),))
    if _looks_dative_first(tokens[idx[0]]):
        return _make("SENDS",text,tokens,(_port("recipient",tokens,idx[:1],"DAT"),_port("object",tokens,idx[1:],"ACC")))
    return _make("SENDS",text,tokens,(_port("object",tokens,idx[:-1],"ACC"),_port("recipient",tokens,idx[-1:],"DAT")))

def _unary(op,text,tokens,v):
    end=_clause_end(tokens,v+1); return _make(op,text,tokens,(_port("object",tokens,_indices(tokens,v+1,end,4),"ACC"),))

def _set_status(text,tokens,low,v):
    end=_clause_end(tokens,v+1); tail=low[v+1:end]; ports=[]
    key=next((k for k in ("rekordu","rekord") if k in tail),None)
    if key:
        i=low.index(key,v+1,end); ports.append(_port("record",tokens,_indices(tokens,i+1,end,1),"GEN" if key=="rekordu" else "ACC"))
    if "na" in tail:
        i=low.index("na",v+1,end); ports.append(_port("status",tokens,_indices(tokens,i+1,end,1),adposition="na"))
    elif "status" in tail:
        i=low.index("status",v+1,end); cand=_port("status",tokens,_indices(tokens,i+1,end,1))
        if cand and _norm(cand.entity) not in {"rekord","rekordu"}: ports.append(cand)
    return _make("SETS_STATUS",text,tokens,ports)

def _approve(text,tokens,v):
    end=_clause_end(tokens,v+1); return _make("APPROVES_SUPPLIER",text,tokens,(_port("supplier",tokens,_indices(tokens,v+1,end,2),"ACC"),))

def _contract(text,tokens,low,v):
    end=_clause_end(tokens,v+1); tail=low[v+1:end]
    if "z" not in tail: return None
    i=low.index("z",v+1,end); return _make("CREATES_CONTRACT",text,tokens,(_port("counterparty",tokens,_indices(tokens,i+1,end,2),"INS","z"),))

def extract_polish_action_intent_frames(text:str)->list[ActionIntentFrame]:
    tokens=_tokens(text); low=[_norm(t) for t in tokens]; frames=[]
    for i,w in enumerate(low):
        frame=None
        if w in {"wyślij","wyslij","wyślijcie","wysyłaj","wysylaj"}: frame=_send(text,tokens,low,i)
        elif w in {"zarchiwizuj","archiwizuj"}: frame=_unary("ARCHIVES",text,tokens,i)
        elif w in {"usuń","usun","usuwaj"}: frame=_unary("DELETES",text,tokens,i)
        elif w in {"zmień","zmien","ustaw"}: frame=_set_status(text,tokens,low,i)
        elif w in {"zatwierdź","zatwierdz","zatwierdzaj"}: frame=_approve(text,tokens,i)
        elif w in {"utwórz","utworz","stwórz","stworz","twórz","tworz"} and i+1<len(low) and low[i+1] in {"kontrakt","kontraktu","umowę","umowe"}: frame=_contract(text,tokens,low,i)
        if frame: frames.append(frame)
    out={}
    for f in frames: out.setdefault(f.commitment,f)
    return list(out.values())

__all__=["ACTION_INTENT_FRAME_SCHEMA","ActionIntentPort","ActionIntentFrame","extract_polish_action_intent_frames"]
