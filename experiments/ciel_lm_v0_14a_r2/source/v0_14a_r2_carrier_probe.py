from __future__ import annotations
import hashlib, json, sys
from pathlib import Path
from corpus import _clean, _strings
from carrier import carrier_diagnostics

NAMESPACE='CIEL_LM_V0_14_CIEL_OMEGA_DOCS_REPLACEMENT_R2'
SOURCE_ARCHIVE_SHA256='fef25a4cb20380483fec5b3e84ad8a2d1465e6a53ecf6dfd9ec42ec67d82e9ef'
SOURCE_UNIVERSE_SHA256='9d5530ece47dc8132d2e015ab0f0c7d7e75155ee75ba2744ad602d1acde63d88'
ATLAS_SHA256='c3eaf295517fa8116528de150be8ec434b8fa2565ca84d7f946c21ef2d651050'
CLEANER_SHA256='4959ea4436806595022feb67c5e16ce423261f7f3806061e74f6f48cc40e76b7'
HELDOUT=[
'docs/operations/README.md',
'docs/object_cards/satellites/SAT-P3-0001.md',
'docs/integration/SAPIENS_SURFACE_BINDING.md',
'docs/MASTER_PLAN_4_ALL_AGENTS_ATTENTION.md',
'docs/operations/OFFLINE_DEPENDENCY_BUNDLE_V1.md',
'docs/architecture/POST_MERGE_RECONCILIATION.md',
'docs/integration/ORBITAL_INFRASTRUCTURE_RULES.md',
]
GATE={'validation_nonzero_relation_windows_min':8,'training_nonzero_relation_windows_min':16,'unique_nonzero_validation_vectors_min':2}

def sha(p:Path): return hashlib.sha256(p.read_bytes()).hexdigest()
def clean_text(p:Path):
    if p.suffix.lower()=='.json':
        d=json.loads(p.read_text(encoding='utf-8')); vals=[_clean(s) for s in _strings(d) if len(s.strip())>1]; return '\n'.join(v for v in vals if v)
    return _clean(p.read_text(encoding='utf-8',errors='ignore'))
def manifest_sha(root:Path):
    fs=sorted(p for p in (root/'docs').rglob('*.md') if p.is_file())
    m={p.relative_to(root).as_posix():sha(p) for p in fs}
    return len(fs),hashlib.sha256(json.dumps(m,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def spaced_starts(n,b,count):
    mx=max(0,n-b); s=sorted(set(round(i*mx/(count-1)) for i in range(count)))
    if len(s)!=count: raise RuntimeError(f'START_COUNT_MISMATCH:{len(s)}')
    return s
def iszero(v): return all(abs(float(x))<=1e-15 for x in v)
def stats(tokens,starts,atlas,b=24):
    rows=[carrier_diagnostics(tokens[s:s+b],atlas) for s in starts]
    nz=[r for r in rows if not iszero(r['vector'])]
    return {'windows':len(rows),'nonzero_relation_windows':len(nz),'unique_nonzero_vectors':len({tuple(round(float(x),15) for x in r['vector']) for r in nz}),'total_exact_candidates':sum(r['candidate_count'] for r in rows),'operator_bound_candidates':sum(r['operator_bound_candidate_count'] for r in rows),'component_nonzero_counts':[sum(abs(float(r['vector'][i]))>1e-15 for r in rows) for i in range(4)],'all_candidate_scores_exact':all(r['all_candidate_scores_exact'] for r in rows),'rows':rows}
def split(root:Path):
    fs=sorted(p for p in (root/'docs').rglob('*.md') if p.is_file()); held=set(HELDOUT); tr=[]; va=[]; seen=set()
    for p in fs:
        rel=p.relative_to(root).as_posix(); seen.add(rel); (va if rel in held else tr).append(clean_text(p))
    if not held.issubset(seen): raise RuntimeError('HELDOUT_MISSING')
    return '\n'.join(tr),'\n'.join(va)
def run(root:Path,atlas:Path,cleaner_path:Path):
    if sha(atlas)!=ATLAS_SHA256: raise RuntimeError('ATLAS_SHA_MISMATCH')
    if sha(cleaner_path)!=CLEANER_SHA256: raise RuntimeError('CLEANER_SHA_MISMATCH')
    n,mh=manifest_sha(root)
    if n!=109 or mh!=SOURCE_UNIVERSE_SHA256: raise RuntimeError(f'SOURCE_UNIVERSE_MISMATCH:{n}:{mh}')
    tr,va=split(root); trt=tr.split(); vat=va.split()
    vs=spaced_starts(len(vat),24,16); ts=spaced_starts(len(trt),24,64)
    vr=stats(vat,vs,atlas); trr=stats(trt,ts,atlas)
    gate={'source_hashes':'PASS','all_candidate_scores_exact':vr['all_candidate_scores_exact'] and trr['all_candidate_scores_exact'],'validation_nonzero_relation_windows':vr['nonzero_relation_windows']>=8,'training_nonzero_relation_windows':trr['nonzero_relation_windows']>=16,'unique_nonzero_validation_vectors':vr['unique_nonzero_vectors']>=2}
    return {'schema':'CIEL_LM_V0_14A_R2_CARRIER_REPORT_V1','namespace':NAMESPACE,'status':'PASS_CARRIER_ADMISSION' if all(x is True or x=='PASS' for x in gate.values()) else 'BLOCK_CARRIER_ADMISSION','source_universe_sha256':mh,'train_tokens':len(trt),'validation_tokens':len(vat),'training':{k:v for k,v in trr.items() if k!='rows'},'validation':{k:v for k,v in vr.items() if k!='rows'},'gate':gate,'lm_quality_outcome_observed':False,'canon_allowed':False}
if __name__=='__main__':
    root=Path(sys.argv[1]); atlas=Path(sys.argv[2]); cleaner=Path(sys.argv[3]); print(json.dumps(run(root,atlas,cleaner),indent=2))
