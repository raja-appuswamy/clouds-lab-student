"""EurecomGPT — a tiny character-(byte-)level GPT in PyTorch (~5M params).

You implement the heart of the transformer — ``scaled_dot_product_attention`` — and the
rest of the network is provided. You train this in Colab (see the notebook + TASKS.md),
across CPU / threaded / GPU / TPU runtimes, then upload the weights to Cloud Storage.

Imports torch, so this module is used in Colab; the autograder never imports it (it checks
your uploaded weights by their shapes). Architecture dims live in ``config.py``.
"""

from __future__ import annotations

import math

import torch
import torch.nn as nn
import torch.nn.functional as F

from config import CONFIG, GPTConfig


def scaled_dot_product_attention(q, k, v, mask):
    """Causal scaled dot-product attention.

    Args:
        q, k, v: tensors of shape ``(B, n_head, T, head_dim)``.
        mask: boolean tensor ``(T, T)``, ``True`` where attention is allowed
              (lower-triangular — position i may attend to j <= i).
    Returns:
        tensor ``(B, n_head, T, head_dim)``:
            att = softmax( (q @ kᵀ) / sqrt(head_dim)  with masked positions set to -inf )
            out = att @ v
    """
    # TODO: scores = q @ kᵀ / sqrt(head_dim); mask out where ~mask with -inf;
    #       softmax over the last dim; return att @ v.
    raise NotImplementedError("Phase 2: implement scaled_dot_product_attention()")


class CausalSelfAttention(nn.Module):
    def __init__(self, cfg: GPTConfig):
        super().__init__()
        assert cfg.n_embd % cfg.n_head == 0
        self.n_head = cfg.n_head
        self.c_attn = nn.Linear(cfg.n_embd, 3 * cfg.n_embd)
        self.c_proj = nn.Linear(cfg.n_embd, cfg.n_embd)
        # persistent=False → not saved in state_dict, so the uploaded weights contain
        # only real parameters (keeps the safetensors param count exact for grading).
        self.register_buffer(
            "mask",
            torch.tril(torch.ones(cfg.block_size, cfg.block_size, dtype=torch.bool)),
            persistent=False,
        )

    def forward(self, x):
        B, T, C = x.shape
        q, k, v = self.c_attn(x).split(C, dim=2)
        hd = C // self.n_head
        q = q.view(B, T, self.n_head, hd).transpose(1, 2)
        k = k.view(B, T, self.n_head, hd).transpose(1, 2)
        v = v.view(B, T, self.n_head, hd).transpose(1, 2)
        y = scaled_dot_product_attention(q, k, v, self.mask[:T, :T])
        y = y.transpose(1, 2).contiguous().view(B, T, C)
        return self.c_proj(y)


class MLP(nn.Module):
    def __init__(self, cfg: GPTConfig):
        super().__init__()
        self.fc = nn.Linear(cfg.n_embd, 4 * cfg.n_embd)
        self.proj = nn.Linear(4 * cfg.n_embd, cfg.n_embd)

    def forward(self, x):
        return self.proj(F.gelu(self.fc(x)))


class Block(nn.Module):
    def __init__(self, cfg: GPTConfig):
        super().__init__()
        self.ln1 = nn.LayerNorm(cfg.n_embd)
        self.attn = CausalSelfAttention(cfg)
        self.ln2 = nn.LayerNorm(cfg.n_embd)
        self.mlp = MLP(cfg)

    def forward(self, x):
        x = x + self.attn(self.ln1(x))
        x = x + self.mlp(self.ln2(x))
        return x


class GPT(nn.Module):
    def __init__(self, cfg: GPTConfig = CONFIG):
        super().__init__()
        self.cfg = cfg
        self.tok_emb = nn.Embedding(cfg.vocab_size, cfg.n_embd)
        self.pos_emb = nn.Embedding(cfg.block_size, cfg.n_embd)
        self.blocks = nn.ModuleList([Block(cfg) for _ in range(cfg.n_layer)])
        self.ln_f = nn.LayerNorm(cfg.n_embd)
        self.head = nn.Linear(cfg.n_embd, cfg.vocab_size, bias=False)

    def forward(self, idx, targets=None):
        B, T = idx.shape
        pos = torch.arange(T, device=idx.device)
        x = self.tok_emb(idx) + self.pos_emb(pos)
        for block in self.blocks:
            x = block(x)
        logits = self.head(self.ln_f(x))
        loss = None
        if targets is not None:
            loss = F.cross_entropy(logits.view(-1, logits.size(-1)), targets.view(-1))
        return logits, loss

    @torch.no_grad()
    def generate(self, idx, max_new_tokens: int, temperature: float = 1.0):
        for _ in range(max_new_tokens):
            idx_cond = idx[:, -self.cfg.block_size:]
            logits, _ = self(idx_cond)
            logits = logits[:, -1, :] / temperature
            probs = F.softmax(logits, dim=-1)
            idx = torch.cat([idx, torch.multinomial(probs, 1)], dim=1)
        return idx

    def num_params(self) -> int:
        return sum(p.numel() for p in self.parameters())
