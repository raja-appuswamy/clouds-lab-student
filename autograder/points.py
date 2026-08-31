"""Points / visibility decorators and the pytest plugin that scores a test run.

Usage in a test module::

    from autograder.points import points, visibility

    @points(5)
    def test_python_is_supported(report):
        assert report["python"]["ok"]

    @points(5)
    @visibility("hidden")          # instructor-only; hidden from students
    def test_repo_actually_public(report):
        ...

Enable the plugin and emit a Gradescope-style ``results.json``::

    pytest phase-0-setup/tests -p autograder.points --results-json score.json

By default hidden tests are *deselected* (students never run them). Pass
``--include-hidden`` (the instructor grader does) to run and score them too.
"""

from __future__ import annotations

import json

import pytest

# Accumulates one record per executed test's "call" phase for this session.
_RESULTS: list[dict] = []


def points(n):
    """Tag a test with the number of points it is worth (default 0 if untagged)."""

    def deco(func):
        func._points = n
        return func

    return deco


def visibility(v):
    """Tag a test as ``"public"`` (ships to students) or ``"hidden"`` (instructor-only)."""

    if v not in ("public", "hidden"):
        raise ValueError(f"visibility must be 'public' or 'hidden', got {v!r}")

    def deco(func):
        func._visibility = v
        return func

    return deco


def _points_of(item) -> int:
    return int(getattr(item.function, "_points", 0))


def _visibility_of(item) -> str:
    return getattr(item.function, "_visibility", "public")


# --------------------------------------------------------------------------- #
# pytest plugin hooks
# --------------------------------------------------------------------------- #
def pytest_addoption(parser):
    group = parser.getgroup("autograder")
    group.addoption(
        "--include-hidden",
        action="store_true",
        default=False,
        help="Include hidden (instructor-only) tests when running/scoring.",
    )
    group.addoption(
        "--results-json",
        action="store",
        default=None,
        help="Path to write the results.json score file.",
    )


def pytest_configure(config):
    # Reset in case the plugin is reused within one process (e.g. grade.py).
    _RESULTS.clear()


def pytest_collection_modifyitems(config, items):
    """Deselect hidden tests unless --include-hidden was passed."""
    if config.getoption("--include-hidden"):
        return
    kept, deselected = [], []
    for item in items:
        (deselected if _visibility_of(item) == "hidden" else kept).append(item)
    if deselected:
        config.hook.pytest_deselected(items=deselected)
        items[:] = kept


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    # Score on the "call" phase for tests that ran; capture setup errors too so a
    # crash (e.g. an unfilled TODO raising at import) still counts as 0, not silence.
    if report.when == "setup" and report.failed:
        _RESULTS.append(
            {
                "name": item.nodeid,
                "score": 0,
                "max_score": _points_of(item),
                "visibility": _visibility_of(item),
                "status": "error",
                "output": report.longreprtext,
            }
        )
        return
    if report.when != "call":
        return
    if report.skipped:
        # A skipped test (e.g. hidden network check offline) is "not attempted",
        # not a zero — leave it out of the tally entirely.
        return
    max_score = _points_of(item)
    _RESULTS.append(
        {
            "name": item.nodeid,
            "score": max_score if report.passed else 0,
            "max_score": max_score,
            "visibility": _visibility_of(item),
            "status": report.outcome,
            "output": "" if report.passed else report.longreprtext,
        }
    )


def pytest_terminal_summary(terminalreporter):
    if not _RESULTS:
        return
    total = sum(r["score"] for r in _RESULTS)
    max_total = sum(r["max_score"] for r in _RESULTS)
    terminalreporter.write_sep("=", f"AUTOGRADER SCORE: {total} / {max_total}")
    for r in _RESULTS:
        mark = "PASS" if r["score"] == r["max_score"] and r["status"] == "passed" else "FAIL"
        terminalreporter.write_line(
            f"  [{mark}] {r['score']:>3}/{r['max_score']:<3} {r['name']}"
        )


def pytest_sessionfinish(session, exitstatus):
    path = session.config.getoption("--results-json")
    if not path:
        return
    total = sum(r["score"] for r in _RESULTS)
    max_total = sum(r["max_score"] for r in _RESULTS)
    doc = {"score": total, "max_score": max_total, "tests": list(_RESULTS)}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2)
