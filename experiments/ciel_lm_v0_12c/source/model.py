from __future__ import annotations
from dataclasses import dataclass, asdict
import math
import torch
from torch import nn
import torch.nn.functional as F

@dataclass
class ModelConfig:
    vocab_size: int
    block_size: int = 48
    d_model: int = 96
    n_heads: int = 4
    n_layers: int = 2
    dropout: float = 0.1
    structural_weight: float = 0.25
    global_feature_dim: int = 5

    def to_dict(self):
        return asdict(self)

class CausalSelfAttention(nn.Module):
    def __init__(self, cfg: ModelConfig):
        super().__init__()
        assert cfg.d_model % cfg.n_heads == 0
        self.n_heads = cfg.n_heads
        self.head_dim = cfg.d_model // cfg.n_heads
        self.qkv = nn.Linear(cfg.d_model, 3 * cfg.d_model)
        self.proj = nn.Linear(cfg.d_model, cfg.d_model)
        self.dropout = nn.Dropout(cfg.dropout)
        self.structural_weight = cfg.structural_weight

    def forward(self, x, structural_bias=None):
        B, T, C = x.shape
        qkv = self.qkv(x).view(B, T, 3, self.n_heads, self.head_dim).permute(2, 0, 3, 1, 4)
        q, k, v = qkv[0], qkv[1], qkv[2]
        scores = (q @ k.transpose(-2, -1)) / math.sqrt(self.head_dim)
        causal = torch.triu(torch.ones(T, T, device=x.device, dtype=torch.bool), diagonal=1)
        scores = scores.masked_fill(causal[None, None, :, :], float('-inf'))
        if structural_bias is not None and self.structural_weight != 0.0:
            if structural_bias.dim() == 2:
                structural_bias = structural_bias.unsqueeze(0)
            scores = scores + self.structural_weight * structural_bias[:, None, :T, :T]
        att = F.softmax(scores, dim=-1)
        att = self.dropout(att)
        y = att @ v
        y = y.transpose(1, 2).contiguous().view(B, T, C)
        return self.proj(y)

class Block(nn.Module):
    def __init__(self, cfg: ModelConfig):
        super().__init__()
        self.ln1 = nn.LayerNorm(cfg.d_model)
        self.attn = CausalSelfAttention(cfg)
        self.ln2 = nn.LayerNorm(cfg.d_model)
        self.ff = nn.Sequential(
            nn.Linear(cfg.d_model, 4 * cfg.d_model),
            nn.GELU(),
            nn.Linear(4 * cfg.d_model, cfg.d_model),
            nn.Dropout(cfg.dropout),
        )
    def forward(self, x, structural_bias=None):
        x = x + self.attn(self.ln1(x), structural_bias)
        x = x + self.ff(self.ln2(x))
        return x

class TinyCielLM(nn.Module):
    """Decoder-only text LM with a CIEL/Lingophysics structural sidecar."""
    def __init__(self, cfg: ModelConfig):
        super().__init__()
        self.cfg = cfg
        self.token_emb = nn.Embedding(cfg.vocab_size, cfg.d_model)
        self.pos_emb = nn.Embedding(cfg.block_size, cfg.d_model)
        self.global_proj = nn.Sequential(
            nn.Linear(cfg.global_feature_dim, cfg.d_model),
            nn.Tanh(),
        )
        self.blocks = nn.ModuleList([Block(cfg) for _ in range(cfg.n_layers)])
        self.ln_f = nn.LayerNorm(cfg.d_model)
        self.lm_head = nn.Linear(cfg.d_model, cfg.vocab_size, bias=False)
        self.apply(self._init_weights)
        self.lm_head.weight = self.token_emb.weight

    @staticmethod
    def _init_weights(module):
        if isinstance(module, (nn.Linear, nn.Embedding)):
            nn.init.normal_(module.weight, mean=0.0, std=0.02)
            if isinstance(module, nn.Linear) and module.bias is not None:
                nn.init.zeros_(module.bias)

    def forward(self, idx, *, structural_bias=None, global_features=None, targets=None):
        B, T = idx.shape
        if T > self.cfg.block_size:
            raise ValueError(f"sequence length {T} exceeds block_size={self.cfg.block_size}")
        pos = torch.arange(T, device=idx.device)
        x = self.token_emb(idx) + self.pos_emb(pos)[None, :, :]
        if global_features is not None:
            if global_features.dim() == 1:
                global_features = global_features.unsqueeze(0)
            x = x + self.global_proj(global_features)[:, None, :]
        for block in self.blocks:
            x = block(x, structural_bias)
        logits = self.lm_head(self.ln_f(x))
        loss = None
        if targets is not None:
            loss = F.cross_entropy(logits.reshape(-1, logits.size(-1)), targets.reshape(-1))
        return logits, loss

    @torch.no_grad()
    def generate(self, idx, *, steps: int, sidecar_fn=None, tokenizer=None, temperature: float = 0.9, top_k: int = 20):
        self.eval()
        for _ in range(steps):
            ctx = idx[:, -self.cfg.block_size:]
            bias = None
            gf = None
            if sidecar_fn is not None and tokenizer is not None:
                tokens = tokenizer.tokens(ctx[0].tolist())
                rep = sidecar_fn(tokens)
                bias = torch.tensor(rep.attention_bias, dtype=torch.float32, device=idx.device).unsqueeze(0)
                gf = torch.tensor(rep.global_features, dtype=torch.float32, device=idx.device).unsqueeze(0)
            logits, _ = self(ctx, structural_bias=bias, global_features=gf)
            next_logits = logits[:, -1, :] / max(1e-6, temperature)
            if top_k and top_k < next_logits.size(-1):
                v, _ = torch.topk(next_logits, top_k)
                next_logits[next_logits < v[:, [-1]]] = float('-inf')
            probs = F.softmax(next_logits, dim=-1)
            nxt = torch.multinomial(probs, 1)
            idx = torch.cat([idx, nxt], dim=1)
        return idx
