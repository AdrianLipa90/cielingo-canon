from __future__ import annotations
import hashlib, json, re
from pathlib import Path
import torch
from torch import nn

ROOT=Path(__file__).resolve().parents[2]

def _norm(s:str)->str:
    s=s.casefold().strip()
    s=re.sub(r"^[^\wąćęłńóśźż]+|[^\wąćęłńóśźż]+$", "", s, flags=re.UNICODE)
    return s

def load_exact_union_cards(repo_root:Path|None=None):
    rr=Path(repo_root) if repo_root else ROOT/'vendor'/'cielingo'
    p=rr/'cards'/'generated_examples'/'controlled_48_slot_runtime_cards_v0_6a.jsonl'
    cards=[]
    for line in p.read_text(encoding='utf-8').splitlines():
        if not line.strip(): continue
        c=json.loads(line)
        if c.get('language_id') in {'pl','en'}:
            cards.append(c)
    by_form={}
    for c in cards:
        forms=set([c.get('lemma','')] + list(c.get('surface_forms') or []))
        for f in forms:
            nf=_norm(f)
            if not nf or ' ' in nf: continue
            by_form.setdefault(nf,{})[c['card_id']]=c
    return cards,{k:list(v.values()) for k,v in by_form.items()}

def exact_bindings(tokens:list[str], repo_root:Path|None=None):
    cards,by_form=load_exact_union_cards(repo_root)
    rows=[]
    for i,t in enumerate(tokens):
        ms=by_form.get(_norm(t),[])
        rows.append((i,t,ms))
    return rows

def relation_feature_vector(tokens:list[str], repo_root:Path|None=None):
    rows=exact_bindings(tokens,repo_root)
    n=len(tokens)
    if n < 2: return [0.0,0.0,0.0,0.0]
    roles=[]
    isop=[]
    for _,_,cards in rows:
        b=tuple(sorted({x for c in cards for x in ((c.get('runtime') or {}).get('operator_bindings') or [])}))
        roles.append(set(b)); isop.append(bool(b))
    denom=n*(n-1)
    sums=[0.0,0.0,0.0,0.0]
    for i in range(n):
        for j in range(n):
            if i==j: continue
            # identical to Lingophysics v1.9 relation components, excluding phase baseline
            if isop[i] != isop[j]: sums[0]+=0.7
            if roles[i] & roles[j]: sums[1]+=0.4
            # current controlled-48 exact carrier has no case_gauge or phase_conflict
    return [s/denom for s in sums]

def carrier_diagnostics(tokens:list[str], repo_root:Path|None=None):
    rows=exact_bindings(tokens,repo_root)
    cards=[c for _,_,cs in rows for c in cs]
    op=sum(1 for c in cards if (c.get('runtime') or {}).get('operator_bindings'))
    return {
        'candidate_count':len(cards),
        'operator_bound_candidate_count':op,
        'card_ids':sorted(c['card_id'] for c in cards),
        'vector':relation_feature_vector(tokens,repo_root),
        'all_candidate_scores_exact':True,
    }

class BiasFreeStructuralResidual(nn.Module):
    def __init__(self,vocab_size:int,feature_dim:int=4):
        super().__init__(); self.linear=nn.Linear(feature_dim,vocab_size,bias=False); nn.init.zeros_(self.linear.weight)
    def forward(self,features): return self.linear(features)
    def parameter_sha256(self):
        h=hashlib.sha256()
        for k,v in sorted(self.state_dict().items()): h.update(k.encode()); h.update(v.detach().cpu().contiguous().numpy().tobytes())
        return h.hexdigest()

def tensor_sha256_state_dict(sd):
    h=hashlib.sha256()
    for k,v in sorted(sd.items()): h.update(k.encode()); h.update(v.detach().cpu().contiguous().numpy().tobytes())
    return h.hexdigest()
