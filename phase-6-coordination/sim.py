"""Deterministic simulators for 2PC and Raft with failure injection (provided).

These drive the functions you implement in ``twopc.py`` / ``raft.py`` through the scenarios
the tests check — happy path, abort, coordinator crash (2PC blocking), leader election,
re-election, and network partition (split-brain prevention).
"""

from __future__ import annotations

from raft import (Node, handle_append_entries, handle_request_vote, has_majority,
                  last_log, start_election)
from twopc import coordinator_decision, participant_outcome


def run_2pc(votes: list[str], coordinator_crashes: bool = False) -> dict:
    """Run 2PC over participants with the given votes.

    If ``coordinator_crashes`` is True, the coordinator fails after collecting votes but
    before disseminating the decision, so participants never learn it (decision = None).
    """
    decision = None if coordinator_crashes else coordinator_decision(votes)
    outcomes = [participant_outcome(v, decision) for v in votes]
    return {"decision": decision, "outcomes": outcomes}


class RaftCluster:
    """An n-node Raft cluster with an optional network partition."""

    def __init__(self, n: int = 3, minority: frozenset = frozenset()):
        self.n = n
        self.nodes = [Node(i) for i in range(n)]
        self.minority = set(minority)  # node ids isolated on the minority side

    def _connected(self, a: int, b: int) -> bool:
        return (a in self.minority) == (b in self.minority)

    def elect(self, candidate_id: int, down: frozenset = frozenset()):
        """Run one election started by ``candidate_id``. Return the leader id, or None."""
        cand = self.nodes[candidate_id]
        start_election(cand)
        idx, term = last_log(cand)
        for other in self.nodes:
            if other.id == candidate_id or other.id in down:
                continue
            if not self._connected(candidate_id, other.id):
                continue  # partitioned — the RequestVote never arrives
            if handle_request_vote(other, cand.current_term, cand.id, idx, term):
                cand.votes.add(other.id)
        if has_majority(cand.votes, self.n):
            cand.state = "leader"
            return cand.id
        cand.state = "candidate"
        return None

    def leaders(self) -> list[int]:
        return [nd.id for nd in self.nodes if nd.state == "leader"]

    def replicate(self, leader_id: int, value, down: frozenset = frozenset()) -> dict:
        """Leader appends ``value`` and replicates it. Committed once a majority ack."""
        leader = self.nodes[leader_id]
        leader.log.append((leader.current_term, value))
        acks = 1
        for other in self.nodes:
            if other.id == leader_id or other.id in down:
                continue
            if not self._connected(leader_id, other.id):
                continue
            if handle_append_entries(other, leader.current_term, [(leader.current_term, value)]):
                acks += 1
        return {"acks": acks, "committed": acks > self.n // 2}
