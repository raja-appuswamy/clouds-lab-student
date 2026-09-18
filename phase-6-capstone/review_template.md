# Phase 6 — Review of PR #12 (an agent's Terraform)

Copy this file to `submission/phase6_review.md`, fill in every answer slot, and commit it:

```bash
cp phase-6-capstone/review_template.md submission/phase6_review.md
```

**How to fill it in.** Each answer sits between a pair of `<!--answer:...-->` markers. Replace
the `TODO` line with your answer — **leave the markers themselves untouched**. Anything outside
the markers is ignored.

You are reviewing [review/main.tf](review/main.tf): a complete, valid, applyable Terraform for
the EurecomGPT stack, written by an agent from `SPEC.md`. It contains **three faults** that a
careless reviewer would approve. Read it against the spec, line by line, the way you would
review a colleague's pull request before it touches production — because that is what it is.

---

## The three faults

For each: which resource and line, what is wrong relative to `SPEC.md`, what it would have
**cost or exposed** had you approved it, and the fix (the corrected HCL, verbatim).

**Fault A**

<!--answer:fault_a_where-->
TODO — resource name and line number
<!--/answer-->

<!--answer:fault_a_what-->
TODO — what is wrong, and what would happen if applied (~40 words)
<!--/answer-->

<!--answer:fault_a_fix-->
TODO — the corrected HCL
<!--/answer-->

**Fault B**

<!--answer:fault_b_where-->
TODO
<!--/answer-->

<!--answer:fault_b_what-->
TODO
<!--/answer-->

<!--answer:fault_b_fix-->
TODO
<!--/answer-->

**Fault C**

<!--answer:fault_c_where-->
TODO
<!--/answer-->

<!--answer:fault_c_what-->
TODO
<!--/answer-->

<!--answer:fault_c_fix-->
TODO
<!--/answer-->

---

## Verdict

Would you approve this PR after the three fixes, or is there anything else you would change
before it reaches your project? Which of the three faults would have been hardest to notice
*after* apply, and how would you have found out? (~60 words)

<!--answer:verdict-->
TODO
<!--/answer-->
