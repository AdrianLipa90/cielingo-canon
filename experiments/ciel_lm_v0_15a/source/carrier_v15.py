from __future__ import annotations
import json, re
from pathlib import Path

_PUNCT_RE = re.compile(r"^[^\wąćęłńóśźż]+|[^\wąćęłńóśźż]+$", flags=re.UNICODE)

def _norm(s: str) -> str:
    return _PUNCT_RE.sub("", s.casefold().strip())

def load_exact_union_cards(atlas_path: Path):
    cards=[]
    for line in Path(atlas_path).read_text(encoding='utf-8').splitlines():
        if not line.strip(): continue
        c=json.loads(line)
        if c.get('language_id') in {'pl','en'}: cards.append(c)
    by_form={}
    for c in cards:
        for f in {c.get('lemma',''), *(c.get('surface_forms') or [])}:
            nf=_norm(f)
            if not nf or ' ' in nf: continue
            by_form.setdefault(nf,{})[c['card_id']]=c
    return cards,{k:list(v.values()) for k,v in by_form.items()}

def exact_bindings(tokens: list[str], atlas_path: Path):
    _,by_form=load_exact_union_cards(atlas_path)
    return [(i,t,by_form.get(_norm(t),[])) for i,t in enumerate(tokens)]

def relation_feature_vector(tokens: list[str], atlas_path: Path):
    rows=exact_bindings(tokens,atlas_path); n=len(tokens)
    if n < 2: return [0.0]*5
    bound=[]; roles=[]; isop=[]
    for _,_,cards in rows:
        b=tuple(sorted({x for c in cards for x in ((c.get('runtime') or {}).get('operator_bindings') or [])}))
        bound.append(bool(cards)); roles.append(set(b)); isop.append(bool(b))
    denom=n*(n-1); sums=[0.0]*5
    for i in range(n):
        for j in range(n):
            if i==j: continue
            if bound[i] != bound[j]: sums[0]+=1.0
            if isop[i] != isop[j]: sums[1]+=0.7
            if roles[i] & roles[j]: sums[2]+=0.4
    return [x/denom for x in sums]

def carrier_diagnostics(tokens: list[str], atlas_path: Path):
    rows=exact_bindings(tokens,atlas_path); cards=[c for _,_,cs in rows for c in cs]
    v=relation_feature_vector(tokens,atlas_path)
    return {
      'candidate_count':len(cards),
      'bound_token_positions':sum(bool(cs) for _,_,cs in rows),
      'operator_bound_candidate_count':sum(1 for c in cards if (c.get('runtime') or {}).get('operator_bindings')),
      'card_ids':sorted(c['card_id'] for c in cards),
      'vector':v,
      'legacy_relation_nonzero':any(abs(float(x))>1e-15 for x in v[1:]),
      'all_candidate_scores_exact':True,
    }
