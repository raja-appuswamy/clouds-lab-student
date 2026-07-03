# Phase 0 — Tasks & Deliverables

Work through these in order. Read [README.md](README.md) first for the background links
and the free-tier safety rules.

## Tasks

- [ ] **1. Create a GCP project and claim the free tier.**
  Sign in at <https://console.cloud.google.com>, create a new project (note its
  **project id** — you will need it), and confirm your account shows the *Always Free*
  tier. Set a **Cloud Budget alert at €0.01** so you are emailed if anything ever bills.

- [ ] **2. Install and initialise the `gcloud` CLI.**
  Install the Google Cloud SDK, then run `gcloud init` and `gcloud auth login`. Point it
  at your Phase-0 project: `gcloud config set project <YOUR_PROJECT_ID>`. Verify with
  `gcloud config list` — it must show your **account** and **project**.

- [ ] **3. Create a public GitHub repo from the course template.**
  Use the template to create **your own** repository and make it **public** (Settings →
  General → Danger Zone → Change visibility, or choose "Public" at creation). Clone it
  locally. Confirm `git remote get-url origin` prints your `github.com` URL.

- [ ] **4. Create a Python 3.11 virtual environment and install requirements.**
  ```bash
  python3.11 -m venv .venv
  # Windows:  .venv\Scripts\activate     macOS/Linux:  source .venv/bin/activate
  pip install -r requirements.txt
  ```
  Confirm `python --version` reports **3.11.x**.

- [ ] **5. Install Docker Desktop.**
  Install and start Docker Desktop. Confirm `docker --version` prints a version. (You do
  not run any container in Phase 0 — this just readies you for Phase 1.)

- [ ] **6. Implement the two TODOs in `verify_setup.py`.**
  Open [verify_setup.py](verify_setup.py) and implement:
  - `parse_gcloud_config(raw)` — extract account + project from gcloud's JSON output.
  - `parse_repo_slug(remote_url)` — turn a git remote URL into `owner/repo`.
  Run the public unit tests as you go (they need no cloud access):
  ```bash
  python -m pytest phase-0-setup/tests/test_public.py -p autograder.points -q
  ```

- [ ] **7. Run the self-check, commit, and push.**
  From the **repo root**:
  ```bash
  python phase-0-setup/verify_setup.py
  ```
  This writes `submission/phase0_report.json`. Commit it **and** your completed
  `verify_setup.py`, then push. Open the **Actions** tab and confirm the
  `autograde-phase-0` workflow is **green**.

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
| Python is 3.11 | 5 | public (report) |
| gcloud account + project configured | 5 | public (report) |
| Docker installed | 5 | public (report) |
| git remote is GitHub | 5 | public (report) |
| Repo is *actually* public (GitHub API) | 25 | **hidden** |
| Project id is a real GCP id, not a placeholder | 15 | **hidden** |
| **Total** | **100** | |

Public checks (60 pts) you can verify yourself before submitting; hidden checks (40 pts)
are run by the instructor. Run `python -m pytest phase-0-setup/tests/test_public.py -p autograder.points`
any time to see your current public score.
