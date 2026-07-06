# Phase 0 — Tasks & Deliverables

Work through these in order. Read [README.md](README.md) first for the background links
and the free-tier safety rules.

> **Environment:** do all of this in **Google Cloud Shell** (the mandated environment — see
> [README.md](README.md)). Steps marked _(local only)_ are for the optional local-IDE path
> and can be **skipped in Cloud Shell**, where `gcloud`, Docker, git, and Python are already
> installed.

## Tasks

- [ ] **1. Create a GCP project.**
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

1. Your **public GitHub repo URL**.
2. A committed `submission/phase0_report.json` (produced by `verify_setup.py`).
3. A **green** `autograde-phase-0` CI run on your latest push.
4. A screenshot of `gcloud config list` (place it at `submission/gcloud_config.png`).

## Grading rubric (100 pts)

Autograded — the point values match the test suite exactly.

| Check | Points | Where |
|---|---:|---|
| `parse_gcloud_config` extracts account + project | 10 | public unit test |
| `parse_gcloud_config` handles empty input | 5 | public unit test |
| `parse_repo_slug` — HTTPS form | 10 | public unit test |
| `parse_repo_slug` — SSH form | 10 | public unit test |
| `parse_repo_slug` — rejects non-GitHub | 5 | public unit test |
| Python is 3.11/3.12 | 5 | public (report) |
| gcloud account + project configured | 5 | public (report) |
| Docker installed | 5 | public (report) |
| git remote is GitHub | 5 | public (report) |
| Repo is *actually* public (GitHub API) | 25 | **hidden** |
| Project id is a real GCP id, not a placeholder | 15 | **hidden** |
| **Total** | **100** | |

Public checks (60 pts) you can verify yourself before submitting; hidden checks (40 pts)
are run by the instructor. While coding, run the offline unit tests
(`phase-0-setup/tests/test_units.py`); after `verify_setup.py`, run the full public suite
(`phase-0-setup/tests`) to see your current public score.
