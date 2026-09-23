# Phase 6 — Supervision Log

Copy this file to `submission/phase6_supervision.md`, fill in every answer slot, and commit it:

```bash
cp phase-6-capstone/supervision_template.md submission/phase6_supervision.md
```

**How to fill it in.** Each answer sits between a pair of `<!--answer:...-->` markers. Replace
the `TODO` line with your answer — **leave the markers themselves untouched**. Fill it *as you
go*, not from memory afterwards: the approvals table is a log, and its value is in what you
decided at the time.

---

## 1. Setup

**Which agent, and how you ran it** (tool and version; where `policy.json` was translated to):

<!--answer:agent_tool-->
TODO
<!--/answer-->

**The identity you gave it.** The roles you granted `agent-operator` and the one role you
deliberately withheld — and why that one. (~50 words)

<!--answer:agent_identity-->
TODO
<!--/answer-->

**Your boundary, in one paragraph.** Why those commands are auto-allowed, why those need
approval, and why those are forbidden outright rather than merely prompted. (~60 words)

<!--answer:boundary_rationale-->
TODO
<!--/answer-->

---

## 2. The log

Every time the agent asked for approval. **At least four rows**, including at least one **no**.
Keep the table format (the grader counts rows):

<!--answer:approvals-->
| # | What it wanted to run | Why it said it needed to | Decision | Why |
|---|---|---|---|---|
| 1 | TODO | TODO | yes / no | TODO |
| 2 | TODO | TODO | yes / no | TODO |
| 3 | TODO | TODO | yes / no | TODO |
| 4 | TODO | TODO | yes / no | TODO |
<!--/answer-->

**The refusal.** Pick one row where you said no. What would have happened if you had said yes?
(~40 words)

<!--answer:refusal-->
TODO
<!--/answer-->

**The 403.** At some point the agent tried something `agent-operator` was not allowed to do.
What was it, what did the error say, and what did the agent propose? You granted
`projectIamAdmin` — for how long, and did you revoke it afterwards? What could the agent have
done with it in that window that you would not have approved? (~70 words)

<!--answer:iam_403-->
TODO
<!--/answer-->

---

## 3. Judgement

**Something the agent got wrong** — a hallucinated attribute, a wrong diagnosis, a fix that
made things worse — and how you caught it. Quote the relevant line. (~60 words)

<!--answer:agent_mistake-->
TODO
<!--/answer-->

**Something you did by hand**, and why you did not delegate it. (~40 words)

<!--answer:by_hand-->
TODO
<!--/answer-->

**Trust.** After this phase: which parts of operating a stack would you hand to an agent
unsupervised, which with approval, and which never? One line each, with the reason. (~80 words)

<!--answer:trust_boundary-->
TODO
<!--/answer-->
