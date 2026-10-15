#!/usr/bin/env python3
"""The "Guardiola indicator": how many points more/fewer after the squad
change. guard = the CURRENT squad's points - LAST WEEK's squad's points in
the SAME round. Negative: the change cost points.

G1: with an UNCHANGED squad EXACTLY 0. (This is the assertion that breaks
    most easily: if the two sides count differently - one from the stored
    `week`, the other from the breakdown -, the halving of a bench player
    slips by 0.01, and the indicator would show "+0.01" although the manager
    did not touch the squad.)
G2: a better transfer -> positive, a worse one -> negative, the difference
    is exact.
G3: LAST WEEK's ROLES count, not the current ones (captain, bench).
G4: the Hungarian rule bonus applies to the alternative too - if it is lost
    because of the Hungarian player transferred out, it shows in the indicator.
G5: nothing to compare with (first round) -> no value.
G6: the round's breakdown is not available yet (not closed) -> no value.
G7: a player who is no longer in the breakdown (dropped from the roster)
    gives 0 points.
G8: the breakdown collection also covers the players EVER OWNED (`extra`) -
    without it a player who left the league counted with 0, and the
    indicator slipped in favour of whoever had just got rid of them.
G9: an EXISTING breakdown file is only COMPLETED (with the few missing
    players), all 385 are not fetched again.
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import collect as c

failures, total = [], 0


def check(cond, label):
    global total
    total += 1
    print(("OK   " if cond else "FAIL ") + label)
    if not cond:
        failures.append(label)


def player(pid, hun=False, u21=False, cap=False, sub=False):
    return {"id": pid, "name": "J%d" % pid, "hun": hun, "u21": u21,
            "cap": cap, "sub": sub, "pos": "KP", "week": 0}


def squad(ids, **kw):
    """15-player squad: the first 11 are starters, the last 4 on the bench."""
    sq = []
    for i, pid in enumerate(ids):
        sq.append(player(pid, sub=(i >= 11), **kw))
    return sq


BASE_IDS = list(range(1, 16))
# every player scores 5 points in this round
RAW = {str(x): 5 for x in range(1, 40)}
c.raw_points = lambda r: RAW

print("--- G1: unchanged squad -> exactly 0 ---")
h = {"1": {"A": squad(BASE_IDS)}, "2": {"A": squad(BASE_IDS)}}
g = c.guardiola(h, 2)
check(g and g["A"]["guard"] == 0,
      "G1: with an unchanged squad the indicator is exactly 0 - got: %s" % (g and g["A"]))

print("\n--- G1b: exactly 0 with a BENCH player too (rounding of the halving) ---")
# 0.75 raw points -> the bench halves it to 0.38 (the API rounds) - the two
# sides must count from the same source, otherwise 0.01 would come out here
RAW_FRACTION = {str(x): 0.75 for x in range(1, 40)}
c.raw_points = lambda r: RAW_FRACTION
g = c.guardiola(h, 2)
check(g and g["A"]["guard"] == 0,
      "G1b: exactly 0 with fractional points too - got: %s" % (g and g["A"]))
c.raw_points = lambda r: RAW

print("\n--- G2: transfer -> the difference is exact ---")
# number 20 comes in for number 2 (a starter, 5 points), and scores 9
RAW2 = dict(RAW); RAW2["20"] = 9
c.raw_points = lambda r: RAW2
new = squad(BASE_IDS[:1] + [20] + BASE_IDS[2:])    # number 20 in place of STARTER number 2
h2 = {"1": {"A": squad(BASE_IDS)}, "2": {"A": new}}
g = c.guardiola(h2, 2)
check(g and g["A"]["guard"] == 4,
      "G2: the 9-point player came in for the 5-point one -> +4 - got: %s" % (g and g["A"]))
h3 = {"1": {"A": new}, "2": {"A": squad(BASE_IDS)}}
g = c.guardiola(h3, 2)
check(g and g["A"]["guard"] == -4,
      "G2: the other way round -4 - got: %s" % (g and g["A"]))
c.raw_points = lambda r: RAW

print("\n--- G3: LAST WEEK's roles count ---")
# last week number 3 was captain, now number 4. In the alternative number 3
# must be doubled. Give number 3 10 points, the rest 5.
RAW3 = dict(RAW); RAW3["3"] = 10
c.raw_points = lambda r: RAW3
old = squad(BASE_IDS); old[2]["cap"] = True        # number 3 is captain
new = squad(BASE_IDS); new[3]["cap"] = True        # number 4 is captain
g = c.guardiola({"1": {"A": old}, "2": {"A": new}}, 2)
# actual: 10 + 5x10 + 5 (number 4 doubled) + bench... the DIFFERENCE is what matters:
# alternative = +10 (number 3 doubled), actual = +5 (number 4 doubled) -> -5
check(g and g["A"]["guard"] == -5,
      "G3: last week's captain is doubled in the alternative -> -5 - got: %s"
      % (g and g["A"]))
c.raw_points = lambda r: RAW

print("\n--- G4: the Hungarian rule bonus applies to the alternative too ---")
# last week 5 Hungarian starters (one of them u21) -> +10. Now one of them was
# replaced by a foreign player, so the actual does NOT get +10, the alternative does.
old = squad(BASE_IDS)
for i in range(5):
    old[i]["hun"] = True
old[0]["u21"] = True
new = squad(BASE_IDS)
for i in range(1, 5):                              # only 4 Hungarians remain
    new[i]["hun"] = True
new[1]["u21"] = True
g = c.guardiola({"1": {"A": old}, "2": {"A": new}}, 2)
check(g and g["A"]["guard"] == -10,
      "G4: the lost Hungarian rule bonus shows as -10 - got: %s" % (g and g["A"]))

print("\n--- G5/G6: when there is no value ---")
check(c.guardiola({"1": {"A": squad(BASE_IDS)}}, 1) is None,
      "G5: no indicator for the first round")
c.raw_points = lambda r: None
check(c.guardiola(h, 2) is None,
      "G6: no indicator without a breakdown (round not closed)")
c.raw_points = lambda r: RAW

print("\n--- G7: a player no longer in the breakdown gives 0 points ---")
NARROW = {str(x): 5 for x in range(1, 15)}         # number 15 is missing
c.raw_points = lambda r: NARROW
old = squad(BASE_IDS)                              # number 15: ON THE BENCH
new = squad(BASE_IDS[:14] + [21])                  # number 21 instead, also on the bench
NARROW["21"] = 5
g = c.guardiola({"1": {"A": old}, "2": {"A": new}}, 2)
# number 15 gives 0 (bench: 0), number 21 gives 5 (bench: 2.5) -> +2.5
check(g and g["A"]["guard"] == 2.5,
      "G7: the player missing from the breakdown gives 0 points -> +2.5 - got: %s"
      % (g and g["A"]))

print("\n--- G8-G9: the breakdown collection covers the players ever owned ---")
import json as _json, shutil, tempfile

_workdir = tempfile.mkdtemp()
_old_cwd = os.getcwd()
_old_api = c.api_get
_requested = []


def _api(url):
    _requested.append(url.split("competition_player_id%5D=")[1].split("&")[0])
    return 200, {"data": [{"competition_stat_config": {"name": "Gol"},
                           "value": 1, "points": 5}]}


try:
    os.chdir(_workdir)
    c.api_get = _api
    ROSTER = {"1": {}, "2": {}}
    # number 99 is no longer in the roster, but someone owned them once
    c.collect_breakdowns([2], set(), ROSTER, {"99"})
    with open("bontasok/2.json", encoding="utf-8") as f:
        b = _json.load(f)["bontasok"]
    check(set(b) == {"1", "2", "99"},
          "G8: the player who left but was owned is in the breakdown too - got: %s"
          % sorted(b))

    # G9: an existing file where only number 99 is missing
    c.write_compact("bontasok/2.json", {"round": 2, "bontasok": {"1": [], "2": []}})
    del _requested[:]
    c.collect_breakdowns([2], set(), ROSTER, {"99"})
    with open("bontasok/2.json", encoding="utf-8") as f:
        b = _json.load(f)["bontasok"]
    check(_requested == ["99"],
          "G9: only the missing player was fetched, not the rest - got: %s" % _requested)
    check(set(b) == {"1", "2", "99"},
          "G9: the existing rows remained after the completion - got: %s" % sorted(b))

    # once nothing is missing, not a single request goes out
    del _requested[:]
    c.collect_breakdowns([2], set(), ROSTER, {"99"})
    check(_requested == [], "G9: no request for a complete file - got: %s" % _requested)
finally:
    c.api_get = _old_api
    os.chdir(_old_cwd)
    shutil.rmtree(_workdir, ignore_errors=True)

if failures:
    print("\n%d assertions failed." % len(failures))
    sys.exit(1)
print("\nAll %d assertions passed." % total)
