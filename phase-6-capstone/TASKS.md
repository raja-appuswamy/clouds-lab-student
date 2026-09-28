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

## What you hand in — open these files *before* Task 1

Three of this phase's deliverables are writeups, and two of them record things that **cannot be
reconstructed afterwards**: which approvals you granted, what you were thinking when you granted
them, and what the agent said before it corrected itself. A transcript will not save you — agents
are verbose and your own reasoning was never in it. So copy the templates now and write as you
go:

```bash
mkdir -p submission
cp phase-6-capstone/supervision_template.md submission/phase6_supervision.md
cp phase-6-capstone/postmortem_template.md  submission/phase6_postmortem.md
cp phase-6-capstone/review_template.md      submission/phase6_review.md
```

Each task below ends with a **Record now** line naming exactly what to add. This is the map:

| Task | Goes into | Which answers |
|---|---|---|
| 1 | supervision | `agent_tool`, `agent_identity` |
| 2 | supervision | `boundary_rationale` |
| 3 | supervision | `approvals` rows, `claim_checked` |
| 4 | supervision + post-mortem | `approvals`, `refusal`, `iam_403`, `by_hand` · `what_broke` |
| 5 | post-mortem | the load-test numbers, `elasticity_explanation` |
| 6 | post-mortem | `log_sink_query` |
| 7 | review | all ten slots |
| 8 | supervision | `trust_boundary`, and anything still `TODO` |
| 9 | post-mortem | `iac_scope`, `scale_1000x` |
| 10 | post-mortem | `tf_remaining` (the destroy count) |

The approvals table is the one to be disciplined about: **write the row when you approve, not
at the end of the day.** Four rows minimum, one of them a refusal, and "I approved everything"
is both a bad log and a bad grade.

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

**Record now.** In `phase6_supervision.md`: `agent_tool` (which agent, which version, how you
ran it) and `agent_identity` (the service account, the roles you gave it, and the one you
deliberately withheld).

**Verified by.** `gcloud projects get-iam-policy $PROJECT --flatten=bindings --filter="bindings.members:agent-operator"`
lists exactly those roles. Terraform picks up the same identity through `impersonate` in
`terraform.tfvars`.

---

## Task 2 — Set the approval boundary

**Objective.** A repaired `agent/policy.json` — three lists saying what the agent may run
**without asking**, what needs your **approval**, and what is **forbidden** outright.

You do not write it from scratch. [agent/policy.draft.json](agent/policy.draft.json) is what
the agent proposed when asked to propose its own boundary, and like most such proposals it is
tilted towards its own convenience. **It contains four faults.** Copy it and fix them:

```bash
cp phase-6-capstone/agent/policy.draft.json phase-6-capstone/agent/policy.json
```

Three criteria decide where a command belongs, and they are the whole lesson:

| List | Criterion | Why |
|---|---|---|
| `auto` | reads state, changes nothing | interrupting you for a `plan` wastes both of you |
| `confirm` | changes cloud state, reversibly | you should know before your project changes |
| `forbidden` | you cannot take it back, or it widens the agent's own power | an approval prompt is not a safeguard when the answer is always yes at 2 a.m. |

Read the draft's `_agent_note` before you edit: it argues for itself, and one of its arguments
is wrong in a way worth naming in the supervision log. Two of the four faults are obvious once
you apply the criteria; two are the kind a tired reviewer waves through.

Then translate your repaired boundary into your agent's own settings
([agent/gemini-settings.json](agent/gemini-settings.json) and
[agent/claude-settings.json](agent/claude-settings.json) are starting points; the schema varies
by tool version, so check your tool's docs) — `policy.json` stays as the record of what you
decided. Give the agent its brief: [agent/GEMINI.md](agent/GEMINI.md) points it at `SPEC.md`
and states the rules.

The autograder reads `policy.json` and fails on every unrepaired fault, so this test is your
check:

```bash
python -m pytest phase-6-capstone/tests/test_units.py -p autograder.points -q -k agent_policy
```

Beyond the four faults the boundary is yours: where `curl` against your own service sits,
whether the agent may run the test suite unattended, what else you add to `forbidden`. The
supervision log asks you to justify one line you changed and one you left alone.

**Record now.** In `phase6_supervision.md`: `boundary_rationale` — the faults you found in the
draft and why each mattered, plus one line you changed beyond them and one you left alone.

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
can happen here, and the log has a slot for it — but the slot asks, more generally, for one
claim of the agent's that you checked yourself and what the check showed.

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

**Record now.** In `phase6_supervision.md`: a row in the `approvals` table for anything you
approved during this task, and `claim_checked` — one claim the agent made, how you verified it
yourself, what you found. Write it while the diff is still on your screen.

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

**Record now.** In `phase6_supervision.md`: the `approvals` row for the apply, `iam_403` (what
you saw, what you decided, how long the agent held the role), `by_hand` if you did any of it
yourself, and — if you refused something the agent asked for — `refusal`. In
`phase6_postmortem.md`: `what_broke`, while the error text is still in your scrollback.

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

**Record now.** In `phase6_postmortem.md`: the section-1 numbers, copied from
`submission/phase6_loadtest.json` rather than retyped, and `elasticity_explanation`.

**Taught in.** Core Services M4 *Resource Monitoring* · Lecture 1 (elasticity) · Lecture 2

**Verified by.** The report: ≥ 500 requests, error rate ≤ 5 %, p50 ≤ p95 ≤ p99, peak instances
≥ 2.

---

## Task 6 — Query your own request logs

**Objective.** One SQL query of your own, run against the request logs your stack exported to
BigQuery, with the query and one line of its result kept for the post-mortem.

**Where those logs came from.** The log sink Terraform created
(`google_logging_project_sink.requests_to_bq`) copies every Cloud Run *request* log line for
your service into the `eurecomgpt_logs` dataset. Your load test in Task 5 generated a few
thousand of them. Nothing else sends them there and no one queries them for you — this task is
where you look at your own service's traffic as data.

1. **Find the table.** Delivery lags a few minutes after the load test, so if the dataset looks
   empty, wait and list again.

   ```bash
   bq ls $PROJECT:eurecomgpt_logs
   ```

   You are looking for `run_googleapis_com_requests`. Note the **colon** between project and
   dataset: that is `bq`'s syntax. The Terraform output `logs_dataset` uses a dot
   (`project.dataset`) because that is the form SQL wants inside backticks — pass it to `bq ls`
   and you get `Namespace project.project.dataset ... denied (or it may not exist)`, which is a
   confusing way of saying "no such dataset".

2. **Read its schema before you write SQL.** It is log JSON flattened into columns, not a table
   you designed, and the useful fields are nested under `httpRequest`:

   ```bash
   bq show --schema --format=prettyjson $PROJECT:eurecomgpt_logs.run_googleapis_com_requests
   ```

   Note the types: `httpRequest.status` is an integer, but `httpRequest.latency` arrives as a
   string like `0.153s`, so aggregating it means stripping the suffix first.

3. **Run the worked example, then write one of your own.** This is the first SQL you write
   yourself in the lab — Phase 3's query came ready-made in the notebook and Phase 4's lives in
   `retrieval.py` — so here is the shape, counting requests by status code:

   ```bash
   bq query --use_legacy_sql=false "
     SELECT httpRequest.status AS status, COUNT(*) AS n
     FROM \`$PROJECT.eurecomgpt_logs.run_googleapis_com_requests\`
     GROUP BY status ORDER BY n DESC"
   ```

   Now write a **different** one that your load test can answer and that aggregates something
   other than a plain count: latency by URL path, requests per minute across the window, or the
   p99 (`APPROX_QUANTILES(x, 100)[OFFSET(99)]`). Latency is that `0.153s` string, so it needs
   converting before you can average it — `CAST(REPLACE(httpRequest.latency, 's', '') AS FLOAT64)`
   is one way. You may ask the agent for the SQL, but you have to read the result and be able to
   say what it means.

4. **Record now.** Paste your own query and one result row straight into
   `phase6_postmortem.md`'s `log_sink_query` slot — not into a scratch file you will lose.

**Taught in.** Core Services M2 *Storage and Database Services* · Phase 3 Task 11 and Phase 4's
`retrieval.py` showed you BigQuery queries; this is the first one you write.

**Verified by.** The post-mortem slot `log_sink_query` — your own query, verbatim, and a result
line.

---

## Task 7 — Review another agent's pull request

Now the other side of the job. [review/main.tf](review/main.tf) is a complete Terraform for the
same stack, written by an agent from the same `SPEC.md`. It validates, it would apply, and it
contains **three faults** a careless reviewer would approve: one that **costs money**, one that
**grants more than it should**, one that **fails silently**. Read it against the spec line by
line — do not apply it — and fill in `submission/phase6_review.md` (you copied it before
Task 1).

For each fault: where, what is wrong and what it would have cost or exposed, and the corrected
HCL. Then a verdict: would you approve after the fixes, and which fault would have been hardest
to notice *after* apply?

**Taught in.** Everything from Phases 4–5 and this phase's `SPEC.md`. Your own agent may have
made one of these three mistakes in Task 3; check.

**Verified by.** The public test checks the review is complete; the instructor's checks that
you found the right three.

---

## Task 8 — Finish the supervision log

If you followed the **Record now** lines, most of `submission/phase6_supervision.md` is already
written and this task is short: add `trust_boundary` — where, *now that you have done it*, you
would draw the line between what an agent may do unsupervised, what needs approval, and what it
may never do — and fill anything still marked `TODO`.

If you skipped them, this is the task that hurts, and no transcript will rescue the approvals
table: it wants what you were thinking, not what the agent printed.

**Verified by.** The public test checks every slot is filled and the approvals table has ≥ 4
rows with a refusal; the instructor reads it.

---

## Task 9 — Finish the post-mortem

Two slots are left that need the whole phase behind them: `iac_scope` (what Terraform managed,
what it deliberately did not, and why that split is right) and `scale_1000x` (what breaks first
under a thousand times the load). One more, `tf_remaining`, waits for the destroy in Task 10.

The agent may draft any of this; you are accountable for every number and every claim.

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

### If `terraform destroy` will not run

Two failures are common, and neither means your stack is broken.

**`dial tcp [2a00:...]:443: connect: cannot assign requested address`.** Cloud Shell handed the
VM an IPv6 address it cannot actually dial from, and Terraform — a Go binary with its own
resolver — prefers the AAAA record. Nothing was destroyed; this fails during refresh. Editing
`/etc/gai.conf` does *not* help (Go ignores it). Remove the IPv6 stack instead, then retry:

```bash
sudo sysctl -w net.ipv6.conf.all.disable_ipv6=1
sudo sysctl -w net.ipv6.conf.default.disable_ipv6=1
```

**A `403` on the project IAM bindings.** The provider still impersonates `agent-operator`
(`impersonate` in `terraform.tfvars`), and if you revoked `projectIamAdmin` in Task 4 it can no
longer remove those bindings. Comment the `impersonate` line out so Terraform acts as *you* —
which is what this task intends anyway — and destroy again.

### Fallback: tear down by hand, then reconcile state

If neither fixes it, delete the resources yourself and bring the state in line. The graded
report is identical, and doing it this way shows you exactly how much a one-line `destroy` was
doing for you:

```bash
# 1. what Terraform manages, so you delete all of it and nothing else
cd phase-6-capstone/terraform && terraform state list

# 2. delete (gcloud resolves IPv4 happily, so this works when Terraform does not)
gcloud run services delete chat-tf --region=$REGION --quiet
gcloud logging sinks delete chat-tf-requests-to-bq --quiet
gcloud logging metrics delete chat-tf_errors --quiet
gcloud alpha monitoring policies list --format='value(name)' --filter='displayName~chat-tf'   # delete each
gcloud alpha monitoring channels list --format='value(name)' --filter='displayName~EurecomGPT'
bq rm -r -f --dataset $PROJECT:eurecomgpt_tf
bq rm -r -f --dataset $PROJECT:eurecomgpt_logs
gcloud iam service-accounts delete chat-tf-runner@$PROJECT.iam.gserviceaccount.com --quiet
gcloud iam roles delete chattfBigQueryReader --project=$PROJECT --quiet

# 3. make Terraform forget what no longer exists (local only — no API calls)
terraform state list | xargs -d '\n' terraform state rm
python ../make_report.py destroyed
```

**Order matters:** `state rm` deletes nothing in GCP. Run it before step 2 and you have thrown
away the only list of what is still running. And `xargs -d '\n'` is not optional — plain
`xargs` strips the quotes out of `for_each` addresses like
`google_project_iam_member.chat_roles["roles/bigquery.jobUser"]` and Terraform rejects them.

Leave the enabled APIs alone either way: the config sets `disable_on_destroy = false` because
Phases 1–5 still use them, so even a clean destroy only forgets them.

If you used the fallback, say so in `what_broke` — "the tool failed, the platform was fine" is a
real operational distinction, and the diagnosis is the interesting part.

**Taught in.** Terraform badge · Lecture 1 (elasticity includes elasticity to zero)

**Record now.** In `phase6_postmortem.md`: `tf_remaining`, from the report you just wrote. That
is the last slot.

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

