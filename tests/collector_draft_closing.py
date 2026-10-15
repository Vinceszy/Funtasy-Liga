#!/usr/bin/env python3
"""The Draft collector finalising a round - four assertions.

WHY IT IS NEEDED: at the end of the round FPL makes AUTOMATIC SUBSTITUTIONS
(the first bench player who fits comes on for a starter who did not play),
and in doing so it REWRITES the pick's "position" field. Measured: this
happens at "lockdown", its signal is the "current_event_finished" field of
the game endpoint - and AT THAT POINT current_event IS STILL THE OLD ROUND.
If the collector does not fetch the round once more after closing, the squad
freezes for good in its state before the substitution.

D1: while the round is not closed (current_event_finished=false), every run
    fetches it again - even if the squad is already complete.
D2: the run after closing fetches it once more, and the state AFTER THE
    SUBSTITUTION goes in (the "b" flag is computed from the fresh position).
D3: the closed round goes into the "veglegesek" list - but while IT IS THE
    CURRENT one, it is still fetched in every run (later FPL corrections
    come through this way); only once current_event moves on is it left alone.
D4: if the fetch fails, the round is NOT marked final - otherwise the state
    before the substitution would be recorded as final.
D5: ...and not even if the STORED data is already complete from an earlier run.
D6: the CLOSING DIFFERENCE (zarasok.json) is made exactly once, in the
    finalising run: the difference between the stored snapshot before
    closing and the fresh state. The transfers (ki/be) and the points
    changes are in it; if closing changed nothing, an EMPTY entry is made
    (that is a result too). It is not made in the runs before closing, and
    it is not recomputed a second time. The collector merges the old with
    the new, so the stored state does not show whether every team came in
    NOW. This is the real case: the squad already exists from before
    closing, but the fetch after closing fails - the substitution would
    then be missing from exactly that team.
"""
import importlib.util, json, os, sys, tempfile

SOURCE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'collect_draft.py')
os.chdir(tempfile.mkdtemp())
spec = importlib.util.spec_from_file_location('collect_draft', SOURCE)
c = importlib.util.module_from_spec(spec); sys.modules['collect_draft'] = c
spec.loader.exec_module(c)

failures = []
LEAGUE_ENTRIES = [101, 102]
ENTRY = {201: 101, 202: 102}
# the 11 starters + 4 on the bench; number 11 is the starter with 0 minutes,
# number 12 is first on the bench
STARTERS = list(range(1, 12))
BENCH = [12, 13, 14, 15]

state = {"closed": False, "current": 1}
requests = []         # (gw, entry) pairs, so the fetches can be counted


def check(cond, label):
    print(("OK   " if cond else "FAIL ") + label)
    if not cond:
        failures.append(label)


def picks(substituted):
    """substituted=True: FPL has already brought number 12 on for number 11."""
    starters = STARTERS[:] if not substituted else STARTERS[:10] + [12]
    bench = BENCH[:] if not substituted else [11, 13, 14, 15]
    return ([{"element": e, "position": i + 1} for i, e in enumerate(starters)]
            + [{"element": e, "position": 12 + i} for i, e in enumerate(bench)])


def mock(path, retries=3):
    if path == "game":
        return 200, {"current_event": state["current"],
                     "current_event_finished": state["closed"]}
    if path.startswith("league/") and "details" in path:
        return 200, {"league": {"id": 1, "name": "T"},
                     "league_entries": [{"id": l, "entry_id": e, "player_first_name": "A",
                                         "player_last_name": "B", "entry_name": "C"}
                                        for e, l in ENTRY.items()],
                     "matches": [], "standings": [{"league_entry": l} for l in LEAGUE_ENTRIES]}
    if "element-status" in path:
        return 200, {"element_status": []}
    if path.startswith("bootstrap-static"):
        return 200, {"elements": [], "teams": [], "element_types": []}
    if "/live" in path:
        gw = int(path.split("/")[1])
        points = {str(e): {"stats": {"total_points": 1}} for e in range(1, 16)}
        # player 15's points change at closing (bonus correction) - this
        # measures that the closing difference notices points too
        points["15"] = {"stats": {"total_points": 5 if state["closed"] else 2}}
        return 200, {"elements": points}
    if path.startswith("entry/"):
        parts = path.split("/")
        entry, gw = int(parts[1]), int(parts[3])
        requests.append((gw, entry))
        if state.get("fail") == entry:
            return 500, None
        return 200, {"picks": picks(state["closed"])}
    return 404, None


c.fetch = mock

print("--- run 1: the round is STILL IN PROGRESS ---")
c.main()
h = json.load(open("draft_history.json"))
check(len(h["rounds"].get("1") or {}) == 2, "the squads of round 1 are in")
check(not h.get("veglegesek"), "D1: the round in progress is NOT final: " + repr(h.get("veglegesek")))
bench_e = {x["e"] for x in h["rounds"]["1"]["101"] if x["b"]}
check(bench_e == set(BENCH), "the bench is the state BEFORE the substitution: " + repr(sorted(bench_e)))

print("\n--- run 2: still in progress, the squad is already complete ---")
requests.clear()
c.main()
check(len(requests) == 2,
      "D1: the unclosed round is fetched again even with a complete squad (%d requests)" % len(requests))

print("\n--- run 3: LOCKDOWN, FPL has made the substitution ---")
state["closed"] = True
requests.clear()
c.main()
h = json.load(open("draft_history.json"))
bench_e = {x["e"] for x in h["rounds"]["1"]["101"] if x["b"]}
check(len(requests) == 2, "after closing it is fetched once more (%d requests)" % len(requests))
check(bench_e == {11, 13, 14, 15},
      "D2: the state AFTER THE SUBSTITUTION is in - the 0-minute starter to the bench: "
      + repr(sorted(bench_e)))
check(h.get("veglegesek") == [1], "D3: the round is in the veglegesek list: " + repr(h.get("veglegesek")))

z = json.load(open("zarasok.json"))
z1 = z["rounds"].get("1") or {}
check("1" in z["rounds"], "D6: the closing entry was made in the finalising run")
affected = next(iter(z1.values())) if z1 else {}
# the ki/be items have the shape {e, pts}: the incoming player's POINTS tell
# what the substitution brought (and the outgoing one's, why it happened)
check([x["e"] for x in affected.get("ki") or []] == [11]
      and [x["e"] for x in affected.get("be") or []] == [12],
      "D6: the substitution is in it (ki=11, be=12): " + repr(affected))
check(all("pts" in x for x in (affected.get("ki") or []) + (affected.get("be") or [])),
      "D6: the substitution items carry the points too")
points_d6 = affected.get("pont") or []
check(any(x["e"] == 15 and x["elott"] == 2 and x["utan"] == 5 for x in points_d6),
      "D6: the points change is in it too (number 15: 2 -> 5): " + repr(points_d6))

print("\n--- run 4: closed, BUT STILL CURRENT round ---")
requests.clear()
c.main()
check(len(requests) == 2,
      "D3: while the round is the current one, it is fetched after closing too - this is how "
      "a later FPL correction comes through (%d requests)" % len(requests))

z_before = json.dumps(json.load(open("zarasok.json"))["rounds"], sort_keys=True)

print("\n--- run 5: current_event has moved on ---")
state["current"] = 2
state["closed"] = False         # round 2 is already in progress
requests.clear()
c.main()
first = [x for x in requests if x[0] == 1]
check(not first, "D3: the closed round that is NO longer current is not requested any more (%d requests)"
      % len(first))
check([x for x in requests if x[0] == 2], "but round 2 is")
check(json.dumps(json.load(open("zarasok.json"))["rounds"], sort_keys=True) == z_before,
      "D6: the closing entry is not recomputed a second time")

print("\n--- case 6: one of the fetches fails at closing (empty history) ---")
os.chdir(tempfile.mkdtemp())
state["current"] = 1
state["closed"] = True
state["fail"] = 202
c.main()
h = json.load(open("draft_history.json"))
check(not h.get("veglegesek"),
      "D4: after an incomplete fetch it is NOT marked final: " + repr(h.get("veglegesek")))

print("\n--- case 7: the STORED data is already complete, but the closing fetch fails ---")
os.chdir(tempfile.mkdtemp())
state["current"] = 1
state["closed"] = False
state["fail"] = None
c.main()                                   # first run: complete squad, before the substitution
h = json.load(open("draft_history.json"))
check(len(h["rounds"]["1"]) == 2 and not h.get("veglegesek"),
      "the complete state BEFORE the substitution exists")
state["closed"] = True                     # lockdown...
state["fail"] = 202                        # ...but one of the fetches fails
c.main()
h = json.load(open("draft_history.json"))
bench_e = {x["e"] for x in h["rounds"]["1"]["102"] if x["b"]}
check(bench_e == set(BENCH),
      "for team 102 the substitution did NOT come in (the fetch failed): " + repr(sorted(bench_e)))
check(not h.get("veglegesek"),
      "D5: complete stored data + incomplete current fetch -> NOT finalised: "
      + repr(h.get("veglegesek")))

if failures:
    print("\n%d assertions failed." % len(failures)); sys.exit(1)
print("\nAll nineteen assertions passed.")
