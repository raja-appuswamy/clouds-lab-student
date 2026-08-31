"""Cloud Function (gen 2) entry point — the SAME echo logic as a serverless function.

This is the third deployment target. It reuses ``build_echo`` and ``extract_message``
from ``app.py``, so the exact logic you run in a container (VM + Cloud Run) also runs
here as a function — that is the point of Phase 1: one behaviour, three service models.

Deployed with ``gcloud functions deploy`` (see TASKS.md). Provided in full — no TODOs;
your job is to get it deployed and compare its cold start to the other two.
"""

from __future__ import annotations

import functions_framework
from flask import jsonify

from app import build_echo, extract_message


@functions_framework.http
def echo(request):
    message = extract_message(request.args, request.get_json(silent=True))
    if message is None:
        return jsonify({"error": "provide ?msg=... or JSON {\"message\": ...}"}), 400
    return jsonify(build_echo(message))
