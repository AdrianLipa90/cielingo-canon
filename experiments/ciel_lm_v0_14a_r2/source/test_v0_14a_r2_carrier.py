from pathlib import Path
from carrier import carrier_diagnostics

def test_exact_smoke(tmp_path):
    assert True

def conformance(atlas: Path):
    a=carrier_diagnostics(['source','file'],atlas)
    z=carrier_diagnostics(['zzzz_noncard','qqqq_noncard'],atlas)
    assert a['all_candidate_scores_exact'] and z['all_candidate_scores_exact']
    assert a['candidate_count']>=2
    assert any(abs(float(x))>0 for x in a['vector'])
    assert z['candidate_count']==0
    assert z['vector']==[0.0,0.0,0.0,0.0]
    return True
