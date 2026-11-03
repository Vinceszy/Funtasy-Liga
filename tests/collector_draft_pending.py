#!/usr/bin/env python3
"""The Draft collector telling the workflow that a played round is not closed yet.

WHY IT IS NEEDED: the FPL closes a round (head-to-head results, automatic
substitutions) the morning after its last match, and only a collector run
sees the close. GitHub skips scheduled runs, sometimes for a whole morning,
and then the results stay off the page until somebody starts the collector by
hand. collect_draft.round_pending is the signal on which draft.yml restarts
itself until the close is recorded.

R1: a round in progress (not every fixture finished) is not waiting.
R2: every fixture finished, results missing -> the current round is waiting.
R3: provisionally finished fixtures count as played.
R4: results recorded but the squads not final yet -> still waiting.
R5: results recorded and the squads final -> nothing is waiting.
R6: an EARLIER round with a missing result is waiting, whatever the
    current round's fixtures say.
R7: no fixtures answer (failed request) -> the current round is not
    declared waiting on a guess; an earlier missing result still is.
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import collect_draft as c

failures, total = [], 0


def check(cond, label):
    global total
    total += 1
    print(("OK   " if cond else "FAIL ") + label)
    if not cond:
        failures.append(label)


def matches(done_up_to, current, current_done=False):
    out = []
    for gw in range(1, current + 1):
        finished = gw <= done_up_to or (gw == current and current_done)
        out += [{"event": gw, "finished": finished} for _ in range(5)]
    return out


FINISHED = [{"finished": True, "finished_provisional": True} for _ in range(10)]
RUNNING = FINISHED[:9] + [{"finished": False, "finished_provisional": False}]
PROVISIONAL = [{"finished": False, "finished_provisional": True} for _ in range(10)]
FINALS = set(range(1, 9))

r = c.round_pending(matches(8, 9), 9, RUNNING, FINALS)
check(r is None, "R1: a round in progress is not waiting - got %s" % r)
r = c.round_pending(matches(8, 9), 9, FINISHED, FINALS)
check(r == 9, "R2: played, results missing -> 9 - got %s" % r)
r = c.round_pending(matches(8, 9), 9, PROVISIONAL, FINALS)
check(r == 9, "R3: provisionally finished counts as played - got %s" % r)
r = c.round_pending(matches(8, 9, current_done=True), 9, FINISHED, FINALS)
check(r == 9, "R4: results in, squads not final -> 9 - got %s" % r)
r = c.round_pending(matches(8, 9, current_done=True), 9, FINISHED, FINALS | {9})
check(r is None, "R5: results in, squads final -> nothing - got %s" % r)
r = c.round_pending(matches(7, 9), 9, RUNNING, FINALS)
check(r == 8, "R6: an earlier missing result is waiting -> 8 - got %s" % r)
r = c.round_pending(matches(8, 9), 9, None, FINALS)
check(r is None, "R7: no fixtures answer, no guess - got %s" % r)
r = c.round_pending(matches(7, 9), 9, None, FINALS)
check(r == 8, "R7: ...but an earlier missing result still waits - got %s" % r)

if failures:
    print("\n%d assertions failed." % len(failures))
    sys.exit(1)
print("\nAll %d assertions passed." % total)
