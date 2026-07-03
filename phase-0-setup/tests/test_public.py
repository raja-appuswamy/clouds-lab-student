"""Phase 0 public tests — these ship to students so they can self-check.

Two kinds of test here:

  * Unit tests for the functions you implement (``parse_gcloud_config``,
    ``parse_repo_slug``). These use canned inputs and pass/fail purely on YOUR code —
    no cloud, no network. They fail while the TODOs are unfilled and pass once done.
  * Environment tests that read ``submission/phase0_report.json`` to confirm your
    machine is actually set up (Python 3.11, gcloud configured, Docker, GitHub remote).

Total: 60 points (the hidden instructor tests add the rest — see the rubric in TASKS.md).
"""

from __future__ import annotations

import verify_setup as vs
from autograder.points import points

# --------------------------------------------------------------------------- #
# Unit tests for the functions students implement (offline, deterministic)
# --------------------------------------------------------------------------- #
SAMPLE_GCLOUD_JSON = """
{
  "core": {
    "account": "student@eurecom.fr",
    "project": "eurecomgpt-abc123",
    "disable_usage_reporting": "True"
  }
}
"""


@points(10)
def test_parse_gcloud_config_extracts_account_and_project():
    result = vs.parse_gcloud_config(SAMPLE_GCLOUD_JSON)
    assert result["account"] == "student@eurecom.fr"
    assert result["project"] == "eurecomgpt-abc123"


@points(5)
def test_parse_gcloud_config_handles_empty():
    assert vs.parse_gcloud_config("") == {"account": "", "project": ""}


@points(10)
def test_parse_repo_slug_https():
    url = "https://github.com/eurecom/clouds-lab.git"
    assert vs.parse_repo_slug(url) == "eurecom/clouds-lab"


@points(10)
def test_parse_repo_slug_ssh():
    url = "git@github.com:eurecom/clouds-lab.git"
    assert vs.parse_repo_slug(url) == "eurecom/clouds-lab"


@points(5)
def test_parse_repo_slug_rejects_non_github():
    assert vs.parse_repo_slug("https://gitlab.com/x/y.git") == ""
    assert vs.parse_repo_slug("") == ""


# --------------------------------------------------------------------------- #
# Environment tests (read the submission report)
# --------------------------------------------------------------------------- #
@points(5)
def test_python_is_311(report):
    assert report["python"]["ok"], (
        f"expected Python 3.11, report says {report['python']['version']}"
    )


@points(5)
def test_gcloud_configured(report):
    gc = report["gcloud"]
    assert gc["account"], "gcloud account is empty — run `gcloud auth login`"
    assert gc["project"], "gcloud project is empty — run `gcloud config set project ...`"


@points(5)
def test_docker_present(report):
    assert report["docker"]["present"], "Docker not detected — is Docker Desktop installed/running?"


@points(5)
def test_git_remote_is_github(report):
    git = report["git"]
    assert git["is_github"], f"git remote is not a github.com URL: {git['remote']!r}"
    assert git["slug"], "could not derive owner/repo — check parse_repo_slug()"
