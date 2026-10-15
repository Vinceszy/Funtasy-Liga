#!/usr/bin/env python3
"""NB1 points adjustment after the end of a match (collect.py closing_changes) - 10 assertions.

WHY IT EXISTS: by the official rules the points are determined after every
match, but the weekly total is FINAL only at the end of the round's last
matchday. In between MLSZ can still adjust - the collector applied these,
but did not keep them, although afterwards they cannot be reconstructed.

The shape of the store follows PL's zarasok.json, so that the page can use
the same display:  {manager: {"pont": [{n,cp,pos,tm,elott,utan,d}]}}

This part rarely fires in production, so the test is the ONLY place where
it is visible whether it works.
"""
import importlib.util, os, sys

SOURCE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'collect.py')
spec = importlib.util.spec_from_file_location('collect', SOURCE)
c = importlib.util.module_from_spec(spec); sys.modules['collect'] = c
spec.loader.exec_module(c)
failures = []


def check(cond, label):
    print(("OK   " if cond else "FAIL ") + label)
    if not cond:
        failures.append(label)


def pl(name, week, cp=1, finished=True, cap=False, sub=False, pos="MF", team="MTK"):
    return {"name": name, "id": cp, "week": week, "vege": finished, "cap": cap,
            "sub": sub, "pos": pos, "team": team}


def rows(t, mgr="Katyul"):
    return (t.get(mgr) or {}).get("pont") or []


TODAY = "2026-08-25"

# --- a change after a finished match: this is the news ---
t = {}
n = c.closing_changes({"Katyul": [pl("A", 5.0)]}, {"Katyul": [pl("A", 6.0)]}, t, TODAY)
check(n == 1 and rows(t) == [{"n": "A", "cp": 1, "pos": "MF", "tm": "MTK",
                              "elott": 5.0, "utan": 6.0, "d": TODAY}],
      "points changed after a finished match are recorded (%s)" % t)

# --- DURING a match it is not news: the points are still ticking ---
t = {}
n = c.closing_changes({"Katyul": [pl("A", 5.0, finished=False)]},
                      {"Katyul": [pl("A", 6.0, finished=False)]}, t, TODAY)
check(n == 0 and t == {}, "a change during the match is NOT recorded (the points are still ticking)")

# --- unchanged points are not news ---
t = {}
check(c.closing_changes({"Katyul": [pl("A", 5.0)]}, {"Katyul": [pl("A", 5.0)]}, t, TODAY) == 0
      and t == {}, "no entry is made for unchanged points")

# --- the CAPTAIN doubling is worked back: it is the same change ---
# old: starter 5.0 -> new: captain 12.0 (base points 6.0). The change is 5 -> 6,
# NOT 5 -> 12: the player's own points changed, not the multiplier of the role.
t = {}
c.closing_changes({"Katyul": [pl("A", 5.0)]}, {"Katyul": [pl("A", 12.0, cap=True)]}, t, TODAY)
s = rows(t)
check(s and s[0]["elott"] == 5.0 and s[0]["utan"] == 6.0,
      "the captain doubling is worked back (%s)" % (s[0] if s else None))

# --- and the BENCH halving too, rounded to a quarter ---
# a bench value of 0.38 = 0.75 base points (the API rounds to two decimals after halving)
t = {}
c.closing_changes({"Katyul": [pl("A", 0.38, sub=True)]},
                  {"Katyul": [pl("A", 0.5, sub=True)]}, t, TODAY)
s = rows(t)
check(s and s[0]["elott"] == 0.75 and s[0]["utan"] == 1.0,
      "the bench halving is worked back, rounded to a quarter (%s)" % (s[0] if s else None))

# --- the same player in SEVERAL squads: the row is there for every manager ---
# As on the PL panel, it is grouped by manager: everyone who had the player
# must see the change in their block.
t = {}
n = c.closing_changes({"Katyul": [pl("A", 5.0)], "Bazsa": [pl("A", 5.0)], "Csendi": [pl("A", 5.0)]},
                      {"Katyul": [pl("A", 6.0)], "Bazsa": [pl("A", 6.0)], "Csendi": [pl("A", 6.0)]},
                      t, TODAY)
check(n == 3 and sorted(t) == ["Bazsa", "Csendi", "Katyul"]
      and all(len(rows(t, m)) == 1 for m in t),
      "the same change appears for all three managers (%s)" % sorted(t))

# --- the same run twice: the dedup does not duplicate ---
c.closing_changes({"Katyul": [pl("A", 5.0)]}, {"Katyul": [pl("A", 6.0)]}, t, TODAY)
check(len(rows(t)) == 1, "the same adjustment is not recorded twice (%s)" % rows(t))

# --- but a LATER, new adjustment must not be lost ---
c.closing_changes({"Katyul": [pl("A", 6.0)]}, {"Katyul": [pl("A", 5.5)]}, t, "2026-08-26")
s = rows(t)
check(len(s) == 2 and s[1]["elott"] == 6.0 and s[1]["utan"] == 5.5,
      "the later, new adjustment is recorded too, the dedup does not swallow it (%s)" % s)

# --- missing data cannot be read as a change ---
t = {}
c.closing_changes({"Katyul": [pl("A", None)]}, {"Katyul": [pl("A", 6.0)]}, t, TODAY)
c.closing_changes({"Katyul": [pl("A", 5.0)]},
                  {"Katyul": [{"name": "A", "id": 1, "vege": True}]}, t, TODAY)
check(t == {}, "missing points count as a change in neither direction")

# --- a player transferred out: no pair, no entry ---
t = {}
c.closing_changes({"Katyul": [pl("A", 5.0, cp=1)]}, {"Katyul": [pl("B", 9.0, cp=2)]}, t, TODAY)
check(t == {}, "no change is made up for a player who is no longer in the squad")

if failures:
    print("\n%d assertions failed." % len(failures))
    sys.exit(1)
print("\nAll 10 assertions passed.")
