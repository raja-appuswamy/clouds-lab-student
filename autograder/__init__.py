"""Shared autograding utilities for the CLOUDS lab.

Reused by every phase. The two public pieces are:

- ``points`` / ``visibility`` decorators (see :mod:`autograder.points`) used to tag
  test functions with a score and a public/hidden visibility.
- ``env_checks`` (see :mod:`autograder.env_checks`) — reusable environment probes
  (python version, git remote, subprocess runner) so phases don't re-implement them.

The pytest plugin lives in :mod:`autograder.points`; enable it with
``pytest -p autograder.points``.
"""

from .points import points, visibility  # noqa: F401

__all__ = ["points", "visibility"]
