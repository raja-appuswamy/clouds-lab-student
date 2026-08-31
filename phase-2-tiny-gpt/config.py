"""Model configuration for EurecomGPT — a tiny character-(byte-)level GPT (~5M params).

Kept torch-free on purpose so the autograder can import it without installing PyTorch.
Both ``model.py`` (which builds the network) and the tests (which validate your uploaded
weights) read these dims, so the expected architecture is defined in exactly one place.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GPTConfig:
    vocab_size: int = 256   # byte-level tokenizer: every byte is a token (0..255)
    block_size: int = 256   # context length
    n_layer: int = 6
    n_head: int = 8
    n_embd: int = 256       # must be divisible by n_head


CONFIG = GPTConfig()


def expected_param_count(cfg: GPTConfig = CONFIG) -> int:
    """Analytic parameter count for the architecture in model.py (no torch needed)."""
    e, v, b, L = cfg.n_embd, cfg.vocab_size, cfg.block_size, cfg.n_layer
    emb = v * e + b * e                      # token + positional embeddings
    ln = 2 * e                               # a LayerNorm = weight + bias
    per_block = (
        ln                                   # ln1
        + (e * 3 * e + 3 * e)                # attn c_attn (Linear e -> 3e)
        + (e * e + e)                        # attn c_proj (Linear e -> e)
        + ln                                 # ln2
        + (e * 4 * e + 4 * e)                # mlp fc  (Linear e -> 4e)
        + (4 * e * e + e)                    # mlp proj (Linear 4e -> e)
    )
    head = e * v                             # lm_head (Linear e -> v, no bias, untied)
    return emb + L * per_block + ln + head   # + final LayerNorm
