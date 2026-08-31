"""Toy Raft — leader election + log replication core (Lecture 11).

You implement the four functions that make Raft safe: starting an election, the RequestVote
rule (which prevents two leaders in a term), the majority check, and AppendEntries. The
simulator in ``sim.py`` runs a 3-node cluster with crashes and network partitions on top of
them. Run the offline tests:

    python -m pytest phase-6-coordination/tests/test_units.py -p autograder.points -q
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Node:
    id: int
    current_term: int = 0
    voted_for: int | None = None
    state: str = "follower"  # "follower" | "candidate" | "leader"
    log: list = field(default_factory=list)   # entries are (term, value)
    votes: set = field(default_factory=set)


def last_log(node: Node) -> tuple[int, int]:
    """Return the node's ``(last_index, last_term)`` (both 0 for an empty log) — provided."""
    return (len(node.log), node.log[-1][0]) if node.log else (0, 0)


def start_election(node: Node) -> None:
    """Become a candidate for the next term: bump the term, vote for yourself."""
    # TODO: current_term += 1; state = "candidate"; voted_for = own id; votes = {own id}.
    raise NotImplementedError("Phase 6: implement start_election()")


def handle_request_vote(node: Node, cand_term: int, cand_id: int,
                        cand_last_index: int, cand_last_term: int) -> bool:
    """RequestVote RPC handler. Return True iff this node grants its vote.

    Rules: reject a stale term; if the candidate's term is newer, step down and clear the
    vote for the new term; grant iff we haven't already voted for someone else this term AND
    the candidate's log is at least as up-to-date as ours (compare (term, index)).
    """
    # TODO: implement the RequestVote rule described in the docstring.
    raise NotImplementedError("Phase 6: implement handle_request_vote()")


def has_majority(votes: set, cluster_size: int) -> bool:
    """True iff ``votes`` is a strict majority of the cluster."""
    # TODO: a strict majority is more than half the cluster.
    raise NotImplementedError("Phase 6: implement has_majority()")


def handle_append_entries(node: Node, leader_term: int, entries: list) -> bool:
    """AppendEntries RPC handler. Accept (and append) iff the leader's term is current."""
    # TODO: reject if leader_term < current_term; otherwise adopt the term, become a
    #       follower, append the entries, and return True.
    raise NotImplementedError("Phase 6: implement handle_append_entries()")
