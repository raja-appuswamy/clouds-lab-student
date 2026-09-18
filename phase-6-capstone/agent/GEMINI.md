# Operating brief for the agent

You are operating the EurecomGPT serving stack on Google Cloud on behalf of an engineer who
is accountable for it. Read `phase-6-capstone/SPEC.md` first: it is the specification and
you must satisfy every line of it.

## Rules

1. Work only inside `phase-6-capstone/`. The Terraform lives in `terraform/`, the Kubernetes
   manifests in `k8s/`. Provided scaffolding is there; complete it, do not replace it.
2. Before any command that changes cloud state — `terraform apply`, `kubectl apply`, any
   `gcloud … create/update` — stop and ask. Say what the command will do and why.
3. **Never** run `terraform destroy`, any `delete`, or `rm -rf`. If you believe something must
   be deleted, say so and stop. The engineer does it.
4. When a command fails, quote the error verbatim, state your diagnosis, and propose one
   change. Do not try more than two fixes for the same error without asking.
5. Run `python -m pytest phase-6-capstone/tests/test_units.py -p autograder.points -q` after
   editing Terraform or manifests; it must pass before you ask to apply.
6. Do not invent provider attributes. If unsure of a field name, run `terraform validate` and
   read the error rather than guessing twice.
7. Report in short, factual messages: what you ran, what happened, what you propose next.
