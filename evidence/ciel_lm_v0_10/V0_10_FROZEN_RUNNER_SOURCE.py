from __future__ import annotations
import argparse, hashlib, itertools, json, math, random, sys, time
from pathlib import Path
import torch
import torch.nn.functional as F

ROOT=Path(__file__).resolve().parents[1]
VENDOR=ROOT/'vendor'
sys.path.insert(0,str(ROOT/'src'))
from ciel_lm_text.tokenizer import WordTokenizer
from ciel_lm_text.model import TinyCielLM, ModelConfig
from ciel_lm_text.corpus import _strings,_clean
from ciel_lm_text.structure import CielStructureAdapter
from ciel_lm_text.residual import BiasFreeStructuralResidual, relation_feature_vector, tensor_sha256_state_dict

PREREG=ROOT/'protocols'/'V0_10_V2_FROZEN_BASE_STRUCTURAL_RESIDUAL_PREREGISTRATION.json'
EXPECTED='d6dce9cd0c0b239e3870695bf0b452327f8dde4f7ae9367b9cf469bf4ef855bf'
NAMESPACE='CIEL_LM_V0_10_FROZEN_BASE_RESIDUAL'

def sha_file(p:Path)->str: return hashlib.sha256(p.read_bytes()).hexdigest()
def clean_text(p:Path)->str:
    if p.suffix.lower()=='.json':
        d=json.loads(p.read_text(encoding='utf-8')); vals=[_clean(s) for s in _strings(d) if len(s.strip())>1]; return '\n'.join(v for v in vals if v)
    return _clean(p.read_text(encoding='utf-8',errors='ignore'))
def source_files():
    return sorted(list((VENDOR/'cielingo'/'corpus').glob('*.json'))+list((VENDOR/'cielingo'/'docs').rglob('*.md'))+list((VENDOR/'lingophysics'/'docs').rglob('*.md')))
def split_registered(pr):
    held=set(pr['selection']['heldout_files']); tr=[]; va=[]; seen=[]
    for p in source_files():
        rel=p.relative_to(VENDOR).as_posix(); seen.append(rel)
        if rel not in pr['selection']['source_file_sha256']: raise RuntimeError('UNREGISTERED_SOURCE:'+rel)
        if sha_file(p)!=pr['selection']['source_file_sha256'][rel]: raise RuntimeError('SOURCE_HASH_MISMATCH:'+rel)
        (va if rel in held else tr).append(clean_text(p))
    if set(seen)!=set(pr['selection']['source_file_sha256']):
        missing=sorted(set(pr['selection']['source_file_sha256'])-set(seen)); extra=sorted(set(seen)-set(pr['selection']['source_file_sha256']))
        raise RuntimeError('SOURCE_SET_MISMATCH missing='+repr(missing)+' extra='+repr(extra))
    return '\n'.join(tr),'\n'.join(va)
def ex(ids,start,b): q=ids[start:start+b+1]; return q[:-1],q[1:]
def state_hash(model): return tensor_sha256_state_dict(model.state_dict())
def train_base(init_seed,ids,starts,cfg,lr):
    torch.manual_seed(init_seed); model=TinyCielLM(cfg); opt=torch.optim.AdamW(model.parameters(),lr=lr,weight_decay=0.01)
    torch.manual_seed(init_seed+100000)
    for st in starts:
        xids,yids=ex(ids,st,cfg.block_size); x=torch.tensor([xids]); y=torch.tensor([yids]); model.train(); opt.zero_grad(set_to_none=True); _,loss=model(x,targets=y); loss.backward(); torch.nn.utils.clip_grad_norm_(model.parameters(),1.0); opt.step()
    model.eval()
    for p in model.parameters(): p.requires_grad_(False)
    return model
def base_samples(model,ids,raw_tokens,starts,b):
    rows=[]
    with torch.no_grad():
        for st in starts:
            xids,yids=ex(ids,st,b); x=torch.tensor([xids]); logits,_=model(x); rows.append((logits[0].detach().clone(),torch.tensor(yids,dtype=torch.long),raw_tokens[st:st+b]))
    return rows
def aggregate_features(adapter,samples,cache):
    out=[]
    for _,_,tokens in samples:
        key=tuple(tokens)
        if key not in cache: cache[key]=relation_feature_vector(adapter,list(tokens))
        out.append(cache[key])
    return out
def permute_features(features,seed,split):
    order=sorted(range(len(features)),key=lambda i:hashlib.sha256(f'{NAMESPACE}|{seed}|{split}|{i}'.encode()).hexdigest())
    return [features[j] for j in order],order
def train_residual(vocab_size,samples,features,lr):
    expert=BiasFreeStructuralResidual(vocab_size); opt=torch.optim.AdamW(expert.parameters(),lr=lr,weight_decay=0.0)
    for (base_logits,targets,_),fv in zip(samples,features):
        f=torch.tensor(fv,dtype=torch.float32); opt.zero_grad(set_to_none=True); logits=base_logits+expert(f)[None,:]; loss=F.cross_entropy(logits,targets); loss.backward(); opt.step()
    return expert
def eval_nll(samples,features=None,expert=None):
    vals=[]; correct=tot=0
    with torch.no_grad():
        for idx,(base_logits,targets,_) in enumerate(samples):
            logits=base_logits
            if expert is not None:
                f=torch.tensor(features[idx],dtype=torch.float32); logits=base_logits+expert(f)[None,:]
            vals.append(float(F.cross_entropy(logits,targets))); correct+=int((logits.argmax(-1)==targets).sum()); tot+=targets.numel()
    nll=sum(vals)/len(vals); return {'nll':nll,'perplexity':math.exp(min(20,nll)),'top1_accuracy':correct/tot,'tokens':tot}
def exact_sign_flip_p(ds):
    obs=sum(ds)/len(ds); ge=0; total=0
    for signs in itertools.product((-1.0,1.0),repeat=len(ds)):
        stat=sum(s*d for s,d in zip(signs,ds))/len(ds); total+=1
        if stat>=obs-1e-15: ge+=1
    return ge/total
def loo(ds): return [sum(ds[:i]+ds[i+1:])/(len(ds)-1) for i in range(len(ds))]
def self_test():
    torch.manual_seed(1); e=BiasFreeStructuralResidual(7); base=torch.randn(24,7); f=torch.tensor([.2,.1,0.,0.]); assert torch.equal(base,base+e(f)[None,:]); opt=torch.optim.AdamW(e.parameters(),lr=4e-4,weight_decay=0.0); y=torch.arange(24)%7
    for _ in range(3): opt.zero_grad(); loss=F.cross_entropy(base+e(f)[None,:],y); loss.backward(); opt.step()
    assert torch.equal(e(torch.zeros(4)),torch.zeros(7)); assert torch.equal(base,base+e(torch.zeros(4))[None,:]); return {'status':'PASS','loss':float(loss.detach())}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--self-test',action='store_true'); args=ap.parse_args()
    if args.self_test: print(json.dumps(self_test(),sort_keys=True)); return
    if sha_file(PREREG)!=EXPECTED: raise SystemExit('PREREG_HASH_MISMATCH')
    pr=json.loads(PREREG.read_text()); trtxt,vatxt=split_registered(pr); trraw=trtxt.split(); varaw=vatxt.split(); tok=WordTokenizer.build(trtxt,min_freq=pr['tokenizer']['min_freq'],max_vocab=pr['tokenizer']['max_vocab']); tr=tok.encode(trtxt); va=tok.encode(vatxt)
    if len(tr)!=len(trraw) or len(va)!=len(varaw): raise SystemExit('TOKEN_ALIGNMENT_LENGTH_MISMATCH')
    b=pr['base_model']['block_size']; vmax=max(0,len(va)-b-2); vstarts=sorted(set(round(i*vmax/15) for i in range(16)));
    if len(vstarts)!=pr['evaluation']['heldout_windows']:
        raise SystemExit(f'HELDOUT_WINDOW_COUNT_MISMATCH:{len(vstarts)}')
    adapter=CielStructureAdapter(language='pl'); cache={}; rows=[]
    oov=sum(i==tok.stoi['<unk>'] for i in va)/len(va)
    for seed in pr['seeds']:
        rng=random.Random(seed+9000); mx=max(0,len(tr)-b-2); starts=[rng.randint(0,mx) for _ in range(pr['base_model']['training_steps'])]
        cfg=ModelConfig(vocab_size=tok.vocab_size,block_size=b,d_model=pr['base_model']['d_model'],n_heads=pr['base_model']['n_heads'],n_layers=pr['base_model']['n_layers'],dropout=pr['base_model']['dropout'],structural_weight=0.0)
        t=time.time(); base=train_base(seed,tr,starts,cfg,pr['base_model']['learning_rate']); base_hash=state_hash(base); train_samples=base_samples(base,tr,trraw,starts,b); val_samples=base_samples(base,va,varaw,vstarts,b); real_train=aggregate_features(adapter,train_samples,cache); real_val=aggregate_features(adapter,val_samples,cache); shuf_train,train_perm=permute_features(real_train,seed,'train'); shuf_val,val_perm=permute_features(real_val,seed,'validation')
        e0=BiasFreeStructuralResidual(tok.vocab_size); zero_init=all(torch.equal(bl,bl+e0(torch.tensor(f,dtype=torch.float32))[None,:]) for (bl,_,_),f in zip(val_samples,real_val)) and all(torch.equal(bl,bl+e0(torch.tensor(f,dtype=torch.float32))[None,:]) for (bl,_,_),f in zip(val_samples,shuf_val)) if val_samples else True
        real=train_residual(tok.vocab_size,train_samples,real_train,pr['residual_expert']['learning_rate']); shuf=train_residual(tok.vocab_size,train_samples,shuf_train,pr['residual_expert']['learning_rate']); base_hash_after=state_hash(base)
        zero=torch.zeros(4); zero_post_real=all(torch.equal(bl,bl+real(zero)[None,:]) for bl,_,_ in val_samples); zero_post_shuffled=all(torch.equal(bl,bl+shuf(zero)[None,:]) for bl,_,_ in val_samples); zero_post=zero_post_real and zero_post_shuffled
        rb=eval_nll(val_samples); rr=eval_nll(val_samples,real_val,real); rs=eval_nll(val_samples,shuf_val,shuf)
        row={'seed':seed,'base':rb,'real':rr,'shuffled':rs,'delta_base':rb['nll']-rr['nll'],'delta_shuffle':rs['nll']-rr['nll'],'base_parameter_sha256':base_hash,'base_parameter_sha256_after_residual_training':base_hash_after,'base_hash_unchanged':base_hash==base_hash_after,'zero_init_exact_equivalence':zero_init,'zero_structural_post_training_exact_equivalence':zero_post,'zero_structural_post_training_real_exact_equivalence':zero_post_real,'zero_structural_post_training_shuffled_exact_equivalence':zero_post_shuffled,'real_residual_sha256':real.parameter_sha256(),'shuffled_residual_sha256':shuf.parameter_sha256(),'train_starts_sha256':hashlib.sha256(json.dumps(starts,separators=(',',':')).encode()).hexdigest(),'train_feature_permutation':train_perm,'validation_feature_permutation':val_perm,'elapsed_seconds':time.time()-t}; rows.append(row); print(json.dumps({'seed':seed,'delta_base':row['delta_base'],'delta_shuffle':row['delta_shuffle'],'base_nll':rb['nll'],'real_nll':rr['nll'],'shuffled_nll':rs['nll'],'base_hash_unchanged':row['base_hash_unchanged'],'zero_post':zero_post},sort_keys=True),flush=True)
    db=[r['delta_base'] for r in rows]; ds=[r['delta_shuffle'] for r in rows]; pbase=exact_sign_flip_p(db); pshuf=exact_sign_flip_p(ds); loob=loo(db); loos=loo(ds); all_zero=all(r['zero_init_exact_equivalence'] and r['zero_structural_post_training_exact_equivalence'] for r in rows); all_hash=all(r['base_hash_unchanged'] for r in rows)
    checks={'mean_delta_base_positive':sum(db)/len(db)>0,'positive_delta_base_seeds_ge_9':sum(d>0 for d in db)>=9,'signflip_p_base_le_0_05':pbase<=0.05,'min_loo_base_positive':min(loob)>0,'mean_delta_shuffle_positive':sum(ds)/len(ds)>0,'positive_delta_shuffle_seeds_ge_9':sum(d>0 for d in ds)>=9,'signflip_p_shuffle_le_0_05':pshuf<=0.05,'min_loo_shuffle_positive':min(loos)>0,'all_zero_equivalence':all_zero,'all_base_hashes_unchanged':all_hash}
    status='PASS_PILOT_MECHANISM' if all(checks.values()) else 'BLOCK_PILOT_MECHANISM'
    report={'schema':'CIEL_LM_FROZEN_BASE_STRUCTURAL_RESIDUAL_REPORT_V0_10_V2','status':status,'prereg_sha256':EXPECTED,'heldout_files':pr['selection']['heldout_files'],'train_tokens':len(tr),'validation_tokens':len(va),'validation_oov_rate':oov,'vocab_size':tok.vocab_size,'feature_cache_size':len(cache),'rows':rows,'aggregate':{'mean_delta_base':sum(db)/len(db),'positive_delta_base_seeds':sum(d>0 for d in db),'signflip_p_base':pbase,'leave_one_out_base':loob,'min_leave_one_out_base':min(loob),'mean_delta_shuffle':sum(ds)/len(ds),'positive_delta_shuffle_seeds':sum(d>0 for d in ds),'signflip_p_shuffle':pshuf,'leave_one_out_shuffle':loos,'min_leave_one_out_shuffle':min(loos),'mean_base_nll':sum(r['base']['nll'] for r in rows)/len(rows),'mean_real_nll':sum(r['real']['nll'] for r in rows)/len(rows),'mean_shuffled_nll':sum(r['shuffled']['nll'] for r in rows)/len(rows),'checks':checks},'canon_allowed':False}
    out=ROOT/'evidence'/'V0_10_FROZEN_BASE_STRUCTURAL_RESIDUAL_REPORT.json'; out.write_text(json.dumps(report,indent=2),encoding='utf-8'); print(json.dumps(report['aggregate']|{'status':status,'validation_oov_rate':oov},indent=2))
if __name__=='__main__': main()
