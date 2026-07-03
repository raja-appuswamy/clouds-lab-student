#!/usr/bin/env python3
"""Phase 0 self-check — probes your environment and writes a submission report.

Run this from the repository root once you have finished the setup tasks::

    python phase-0-setup/verify_setup.py

It inspects your machine (Python version, gcloud config, Docker, git remote) and
writes ``submission/phase0_report.json``. Commit that file and push — your CI and the
instructor grade it.

Two small functions are left for YOU to implement (search for ``TODO``):

  * ``parse_gcloud_config`` — pull the account + project out of ``gcloud`` JSON output.
  * ``parse_repo_slug``     — turn a git remote URL into ``owner/repo``.

Everything else is provided. These are pure functions (input string in, value out),
so you can test them without touching the cloud — see ``tests/test_public.py``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Make the shared `autograder` package importable when run from anywhere.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from autograder import env_checks  # noqa: E402

REPORT_PATH = REPO_ROOT / "submission" / "phase0_report.json"


# --------------------------------------------------------------------------- #
# Functions YOU implement
# --------------------------------------------------------------------------- #
def parse_gcloud_config(raw: str) -> dict:
    """Parse the JSON emitted by ``gcloud config list --format=json``.

    Return ``{"account": <str>, "project": <str>}`` using empty strings when a
    value is absent. The relevant fields live under the ``"core"`` section, e.g.::

        {"core": {"account": "you@example.com", "project": "my-proj-123"}}

    Args:
        raw: the raw stdout string from the gcloud command (may be empty).
    """
    # TODO: parse `raw` as JSON and return {"account": ..., "project": ...}
    #       from the "core" section. Return empty strings if raw is empty or a
    #       field is missing.
    raise NotImplementedError("Phase 0: implement parse_gcloud_config()")


def parse_repo_slug(remote_url: str) -> str:
    """Turn a GitHub remote URL into an ``owner/repo`` slug (no ``.git`` suffix).

    Must handle both forms git prints:

      * HTTPS: ``https://github.com/eurecom/clouds-lab.git``  -> ``eurecom/clouds-lab``
      * SSH:   ``git@github.com:eurecom/clouds-lab.git``      -> ``eurecom/clouds-lab``

    Return ``""`` if the URL is empty or not a github.com URL.

    Args:
        remote_url: output of ``git remote get-url origin`` (may be empty).
    """
    # TODO: return "owner/repo" for both the HTTPS and SSH forms shown above.
    #       Strip any trailing ".git". Return "" if not a github.com URL.
    raise NotImplementedError("Phase 0: implement parse_repo_slug()")


# --------------------------------------------------------------------------- #
# Provided probes (do not modify)
# --------------------------------------------------------------------------- #
def check_python() -> dict:
    major, minor, micro = env_checks.python_version()
    return {
        "version": f"{major}.{minor}.{micro}",
        "ok": env_checks.python_is_required(),
    }


def check_gcloud() -> dict:
    code, out, err = env_checks.run(["gcloud", "config", "list", "--format=json"])
    if code != 0:
        return {"account": "", "project": "", "error": err or "gcloud not found"}
    try:
        parsed = parse_gcloud_config(out)
    except NotImplementedError as exc:
        return {"account": "", "project": "", "error": str(exc)}
    return {"account": parsed["account"], "project": parsed["project"], "error": None}


def check_docker() -> dict:
    code, out, err = env_checks.run(["docker", "--version"])
    return {"version": out if code == 0 else "", "present": code == 0}


def check_git() -> dict:
    url = env_checks.git_remote_url()
    try:
        slug = parse_repo_slug(url)
    except NotImplementedError:
        slug = ""
    return {
        "remote": url,
        "is_github": "github.com" in url,
        "slug": slug,
    }


def build_report() -> dict:
    return {
        "phase": "0",
        "python": check_python(),
        "gcloud": check_gcloud(),
        "docker": check_docker(),
        "git": check_git(),
    }


def _print_summary(report: dict) -> None:
    def mark(ok: bool) -> str:
        return "OK  " if ok else "MISS"

    py = report["python"]
    gc = report["gcloud"]
    dk = report["docker"]
    gt = report["git"]
    print("Phase 0 environment check")
    print("-" * 40)
    print(f"[{mark(py['ok'])}] Python {py['version']} (need 3.11)")
    print(f"[{mark(bool(gc['account']))}] gcloud account: {gc['account'] or '(unset)'}")
    print(f"[{mark(bool(gc['project']))}] gcloud project: {gc['project'] or '(unset)'}")
    print(f"[{mark(dk['present'])}] {dk['version'] or 'docker not found'}")
    print(f"[{mark(gt['is_github'])}] git remote: {gt['remote'] or '(unset)'}")
    print("-" * 40)


def main() -> int:
    report = build_report()
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    _print_summary(report)
    print(f"\nWrote {REPORT_PATH.relative_to(REPO_ROOT)} — commit it and push.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
