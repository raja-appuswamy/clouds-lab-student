# Phase 6 — Tasks & Deliverables

Do everything in **Google Cloud Shell**. Read [README.md](README.md) and [SPEC.md](SPEC.md)
first. Two halves: Tasks 1–6 (identity, boundary, the agent builds and applies, load test,
logs), then Tasks 7–11 (the review, the writeups, teardown, submission).

> **How this task sheet differs from the others.** Phases 0–5 withheld the `gcloud` commands
> because you were learning the primitives. In Phase 6 you are learning something else: to
> **supervise an AI agent that operates your stack** — one that writes the Terraform, runs the
> plan/apply loop, reads errors and retries. So the commands are *its* job,
> and yours is to decide what it may do, watch what it does, catch what it gets wrong, and
> sign off. The stack it builds is graded exactly as before; how you supervised is graded too.
>
> Where a command is for **you** rather than the agent — giving it an identity, running the
> destroy — it is given in full (agent tooling is not in the Google Cloud track). Where the
> agent gets stuck, *you* still know the primitives: that is the point of the five phases
> before this one.

**The agent.** [Gemini CLI](https://github.com/google-gemini/gemini-cli) runs in Cloud Shell,
executes shell commands with per-action approval, and has a free tier on a personal Google
account. Any agent with the same properties is fine — Claude Code, Copilot CLI — the grading
is evidence-based and does not care which. **Time-box it:** if the agent has not produced a
valid plan after 30 minutes on a task, do that step yourself and say so in the supervision log.
The whole phase can be done without an agent; the log then says so and the phase is graded
on its outcomes.

**Install the phase's Python dependencies once**, into the virtualenv you made in Phase 0 —
the autograder parses your Terraform with `python-hcl2` and your manifests with `pyyaml`, and
without them every static test errors out with `ModuleNotFoundError`:

```bash
pip install -r requirements.txt -r phase-6-capstone/requirements.txt
```

Then set these once per shell session:

```bash
export PROJECT=$(gcloud config get-value project)
export REGION=us-central1
export IMAGE=$REGION-docker.pkg.dev/$PROJECT/eurecomgpt/chat:v2      # the Phase-5 image
export AGENT_SA=agent-operator@$PROJECT.iam.gserviceaccount.com
cd phase-6-capstone/terraform && cp -n terraform.tfvars.example terraform.tfvars && cd -
```

Edit `phase-6-capstone/terraform/terraform.tfvars` with your project id, `$IMAGE`, the alert
e-mail, and `impersonate = "<AGENT_SA>"`. It is git-ignored.

---

## Task 1 — Give the agent an identity *(commands given)*

An agent that runs as *you* runs as Owner. Instead it gets its own service account with only
the roles the stack in `SPEC.md` needs, and your Cloud Shell **impersonates** it: your own
login mints short-lived tokens for it; no key file ever exists.

**Objective.** A service account `agent-operator` with these project roles — and no others:

| Role | Why the stack needs it |
|---|---|
| `roles/serviceusage.serviceUsageAdmin` | enable the APIs |
| `roles/iam.serviceAccountAdmin` + `roles/iam.serviceAccountUser` | create the chat SA and let Cloud Run run as it |
| `roles/iam.roleAdmin` | create the custom role |
| `roles/run.admin` | the service and its public binding |
| `roles/bigquery.admin` | datasets, the load job, the sink's dataset binding |
| `roles/monitoring.editor` | channel + alert policy |
| `roles/logging.configWriter` + `roles/logging.admin` | log metric + sink |
| `roles/storage.objectViewer` | read the bucket as a data source |

Deliberately **not** granted: `roles/owner`, `roles/editor`, and
`roles/resourcemanager.projectIamAdmin`. Note that last one — Task 4 comes back to it.

```bash
gcloud services enable cloudresourcemanager.googleapis.com serviceusage.googleapis.com iamcredentials.googleapis.com
gcloud iam service-accounts create agent-operator --display-name="Phase 6 agent operator"
for ROLE in roles/serviceusage.serviceUsageAdmin roles/iam.serviceAccountAdmin roles/iam.serviceAccountUser \
            roles/iam.roleAdmin roles/run.admin roles/bigquery.admin roles/monitoring.editor \
            roles/logging.configWriter roles/logging.admin roles/storage.objectViewer; do
  gcloud projects add-iam-policy-binding $PROJECT --member="serviceAccount:$AGENT_SA" --role="$ROLE" --quiet
done
# let YOU mint tokens for it, then make every gcloud call in this shell act as it
gcloud iam service-accounts add-iam-policy-binding $AGENT_SA \
    --member="user:$(gcloud config get-value account)" --role=roles/iam.serviceAccountTokenCreator
gcloud config set auth/impersonate_service_account $AGENT_SA
gcloud auth print-identity-token >/dev/null && echo "impersonating $AGENT_SA"
```

**Taught in.** Core Services M1 *Identity and Access Management* — service accounts,
impersonation, least privilege. Phase 3 Task 3 and Phase 4 Task 5 were the rehearsals.

**Verified by.** `gcloud projects get-iam-policy $PROJECT --flatten=bindings --filter="bindings.members:agent-operator"`
lists exactly those roles. Terraform picks up the same identity through `impersonate` in
`terraform.tfvars`.

---

## Task 2 — Set the approval boundary

**Objective.** [agent/policy.json](agent/policy.json) says what the agent may run **without
asking**, what needs your **approval**, and what is **forbidden** outright. Read it, decide
whether you agree, edit it if not — then translate it into your agent's own settings
([agent/gemini-settings.json](agent/gemini-settings.json) and
[agent/claude-settings.json](agent/claude-settings.json) are starting points; the schema
varies by tool version, so check your tool's docs). Give the agent its brief:
[agent/GEMINI.md](agent/GEMINI.md) points it at `SPEC.md` and states the rules.

The autograder reads `policy.json`: destroy and delete must be forbidden, `apply` must need
approval, `plan` must be automatic. Beyond that the boundary is yours to argue for in the
supervision log.

```bash
python -m pytest phase-6-capstone/tests/test_units.py -p autograder.points -q -k agent_policy
```

**Taught in.** Lecture 2 (what a container may do is decided outside it) — the same idea,
applied to a process that decides its own next command.

---

## Task 3 — Let it build

**Objective.** The agent completes [terraform/](terraform/) from `SPEC.md` and the provided
scaffolding, and runs `init`, `validate` and `plan` — all inside its auto-allowed set. You
read the plan: around 19 resources to add, nothing to change or destroy, every one of them
recognisable from Phases 4–5 — including the BigQuery *load job* that rebuilds the TF-IDF
table from your Phase-3 Parquet.

Start the agent in the repo root and give it the kickoff prompt in
[agent/PROMPT.md](agent/PROMPT.md) — paste it verbatim, or adapt it and say in the supervision
log what you changed. It asks the agent for more than code: for each resource it must name the
line of `SPEC.md` that requires it, the one attribute that would silently break it and what the
symptom would be, what it costs, and which test the change should turn green — then stop and
wait for you. An agent told only "write the Terraform" produces code you cannot review, and
reviewing it is what this phase grades.

Then **watch**. Every command it proposes, every explanation it gives, every error it reads,
every fix it tries — this is the loop you will describe in the supervision log. Read the
explanations as you would a colleague's: a confident wrong one is the most useful thing that
can happen here, and it fills the log's "one thing the agent got wrong" slot.

Run the offline tests **throughout**, not at the end. They parse the files on disk, need no
cloud resources and change nothing, so they are safe to run at any moment — and they fail from
the start, because five of the seven checks describe Terraform that does not exist yet. Their
assertion messages are the to-do list:

```bash
python -m pytest phase-6-capstone/tests/test_units.py -p autograder.points -q
```

The loop looks like this:

1. The agent edits a `.tf` file.
2. It runs `terraform validate` and the command above — both auto-allowed in your policy —
   and reads what still fails. (Rule 5 of [agent/GEMINI.md](agent/GEMINI.md) requires it to;
   rule 4 caps it at two attempts on the same error before it has to come back to you.)
3. It fixes and re-runs. You watch the diffs, not just the summaries.
4. **You run the tests yourself** before approving anything — the agent reporting green is not
   evidence, your own run is.

You are done with this task when every check in `test_units.py` passes and `terraform plan`
shows resources to add, none to change and none to destroy.

**Taught in.** Terraform badge · Elastic M3 — you can read a plan; now you read one you did not
write.

**Verified by.** The static tests pass; `terraform plan` is clean. If the agent invents a
provider attribute, `terraform validate` will say so — let it read the error before you help.

---

## Task 4 — Apply, under supervision

**Objective.** The stack applied by the agent, with your approval at each state-changing step
— and one privileged operation that the agent cannot perform, which you have to decide what to
do about. That decision, not the apply, is what this task is for.

**Step 1 — tell the agent to apply.** Your policy puts `terraform apply` in `confirm`, so it
stops and asks. Approve it deliberately: before you say yes, know how many resources the plan
adds and which of them cost money. Write the approval row in `phase6_supervision.md` **now**,
while you remember what you were thinking — not at the end of the phase.

**Step 2 — the apply stops partway, with a 403.** Most of the stack comes up, then Terraform
fails on the project IAM bindings for the chat service account:

```
Error: Error applying IAM policy for project "...": googleapi: Error 403: Policy update access denied.
```

This is designed, not broken. Task 1 gave `agent-operator` every role the stack needs *except*
`roles/resourcemanager.projectIamAdmin`, and `google_project_iam_member.chat_roles` /
`chat_custom_role` cannot be created without it. Terraform applies resource by resource, so
everything created before the failure still exists — re-running apply continues from there.

**Step 3 — grant the role, and decide how long it keeps it.** The agent will propose
something, usually "grant me the role". Grant it — but note that you cannot grant a role
*while impersonating* the account that lacks it, so be yourself for that command:

```bash
gcloud config unset auth/impersonate_service_account
gcloud projects add-iam-policy-binding $PROJECT --member="serviceAccount:$AGENT_SA" \
    --role=roles/resourcemanager.projectIamAdmin --quiet
gcloud config set auth/impersonate_service_account $AGENT_SA
```

The agent re-runs apply and the stack completes. **Now the graded decision: does it keep the
role?** With `projectIamAdmin`, `agent-operator` can change anyone's permissions in the
project — including granting itself more. The disciplined answer is to take it back the moment
the apply is done, and to know how long it held it:

```bash
gcloud config unset auth/impersonate_service_account
gcloud projects remove-iam-policy-binding $PROJECT --member="serviceAccount:$AGENT_SA" \
    --role=roles/resourcemanager.projectIamAdmin --quiet
gcloud config set auth/impersonate_service_account $AGENT_SA
```

Leaving it granted is a choice too — cheaper, and it means the next apply just works. If you
leave it, say so and defend it. The supervision log's `iam_403` slot asks what you saw, what
you decided, how long the agent held the role, and what you gave up by deciding that way.

**Step 4 — finish the apply and record it.** Re-run apply until it completes with no errors,
check the service answers, then write the report:

```bash
terraform output -raw chat_url                      # the new service (chat-tf, not Phase 5's chat)
curl -s $(terraform output -raw chat_url)/health    # expect "store": "firestore"
python phase-6-capstone/make_report.py terraform
```

**Taught in.** Core Services M1 — the difference between *can* and *should*.

**Verified by.** `chat_url` answers `/health` with `"store": "firestore"` and `/chat` returns a
reply; the CI live tests hit the same URL.


---

## Task 5 — Load test, and watch it scale

```bash
python phase-6-capstone/loadtest.py --url $CHAT_URL --clients 20 --seconds 120
python phase-6-capstone/make_report.py loadtest
```

(`CHAT_URL` is `terraform output -raw chat_url`; the agent can run this too — it is read-only
against the service.) Twenty clients for two minutes against the cheap endpoints (one `/chat`
in twenty-five). The script records latency percentiles and error rate, then waits and asks
**Cloud Monitoring** for the peak `instance_count` of your service over the window. You want
≥ 2 — with concurrency 5 and twenty clients, Cloud Run has to scale out.

**While it runs**, open the console: *Cloud Run → chat-tf → Metrics* (instance count, request
latency) and *Monitoring → Alerting*.

**Taught in.** Core Services M4 *Resource Monitoring* · Lecture 1 (elasticity) · Lecture 2

**Verified by.** The report: ≥ 500 requests, error rate ≤ 5 %, p50 ≤ p95 ≤ p99, peak instances
≥ 2.

---

## Task 6 — Query your own request logs

**Objective.** The log sink delivered: a `run_googleapis_com_requests` table exists in the
`eurecomgpt_logs` dataset (Terraform output `logs_dataset`), and you have run at least one SQL
query over it — requests per status code, or p99 latency by URL path — and kept the query and
one result line for the post-mortem. Ask the agent for the query if you like; you still have to
read the answer.

**Taught in.** Core Services M2 · Phase 3 Task 11 (BigQuery)

**Verified by.** The post-mortem slot `log_sink_query`. Sink delivery lags a few minutes.

---

## Task 7 — Review another agent's pull request

Now the other side of the job. [review/main.tf](review/main.tf) is a complete Terraform for the
same stack, written by an agent from the same `SPEC.md`. It validates, it would apply, and it
contains **three faults** a careless reviewer would approve: one that **costs money**, one that
**grants more than it should**, one that **fails silently**. Read it against the spec line by
line — do not apply it — and fill in the review:

```bash
cp phase-6-capstone/review_template.md submission/phase6_review.md
```

For each fault: where, what is wrong and what it would have cost or exposed, and the corrected
HCL. Then a verdict: would you approve after the fixes, and which fault would have been hardest
to notice *after* apply?

**Taught in.** Everything from Phases 4–5 and this phase's `SPEC.md`. Your own agent may have
made one of these three mistakes in Task 3; check.

**Verified by.** The public test checks the review is complete; the instructor's checks that
you found the right three.

---

## Task 8 — The supervision log

```bash
cp phase-6-capstone/supervision_template.md submission/phase6_supervision.md
```

You should have been filling this since Task 2. It asks for: which agent and how you ran it;
the identity you gave it and the role you withheld; your boundary and why; **every approval it
requested** (at least four, including at least one you refused); the 403 in Task 4 and what you
decided; one thing the agent got wrong and how you caught it; one thing you did by hand; and
where, now, you would draw the line between unsupervised, approved, and never.

**Verified by.** The public test checks every slot is filled and the approvals table has ≥ 4
rows with a refusal; the instructor reads it.

---

## Task 9 — The post-mortem

```bash
cp phase-6-capstone/postmortem_template.md submission/phase6_postmortem.md
```

Fill every slot after Task 10 (section 1 needs the destroy count). It asks what Terraform
managed and did not; what broke; why the service scaled the way it did and what your alert
watches; the SQL over your own logs; and what breaks first at 1,000× the load. The agent may
draft; you are accountable for every number.

---

## Task 10 — Tear it all down, yourself *(commands given)*

**Objective.** The stack destroyed — by **you**. This is the one thing in the phase the agent
is forbidden from (Task 2), and the reason is the point: destruction is the action whose blast
radius you cannot take back, so it stays with the human. Your data — bucket, Firestore, images
— remains.

```bash
cd phase-6-capstone/terraform && terraform destroy && cd -
python phase-6-capstone/make_report.py destroyed
gcloud config unset auth/impersonate_service_account       # you are yourself again
```

If you granted `agent-operator` anything beyond Task 1's list along the way, revoke it now, and
say so in the log.

**Taught in.** Terraform badge · Lecture 1 (elasticity includes elasticity to zero)

**Verified by.** The report records an empty state and a dead URL. The CI live tests skip once
this is recorded.

---

## Task 11 — Commit and push

Commit `phase-6-capstone/terraform/*.tf`, `phase-6-capstone/agent/policy.json`,
`submission/phase6_report.json`, `submission/phase6_loadtest.json`,
`submission/phase6_review.md`, `submission/phase6_supervision.md` and
`submission/phase6_postmortem.md`, then push. **Push once before Task 10 too** — that is the
run in which the live tests see your service.

## Deliverables

1. Completed `terraform/*.tf` (by the agent, reviewed by you) and `agent/policy.json` (by you).
2. `submission/phase6_report.json` with all four stages, plus `submission/phase6_loadtest.json`.
3. `submission/phase6_review.md` — the three faults in PR #12.
4. `submission/phase6_supervision.md` — the log.
5. `submission/phase6_postmortem.md`.
6. A **green** `autograde-phase-6` CI run — one *before* the destroy (live tests) and the final
   one after it.

## How your work is checked

Your grade comes from the autograder, plus the review, the supervision log and the post-mortem,
which the instructor assesses. Run the public suite yourself before you push (after
each `make_report.py` stage and once the three writeups are filled):

```bash
python -m pytest phase-6-capstone/tests -p autograder.points -q
```

While the agent is editing Terraform, `phase-6-capstone/tests/test_units.py`
alone is enough — it needs no cloud resources. The instructor also runs checks that are not in
your repo, so a green public run is necessary but not sufficient.

