# Phase 2 — Tasks & Deliverables

Read [README.md](README.md) first. You **code** the two attention functions on any machine
(Cloud Shell is fine for editing + the offline tests), then **train** in **Google Colab**
with a **GPU runtime**. Work through the tasks in order.

---

## Task 1 — Implement the attention code and run the unit tests

Fill the TODOs:
- [attention_numpy.py](attention_numpy.py) — `attention_naive` (loops) and
  `attention_vectorized` (matrix ops).
- [model.py](model.py) — `scaled_dot_product_attention` (the transformer core).

Run the offline unit tests (NumPy only — no GPU, no torch needed for these):

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r phase-2-tiny-gpt/requirements.txt
python -m pytest phase-2-tiny-gpt/tests/test_units.py -p autograder.points -q
```

---

## Task 2 — Open the notebook in Colab with a GPU runtime

Upload [notebook.ipynb](notebook.ipynb) to <https://colab.research.google.com> (or open it
from your GitHub repo). Set **Runtime → Change runtime type → T4 GPU**. In the first cell,
edit the `git clone` URL to **your** repo so Colab picks up your filled-in code.

---

## Task 3 — Run the parallelism experiments (Lecture 3)

Run the notebook cells top to bottom:
1. **CPU naive vs vectorized attention** — see the SIMD speedup; `numpy.show_config()`
   confirms an AVX-enabled BLAS.
2. **CPU threading sweep** — `torch.set_num_threads(1..8)`; the plot shows where extra
   threads stop helping (the contention point).
3. **GPU (CUDA)** — the same training loop on the T4; expect a large speedup vs CPU.
4. **TPU** — optionally switch to a TPU runtime and run with `torch_xla`; otherwise explain
   the systolic-array execution in your reflection and record any timing you got.

---

## Task 4 — Train the model and generate a sample

Run the training cell (~2000 steps, minutes on a GPU). Confirm the loss drops well below
the random-init value (~5.55) and the generated sample looks text-like.

---

## Task 5 — Upload the weights to Cloud Storage (public)

The notebook does this for you:

```bash
gcloud storage buckets create gs://$PROJECT-eurecomgpt --location=US   # first time
gcloud storage cp model.safetensors gs://$PROJECT-eurecomgpt/model.safetensors
gcloud storage objects update gs://$PROJECT-eurecomgpt/model.safetensors \
    --add-acl-grant=entity=allUsers,role=READER                        # make it public
```

Your model URL is `https://storage.googleapis.com/$PROJECT-eurecomgpt/model.safetensors`.
Confirm it is public (open it in a browser — it should download).

---

## Task 6 — Write the report and the 1-page reflection

The final notebook cell writes `submission/phase2_report.json` (timings, final loss, sample,
and your model's public URL). Also write `submission/phase2_reflection.md` (~1 page):
**where does parallelism stop helping, and why?**

---

## Task 7 — Commit, push, confirm green CI

Commit your filled `attention_numpy.py`, `model.py`, `submission/phase2_report.json`, and
`submission/phase2_reflection.md`, then push. The **`autograde-phase-2`** workflow runs the
NumPy tests + validates your public model + checks the report.

```bash
python -m pytest phase-2-tiny-gpt/tests -p autograder.points -q   # full public suite locally
```

## Deliverables

1. Filled `attention_numpy.py` and `model.py`.
2. The completed **Colab notebook** (with outputs + the threading plot).
3. `submission/phase2_report.json` and a **public** `model.safetensors` in Cloud Storage.
4. `submission/phase2_reflection.md` — the 1-page "where does parallelism stop helping?".
5. A **green** `autograde-phase-2` CI run.

## Grading rubric (100 pts)

| Check | Points | Where |
|---|---:|---|
| `attention_naive` matches reference | 10 | public unit test |
| `attention_vectorized` matches reference | 10 | public unit test |
| naive and vectorized agree | 10 | public unit test |
| output shape / convexity | 5 | public unit test |
| uploaded model is a ~5M-param model | 10 | public (GCS header) |
| architecture matches spec (embedding, layers, head) | 15 | public (GCS header) |
| all measurements present (attn, threads, cpu/gpu) | 10 | public (report) |
| parallelism helped (vectorized<naive, GPU<CPU) | 10 | public (report) |
| training + sample + model URL recorded | 5 | public (report) |
| model actually trained (final loss < 3.0) | 8 | **hidden** |
| training metadata sane (params, steps, sample, sweep) | 7 | **hidden** |
| **Total** | **100** | |

The notebook and the 1-page reflection are assessed separately by the instructor. Public
checks (85 pts) you can verify yourself once the notebook has produced the report + upload.
