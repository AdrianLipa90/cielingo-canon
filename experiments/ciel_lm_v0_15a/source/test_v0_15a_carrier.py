from pathlib import Path
from carrier_v15 import carrier_diagnostics

def conformance(atlas:Path):
    nonop=carrier_diagnostics(['file','zzzz_noncard','qqqq_noncard'],atlas)
    mixed=carrier_diagnostics(['source','file','zzzz_noncard'],atlas)
    zero=carrier_diagnostics(['zzzz_noncard','qqqq_noncard','xxxx_noncard'],atlas)
    assert nonop['vector'][0] > 0 and nonop['vector'][1:] == [0.0,0.0,0.0,0.0]
    assert mixed['vector'][0] > 0 and mixed['vector'][1] > 0
    assert zero['vector'] == [0.0]*5
    assert nonop['all_candidate_scores_exact'] and mixed['all_candidate_scores_exact'] and zero['all_candidate_scores_exact']
    return True
