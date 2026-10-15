#!/usr/bin/env python3
"""The data of the "Valtoztatasok" tab (collect.py squad_changes).

The whole point of the tab is that the GUARD number in the table can be
DERIVED. So the main assertion here is not "there is a list", but that the
sum of the items is EXACTLY the Guardiola indicator - with no rounding
remainder.

K1: a sold player counts with LAST WEEK's role (captain doubled).
K2: a bought player counts with the CURRENT role.
K3: a player who stayed but whose role changed is a separate item - with
    the difference of the two values.
K4: the change of the Hungarian rule bonus is a separate row (it does not
    hinge on one player).
K5: THE SUM OF THE ITEMS = the `guard` given by guardiola. This is the most
    important assertion: if it slips, the tab's number says something other
    than the table.
K6: with an unchanged squad there are no items, and the indicator is 0.
K7: nothing to compare with -> no data.
K8: NO BREAKDOWN (the round has not closed yet) -> the change STILL comes
    out, only without point values (`pontok: False`, `guard: None`). The
    squad is fixed after the submission deadline, so "whom they sold, whom
    they bought" is already known - its points are not.
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
    return {"id": pid, "name": "J%d" % pid, "team": "K", "pos": "KP",
            "hun": hun, "u21": u21, "cap": cap, "sub": sub, "week": 0}


def squad(ids, **kw):
    return [player(pid, sub=(i >= 11), **kw) for i, pid in enumerate(ids)]


BASE_IDS = list(range(1, 16))
RAW = {str(x): 5 for x in range(1, 30)}
c.raw_points = lambda r: RAW


def one(old, new, r=2):
    return (c.squad_changes({"1": {"A": old}, "2": {"A": new}}, r) or {}).get("A")


print("--- K1-K2: sold with last week's role, bought with the current one ---")
old = squad(BASE_IDS)
old[0]["cap"] = True                       # number 1 is last week's captain
new = squad([21] + BASE_IDS[1:])
new[0]["cap"] = True                       # number 21 is the current captain
v = one(old, new)
check(v and len(v["ki"]) == 1 and v["ki"][0]["id"] == 1 and v["ki"][0]["ert"] == 10,
      "K1: the sold captain's 5 raw points count doubled (10) - got: %s"
      % (v and v["ki"]))
check(v and len(v["be"]) == 1 and v["be"][0]["id"] == 21 and v["be"][0]["ert"] == 10,
      "K2: the bought captain is doubled too - got: %s" % (v and v["be"]))

print("\n--- K3: a role change is a separate item ---")
old = squad(BASE_IDS)
new = squad(BASE_IDS)
new[0]["cap"] = True                       # the same squad, a different role
v = one(old, new)
check(v and not v["ki"] and not v["be"] and len(v["szerep"]) == 1,
      "K3: no transfer, one role change - got: %s" % (v and v["szerep"]))
check(v and v["szerep"][0]["szE"] == "kezdo" and v["szerep"][0]["szU"] == "C"
      and v["szerep"][0]["ertE"] == 5 and v["szerep"][0]["ertU"] == 10,
      "K3: starter -> captain, 5 -> 10 - got: %s" % (v and v["szerep"]))

print("\n--- K4: the change of the Hungarian rule bonus is a separate row ---")
# 5 Hungarian starters, 1 of them u21 -> +10. One Hungarian drops out of the current squad.
old = squad(BASE_IDS)
for i in range(5):
    old[i]["hun"] = True
old[0]["u21"] = True
new = [dict(p) for p in old]
new[4]["hun"] = False                      # only 4 Hungarian starters left
v = one(old, new)
check(v and v["bonusz"] == -10,
      "K4: the lost Hungarian rule bonus is a separate -10 item - got: %s"
      % (v and v["bonusz"]))

print("\n--- K5: THE SUM OF THE ITEMS = the Guardiola indicator ---")


def check_sum(old, new, label):
    hist = {"1": {"A": old}, "2": {"A": new}}
    v = (c.squad_changes(hist, 2) or {}).get("A")
    g = (c.guardiola(hist, 2) or {}).get("A")
    items_sum = round(sum(x["ert"] for x in v["be"]) - sum(x["ert"] for x in v["ki"])
                      + sum(x["ertU"] - x["ertE"] for x in v["szerep"]) + v["bonusz"], 2)
    check(v["stimmel"] and items_sum == g["guard"] == v["guard"],
          "K5: %s - items %s, guardiola %s, tab %s"
          % (label, items_sum, g["guard"], v["guard"]))


# mixed case: transfer + role change + captain change + halving at once
RAW.update({"1": 3.25, "2": 0.75, "3": 14.25, "21": 5.25, "22": 0.25})
old = squad(BASE_IDS)
old[2]["cap"] = True
new = squad([21, 22] + BASE_IDS[2:])
new[0]["cap"] = True
new[3]["sub"] = True                       # from starter to bench
check_sum(old, new, "transfer + role change + captain change")

# bench halving with rounding (0.75 -> 0.38): this is where it would slip most easily
old2 = squad(BASE_IDS)
old2[1]["sub"] = True
new2 = squad(BASE_IDS)
new2[1]["sub"] = False
check_sum(old2, new2, "bench -> starter, with halving and rounding")

# the Hungarian rule moves too
old3 = squad(BASE_IDS)
for i in range(5):
    old3[i]["hun"] = True
old3[0]["u21"] = True
new3 = squad([21] + BASE_IDS[1:])
for i in range(1, 5):
    new3[i]["hun"] = True
check_sum(old3, new3, "the Hungarian rule bonus is lost too")

print("\n--- K6-K7: edge cases ---")
RAW.clear()
RAW.update({str(x): 5 for x in range(1, 30)})
v = one(squad(BASE_IDS), squad(BASE_IDS))
check(v and not v["ki"] and not v["be"] and not v["szerep"] and v["guard"] == 0,
      "K6: with an unchanged squad there are no items and the indicator is 0 - got: %s" % (v,))
check(c.squad_changes({"1": {"A": squad(BASE_IDS)}}, 1) is None,
      "K7: no data for the first round")
print("\n--- K8: without a breakdown the change still comes out, without points ---")
c.raw_points = lambda r: None
old8 = squad(BASE_IDS)
old8[0]["cap"] = True
new8 = squad([21] + BASE_IDS[1:])
new8[1]["sub"] = True                      # from starter to bench
v8 = (c.squad_changes({"1": {"A": old8}, "2": {"A": new8}}, 2) or {}).get("A")
check(v8 and v8["pontok"] is False and v8["guard"] is None,
      "K8: the shape without points (pontok=False, guard=None) - got: %s"
      % ((v8 and (v8["pontok"], v8["guard"])),))
check(v8 and [x["id"] for x in v8["ki"]] == [1] and [x["id"] for x in v8["be"]] == [21],
      "K8: the transfer is still visible - got: ki=%s be=%s"
      % ((v8 and [x["id"] for x in v8["ki"]]), (v8 and [x["id"] for x in v8["be"]])))
check(v8 and len(v8["szerep"]) == 1 and v8["szerep"][0]["szE"] == "kezdo"
      and v8["szerep"][0]["szU"] == "pad",
      "K8: and so is the role change - got: %s" % ((v8 and v8["szerep"]),))
check(v8 and not any("ert" in x or "nyers" in x for x in v8["ki"] + v8["be"])
      and "bonusz" not in v8,
      "K8: there is NO POINT VALUE anywhere in it (ert/nyers/bonusz)")

if failures:
    print("\n%d assertions failed." % len(failures))
    sys.exit(1)
print("\nAll %d assertions passed." % total)
