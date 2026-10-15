#!/usr/bin/env python3
"""The data of the "Valtoztatasok" tab on PL (collect_draft.py draft_squad_changes).

The tab derives where the Guardiola indicator came from - and in Draft that
requires SEPARATING what the HUMAN did from what the MACHINE fixed on top of
it. FPL makes automatic substitutions at the end of the round; if they were
shown together, it would look as if the manager had rotated well, while it
was the machine that repaired the squad (or the other way round).

P1: a released player counts with LAST WEEK's named role (bench = 0).
P2: an acquired player counts with the CURRENT named role.
P3: a starter <-> bench switch is a separate item.
P4: THE MACHINE SEPARATELY: the gain of the automatic substitution is not
    among the player items, but in its own row (gepE -> gepU).
P5: THE SUM OF THE ITEMS (human + machine) = the `guard` given by
    draft_guardiola.
P6: with an unchanged squad there are no items and the indicator is 0.
P7: nothing to compare with -> no data.
P8: NO POINTS DATA (the round is still in progress) -> the change STILL
    comes out, only without point values; the automatic substitution row is
    not in it either, since the automatic substitution has not happened yet.
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


POSITION = {}
STARTERS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
BENCH = [12, 13, 14, 15]
for e in STARTERS + BENCH + [20, 21]:
    POSITION[str(e)] = ("GKP" if e in (1, 12) else "DEF" if e in (2, 3, 4, 5, 13, 20)
                        else "MID" if e in (6, 7, 8, 9, 14, 21) else "FWD")


def squad(ids, bench):
    return ([{"e": e, "b": False, "pts": 0} for e in ids]
            + [{"e": e, "b": True, "pts": 0} for e in bench])


def points(base=5, minutes=90, **overrides):
    d = {str(e): [base, minutes] for e in POSITION}
    for k, v in overrides.items():
        d[k.lstrip("j")] = v
    return d


def one(old, new, p, gw=2):
    return (c.draft_squad_changes({"1": {"L": old}, "2": {"L": new}}, gw, p, POSITION)
            or {}).get("L")


print("--- P1-P3: the HUMAN's items by the named role ---")
p = points()
p["20"] = [9, 90]
v = one(squad(STARTERS, BENCH), squad([20] + STARTERS[1:], BENCH), p)
check(v and len(v["ki"]) == 1 and v["ki"][0]["e"] == 1 and v["ki"][0]["ert"] == 5
      and v["ki"][0]["sz"] == "kezdo",
      "P1: the released starter's 5 points count - got: %s" % (v and v["ki"]))
check(v and len(v["be"]) == 1 and v["be"][0]["e"] == 20 and v["be"][0]["ert"] == 9,
      "P2: the acquired starter's 9 points count - got: %s" % (v and v["be"]))

# number 11 (FWD) goes to the bench, number 15 (FWD) starts in their place
v = one(squad(STARTERS, BENCH), squad(STARTERS[:10] + [15], BENCH[:3] + [11]), points())
check(v and not v["ki"] and not v["be"] and len(v["szerep"]) == 2,
      "P3: no transfer, two role changes - got: %s" % (v and v["szerep"]))
check(v and sorted((x["szE"], x["szU"], x["ertE"], x["ertU"]) for x in v["szerep"])
      == [("kezdo", "pad", 5, 0), ("pad", "kezdo", 0, 5)],
      "P3: starter->bench 5->0 and bench->starter 0->5 - got: %s" % (v and v["szerep"]))

print("\n--- P4: the MACHINE stands apart ---")
# Starter number 11 played 0 minutes; number 15 (FWD, bench) brought 12
# points, so the automatic substitution brings them on - this is NOT the
# manager's merit.
p = points()
p["11"] = [0, 0]                       # the FWD starter did not even take the field
for e in ("12", "13", "14"):           # besides them only number 15 played from the bench
    p[e] = [0, 0]
p["15"] = [12, 90]
v = one(squad(STARTERS, BENCH), squad(STARTERS, BENCH), p)
check(v and not v["ki"] and not v["be"] and not v["szerep"],
      "P4: the human changed nothing - got: %s"
      % ((v and (v["ki"], v["be"], v["szerep"])),))
check(v and v["gepE"] == 12 and v["gepU"] == 12 and v["guard"] == 0,
      "P4: the substitution's gain is 12 on both sides, the indicator is 0 - got: %s"
      % ((v and (v["gepE"], v["gepU"], v["guard"])),))

# now the manager reorders the bench: the 12-point number 15 moves forward on
# the bench, but number 13 (DEF) could not come on for the FWD - the order matters
v2 = one(squad(STARTERS, BENCH), squad(STARTERS, [15] + BENCH[:3]), p)
check(v2 and v2["gepU"] == 12 and v2["guard"] == 0,
      "P4: reordering the bench changes nothing here (number 15 comes on anyway) - got: %s"
      % ((v2 and (v2["gepU"], v2["guard"])),))

print("\n--- P5: HUMAN + MACHINE = the Guardiola indicator ---")


def check_sum(old, new, p, label):
    hist = {"1": {"L": old}, "2": {"L": new}}
    v = (c.draft_squad_changes(hist, 2, p, POSITION) or {}).get("L")
    g = (c.draft_guardiola(hist, 2, p, POSITION) or {}).get("L")
    human = round(sum(x["ert"] for x in v["be"]) - sum(x["ert"] for x in v["ki"])
                  + sum(x["ertU"] - x["ertE"] for x in v["szerep"]), 2)
    machine = round(v["gepU"] - v["gepE"], 2)
    check(v["stimmel"] and round(human + machine, 2) == g["guard"] == v["guard"],
          "P5: %s - human %s + machine %s = %s, guardiola %s"
          % (label, human, machine, round(human + machine, 2), g["guard"]))


p = points()
p["11"] = [0, 0]
p["15"] = [12, 90]
p["20"] = [9, 90]
check_sum(squad(STARTERS, BENCH), squad([20] + STARTERS[1:], BENCH),
          p, "transfer + automatic substitution at once")
check_sum(squad(STARTERS, BENCH), squad(STARTERS[:10] + [15], BENCH[:3] + [11]),
          p, "role change + automatic substitution")
p2 = points()
p2["1"] = [0, 0]          # the goalkeeper did not play -> only a goalkeeper can replace them
p2["12"] = [7, 90]
check_sum(squad(STARTERS, BENCH), squad(STARTERS, BENCH[1:] + [12]), p2,
          "the bench order changes, goalkeeper substitution")

print("\n--- P6-P7: edge cases ---")
v = one(squad(STARTERS, BENCH), squad(STARTERS, BENCH), points())
check(v and not v["ki"] and not v["be"] and not v["szerep"] and v["guard"] == 0,
      "P6: with an unchanged squad there are no items and the indicator is 0 - got: %s" % (v,))
check(c.draft_squad_changes({"1": {"L": squad(STARTERS, BENCH)}}, 1, points(), POSITION) is None,
      "P7: no data for the first round")
print("\n--- P8: the change comes out without points data too ---")
new8 = squad(STARTERS[:10] + [20], BENCH)      # number 20 instead of number 11
v8 = (c.draft_squad_changes({"1": {"L": squad(STARTERS, BENCH)}, "2": {"L": new8}},
                            2, None, POSITION) or {}).get("L")
check(v8 and v8["pontok"] is False and v8["guard"] is None,
      "P8: the shape without points - got: %s" % ((v8 and (v8["pontok"], v8["guard"])),))
check(v8 and [x["e"] for x in v8["ki"]] == [11] and [x["e"] for x in v8["be"]] == [20],
      "P8: the transfer is visible - got: ki=%s be=%s"
      % ((v8 and [x["e"] for x in v8["ki"]]), (v8 and [x["e"] for x in v8["be"]])))
check(v8 and "gepE" not in v8 and "gepU" not in v8,
      "P8: the automatic substitution row is not in it (it has not happened yet)")

if failures:
    print("\n%d assertions failed." % len(failures))
    sys.exit(1)
print("\nAll %d assertions passed." % total)
