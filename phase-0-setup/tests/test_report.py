"""Phase 0 environment tests — read the submission report.

These confirm your machine is actually set up. They read
``submission/phase0_report.json``, so you must run the self-check FIRST:

    python phase-0-setup/verify_setup.py                 # generates the report
    python -m pytest phase-0-setup/tests/test_report.py -p autograder.points -q

If you run these before generating the report, they fail with a clear message telling
you to run ``verify_setup.py`` — that is expected, not a bug. (20 points.)
"""

from __future__ import annotations

from autograder.points import points


@points(5)
def test_python_is_supported(report):
    assert report["python"]["ok"], (
        f"expected Python 3.11 or 3.12, report says {report['python']['version']}"
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
