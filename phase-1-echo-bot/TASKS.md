# Phase 1 — Tasks & Deliverables

Do everything in **Google Cloud Shell**. Read [README.md](README.md) first. All commands
assume you are at the **repo root** unless noted.

Set these once per shell session (reuse your Phase-0 project):

```bash
export PROJECT=$(gcloud config get-value project)
export REGION=us-central1
export ZONE=us-central1-a
export IMAGE=$REGION-docker.pkg.dev/$PROJECT/eurecomgpt/echo-bot:v1
```

Work through the tasks below in order.

---

## Task 1 — Enable the APIs

```bash
gcloud services enable artifactregistry.googleapis.com run.googleapis.com \
    cloudfunctions.googleapis.com cloudbuild.googleapis.com compute.googleapis.com
```

---

## Task 2 — Implement the code and run the unit tests

Fill the TODOs in [app.py](app.py) (`build_echo`, `extract_message`) and the two TODO
lines in the [Dockerfile](Dockerfile).

> **New to Flask?** Skim the official quickstart first — it covers exactly what you need
> here (defining routes, reading query params via `request.args`, reading a JSON body, and
> returning JSON with `jsonify`): <https://flask.palletsprojects.com/en/stable/quickstart/>.
> The routes in `app.py` are already written for you; you only implement the two small
> pure functions they call.

Then run the offline unit tests:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r phase-1-echo-bot/requirements.txt
python -m pytest phase-1-echo-bot/tests/test_units.py -p autograder.points -q
```

You can also run the app locally and preview it (Cloud Shell **Web Preview**, port 8080):

```bash
python phase-1-echo-bot/app.py     # then GET /echo?msg=hi
```

---

## Task 3 — Build the image and push it to Artifact Registry

```bash
gcloud artifacts repositories create eurecomgpt \
    --repository-format=docker --location=$REGION       # first time only
gcloud builds submit phase-1-echo-bot --tag $IMAGE       # builds your Dockerfile, pushes
```

Check the image size (discuss it in your report): the Artifact Registry console shows it,
or `gcloud artifacts docker images list $REGION-docker.pkg.dev/$PROJECT/eurecomgpt`.

---

## Task 4 — IaaS path: run the container on an `e2-micro` VM

```bash
gcloud compute instances create echo-vm \
    --zone=$ZONE --machine-type=e2-micro \
    --image-family=debian-12 --image-project=debian-cloud --tags=echo-http
# open port 8080 to the internet for the echo-http tag
gcloud compute firewall-rules create allow-echo-8080 \
    --allow=tcp:8080 --target-tags=echo-http --source-ranges=0.0.0.0/0
# let the VM's service account pull from Artifact Registry
VM_SA=$(gcloud compute instances describe echo-vm --zone=$ZONE \
    --format='value(serviceAccounts[0].email)')
gcloud projects add-iam-policy-binding $PROJECT \
    --member="serviceAccount:$VM_SA" --role="roles/artifactregistry.reader"
# SSH in and run the container
gcloud compute ssh echo-vm --zone=$ZONE
#   --- on the VM: ---
sudo apt-get update && sudo apt-get install -y docker.io
sudo gcloud auth configure-docker us-central1-docker.pkg.dev --quiet
sudo docker run -d -p 8080:8080 <PASTE $IMAGE HERE>
exit
```

Your VM URL is `http://<EXTERNAL_IP>:8080` — get the IP with:

```bash
gcloud compute instances describe echo-vm --zone=$ZONE \
    --format='value(networkInterfaces[0].accessConfigs[0].natIP)'
```

---

## Task 5 — Container PaaS path: deploy the same image to Cloud Run

```bash
gcloud run deploy echo-bot --image=$IMAGE --region=$REGION \
    --allow-unauthenticated --min-instances=0 --max-instances=3 --port=8080
# get its URL
gcloud run services describe echo-bot --region=$REGION --format='value(status.url)'
```

---

## Task 6 — Serverless path: deploy `main.py` as a Cloud Function (gen 2)

```bash
gcloud functions deploy echo --gen2 --region=$REGION \
    --runtime=python311 --source=phase-1-echo-bot \
    --entry-point=echo --trigger-http --allow-unauthenticated
# get its URL
gcloud functions describe echo --gen2 --region=$REGION --format='value(serviceConfig.uri)'
```

---

## Task 7 — Measure all three and write the report

```bash
python phase-1-echo-bot/measure.py \
    --vm       http://<VM_EXTERNAL_IP>:8080 \
    --cloudrun https://echo-bot-<hash>-<region>.run.app \
    --function https://<function-url>
```

This writes `submission/phase1_report.json` (URLs + cold/warm latencies) and prints a
summary. For an honest **cold** number on Cloud Run/Functions, leave them idle ~15 min,
then re-run with `--cold-only` and note the difference.

---

## Task 8 — Commit, push, confirm green CI

Commit your `app.py`, `Dockerfile`, and `submission/phase1_report.json`, then push. The
**`autograde-phase-1`** workflow runs your unit tests and live-curls all three URLs.

---

## Task 9 — Write the comparison report

Produce the 2-page comparison described under **Deliverables** below.

---

## Task 10 — Tear down (after you're graded)

Protect your quota once your grade is in:

```bash
gcloud run services delete echo-bot --region=$REGION --quiet
gcloud functions delete echo --gen2 --region=$REGION --quiet
gcloud compute instances delete echo-vm --zone=$ZONE --quiet
```

---

## Deliverables

1. Your repo with committed `app.py`, `Dockerfile`, and `submission/phase1_report.json`.
2. A **green** `autograde-phase-1` CI run (offline tests + 3 live endpoints).
3. A **2-page comparison report** (`submission/phase1_report.md`) covering, for each of the
   three platforms: image size, measured cold vs warm latency (with your histogram/plot),
   scaling behaviour, cost model, and deployment effort — and *when you would choose each*.

## Grading rubric (100 pts)

| Check | Points | Where |
|---|---:|---|
| `build_echo` correct | 10 | public unit test |
| `extract_message` correct (query + JSON + missing) | 10 | public unit test |
| `/healthz` returns 200 "ok" | 5 | public unit test |
| `GET /echo` echoes | 10 | public unit test |
| `POST /echo` echoes | 5 | public unit test |
| missing message → 400 | 5 | public unit test |
| IaaS VM endpoint echoes (live) | 10 | public (live-curl) |
| Cloud Run endpoint echoes (live) | 10 | public (live-curl) |
| Cloud Function endpoint echoes (live) | 10 | public (live-curl) |
| cold + warm latencies recorded for all three | 10 | public (report) |
| the three URLs are distinct | 5 | **hidden** |
| URLs look like real GCP endpoints (run.app / cloudfunctions / VM IP) | 10 | **hidden** |
| **Total** | **100** | |

The 2-page report is assessed separately by the instructor. Public checks (85 pts) you can
see yourself: run `python -m pytest phase-1-echo-bot/tests -p autograder.points -q` (after
deploying + `measure.py`); while coding just use `tests/test_units.py`.
