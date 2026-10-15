#!/usr/bin/env python3
"""The SAVED round points are added up from the ITEMISED BREAKDOWN, not taken
from the FPL total - the same rule as on the page.

WHY: FPL keeps stats.total_points and the explain event list SEPARATELY, and
the total can get stuck (GW2: the row showed 1 point, the breakdown 90
minutes and a goal, 8 in total; the same in the official FPL app). The
collector NEVER fetches a closed round again, and from then on the page shows
the SAVED number - whatever went in at closing stays in for good.

P1: next to a stuck total, the sum of the breakdown goes into the stored data.
P2: if there is no explain (the player did not play), stats stays the
    source - an API change thus gives back the OLD behaviour, not zeros.
P3: in a double gameweek the breakdowns of the two matches ADD UP.
P4: on a mismatch the run reports LOUDLY (the log shows if it is recurring).
"""
import io, os, sys, contextlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import collect_draft as c

failures, total = [], 0


def check(cond, label):
    global total
    total += 1
    print(("OK   " if cond else "FAIL ") + label)
    if not cond:
        failures.append(label)


def row(stat, points, value=0):
    return {"name": stat, "stat": stat, "points": points, "value": value}


print("--- P1: next to a stuck total, the breakdown wins ---")
stuck = {"stats": {"total_points": 1, "minutes": 9},
         "explain": [[[row("minutes", 2, 90), row("goals_scored", 4, 1),
                       row("bonus", 2, 2)], 12]]}
p, from_breakdown = c.player_points(stuck)
check(p == 8, "P1: the stored points are the breakdown's sum (8), not the stuck 1 - got: %s" % p)
check(from_breakdown, "P1: the function signals that it came from the breakdown")

print("\n--- P2: no breakdown -> stats stays ---")
for label, v in (("empty explain", {"stats": {"total_points": 3}, "explain": []}),
                 ("no explain key", {"stats": {"total_points": 3}}),
                 ("unknown structure", {"stats": {"total_points": 3},
                                        "explain": [{"fixture": 1, "stats": []}]})):
    p, from_breakdown = c.player_points(v)
    check(p == 3 and not from_breakdown,
          "P2: %s -> the stats total stays (3) - got: %s" % (label, p))

print("\n--- P3: double gameweek: the two matches add up ---")
double = {"stats": {"total_points": 0},
          "explain": [[[row("minutes", 2, 90), row("goals_scored", 4, 1)], 12],
                      [[row("minutes", 2, 90), row("assists", 3, 1)], 15]]}
p, _ = c.player_points(double)
check(p == 11, "P3: the breakdowns of the two matches add up (2+4+2+3 = 11) - got: %s" % p)

print("\n--- P4: missing fields do not break it ---")
for label, v in (("empty dict", {}), ("None", None),
                 ("explain=None", {"stats": {"total_points": 5}, "explain": None})):
    try:
        p, _ = c.player_points(v)
        check(True, "P4: %s -> does not fail (%s points)" % (label, p))
    except Exception as e:
        check(False, "P4: %s -> EXCEPTION: %r" % (label, e))

if failures:
    print("\n%d assertions failed." % len(failures))
    sys.exit(1)
print("\nAll %d assertions passed." % total)
