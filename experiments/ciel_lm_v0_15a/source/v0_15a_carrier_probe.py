from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
from corpus import _clean,_strings
from carrier_v15 import carrier_diagnostics

NAMESPACE='CIEL_LM_V0_15_BOUND_CONTEXT_CARRIER'
SOURCE_UNIVERSE_SHA256='9d5530ece47dc8132d2e015ab0f0c7d7e75155ee75ba2744ad602d1acde63d88'
ATLAS_SHA256='c3eaf295517fa8116528de150be8ec434b8fa2565ca84d7f946c21ef2d651050'
CLEANER_SHA256='4959ea4436806595022feb67c5e16ce423261f7f3806061e74f6f48cc40e76b7'
HELDOUT=[
'docs/science/HYPOTHESES.md',
'docs/science/RELATIONAL_ORBITAL_DYNAMICS_SPEC_V0.md',
'docs/desktop/CIEL_DESKTOP_BOOTSTRAP_ON_SOT.md',
'docs/object_cards/satellites/SAT-AUDIO-0001.md',
'docs/architecture/DOCS_INDEX_MD_REPLACEMENT.md',
'docs/architecture/HYPERSPACE_INDEX_JSON_REPLACEMENT.md',
'docs/architecture/CONFLICT_AUDIT_POST_MERGE.md']

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def clean_text(p): return _clean(Path(p).read_text(encoding='utf-8',errors='ignore'))
def manifest_sha(root):
 fs=sorted(p for p in (Path(root)/'docs').rglob('*.md') if p.is_file()); m={p.relative_to(root).as_posix():sha(p) for p in fs}; return len(fs),hashlib.sha256(json.dumps(m,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def spaced(n,b,c):
 mx=max(0,n-b); s=sorted(set(round(i*mx/(c-1)) for i in range(c)))
 if len(s)!=c: raise RuntimeError('START_COUNT_MISMATCH')
 return s
def iszero(v): return all(abs(float(x))<=1e-15 for x in v)
def stats(tokens,starts,atlas,b=24):
 rows=[carrier_diagnostics(tokens[s:s+b],atlas) for s in starts]; nz=[r for r in rows if not iszero(r['vector'])]
 return {'windows':len(rows),'nonzero_carrier_windows':len(nz),'unique_nonzero_vectors':len({tuple(round(float(x),15) for x in r['vector']) for r in nz}),'exact_candidate_windows':sum(r['candidate_count']>0 for r in rows),'total_exact_candidates':sum(r['candidate_count'] for r in rows),'bound_token_positions':sum(r['bound_token_positions'] for r in rows),'operator_bound_candidates':sum(r['operator_bound_candidate_count'] for r in rows),'legacy_relation_nonzero_windows':sum(r['legacy_relation_nonzero'] for r in rows),'component_nonzero_counts':[sum(abs(float(r['vector'][i]))>1e-15 for r in rows) for i in range(5)],'all_candidate_scores_exact':all(r['all_candidate_scores_exact'] for r in rows)}
def split(root):
 root=Path(root); held=set(HELDOUT); tr=[];va=[];seen=set()
 for p in sorted(x for x in (root/'docs').rglob('*.md') if x.is_file()):
  rel=p.relative_to(root).as_posix();seen.add(rel);(va if rel in held else tr).append(clean_text(p))
 if not held.issubset(seen): raise RuntimeError('HELDOUT_MISSING')
 return '\n'.join(tr),'\n'.join(va)
def run(root,atlas,cleaner):
 root=Path(root);atlas=Path(atlas);cleaner=Path(cleaner)
 if sha(atlas)!=ATLAS_SHA256: raise RuntimeError('ATLAS_SHA_MISMATCH')
 if sha(cleaner)!=CLEANER_SHA256: raise RuntimeError('CLEANER_SHA_MISMATCH')
 n,m=manifest_sha(root)
 if n!=109 or m!=SOURCE_UNIVERSE_SHA256: raise RuntimeError('SOURCE_UNIVERSE_MISMATCH')
 tr,va=split(root);trt=tr.split();vat=va.split(); vr=stats(vat,spaced(len(vat),24,16),atlas); rr=stats(trt,spaced(len(trt),24,64),atlas)
 gate={'source_hashes':'PASS','all_candidate_scores_exact':vr['all_candidate_scores_exact'] and rr['all_candidate_scores_exact'],'validation_nonzero_carrier_windows':vr['nonzero_carrier_windows']>=8,'training_nonzero_carrier_windows':rr['nonzero_carrier_windows']>=16,'unique_nonzero_validation_vectors':vr['unique_nonzero_vectors']>=2}
 return {'schema':'CIEL_LM_V0_15A_BOUND_CONTEXT_CARRIER_REPORT_V1','status':'PASS_CARRIER_ADMISSION' if all(v is True or v=='PASS' for v in gate.values()) else 'BLOCK_CARRIER_ADMISSION','source_universe_sha256':m,'train_tokens':len(trt),'validation_tokens':len(vat),'training':rr,'validation':vr,'gate':gate,'lm_quality_outcome_observed':False,'canon_allowed':False}
if __name__=='__main__': print(json.dumps(run(Path(sys.argv[1]),Path(sys.argv[2]),Path(sys.argv[3])),indent=2))
