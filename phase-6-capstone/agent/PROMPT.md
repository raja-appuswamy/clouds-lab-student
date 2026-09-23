# The kickoff prompt

Paste this to the agent once, in the repo root, after you have set your approval boundary
(Task 2). It is deliberately longer than "write the Terraform": an agent told only to produce
code produces code you cannot review, and this phase grades whether you can review it.

Adapt it — it is your prompt, not a fixed input. If you change it, say what you changed and
why in the supervision log; that is a supervision decision like any other.

---

```text
Read phase-6-capstone/SPEC.md and phase-6-capstone/agent/GEMINI.md first. Your task is to
complete the Terraform in phase-6-capstone/terraform/ so that it satisfies every line of the
spec and `terraform plan` is clean.

Work one file at a time, and for each file follow this order:

1. Say which part of the spec you are about to implement, in one sentence.
2. Write the code.
3. Explain it to me before you move on. For every resource you add or complete, tell me:
   - what it creates, in plain words;
   - which line of SPEC.md requires it;
   - the one attribute that would silently break it if it were wrong, and what the symptom
     would be — a 403, an empty table, an alert that never fires, a bill;
   - what it costs, or why it is free.
4. Name the test in phase-6-capstone/tests/test_units.py that your change should turn green,
   then run `python -m pytest phase-6-capstone/tests/test_units.py -p autograder.points -q`
   and `terraform validate`, and show me the output.
5. Stop and wait for me. I may ask you to justify a choice or change it.

Rules for the explanations:
- Explain the choice, not the syntax. I can read HCL; I want to know why this argument has
  this value.
- Where the spec leaves something open, say that it is your choice, give the alternative you
  rejected, and say why.
- Where you are unsure whether an attribute exists, run `terraform validate` and read the
  error instead of guessing.
- Never say a test passes without showing me its output.

Do not run `terraform apply`, and do not create, update or delete any cloud resource. When the
plan is clean, summarise: how many resources it will add, which of them cost money under load,
and which single resource you are least confident about and why.
```

---

**Using it with a follow-up.** When the agent goes quiet on the reasoning — and it will — the
two questions that recover it are *"what would happen if that value were wrong?"* and *"what
did you consider and reject here?"*. Both make good approval-row entries in
`phase6_supervision.md`.

**When its explanation is wrong.** That is the most valuable thing that can happen in this
phase. Catch one — a confident, plausible, incorrect explanation — and write it up as the
"one thing the agent got wrong" slot in the supervision log. You have the five phases behind
you to catch it with.
