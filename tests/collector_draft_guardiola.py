#!/usr/bin/env python3
"""The "Guardiola indicator" on PL - the same definition as on NB1:
guard = the CURRENT squad's points MINUS LAST WEEK's squad's points in the
SAME round. Draft has no captain, and bench points do not count; but there
are AUTOMATIC SUBSTITUTIONS at the end of the round, and they must be
applied to the alternative too - otherwise last week's squad would be
under-measured, and the indicator would be systematically skewed in favour
of making changes.

D1: with an unchanged squad EXACTLY 0.
D2: the difference of a transfer is exact.
D3: AUTOMATIC SUBSTITUTION: a starter who did not take the field is replaced
    by the first bench player who played.
D4: the substitution may only produce a VALID formation (a goalkeeper can
    only be replaced by a goalkeeper - two goalkeepers are not valid).
D5: if no bench player played, there is no substitution (the 0 points stay).
D6: nothing to compare with / no points data -> no value.
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


# 15-player squad: 1 GKP + 4 DEF + 4 MID + 2 FWD starters, then 4 on the bench
POSITION = {}
def squad(ids, bench):
    sq = [{"e": e, "b": False, "pts": 0} for e in ids]
    sq += [{"e": e, "b": True, "pts": 0} for e in bench]
    return sq

STARTERS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
BENCH = [12, 13, 14, 15]
for e in STARTERS + BENCH + [20, 21]:
    POSITION[str(e)] = ("GKP" if e in (1, 12) else "DEF" if e in (2, 3, 4, 5, 13)
                        else "MID" if e in (6, 7, 8, 9, 14) else "FWD")

def points(base=5, minutes=90, **overrides):
    """{element: [points, minutes]} - single players can be overridden in overrides."""
    d = {str(e): [base, minutes] for e in list(POSITION)}
    for k, v in overrides.items():
        d[k.lstrip("j")] = v
    return d


print("--- D1: unchanged squad -> exactly 0 ---")
h = {"1": {"L": squad(STARTERS, BENCH)}, "2": {"L": squad(STARTERS, BENCH)}}
g = c.draft_guardiola(h, 2, points(), POSITION)
check(g and g["L"]["guard"] == 0,
      "D1: 0 with an unchanged squad - got: %s" % (g and g["L"]))

print("\n--- D2: transfer -> the difference is exact ---")
new = squad([20] + STARTERS[1:], BENCH)            # number 20 instead of number 1 (GKP)
POSITION["20"] = "GKP"
p = points(); p["20"] = [12, 90]
g = c.draft_guardiola({"1": {"L": squad(STARTERS, BENCH)}, "2": {"L": new}}, 2, p, POSITION)
check(g and g["L"]["guard"] == 7,
      "D2: the 12-point player came in for the 5-point one -> +7 - got: %s" % (g and g["L"]))

print("\n--- D3: automatic substitution for a starter who did not play ---")
# Starter number 11 (FWD) played 0 minutes. THE BENCH ORDER matters: number 12
# is a goalkeeper and cannot come on (two goalkeepers are not valid), numbers
# 13 and 14 DID NOT PLAY, so the first one who can come on is number 15
# (8 points). This measures the order, the validity and the skipping of a
# bench player who did not play at once.
p = points(); p["11"] = [0, 0]; p["13"] = [9, 0]; p["14"] = [9, 0]; p["15"] = [8, 90]
g = c.draft_guardiola(h, 2, p, POSITION)
# 10 starters who played x 5 + number 15 coming on with 8 = 58
check(g and g["L"]["teny"] == 58,
      "D3: the bench player who did not play is skipped, number 15 comes on (58) - got: %s"
      % (g and g["L"]))

# and if number 13 DID play, THEY come on - they are further ahead on the bench
p2 = points(); p2["11"] = [0, 0]; p2["13"] = [9, 90]; p2["15"] = [8, 90]
g2 = c.draft_guardiola(h, 2, p2, POSITION)
check(g2 and g2["L"]["teny"] == 59,
      "D3: the bench ORDER decides - number 13 comes on, not number 15 (59) - got: %s"
      % (g2 and g2["L"]))

print("\n--- D4: the substitution may only produce a valid formation ---")
# goalkeeper number 1 did not play. The first bench player who played is
# number 13 (DEF) - they must NOT come on (0 goalkeepers), only goalkeeper 12.
p = points(); p["1"] = [0, 0]; p["12"] = [3, 90]; p["13"] = [9, 90]
g = c.draft_guardiola(h, 2, p, POSITION)
# 10 starters x 5 + the GOALKEEPER coming on with 3 = 53 (not 59, which number 13 would give)
check(g and g["L"]["teny"] == 53,
      "D4: a goalkeeper can only be replaced by a goalkeeper (53, not 59) - got: %s"
      % (g and g["L"]))

print("\n--- D5: if no bench player played, there is no substitution ---")
p = points(); p["11"] = [0, 0]
for e in BENCH:
    p[str(e)] = [0, 0]
g = c.draft_guardiola(h, 2, p, POSITION)
check(g and g["L"]["teny"] == 50,
      "D5: without a substitution, the points of the 10 starters who played (50) - got: %s"
      % (g and g["L"]))

print("\n--- D7: the MIDFIELD MINIMUM (currently 2) ---")
# THIS CASE PINS THE FORMATION CONSTANT. A defender with 20 points is the
# first bench player who played: with them the shape would be 5-2-3.
#   - if the midfield minimum is 2 (current setting): the DEFENDER comes on -> 40
#   - if it were 3: they could not come on, and the bench midfielder would -> 21
# If the Draft rule turns out to be 3, the FORMATION line of collect_draft.py
# changes, and this assertion flips.
# Starters: 1 goalkeeper + 4 defenders + 3 midfielders + 3 forwards (NOT 5
# defenders, otherwise the substitution would fail on the DEFENDER MAXIMUM,
# not on the midfield minimum - the test would not measure what it believes
# it does); one of the midfielders did not play.
P7 = {}
S7 = [101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111]
B7 = [112, 113, 114, 115]
for e in S7 + B7:
    P7[str(e)] = ("GKP" if e in (101, 112) else
                  "DEF" if e in (102, 103, 104, 105, 113) else
                  "MID" if e in (106, 107, 108, 114) else "FWD")
h7 = {"1": {"L": squad(S7, B7)}, "2": {"L": squad(S7, B7)}}
p7 = {str(e): [2, 90] for e in S7 + B7}
p7["108"] = [0, 0]        # the third midfielder did not play
p7["113"] = [20, 90]      # bench DEFENDER, many points - may NOT come on
p7["114"] = [1, 90]       # bench midfielder - may come on
g = c.draft_guardiola(h7, 2, p7, P7)
# 10 starters who played x 2 = 20, + the DEFENDER coming on with 20 = 40
check(g and g["L"]["teny"] == 40,
      "D7: the 20-point defender COMES ON (5-2-3 is valid, the midfield minimum is 2) "
      "- got: %s" % (g and g["L"]))

print("\n--- D6: when there is no value ---")
check(c.draft_guardiola({"1": {"L": squad(STARTERS, BENCH)}}, 1, points(), POSITION) is None,
      "D6: no indicator for the first round")
check(c.draft_guardiola(h, 2, None, POSITION) is None,
      "D6: no indicator without points data")

if failures:
    print("\n%d assertions failed." % len(failures))
    sys.exit(1)
print("\nAll %d assertions passed." % total)
