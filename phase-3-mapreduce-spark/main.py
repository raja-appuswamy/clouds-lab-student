"""Cloud Run function: one MapReduce *worker* (provided — no TODOs).

Hadoop runs your mapper and reducer inside worker processes on a cluster; here the same
role is played by a serverless function that Cloud Workflows invokes once per task. The
function is stateless — every task reads its input from Cloud Storage and writes its
output back there — so any invocation can run on any instance, and a failed task can
simply be run again (the outputs are overwritten, i.e. tasks are **idempotent**).

Two task types share one deployment, selected by the JSON body's ``task`` field:

``map``     {"task": "map", "bucket", "job", "split": i, "num_reducers": R}
    Reads ``<job>/input/split-<i>.json`` (a list of ``[doc_id, text]``), runs YOUR
    ``map_wc`` on every document, then *partitions* the emitted pairs by
    ``partition(word, R)`` and writes one file per reducer:
    ``<job>/shuffle/split-<i>/part-<r>.json``. That per-reducer split is the first half
    of the shuffle — Hadoop's mappers do exactly this on local disk.

``reduce``  {"task": "reduce", "bucket", "job", "partition": r, "num_splits": M}
    Reads its partition file from EVERY map task (``split-0..M-1/part-<r>.json``) — the
    second half of the shuffle, the "fetch" — concatenates the pairs, then runs YOUR
    ``shuffle`` (group by key) and ``reduce_wc`` (sum), writing ``<job>/output/part-<r>.json``.

Optional ``"chaos": p`` makes a task fail with HTTP 503 with probability ``p`` *before*
doing any work, to show that the job tracker (the workflow's retry policy) — not the
task — is responsible for fault tolerance. Deployed with ``gcloud functions deploy``
(see TASKS.md); run locally with ``python -m functions_framework --target=mr_worker``.
"""

from __future__ import annotations

import json
import random

import functions_framework
from flask import jsonify

from mapreduce import map_wc, partition, reduce_wc, shuffle


# --------------------------------------------------------------------------- #
# Cloud Storage access — tiny adapter so the unit tests can swap in a fake.
# --------------------------------------------------------------------------- #
def read_json(bucket: str, key: str):
    from google.cloud import storage

    blob = storage.Client().bucket(bucket).blob(key)
    return json.loads(blob.download_as_bytes().decode("utf-8"))


def write_json(bucket: str, key: str, obj) -> None:
    from google.cloud import storage

    blob = storage.Client().bucket(bucket).blob(key)
    blob.upload_from_string(json.dumps(obj), content_type="application/json")


# --------------------------------------------------------------------------- #
# The two task types
# --------------------------------------------------------------------------- #
def run_map(bucket: str, job: str, split: int, num_reducers: int) -> dict:
    docs = read_json(bucket, f"{job}/input/split-{split:03d}.json")

    # MAP: your map_wc, once per document in this split.
    pairs = [pair for _doc_id, text in docs for pair in map_wc(text)]

    # PARTITION: bucket the pairs by reducer, so each reducer can fetch just its share.
    by_reducer: list[list] = [[] for _ in range(num_reducers)]
    for word, one in pairs:
        by_reducer[partition(word, num_reducers)].append([word, one])
    for r, part in enumerate(by_reducer):
        write_json(bucket, f"{job}/shuffle/split-{split:03d}/part-{r}.json", part)

    return {"task": "map", "split": split, "docs": len(docs), "pairs": len(pairs)}


def run_reduce(bucket: str, job: str, part: int, num_splits: int) -> dict:
    # FETCH: this reducer's slice of every map task's output.
    pairs: list = []
    for split in range(num_splits):
        pairs.extend(tuple(p) for p in read_json(bucket, f"{job}/shuffle/split-{split:03d}/part-{part}.json"))

    # SHUFFLE (group by key) + REDUCE (sum): your code.
    counts = reduce_wc(shuffle(pairs))
    write_json(bucket, f"{job}/output/part-{part}.json", counts)

    return {"task": "reduce", "partition": part, "pairs_in": len(pairs), "keys_out": len(counts)}


def handle(body: dict) -> tuple[dict, int]:
    """Dispatch one task. Returns ``(response_json, http_status)``."""
    chaos = float(body.get("chaos") or 0)
    if chaos and random.random() < chaos:
        # 503 is what a crashed/overloaded worker looks like; the workflow retries it.
        return {"error": "simulated worker crash", "task": body.get("task")}, 503

    task = body.get("task")
    if task == "map":
        return run_map(body["bucket"], body["job"], int(body["split"]), int(body["num_reducers"])), 200
    if task == "reduce":
        return run_reduce(body["bucket"], body["job"], int(body["partition"]), int(body["num_splits"])), 200
    return {"error": f"unknown task {task!r}; expected 'map' or 'reduce'"}, 400


@functions_framework.http
def mr_worker(request):
    body = request.get_json(silent=True) or {}
    payload, status = handle(body)
    return jsonify(payload), status
