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

**Taught in.** Fundamentals M2 *Resources and Access in the Cloud*

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

**Verified by.** Run command below. 
```bash
gcloud artifacts docker images list $REGION-docker.pkg.dev/$PROJECT/eurecomgpt
```

Tasks 5–6 pull this image; the live-curl tests fail if it is missing.

Note the image size once it is pushed — you need it for the comparison report. The Artifact
Registry console shows it, and so does the CLI.


---

## Task 4 — Build a network to put it on

**Objective.** A **custom-mode VPC** named `echo-net` with one subnet `echo-subnet` in
`$REGION`, plus **two** ingress firewall rules for instances carrying the network tag
`echo-http`: TCP **8080** for the app, and TCP **22** so you can SSH in at all.

Do **not** use the `default` network. Every other phase in this lab hides networking behind
managed services; this is the one place you build it yourself.

> **The trap:** the `default` network ships with pre-populated rules including
> `default-allow-ssh`. A **custom-mode VPC has none** — it starts with only two implied
> rules, allow-all-egress and deny-all-ingress. If you create only the 8080 rule the VM
> comes up fine and `gcloud compute ssh` then hangs and times out. That is the firewall,
> not the VM.

**Taught in.** Foundation M2 *Virtual Networks*

**Verified by.** Not autograded yet — record the network and subnet names in your comparison
report, and be ready to explain in the report why the firewall rule needs the tag.


---

## Task 5 — IaaS path: run the container on a VM in your subnet

**Objective.** An `e2-micro` VM named `echo-vm` in `echo-subnet`, tagged `echo-http`, running
your container and answering `http://<EXTERNAL_IP>:8080/echo?msg=hi`. You need to work out five things: create the instance on your own subnet with the right tag
and a Debian image; give its service account permission to pull from Artifact Registry; SSH
in; install and authenticate Docker on the VM; run your container detached on port 8080.
Then find the VM's external IP.

**Taught in.** Fundamentals M3 *Virtual Machines and Networks* · Foundation M3 *Virtual
Machines* · Lecture 1

**Verified by.** Test your service by browsing to `http://<EXTERNAL_IP>:8080/echo?msg=hello`.
You should see the response to your GET request. The address bar can only issue GETs, so test
the POST path from Cloud Shell — that also proves your firewall rule works, not just the
container:

```bash
curl -s -X POST http://<EXTERNAL_IP>:8080/echo \
     -H 'Content-Type: application/json' \
     -d '{"message":"hello"}'
```

Expect `{"echo":"hello","length":5}`. Two things to watch: the JSON key is **`message`**, not
`msg` (that is the query-string name), and the `Content-Type` header is required — get either
wrong and you get a 400 instead of an echo.

If the POST fails but the browser GET worked, run `curl localhost:8080/echo?msg=hi` from inside
the VM: that separates a broken container from a blocked network.

Live-curl tests (a GET and a JSON POST) against the VM URL you record will also be run by
`phase1_report.json`.


---

## Task 6 — Container PaaS path: deploy the same image to Cloud Run

**Objective.** A public Cloud Run service named `echo-bot` in `$REGION` running the *same*
image, scaling to zero, capped at 3 instances, listening on port 8080.

**Taught in.** Fundamentals M6 *Applications in the Cloud* · Lecture 2

**Verified by.** Live-curl tests against the `*.run.app` URL in your report — a GET and
a JSON POST, exactly as in Task 5.

Scaling to zero matters: it is what makes the cold-start measurement in Task 8 meaningful,
and what keeps this phase free.


---

## Task 7 — Serverless path: deploy `main.py` as a Cloud Function (gen 2)

**Objective.** A public gen-2 Cloud Function named `echo` in `$REGION`, Python 3.11, built
from this phase's source with `echo` as the entry point, HTTP-triggered.

**Taught in.** Fundamentals M6 *Applications in the Cloud* · *Set Up an App Dev Environment*
badge · Lecture 2

**Verified by.** Live-curl tests against the function URL in your report — a GET and a
JSON POST, exactly as in Task 5.

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
summary.

**Getting an honest cold number — order matters.** `measure.py` times its *first* request to
each URL as the cold sample; it does nothing to force the instance to be cold. Cloud Run and
your Function only scale to zero after roughly 15 minutes idle, so:

1. **Finish all your correctness checks first** — the GET and POST tests from Tasks 5–7.
2. **Then leave all three endpoints completely alone for ~15 minutes.** Any request restarts
   the idle timer: a stray `curl`, a browser tab you left open on the echo URL, anything.
3. **Then run the command above once, with all three URLs.** Each target is probed in turn
   with its cold request before its warm burst, and the whole run takes under a minute — so
   the later targets are still scaled to zero when their turn comes. One run gives you honest
   cold *and* warm numbers for all three.

Two things to avoid:

- **Do not pass `--cold-only`.** It records no warm samples, and because `measure.py`
  rewrites the whole report each time, a `--cold-only` run replaces your good data with a
  report the grader rejects.
- **Do not re-run with a subset of the URLs.** The report is overwritten wholesale, so
  measuring just one platform deletes the other two.

If a "cold" number comes back suspiciously close to your warm median, the instance had not
scaled down yet — wait longer and run again. The VM has no meaningful cold start at all,
since its container never stops; say so in your report.

---

## Task 9 — Commit, push, confirm green CI

Commit your `app.py`, `Dockerfile`, and `submission/phase1_report.json`, then push. The
**`autograde-phase-1`** workflow runs your unit tests and live-curls all three URLs.

---

## Task 10 — Write the comparison report

Don't start from a blank page — a template with every question already laid out is provided.
Copy it and fill it in:

```bash
cp phase-1-echo-bot/report_template.md submission/phase1_report.md
```

Each answer sits between a pair of `<!--answer:...-->` markers. Replace the `TODO` line with
your answer and **leave the markers alone** — they are how the report is read. Anything you
write outside them is ignored, so add extra prose, tables or images freely.

Your latency figures must **match `submission/phase1_report.json`**. Copy them across rather
than retyping from memory; they are checked against what `measure.py` actually recorded.

Check your own report before you submit — it reports every slot that is missing, unfilled,
too short, or inconsistent with your measurements:

```bash
python phase-1-echo-bot/report_md.py submission/phase1_report.md submission/phase1_report.json
```

---

## Task 11 — Tear down as soon as your CI is green

**Do this the same day you finish — not at the end of the semester.**

The live-curl checks run inside *your* GitHub Actions, so your three endpoints only need to be
up at the moment that workflow runs. Once `autograde-phase-1` has gone green, that run is your
evidence: the remaining hidden checks read only your committed `phase1_report.json`, so nothing
has to stay deployed.

> **Finish your pushes first.** Any later push re-runs the workflow, and if you have already
> torn down, the live-curl tests fail and your green run is replaced by a red one. Commit
> everything — code, report, comparison writeup — confirm green, *then* delete.

**Why the hurry:** the VM is the one resource here that costs real money. The Always Free tier
covers the `e2-micro` instance itself and its boot disk, but **an external IPv4 address is
billed while it exists** — on the order of a few euros a month. Cloud Run and the Function
scale to zero and cost nothing idle, so the VM is the urgent deletion; delete the rest anyway
to keep the project clean.

**Commands given in full — never guess at teardown.** Delete the instance before the network,
or the network delete will fail.

```bash
gcloud run services delete echo-bot --region=$REGION --quiet
gcloud functions delete echo --gen2 --region=$REGION --quiet
gcloud compute instances delete echo-vm --zone=$ZONE --quiet
gcloud compute firewall-rules delete allow-echo-8080 --quiet
gcloud compute firewall-rules delete allow-echo-ssh --quiet
gcloud compute networks subnets delete echo-subnet --region=$REGION --quiet
gcloud compute networks delete echo-net --quiet
```

Confirm nothing survived:

```bash
gcloud compute instances list
gcloud run services list --region=$REGION
```

### Check your billing once

Your Phase-0 budget alert emails you only *after* the first cent is spent, so look at the
actual numbers once here rather than trusting it. In the Console go to
**Billing → Reports**, filter to this project, and group by **SKU**.

Everything in this phase should read €0 except, possibly, an external IP line for however long
your VM existed. If you see anything else non-zero — a running instance you forgot, a service
with `min-instances` above 0 — track it down now. Costs in this lab come from resources left
running, never from the work itself, and every later phase assumes you still have your free
trial credit intact.

---

## Deliverables

1. Your repo with committed `app.py`, `Dockerfile`, and `submission/phase1_report.json`.
2. A **green** `autograde-phase-1` CI run (offline tests + 3 live endpoints).
3. A **2-page comparison report** at `submission/phase1_report.md`, filled in from
   [report_template.md](report_template.md) (Task 10), covering, for each of the
   three platforms: image size, measured cold vs warm latency (with your histogram/plot),
   scaling behaviour and deployment effort. It must also answer:

   - **Why do two of your three numbers look alike?** Your Cloud Run and Cloud Function
     timings are likely to sit much closer to each other than either does to the VM. With both
     deployed, run:

     ```bash
     gcloud run services list
     ```

     Record what it shows. Then explain what that output tells you about how your Function is
     actually being run, why its cold start resembles Cloud Run's so closely, and what — if
     anything — genuinely differs between the two deployment paths.

## How your work is checked

Your grade comes from the autograder, plus any writeup listed under **Deliverables**, which
the instructor assesses separately. Run the public suite yourself before you push (after deploying all three targets and running `measure.py`):

```bash
python -m pytest phase-1-echo-bot/tests -p autograder.points -q
```

While coding, `phase-1-echo-bot/tests/test_units.py` alone is faster — it needs no cloud resources.
The instructor also runs checks that are not in your repo, so a green public run is
necessary but not sufficient.

