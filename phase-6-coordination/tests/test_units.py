"""Phase 6 unit tests — offline, the 2PC + Raft protocol logic (no cloud, no report).

Drives your twopc.py / raft.py through the simulator's failure scenarios. Run while coding:

    python -m pytest phase-6-coordination/tests/test_units.py -p autograder.points -q

(60 points.)
"""

from __future__ import annotations

import sim
from autograder.points import points

# ------------------------------- 2PC (25) ------------------------------------ #
@points(8)
def test_2pc_commits_when_all_yes():
    r = sim.run_2pc(["yes", "yes", "yes"])
    assert r["decision"] == "commit"
    assert r["outcomes"] == ["committed", "committed", "committed"]


@points(8)
def test_2pc_aborts_on_any_no():
    r = sim.run_2pc(["yes", "no", "yes"])
    assert r["decision"] == "abort"
    assert set(r["outcomes"]) == {"aborted"}


@points(9)
def test_2pc_blocks_on_coordinator_crash():
    # Coordinator dies after votes, before the decision: prepared participants BLOCK.
    r = sim.run_2pc(["yes", "yes"], coordinator_crashes=True)
    assert r["decision"] is None
    assert r["outcomes"] == ["blocked", "blocked"]


# ------------------------------- Raft (35) ----------------------------------- #
@points(10)
def test_raft_elects_single_leader():
    c = sim.RaftCluster(3)
    assert c.elect(0) == 0
    assert c.leaders() == [0]


@points(8)
def test_raft_reelection_after_leader_down():
    c = sim.RaftCluster(3)
    assert c.elect(0) == 0
    assert c.elect(1, down={0}) == 1               # old leader unreachable
    assert c.nodes[1].current_term > c.nodes[0].current_term


@points(10)
def test_raft_partition_prevents_split_brain():
    c = sim.RaftCluster(3, minority={0})
    assert c.elect(0) is None                      # minority can't win a majority
    assert c.elect(1) == 1                          # majority side elects a leader
    assert len(c.leaders()) == 1


@points(7)
def test_raft_log_replication_commits_on_majority():
    c = sim.RaftCluster(3)
    c.elect(0)
    r = c.replicate(0, "hello")
    assert r["committed"] and r["acks"] == 3
