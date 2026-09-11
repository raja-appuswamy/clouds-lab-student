#!/usr/bin/env python3
"""Drive one cloud MapReduce job and check it against the local reference (provided).

This is the Hadoop *client*: it does not compute anything itself. It

1. splits the corpus into ``num_splits`` input splits and uploads them to Cloud Storage
   (``gs://<bucket>/<job>/input/split-NNN.json``) — the HDFS "put";
2. starts an execution of your ``mr-wordcount`` workflow (the job tracker) and waits;
3. downloads the reducers' output partitions, merges them, and compares the result with
   ``mapreduce.word_count`` run locally — distributed == sequential is *the* correctness
   property of MapReduce;
4. publishes the merged counts as a public ``wordcount.json`` (what the grader reads) and
   writes ``submission/phase3_mapreduce.json``, which the Colab notebook folds into the
   final report.

Run it in Cloud Shell, after the function and the workflow are deployed (TASKS.md):

    python phase-3-mapreduce-spark/run_mr.py --project <PROJECT> --region <REGION> --worker-url <URL>

Add ``--chaos 0.3`` to make ~30% of task attempts fail, then watch the execution in the
console: the job still succeeds, because the workflow retries each failed task.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PHASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = PHASE_DIR.parent
sys.path.insert(0, str(PHASE_DIR))

import corpus      # noqa: E402
import mapreduce   # noqa: E402
import report      # noqa: E402

OUT_PATH = REPO_ROOT / "submission" / "phase3_mapreduce.json"


# --------------------------------------------------------------------------- #
# Pure helpers (also unit-tested offline)
# --------------------------------------------------------------------------- #
def make_splits(documents: list[tuple[int, str]], num_splits: int) -> list[list[list]]:
    """Cut the corpus into ``num_splits`` contiguous input splits (JSON-friendly lists).

    A split is a *unit of work for one map task*, not one document — Hadoop's InputSplit
    holds many records for the same reason: per-task overhead is paid once per split.
    """
    if not 1 <= num_splits <= len(documents):
        raise ValueError(f"num_splits must be in 1..{len(documents)}, got {num_splits}")
    per = -(-len(documents) // num_splits)          # ceil division
    return [[[doc_id, text] for doc_id, text in documents[i:i + per]]
            for i in range(0, len(documents), per)]


def merge_outputs(parts: list[dict[str, int]]) -> dict[str, int]:
    """Concatenate the reducers' output partitions. Keys never overlap (see ``partition``)."""
    merged: dict[str, int] = {}
    for part in parts:
        for word, count in part.items():
            if word in merged:
                raise ValueError(f"word {word!r} appears in two partitions — partitioner bug")
            merged[word] = count
    return merged


# --------------------------------------------------------------------------- #
# Cloud side
# --------------------------------------------------------------------------- #
def ensure_public_bucket(client, name: str):
    """Get or create the bucket, and make its objects publicly readable (bucket IAM)."""
    try:
        bucket = client.get_bucket(name)
    except Exception:
        bucket = client.create_bucket(name, location="US")
        print(f"created bucket gs://{name}")
    policy = bucket.get_iam_policy(requested_policy_version=3)
    if not any("allUsers" in b["members"] and b["role"] == "roles/storage.objectViewer"
               for b in policy.bindings):
        policy.bindings.append({"role": "roles/storage.objectViewer", "members": {"allUsers"}})
        bucket.set_iam_policy(policy)
    return bucket


def run_workflow(project: str, region: str, workflow: str, args: dict, poll_s: float = 3.0) -> dict:
    """Start one execution and block until it finishes. Returns a plain-dict summary."""
    from google.cloud.workflows import executions_v1

    parent = f"projects/{project}/locations/{region}/workflows/{workflow}"
    client = executions_v1.ExecutionsClient()
    try:
        exe = client.create_execution(
            parent=parent,
            execution=executions_v1.Execution(argument=json.dumps(args)),
        )
    except Exception as exc:                       # surface the most common mistake clearly
        print(f"could not start workflow {parent}: {exc}", file=sys.stderr)
        print("Is it deployed in that region under that name? Try: gcloud workflows list",
              file=sys.stderr)
        raise SystemExit(2)
    exec_id = exe.name.rsplit("/", 1)[-1]
    print(f"execution started: {exe.name}")
    print(f"  watch it: https://console.cloud.google.com/workflows/workflow/{region}/{workflow}"
          f"/execution/{exec_id}?project={project}")

    while True:
        exe = client.get_execution(name=exe.name)
        if exe.state != executions_v1.Execution.State.ACTIVE:
            break
        time.sleep(poll_s)
    return {
        "name": exe.name,
        "state": exe.state.name,
        "result": json.loads(exe.result) if exe.result else None,
        "error": (exe.error.payload if exe.error and exe.error.payload else None),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--project", required=True, help="your GCP project id")
    ap.add_argument("--region", required=True, help="region of the function AND the workflow")
    ap.add_argument("--worker-url", required=True, help="URL of the deployed mr-worker function")
    ap.add_argument("--workflow", default="mr-wordcount", help="workflow name (default: mr-wordcount)")
    ap.add_argument("--bucket", default=None, help="default: <project>-eurecomgpt")
    ap.add_argument("--num-splits", type=int, default=12, help="map tasks (default 12)")
    ap.add_argument("--num-reducers", type=int, default=4, help="reduce tasks (default 4)")
    ap.add_argument("--chaos", type=float, default=0.0, help="per-attempt failure probability")
    a = ap.parse_args(argv)
    bucket_name = a.bucket or f"{a.project}-eurecomgpt"

    from google.cloud import storage
    client = storage.Client(project=a.project)
    bucket = ensure_public_bucket(client, bucket_name)

    # 1. Split + upload -------------------------------------------------------------- #
    docs = corpus.load_documents()
    splits = make_splits(docs, a.num_splits)
    job = "mr-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    for i, split in enumerate(splits):
        bucket.blob(f"{job}/input/split-{i:03d}.json").upload_from_string(
            json.dumps(split), content_type="application/json")
    print(f"uploaded {len(splits)} input splits ({len(docs)} docs) to gs://{bucket_name}/{job}/input/")

    # 2. Run the job ------------------------------------------------------------------ #
    t0 = time.perf_counter()
    exe = run_workflow(a.project, a.region, a.workflow, {
        "worker_url": a.worker_url, "bucket": bucket_name, "job": job,
        "num_splits": len(splits), "num_reducers": a.num_reducers, "chaos": a.chaos,
    })
    cloud_s = time.perf_counter() - t0
    print(f"execution finished: {exe['state']} in {cloud_s:.1f}s")
    if exe["state"] != "SUCCEEDED":
        print("workflow failed:", json.dumps(exe["error"], indent=2)[:2000], file=sys.stderr)
        print("Open the console link above — the failing step and the worker's response are there.",
              file=sys.stderr)
        return 1

    # 3. Collect + verify ------------------------------------------------------------- #
    parts = [json.loads(bucket.blob(f"{job}/output/part-{r}.json").download_as_bytes())
             for r in range(a.num_reducers)]
    cloud_counts = merge_outputs(parts)

    t0 = time.perf_counter()
    local_counts = mapreduce.word_count(docs)
    local_s = time.perf_counter() - t0
    matches = cloud_counts == local_counts
    print(f"cloud job: {len(cloud_counts)} distinct words in {cloud_s:.1f}s  |  "
          f"local reference: {len(local_counts)} in {local_s*1000:.0f} ms  |  "
          f"identical: {matches}")
    if not matches:
        diff = {w for w in set(cloud_counts) | set(local_counts)
                if cloud_counts.get(w) != local_counts.get(w)}
        print(f"  {len(diff)} words differ, e.g. {sorted(diff)[:8]}", file=sys.stderr)

    # 4. Publish + record ------------------------------------------------------------- #
    bucket.blob("wordcount.json").upload_from_string(
        json.dumps(cloud_counts, sort_keys=True), content_type="application/json")
    public_url = f"https://storage.googleapis.com/{bucket_name}/wordcount.json"

    result = {
        "execution": exe["name"],
        "state": exe["state"],
        "job": job,
        "num_splits": len(splits),
        "num_reducers": a.num_reducers,
        "chaos": a.chaos,
        "map_tasks": exe["result"]["map_tasks"],
        "reduce_tasks": exe["result"]["reduce_tasks"],
        "cloud_elapsed_s": round(cloud_s, 1),
        "local_elapsed_s": round(local_s, 3),
        "vocab_size": len(cloud_counts),
        "top_terms": report.top_terms(cloud_counts, n=10),
        "wordcount_gcs_url": public_url,
        "matches_local": matches,
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"public counts: {public_url}")
    print(f"wrote {OUT_PATH.relative_to(REPO_ROOT)} — commit it; the notebook reads it.")
    return 0 if matches else 1


if __name__ == "__main__":
    raise SystemExit(main())
