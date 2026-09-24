from __future__ import annotations
import hashlib
import torch
from torch import nn

class BiasFreeResidual(nn.Module):
    def __init__(self, vocab_size:int, feature_dim:int=5):
        super().__init__(); self.weight=nn.Parameter(torch.zeros(vocab_size,feature_dim))
    def forward(self, f:torch.Tensor): return self.weight @ f
    def parameter_sha256(self): return hashlib.sha256(self.weight.detach().cpu().contiguous().numpy().tobytes()).hexdigest()
