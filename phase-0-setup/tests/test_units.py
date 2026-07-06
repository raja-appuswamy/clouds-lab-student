"""Phase 0 unit tests — offline, no cloud, no report needed.

These test the two functions YOU implement in ``verify_setup.py``
(``parse_gcloud_config``, ``parse_repo_slug``) with canned inputs. Run them freely
**while you are implementing** — they need nothing set up:

    python -m pytest phase-0-setup/tests/test_units.py -p autograder.points -q

They fail while the TODOs are unfilled and pass once your code is correct. (40 points.)
"""

from __future__ import annotations

import verify_setup as vs
from autograder.points import points

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
