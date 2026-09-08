# Phase 2 — Tasks & Deliverables

Read [README.md](README.md) first. You **code** the two attention functions on any machine
(Cloud Shell is fine for editing + the offline tests), then **train** in **Google Colab**
with a **GPU runtime**. Work through the tasks in order.

> **How these task sheets work.** Each cloud task states an *objective*, names the module and
> lecture where you were taught the commands, and says what the autograder checks.
> **The `gcloud` commands are not given** — you have already performed these operations in the
> Google Cloud modules listed under each task. Code, tests and provided scripts are given in
> full; only cloud operations are withheld. Nearly all of this phase runs in the notebook, so there is little to recall here — the heavy command practice is in Phases 1 and 5.
>
> **When you are stuck**, in this order: revisit the module named under the task; then
> `gcloud <group> --help`; then <https://cloud.google.com/sdk/gcloud/reference>. Worked
> commands are released after the submission deadline.

---

## Task 1 — Run the unit tests (implementing the model is optional)

`attention_numpy.py` and `model.py` already contain **working solutions**, so you can go
straight to the tests. Set up and run them (NumPy only — no GPU, no torch needed here):

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r phase-2-tiny-gpt/requirements.txt
python -m pytest phase-2-tiny-gpt/tests/test_units.py -p autograder.points -q
```

**Optional (recommended for the ML practice):** implement the attention yourself. The
[`templates/`](templates/) folder has skeleton versions with TODOs — `attention_naive` /
`attention_vectorized` (the SIMD lesson) and `scaled_dot_product_attention`. Copy one over
the working file and fill in the TODOs, then re-run the tests until they pass again:

```bash
cp templates/attention_numpy.py attention_numpy.py    # and/or templates/model.py
```

Everything from here on (Colab, training, upload, report) is **mandatory**.

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

The notebook does this. **Colab is not logged into gcloud**, so the upload cell first
authenticates your session:

```python
from google.colab import auth
auth.authenticate_user()      # opens a popup to log into your Google account
```

Then it uses the Cloud Storage **Python client** to create a bucket (`<PROJECT>-eurecomgpt`),
grant public read (`allUsers` → `roles/storage.objectViewer`, which works with uniform
bucket-level access), and upload `model.safetensors`. **Set `PROJECT` in that cell to your
Phase-0 project id.**

Your model URL is `https://storage.googleapis.com/<PROJECT>-eurecomgpt/model.safetensors`.
Confirm it is public (open it in a browser — it should download).

**Taught in.** Fundamentals M4 *Storage in the Cloud* · *Set Up an App Dev Environment* badge

If bucket creation fails with an API error, you need to enable Cloud Storage on the project
once — recall that command yourself.


---

## Task 6 — Write the report and the 1-page reflection

The final notebook cell writes `submission/phase2_report.json` (timings, final loss, sample,
and your model's public URL). Also write `submission/phase2_reflection.md` (~1 page):
**where does parallelism stop helping, and why?**

---

## Task 7 — Commit, push, confirm green CI

Commit `attention_numpy.py`, `model.py`, `submission/phase2_report.json`, and
`submission/phase2_reflection.md`, then push. The **`autograde-phase-2`** workflow runs the
NumPy tests + validates your public model + checks the report.

```bash
python -m pytest phase-2-tiny-gpt/tests -p autograder.points -q   # full public suite locally
```

## Deliverables

1. `attention_numpy.py` and `model.py` (the provided solution, or your own optional implementation).
2. The completed **Colab notebook** (with outputs + the threading plot).
3. `submission/phase2_report.json` and a **public** `model.safetensors` in Cloud Storage.
4. `submission/phase2_reflection.md` — the 1-page "where does parallelism stop helping?".
5. A **green** `autograde-phase-2` CI run.

## How your work is checked

Your grade comes from the autograder, plus any writeup listed under **Deliverables**, which
the instructor assesses separately. Run the public suite yourself before you push (once the notebook has produced the report and the upload):

```bash
python -m pytest phase-2-tiny-gpt/tests -p autograder.points -q
```

While coding, `phase-2-tiny-gpt/tests/test_units.py` alone is faster — it needs no cloud resources.
The instructor also runs checks that are not in your repo, so a green public run is
necessary but not sufficient.

