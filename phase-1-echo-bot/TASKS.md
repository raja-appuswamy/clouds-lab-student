# Phase 1 — Tasks & Deliverables

Do everything in **Google Cloud Shell**. Read [README.md](README.md) first. All commands
assume you are at the **repo root** unless noted.

> **How these task sheets work.** Each task states an *objective*, names the module and
> lecture where you were taught the commands, and says what the autograder checks.
> **The commands are not given** — you have already performed these operations in the Google
> Cloud modules listed under each task, and recalling them is the point of the exercise.
>
> **When you are stuck**, in this order: revisit the module named under the task; then
> `gcloud <group> --help` (e.g. `gcloud compute instances --help`); then the CLI reference at
> <https://cloud.google.com/sdk/gcloud/reference>. Worked commands are released after the
> submission deadline.

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

**Objective.** Artifact Registry, Cloud Run, Cloud Functions, Cloud Build and Compute Engine
are all enabled on your project.

**Taught in.** Fundamentals M2 *Resources and Access in the Cloud* · Lecture 1

**Verified by.** Nothing directly — but every later task fails without this.


---

## Task 2 — Implement the code and run the unit tests

Fill the TODOs in [app.py](app.py) (`build_echo`, `extract_message`) and the two TODO
lines in the [Dockerfile](Dockerfile).

> **New to Flask?** Skim the official quickstart first — it covers exactly what you need
> here (defining routes, reading query params via `request.args`, reading a JSON body, and
> returning JSON with `jsonify`): <https://flask.palletsprojects.com/en/stable/quickstart/>.
> The routes in `app.py` are already written for you; you only implement the two small
> pure functions they call.

This task is code, not cloud operations — the commands below are given in full.

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

**Objective.** A Docker repository named `eurecomgpt` in `$REGION`, containing your image
built from this phase's `Dockerfile` and tagged `$IMAGE`.

**Taught in.** Fundamentals M5 *Containers in the Cloud* · Lecture 2

**Verified by.** Tasks 5–6 pull this image; the live-curl tests fail if it is missing.

Note the image size once it is pushed — you need it for the comparison report. The Artifact
Registry console shows it, and so does the CLI.


---

## Task 4 — Build a network to put it on

**Objective.** A **custom-mode VPC** named `echo-net` with one subnet `echo-subnet` in
`$REGION`, plus a firewall rule that allows inbound TCP 8080 from anywhere to instances
carrying the network tag `echo-http`.

Do **not** use the `default` network. Every other phase in this lab hides networking behind
managed services; this is the one place you build it yourself.

**Taught in.** Foundation M2 *Virtual Networks*

**Verified by.** Not autograded yet — record the network and subnet names in your comparison
report, and be ready to explain in the report why the firewall rule needs the tag.


---

## Task 5 — IaaS path: run the container on a VM in your subnet

**Objective.** An `e2-micro` VM named `echo-vm` in `echo-subnet`, tagged `echo-http`, running
your container and answering `http://<EXTERNAL_IP>:8080/echo?msg=hi`.

**Taught in.** Fundamentals M3 *Virtual Machines and Networks* · Foundation M3 *Virtual
Machines* · Lecture 1

**Verified by.** A live-curl test against the VM URL you record in `phase1_report.json`.

You need to work out five things: create the instance on your own subnet with the right tag
and a Debian image; give its service account permission to pull from Artifact Registry; SSH
in; install and authenticate Docker on the VM; run your container detached on port 8080.
Then find the VM's external IP.


---

## Task 6 — Container PaaS path: deploy the same image to Cloud Run

**Objective.** A public Cloud Run service named `echo-bot` in `$REGION` running the *same*
image, scaling to zero, capped at 3 instances, listening on port 8080.

**Taught in.** Fundamentals M6 *Applications in the Cloud* · Lecture 2

**Verified by.** A live-curl test against the `*.run.app` URL in your report.

Scaling to zero matters: it is what makes the cold-start measurement in Task 8 meaningful,
and what keeps this phase free.


---

## Task 7 — Serverless path: deploy `main.py` as a Cloud Function (gen 2)

**Objective.** A public gen-2 Cloud Function named `echo` in `$REGION`, Python 3.11, built
from this phase's source with `echo` as the entry point, HTTP-triggered.

**Taught in.** Fundamentals M6 *Applications in the Cloud* · *Set Up an App Dev Environment*
badge · Lecture 2

**Verified by.** A live-curl test against the function URL in your report.

Note that this path deploys **source**, not your image — that difference is worth a paragraph
in the comparison report.


---

## Task 8 — Measure all three and write the report

The measurement harness is provided — commands given in full.

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

## Task 9 — Commit, push, confirm green CI

Commit your `app.py`, `Dockerfile`, and `submission/phase1_report.json`, then push. The
**`autograde-phase-1`** workflow runs your unit tests and live-curls all three URLs.

---

## Task 10 — Write the comparison report

Produce the 2-page comparison described under **Deliverables** below.

---

## Task 11 — Tear down (after you're graded)

Protect your quota once your grade is in. **Commands given in full — never guess at
teardown.** Delete the instance before the network, or the network delete will fail.

```bash
gcloud run services delete echo-bot --region=$REGION --quiet
gcloud functions delete echo --gen2 --region=$REGION --quiet
gcloud compute instances delete echo-vm --zone=$ZONE --quiet
gcloud compute firewall-rules delete allow-echo-8080 --quiet
gcloud compute networks subnets delete echo-subnet --region=$REGION --quiet
gcloud compute networks delete echo-net --quiet
```

---

## Deliverables

1. Your repo with committed `app.py`, `Dockerfile`, and `submission/phase1_report.json`.
2. A **green** `autograde-phase-1` CI run (offline tests + 3 live endpoints).
3. A **2-page comparison report** (`submission/phase1_report.md`) covering, for each of the
   three platforms: image size, measured cold vs warm latency (with your histogram/plot),
   scaling behaviour, cost model, and deployment effort — and *when you would choose each*.
   Include your VPC and subnet names, and explain why the firewall rule targets a network tag
   rather than an IP.

## How your work is checked

Your grade comes from the autograder, plus any writeup listed under **Deliverables**, which
the instructor assesses separately. Run the public suite yourself before you push (after deploying all three targets and running `measure.py`):

```bash
python -m pytest phase-1-echo-bot/tests -p autograder.points -q
```

While coding, `phase-1-echo-bot/tests/test_units.py` alone is faster — it needs no cloud resources.
The instructor also runs checks that are not in your repo, so a green public run is
necessary but not sufficient.

