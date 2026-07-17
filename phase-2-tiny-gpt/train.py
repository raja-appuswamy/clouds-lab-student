"""Training utilities for EurecomGPT (provided — no TODOs).

Byte-level tokenizer (vocab = 256), batcher, a short training loop, and a safetensors
saver. Called from the Colab notebook. Keep the model tiny so a full run is minutes on a
T4 GPU.
"""

from __future__ import annotations

import time

import torch

from model import GPT


def encode(text: str) -> list[int]:
    """Byte-level encode: each UTF-8 byte is a token in 0..255."""
    return list(text.encode("utf-8"))


def decode(tokens) -> str:
    return bytes(int(t) & 0xFF for t in tokens).decode("utf-8", errors="replace")


def get_batch(data: torch.Tensor, block_size: int, batch_size: int, device: str):
    ix = torch.randint(0, len(data) - block_size - 1, (batch_size,))
    x = torch.stack([data[i:i + block_size] for i in ix])
    y = torch.stack([data[i + 1:i + 1 + block_size] for i in ix])
    return x.to(device), y.to(device)


def train(model: GPT, data: torch.Tensor, *, steps: int = 2000, batch_size: int = 32,
          lr: float = 3e-4, device: str = "cpu", log_every: int = 200):
    """Train in place; return ``(final_loss, elapsed_seconds)``."""
    model.to(device).train()
    opt = torch.optim.AdamW(model.parameters(), lr=lr)
    block_size = model.cfg.block_size
    start = time.perf_counter()
    last = float("nan")
    for step in range(steps):
        x, y = get_batch(data, block_size, batch_size, device)
        _, loss = model(x, y)
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
        last = loss.item()
        if log_every and step % log_every == 0:
            print(f"step {step:>5}  loss {last:.4f}")
    return last, time.perf_counter() - start


def save_model(model: GPT, path: str = "model.safetensors") -> str:
    """Save the state dict as safetensors (what you upload to Cloud Storage)."""
    from safetensors.torch import save_file

    state = {k: v.contiguous().cpu() for k, v in model.state_dict().items()}
    save_file(state, path)
    return path


def sample(model: GPT, prompt: str = "\n", max_new_tokens: int = 200, device: str = "cpu") -> str:
    model.eval()
    idx = torch.tensor([encode(prompt) or [10]], dtype=torch.long, device=device)
    out = model.generate(idx, max_new_tokens=max_new_tokens)[0].tolist()
    return decode(out)
