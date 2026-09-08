# Phase 0 — Tasks & Deliverables

Work through these in order. Read [README.md](README.md) first for the background links
and the free-tier safety rules.

> **Environment:** do all of this in **Google Cloud Shell** (the mandated environment — see
> [README.md](README.md)). Steps marked _(local only)_ are for the optional local-IDE path
> and can be **skipped in Cloud Shell**, where `gcloud`, Docker, git, and Python are already
> installed.

> **Note on this phase.** Phase 0 is setup, so **every command here is given in full** — a
> student who cannot start is blocked on everything. From **Phase 1 onward the `gcloud`
> commands are withheld**: each task states an objective and names the Google Cloud module
> that taught the commands, and you recall them yourself.

## Tasks

- [ ] **1. Create a GCP project.**
  _Taught in: Fundamentals M2 — Resources and Access in the Cloud._
  Sign in at <https://console.cloud.google.com>, create a new project (note its
  **project id** — you will need it). Set a **Cloud Budget alert at €0.01** so you are
  emailed if anything ever bills. (If your $300 free trial has ended, you must have an
  **active/upgraded billing account** for Always Free to apply.)

- [ ] **2. Create your public GitHub repo from the course template.**
  On the course template repo, click **"Use this template" → Create a new repository** and
  make it **public** (or set Settings → General → Danger Zone → Change visibility to Public
  afterward).

- [ ] **3. Open Cloud Shell and clone your repo.**
  Open **Cloud Shell** (`>_` icon in the Console, or <https://shell.cloud.google.com>), then
  click **Open Editor** for the IDE. Clone your repo and `cd` into it:
  ```bash
  git clone https://github.com/<you>/<your-repo>.git
  cd <your-repo>
  git remote get-url origin      # must print your github.com URL
  ```
  _(local only)_ Instead, install git + your IDE locally and clone there.

- [ ] **4. Point `gcloud` at your project and verify.**
  _Taught in: Foundation M1 — Interacting with Google Cloud._
  In Cloud Shell, `gcloud` is already installed and authenticated as your account. Set the
  project and verify:
  ```bash
  gcloud config set project <YOUR_PROJECT_ID>
  gcloud config list                 # must show your account and project
  gcloud billing accounts list       # must show ACCOUNT_ID, NAME, OPEN (True)
  ```
  _(local only)_ First install the Google Cloud SDK, then `gcloud init` and
  `gcloud auth login`, before the commands above.

- [ ] **5. Create a Python virtual environment and install requirements.**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate          # Windows local: .venv\Scripts\activate
  python --version                   # must be 3.11.x (Cloud Shell) — 3.12 also accepted
  pip install -r requirements.txt
  ```

- [ ] **6. Confirm Docker is available.**
  In Cloud Shell, Docker is pre-installed — just check:
  ```bash
  docker --version
  ```
  _(local only)_ Install and start **Docker Desktop** first. (You run no container in
  Phase 0 — this just readies you for Phase 1.)

- [ ] **7. Implement the two TODOs in `verify_setup.py`.**
  Open [verify_setup.py](verify_setup.py) and implement:
  - `parse_gcloud_config(raw)` — extract account + project from gcloud's JSON output.
  - `parse_repo_slug(remote_url)` — turn a git remote URL into `owner/repo`.
  Run the **unit tests** as you go — they are offline and need no report:
  ```bash
  python -m pytest phase-0-setup/tests/test_units.py -p autograder.points -q
  ```

- [ ] **8. Run the self-check, then the report tests.**
  From the **repo root**, generate the report first, *then* run the report tests (they read
  the report — running them before this step fails on purpose):
  ```bash
  python phase-0-setup/verify_setup.py                       # writes submission/phase0_report.json
  python -m pytest phase-0-setup/tests -p autograder.points -q   # full public suite
  ```
  The report also records whether you ran in Cloud Shell.

- [ ] **9. Commit and push.**
  Commit `submission/phase0_report.json` **and** your completed `verify_setup.py`, then push.
  Open the **Actions** tab and confirm the `autograde-phase-0` workflow is **green**.

## Deliverables

1. Your **public GitHub repo URL** with the committed `submission/phase0_report.json` (produced by `verify_setup.py`).
2. A **green** `autograde-phase-0` CI run on your latest push.

## How your work is checked

Your grade comes from the autograder, plus any writeup listed under **Deliverables**, which
the instructor assesses separately. Run the public suite yourself before you push (after `verify_setup.py`):

```bash
python -m pytest phase-0-setup/tests -p autograder.points -q
```

While coding, `phase-0-setup/tests/test_units.py` alone is faster — it needs no cloud resources.
The instructor also runs checks that are not in your repo, so a green public run is
necessary but not sufficient.

