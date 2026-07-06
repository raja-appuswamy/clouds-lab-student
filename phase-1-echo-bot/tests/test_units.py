"""Phase 1 unit tests — offline, no cloud, no report needed.

Test the two functions you implement in ``app.py`` and the routes that use them, via
Flask's test client. Run them while coding:

    python -m pytest phase-1-echo-bot/tests/test_units.py -p autograder.points -q

They fail while the TODOs are unfilled and pass once your code is correct. (45 points.)
"""

from __future__ import annotations

import app as echo_app
from autograder.points import points


@points(10)
def test_build_echo():
    assert echo_app.build_echo("hello") == {"echo": "hello", "length": 5}
    assert echo_app.build_echo("") == {"echo": "", "length": 0}


@points(10)
def test_extract_message():
    assert echo_app.extract_message({"msg": "hi"}, None) == "hi"
    assert echo_app.extract_message({}, {"message": "yo"}) == "yo"
    assert echo_app.extract_message({}, None) is None
    # Query param wins when both are present.
    assert echo_app.extract_message({"msg": "q"}, {"message": "b"}) == "q"


# --- routes (provided) exercised through the two functions above ---
def _client():
    echo_app.app.config.update(TESTING=True)
    return echo_app.app.test_client()


@points(5)
def test_healthz():
    resp = _client().get("/healthz")
    assert resp.status_code == 200
    assert resp.get_data(as_text=True) == "ok"


@points(10)
def test_echo_get():
    resp = _client().get("/echo?msg=hello")
    assert resp.status_code == 200
    assert resp.get_json() == {"echo": "hello", "length": 5}


@points(5)
def test_echo_post_json():
    resp = _client().post("/echo", json={"message": "world"})
    assert resp.status_code == 200
    assert resp.get_json() == {"echo": "world", "length": 5}


@points(5)
def test_echo_missing_message_is_400():
    resp = _client().get("/echo")
    assert resp.status_code == 400
    assert "error" in resp.get_json()
