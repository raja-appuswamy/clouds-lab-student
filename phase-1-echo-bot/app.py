#!/usr/bin/env python3
"""EurecomGPT echo bot — a ~50-line Flask service.

This one app is deployed three ways in Phase 1 (an IaaS VM, Cloud Run, and — via
``main.py`` — a Cloud Function), so you can compare the service models hands-on.

You implement two small pure functions (search for ``TODO``); the routes are provided
and call them. Run the offline unit tests as you go:

    python -m pytest phase-1-echo-bot/tests/test_units.py -p autograder.points -q
"""

from __future__ import annotations

from flask import Flask, jsonify, request

app = Flask(__name__)


# --------------------------------------------------------------------------- #
# Functions YOU implement (pure — no Flask needed; unit-tested offline)
# --------------------------------------------------------------------------- #
def build_echo(message: str) -> dict:
    """Return the echo payload for ``message``.

    Must return exactly ``{"echo": <message>, "length": <len of message>}``.
    """
    # TODO: return {"echo": message, "length": len(message)}
    raise NotImplementedError("Phase 1: implement build_echo()")


def extract_message(args, json_body) -> str | None:
    """Pull the user's message out of a request.

    Accept either a query parameter ``msg`` (GET) or a JSON body ``{"message": ...}``
    (POST). Return the string, or ``None`` if neither is present.

    Args:
        args: request.args (a mapping with ``.get``), e.g. ``{"msg": "hi"}``.
        json_body: parsed JSON body or ``None``, e.g. ``{"message": "hi"}``.
    """
    # TODO: return args["msg"] if present, else json_body["message"] if present,
    #       else None. Use .get() so missing keys don't raise.
    raise NotImplementedError("Phase 1: implement extract_message()")


# --------------------------------------------------------------------------- #
# Routes (provided — they call the functions above)
# --------------------------------------------------------------------------- #
@app.get("/")
def index():
    return jsonify(
        {
            "service": "eurecomgpt-echo",
            "usage": "GET /echo?msg=hello  or  POST /echo {\"message\": \"hello\"}",
        }
    )


@app.get("/healthz")
def healthz():
    return "ok", 200


@app.route("/echo", methods=["GET", "POST"])
def echo():
    message = extract_message(request.args, request.get_json(silent=True))
    if message is None:
        return jsonify({"error": "provide ?msg=... or JSON {\"message\": ...}"}), 400
    return jsonify(build_echo(message))


if __name__ == "__main__":
    # Local dev server only; in the container we run gunicorn (see Dockerfile).
    import os

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
