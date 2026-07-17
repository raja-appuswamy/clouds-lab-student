# Phase 2 — Intra-node parallelism: train your own tiny transformer

**Goal:** train a small GPT while exercising the three layers of parallelism *inside a
single node* — CPU vectorization (SIMD), CPU threads, and accelerators (GPU/TPU) — and
measure where each stops helping.

**Lecture map:** Lecture 3 (SIMD/AVX vectorization, processes vs threads/OpenMP, GPUs &
CUDA/SIMT, TPUs & systolic arrays).

Estimated time: ~12 hours over two weeks. **Environment: Google Colab** with a **GPU (T4)**
runtime — *not* Cloud Shell (there is no free GPU/TPU on GCP; all training is in Colab).
**Prerequisite:** Phase 0 (a GCP project + `gcloud`).

---

## What you build

A **byte-level GPT** (~5M params: 6 layers, 8 heads, `n_embd=256`) in PyTorch and train it
on a small text corpus (TinyShakespeare). You implement:

- `attention_numpy.py` — scaled dot-product attention **twice**: naive Python loops vs
  vectorized NumPy. This is the SIMD lesson; you time both and see the speedup.
- `model.py` — the `scaled_dot_product_attention` at the heart of the transformer.

Then a provided **Colab notebook** drives five runs — CPU-naive, CPU-vectorized, CPU-thread
sweep, GPU, TPU — plots the results, trains the model, uploads the weights to **Cloud
Storage**, and writes your report.

---

## Background reading (study before the tasks)

Lecture 3 topics, with references:
- **Vectorization / SIMD**: why `Q @ Kᵀ` on NumPy is ~100× a Python loop —
  <https://numpy.org/doc/stable/reference/routines.linalg.html> and check your BLAS with
  `numpy.show_config()`.
- **Threads / intra-op parallelism**: PyTorch CPU threading —
  <https://pytorch.org/docs/stable/notes/cpu_threading_torchscript_inference.html>
- **GPU / CUDA / SIMT**: <https://pytorch.org/docs/stable/notes/cuda.html>;
  Colab GPUs — <https://research.google.com/colaboratory/faq.html>
- **TPU / systolic arrays**: `torch_xla` — <https://pytorch.org/xla/> ; background on the
  Matrix Unit (H.T. Kung's systolic arrays).
- **Transformers / GPT** (to understand what you're training): the nanoGPT walkthrough —
  <https://github.com/karpathy/nanoGPT> and "The Illustrated GPT-2" —
  <https://jalammar.github.io/illustrated-gpt2/>.
- **safetensors** (the weight format you upload): <https://github.com/huggingface/safetensors>

Be able to explain afterwards, for the **1-page reflection**: *where does parallelism stop
helping, and why?* (Amdahl's law, thread contention/memory bandwidth, kernel-launch and
host↔device transfer overhead for small batches, when the GPU/TPU is starved.)

---

## How it's graded (torch-free, fast)

- **Offline unit tests** grade your NumPy attention (naive == vectorized == reference).
- **Model check**: the autograder range-reads just your uploaded safetensors **header**
  from your **public GCS URL** and verifies the architecture + ~5M param count — no full
  download, no torch.
- **Report check**: your `submission/phase2_report.json` must show the measured speedups
  (vectorized < naive, GPU < CPU), a trained-down loss, and a text sample.
- The Colab **notebook + 1-page reflection** are assessed by the instructor.

## Free-tier & safety

- All training is in **Colab** (free T4 GPU ~ hours/week). Save nothing large to GCP.
- Only the **weights** (`model.safetensors`, a few MB) go to **Cloud Storage** (≪ 5 GB
  free). Make that one object public so grading can read it.
- Checkpoint if Colab disconnects; the model is tiny so a full run is minutes on a GPU.

Step-by-step with commands is in **[TASKS.md](TASKS.md)**.
