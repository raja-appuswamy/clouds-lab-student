# Phase 7 — Tasks & Deliverables

Do everything in **Google Cloud Shell**. Read [README.md](README.md) first. Two weeks: Tasks 1–6
(Terraform, load test, monitoring) in the first, Tasks 7–12 (Kubernetes, post-mortem, teardown,
demo) in the second.

> **How these task sheets work.** Each cloud task states an *objective*, names the module and
> lecture where you were taught the commands, and says what the autograder checks.
> **The `gcloud`, `terraform` and `kubectl` commands are not given** — you have already performed
> these operations in the Google Cloud modules and skill badges listed under each task. Code,
> tests, manifests and provided scripts are given in full; only cloud operations are withheld.
> Two exceptions, marked *(command given)*: installing `kind`, which the track does not cover,
> and the load tester, which is a provided script.
>
> **When you are stuck**, in this order: revisit the module named under the task; then
> `terraform -help` / `kubectl --help` / `gcloud <group> --help`; then the references. Worked
> commands are released after the submission deadline.

Set these once per shell session:

```bash
export PROJECT=$(gcloud config get-value project)
export REGION=us-central1
export IMAGE=$REGION-docker.pkg.dev/$PROJECT/eurecomgpt/chat:v2      # the Phase-5 image
cd phase-7-capstone/terraform && cp -n terraform.tfvars.example terraform.tfvars && cd -
```

Edit `phase-7-capstone/terraform/terraform.tfvars` with your project id, `$IMAGE`, and the
e-mail address alerts should go to. It is git-ignored — it holds your identifiers, not code.

---

## Task 1 — Let Terraform manage the project

**Objective.** Terraform can talk to your project: the **Cloud Resource Manager** and **Service
Usage** APIs are enabled (Terraform uses them to enable everything else), and `terraform` has
credentials. In Cloud Shell your own login serves as Application Default Credentials.

**Taught in.** Fundamentals M2 *Resources and Access in the Cloud* · Elastic M3 *Infrastructure
Automation* · *Build Infrastructure with Terraform* badge

**Verified by.** Task 3's `plan` succeeds. A `403` mentioning `cloudresourcemanager` or
`serviceusage` means this task is not done.


---

## Task 2 — Fill the Terraform TODOs and run the offline tests

Read all of [terraform/](terraform/) — it is short and every block is commented — then fill the
four TODO blocks:

- [main.tf](terraform/main.tf) — the custom role's `permissions`, and the Cloud Run service's
  `scaling`, `max_instance_request_concurrency`, container `image`, `resources` and `env`. You
  deployed exactly this by hand in Phases 4–5; now it is code.
- [monitoring.tf](terraform/monitoring.tf) — the alert condition (which metric, which filter,
  what threshold) and the log sink's `filter` + `unique_writer_identity`.

Note what is *not* managed and why (the file header explains): the bucket, the Firestore
database, the image. The offline tests parse your files — no cloud needed:

```bash
pip install -r requirements.txt -r phase-7-capstone/requirements.txt
python -m pytest phase-7-capstone/tests/test_units.py -p autograder.points -q
```

**Taught in.** Elastic M3 · Terraform badge · Core Services M4 *Resource Monitoring* · Phases 4–5

---

## Task 3 — Initialise, validate, plan

**Objective.** In `phase-7-capstone/terraform/`: providers downloaded, configuration valid, and
a plan that proposes to **add** the whole stack (around 19 resources) and change or destroy
nothing.

**Taught in.** Terraform badge — the init / validate / plan / apply cycle.

**Verified by.** Read the plan. You should recognise every resource in it from Phases 4–5 —
including the BigQuery *load job* that rebuilds the TF-IDF table from your Phase-3 Parquet. If
the plan wants to destroy something, stop: you are pointed at the wrong project.


---

## Task 4 — Apply: the stack, from zero

**Objective.** The plan applied. Terraform prints the outputs; `chat_url` answers `/health`
with `"store": "firestore"` and `/chat` returns a reply — a service you did not create by hand,
running your Phase-5 image, reading a table this apply just loaded.

**Taught in.** Terraform badge

**Verified by.** Record it, then curl it:

```bash
python phase-7-capstone/make_report.py terraform
```

The stage reads the Terraform state (`terraform show -json`), lists what was created by type,
and live-checks the URL. Then the CI live tests hit the same URL.

Expect the first apply to take a few minutes (the load job, the service revision) and expect
**something to go wrong** at least once — an API not yet enabled, a role the sink needs, an
ordering problem. That is normal Terraform life and the post-mortem has a question for it. Read
the error, fix, apply again: apply is idempotent.


---

## Task 5 — Load test, and watch it scale *(command given)*

```bash
python phase-7-capstone/loadtest.py --url $CHAT_URL --clients 20 --seconds 120
python phase-7-capstone/make_report.py loadtest
```

Twenty clients for two minutes against the cheap endpoints (one `/chat` in twenty-five). The
script records latency percentiles and error rate, then waits and asks **Cloud Monitoring** for
the peak `instance_count` of your service over the window. You want ≥ 2 — with concurrency 5
and twenty clients, Cloud Run has to scale out.

**While it runs**, open the console: *Cloud Run → chat-tf → Metrics* (instance count, request
latency) and *Monitoring → Alerting*. If you see a 5xx burst, your alert should go to
*Incidents* and an e-mail should arrive.

**Taught in.** Core Services M4 *Resource Monitoring* · Lecture 1 (elasticity) · Lecture 2

**Verified by.** The report: ≥ 500 requests, error rate ≤ 5 %, p50 ≤ p95 ≤ p99, peak instances
≥ 2.

---

## Task 6 — Query your own request logs

**Objective.** The log sink delivered: a table for `run.googleapis.com/requests` exists in the
`eurecomgpt_logs` dataset (Terraform output `logs_dataset`), and you have run at least one SQL
query over it — requests per status code, or p99 latency by URL path — and kept the query and
one result line for the post-mortem.

**Taught in.** Core Services M2 · Phase 3 Task 11 (BigQuery)

**Verified by.** The post-mortem slot `log_sink_query`. Sink delivery lags a few minutes; the
load test gives it plenty to deliver.


---

## Task 7 — A Kubernetes cluster in Cloud Shell *(install command given)*

Turn on Cloud Shell **Boost mode** first (the ⋮ menu → *Boost Cloud Shell*): it gives the VM
4 GB, enough for a control plane and two pods.

```bash
curl -Lo ./kind https://kind.sigs.k8s.io/dl/latest/kind-linux-amd64 && chmod +x ./kind && sudo mv ./kind /usr/local/bin/kind
kind create cluster --config phase-7-capstone/k8s/kind-config.yaml
```

**Objective.** `kubectl` talks to a one-node cluster named `eurecomgpt`; `kubectl get nodes`
shows it `Ready`. Read [kind-config.yaml](k8s/kind-config.yaml) — the port mapping is what will
let you reach the Service from Cloud Shell.

**Taught in.** GKE M2 *Containers and Kubernetes* · GKE M3 *Kubernetes Architecture*

---

## Task 8 — Get your image into the cluster

**Objective.** Your Phase-5 chat image (`$IMAGE`) present in the kind node's image store. The
node cannot pull from Artifact Registry (it has no Google credentials), so the route is: pull the
image into Cloud Shell's Docker with your own credentials, then hand it to kind:

```bash
kind load docker-image $IMAGE --name eurecomgpt      # (given — kind is not in the track)
```

**Taught in.** Fundamentals M5 *Containers in the Cloud* · Phase 1 Task 3 (registry auth + pull)

**Verified by.** `kind load` prints the image name; `docker exec eurecomgpt-control-plane
crictl images` lists it.


---

## Task 9 — Deploy, expose, roll out

Fill the TODOs in [k8s/deployment.yaml](k8s/deployment.yaml) (`replicas`, `readinessProbe`,
`resources`) and replace the two placeholders (`IMAGE_PLACEHOLDER`, `PROJECT_PLACEHOLDER`).
[k8s/service.yaml](k8s/service.yaml) is complete.

**Objective.** The Deployment and Service applied; both pods `Ready`; `curl
localhost:30080/health` answers — and, called a few times, shows **two different `instance`
ids**: the Service is balancing across your pods. Then perform a **rolling update** (change any
environment variable on the Deployment) and watch it: old pods drain as new ones become ready,
and the Deployment's revision becomes 2.

**Taught in.** GKE M4 *Kubernetes Operations* — `apply`, `get`, `rollout`, `set env`

**Verified by.**

```bash
python phase-7-capstone/make_report.py k8s
```

reads the Deployment (replicas, readiness, revision, image), the Service, and probes the
Service twenty times counting distinct pods. You want 2/2 ready, revision ≥ 2, ≥ 2 distinct.

Try `curl -X POST localhost:30080/chat …` too. It fails — and the post-mortem asks you why.


---

## Task 10 — The post-mortem

```bash
cp phase-7-capstone/postmortem_template.md submission/phase7_postmortem.md
```

Fill every slot — leave the `<!--answer:...-->` markers in place. Section 1 copies numbers from
`phase7_report.json` (fill it after Task 11 so the destroy count is there); the rest asks for:
what Terraform did and did not manage; what broke and how you fixed it; why the service scaled
the way it did and what your alert watches; the SQL you ran on your own logs; what Kubernetes
made you declare that Cloud Run decided for you, and why `/chat` failed in kind; a **costed**
GKE Autopilot vs Cloud Run comparison at 1× and 1,000× your load; and what breaks first at
1,000×. Pricing pages: <https://cloud.google.com/run/pricing>,
<https://cloud.google.com/kubernetes-engine/pricing>.

Every slot is read and checked when your work is graded; the prose is what you present from.


---

## Task 11 — Tear it all down, and prove it

**Objective.** The Terraform stack destroyed — every resource in the state gone, `chat_url`
unreachable — and the kind cluster deleted. Your bucket, Firestore data and images remain: the
stack was infrastructure; those are data.

**Taught in.** Terraform badge · GKE M4

**Verified by.**

```bash
python phase-7-capstone/make_report.py destroyed
```

records the empty state and the dead URL. The CI live tests skip themselves once this is
recorded; the report test for the destroy needs it.


---

## Task 12 — Commit, push, demo

Commit `phase-7-capstone/terraform/*.tf`, `phase-7-capstone/k8s/deployment.yaml`,
`submission/phase7_report.json`, `submission/phase7_loadtest.json` and
`submission/phase7_postmortem.md`, then push. **Push once before Task 11 too** — that is the run
in which the live tests see your service; after the destroy they skip.

**Demo day (15 minutes per group).** Suggested shape: the project map from your `README.md` (1
min) · `terraform apply` from zero, live, while you talk through the plan (4 min, start it
first) · the chat UI against the fresh URL (1 min) · the load test's instance-count graph and
your alert (3 min) · the kind rollout and the two instance ids (2 min) · your 1,000× answer (2
min) · questions (2 min). Then `terraform destroy` on stage.

## Deliverables

1. Filled `terraform/*.tf` and `k8s/deployment.yaml`.
2. `submission/phase7_report.json` with all four stages, plus `submission/phase7_loadtest.json`.
3. `submission/phase7_postmortem.md` — the filled template.
4. A **green** `autograde-phase-7` CI run — one *before* the destroy (live tests) and the final
   one after it (destroy recorded).
5. The 15-minute demo.

## How your work is checked

Your grade comes from the autograder, plus the post-mortem and the demo, which the instructor
assesses. Run the public suite yourself before you push (after each `make_report.py` stage):

```bash
python -m pytest phase-7-capstone/tests -p autograder.points -q
```

While editing the Terraform and manifests, `phase-7-capstone/tests/test_units.py` alone is
enough — it needs no cloud resources. The instructor also runs checks that are not in your repo,
so a green public run is necessary but not sufficient.

