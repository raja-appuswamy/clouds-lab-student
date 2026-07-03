"""Reusable environment probes shared across phases.

These are *provided* helpers — students do not implement them. They wrap the raw
system calls (running a subprocess, reading the git remote) so that each phase's
``verify_setup.py`` can focus on the small parsing logic students actually fill in.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from typing import Tuple

# Reference Python for the lab. The mandated environment (Google Cloud Shell), Colab, and
# the Cloud Run base image all provide 3.11, and the grading CI pins 3.11. Local installs
# may also use 3.12. Kept narrow on purpose for reproducibility across those environments.
REFERENCE_PYTHON = (3, 11)
SUPPORTED_PYTHON = {(3, 11), (3, 12)}


def run(cmd: list[str], timeout: int = 30) -> Tuple[int, str, str]:
    """Run ``cmd`` and return ``(returncode, stdout, stderr)``.

    Never raises for a non-zero exit or a missing binary; returns ``(127, "", msg)``
    when the executable is absent so callers can degrade gracefully.
    """
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except FileNotFoundError as exc:
        return 127, "", str(exc)
    except subprocess.TimeoutExpired as exc:
        return 124, "", str(exc)


def python_version() -> Tuple[int, int, int]:
    """Return the running interpreter's ``(major, minor, micro)``."""
    return sys.version_info[:3]


def python_is_supported() -> bool:
    """True iff the running interpreter's major.minor is in :data:`SUPPORTED_PYTHON`."""
    return sys.version_info[:2] in SUPPORTED_PYTHON


def in_cloud_shell() -> bool:
    """True iff running inside Google Cloud Shell (which sets CLOUD_SHELL=true)."""
    return (
        os.environ.get("CLOUD_SHELL") == "true"
        or os.environ.get("GOOGLE_CLOUD_SHELL") == "true"
    )


def has_command(name: str) -> bool:
    """True iff ``name`` resolves on PATH."""
    return shutil.which(name) is not None


def git_remote_url(remote: str = "origin") -> str:
    """Return the URL of the given git remote, or ``""`` if unset / not a repo."""
    code, out, _ = run(["git", "remote", "get-url", remote])
    return out if code == 0 else ""
