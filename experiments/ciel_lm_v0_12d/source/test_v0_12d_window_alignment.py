import hashlib
import torch
from ciel_lm_text.model import TinyCielLM, ModelConfig
from ciel_lm_text.v0_12d_runner import (
    SCIENTIFIC_NAMESPACE, SOURCE_MANIFEST_SHA256, carrier_preflight,
    iszero, mask_preserving_shuffle, source_manifest_sha, split_registered,
    validation_samples_internal,
)

def test_source_manifest_exact():
    assert source_manifest_sha() == SOURCE_MANIFEST_SHA256

def test_parent_carrier_replay_exact():
    tr, va = split_registered(); c=carrier_preflight(tr.split(),va.split())
    assert c['validation']['nonzero']==13 and c['training']['nonzero']==52
    assert c['validation']['candidates']==58 and c['validation']['operator_bound']==32

def test_last_validation_window_needs_no_25th_token():
    ids=list(range(40)); raw=[f't{i}' for i in range(40)]
    cfg=ModelConfig(vocab_size=64,block_size=24,d_model=32,n_heads=4,n_layers=1,dropout=0.0,structural_weight=0.0)
    torch.manual_seed(1); m=TinyCielLM(cfg); m.eval()
    start=len(ids)-24
    rows=validation_samples_internal(m,ids,raw,[start],24)
    logits,targets,tokens=rows[0]
    assert logits.shape==(23,64); assert targets.shape==(23,); assert len(tokens)==24
    assert targets.tolist()==ids[start+1:start+24]

def test_mask_support_preserved():
    fs=[[0,0,0,0],[.1,0,0,0],[.2,.01,0,0],[0,0,0,0],[.3,0,0,0]]
    out,src=mask_preserving_shuffle(fs,2146355770,'validation')
    assert [iszero(x) for x in out]==[iszero(x) for x in fs]
    dst=[1,2,4]
    exp=sorted(dst,key=lambda i:hashlib.sha256(f'{SCIENTIFIC_NAMESPACE}|2146355770|validation|{i}'.encode()).hexdigest())
    assert src==exp
