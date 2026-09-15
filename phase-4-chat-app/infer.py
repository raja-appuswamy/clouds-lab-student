"""NumPy inference for the Phase-2 tiny GPT (provided — no torch, keeps the image small).

Loads the safetensors weights you trained in Phase 2 and runs a forward pass + sampling in
plain NumPy. The architecture matches Phase 2's ``config.py`` / ``model.py``.
"""

from __future__ import annotations

import math

import numpy as np

# Architecture (must match Phase 2's GPTConfig).
VOCAB, BLOCK, N_LAYER, N_HEAD, N_EMBD = 256, 256, 6, 8, 256
HEAD_DIM = N_EMBD // N_HEAD


def load_weights(data: bytes) -> dict:
    """Parse safetensors bytes into a dict of float32 NumPy arrays."""
    from safetensors.numpy import load

    return {k: v.astype(np.float32) for k, v in load(data).items()}


def encode(text: str) -> list[int]:
    return list(text.encode("utf-8"))


def decode(ids) -> str:
    return bytes(int(t) & 0xFF for t in ids).decode("utf-8", "replace")


def _ln(x, w, b, eps=1e-5):
    mu = x.mean(-1, keepdims=True)
    var = x.var(-1, keepdims=True)
    return (x - mu) / np.sqrt(var + eps) * w + b


def _gelu(x):
    return 0.5 * x * (1.0 + np.tanh(math.sqrt(2 / math.pi) * (x + 0.044715 * x ** 3)))


def _softmax(x, axis=-1):
    x = x - x.max(axis=axis, keepdims=True)
    e = np.exp(x)
    return e / e.sum(axis=axis, keepdims=True)


def _linear(x, weight, bias):
    # torch Linear stores weight as [out, in]; y = x @ Wᵀ + b.
    return x @ weight.T + bias


def forward(w: dict, idx: np.ndarray) -> np.ndarray:
    """Logits [T, VOCAB] for a 1-D array of token ids."""
    t = len(idx)
    x = w["tok_emb.weight"][idx] + w["pos_emb.weight"][:t]
    mask = np.tril(np.ones((t, t)))
    for i in range(N_LAYER):
        p = f"blocks.{i}."
        a = _ln(x, w[p + "ln1.weight"], w[p + "ln1.bias"])
        qkv = _linear(a, w[p + "attn.c_attn.weight"], w[p + "attn.c_attn.bias"])
        q, k, v = qkv[:, :N_EMBD], qkv[:, N_EMBD:2 * N_EMBD], qkv[:, 2 * N_EMBD:]

        def heads(z):
            return z.reshape(t, N_HEAD, HEAD_DIM).transpose(1, 0, 2)  # [H, T, hd]

        qh, kh, vh = heads(q), heads(k), heads(v)
        att = (qh @ kh.transpose(0, 2, 1)) / math.sqrt(HEAD_DIM)      # [H, T, T]
        att = np.where(mask[None] == 0, -1e9, att)
        att = _softmax(att, axis=-1)
        y = (att @ vh).transpose(1, 0, 2).reshape(t, N_EMBD)          # [T, E]
        x = x + _linear(y, w[p + "attn.c_proj.weight"], w[p + "attn.c_proj.bias"])

        m = _ln(x, w[p + "ln2.weight"], w[p + "ln2.bias"])
        h = _gelu(_linear(m, w[p + "mlp.fc.weight"], w[p + "mlp.fc.bias"]))
        x = x + _linear(h, w[p + "mlp.proj.weight"], w[p + "mlp.proj.bias"])

    x = _ln(x, w["ln_f.weight"], w["ln_f.bias"])
    return x @ w["head.weight"].T


def generate(w: dict, prompt: str, max_new_tokens: int = 120, temperature: float = 0.8,
             seed: int = 0) -> str:
    """Sample a continuation of ``prompt`` and return the newly generated text."""
    rng = np.random.default_rng(seed)
    idx = encode(prompt) or [10]
    start = len(idx)
    for _ in range(max_new_tokens):
        logits = forward(w, np.array(idx[-BLOCK:]))[-1] / max(temperature, 1e-6)
        probs = _softmax(logits)
        idx.append(int(rng.choice(len(probs), p=probs)))
    return decode(idx[start:])
