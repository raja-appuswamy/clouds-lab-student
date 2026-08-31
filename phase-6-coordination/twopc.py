"""Two-phase commit — the coordinator decision + participant outcome (Lecture 10).

You implement two pure functions that capture the essence of 2PC, including its famous
**blocking** behaviour when the coordinator fails. The simulator in ``sim.py`` drives them
through happy-path, abort, and failure scenarios; run the offline tests:

    python -m pytest phase-6-coordination/tests/test_units.py -p autograder.points -q
"""

from __future__ import annotations


def coordinator_decision(votes: list[str]) -> str:
    """Phase-1 result → the global decision.

    ``votes`` is the list of participant votes, each ``"yes"`` or ``"no"``. Return
    ``"commit"`` only if **every** participant voted yes; otherwise ``"abort"``.
    """
    # TODO: "commit" iff all votes are "yes" (and there is at least one), else "abort".
    raise NotImplementedError("Phase 6: implement coordinator_decision()")


def participant_outcome(vote: str, decision: str | None) -> str:
    """A participant's final state given its own vote and the decision it learned.

    ``decision`` is ``"commit"``/``"abort"``, or ``None`` if the coordinator crashed before
    this participant learned the outcome. Return one of:
      - ``"aborted"``   — it voted "no" (it may abort unilaterally, decision or not);
      - ``"committed"`` / ``"aborted"`` — following ``decision`` when it is known;
      - ``"blocked"``   — it voted "yes" but the decision is unknown. **This is the 2PC
        blocking problem**: a prepared participant cannot unilaterally decide, so it waits.
    """
    # TODO:
    #   vote == "no"        -> "aborted"   (can abort unilaterally)
    #   decision is None    -> "blocked"   (voted yes, outcome unknown → 2PC blocks)
    #   decision == "commit"-> "committed" else "aborted"
    raise NotImplementedError("Phase 6: implement participant_outcome()")
