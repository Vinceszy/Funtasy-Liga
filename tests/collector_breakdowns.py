#!/usr/bin/env python3
"""Saving the itemised breakdown of closed rounds (collect.py collect_breakdowns).

WHY IT EXISTS: the breakdown used to be fetched only by the browser, on a
click, with a live MLSZ call - if the API or the proxy did not answer, the
drop-down showed an error. The breakdown of a closed round never changes,
though, so it can be fetched once and kept. This part runs ONCE per round,
so the test is the only place where it is visible whether it works.
"""
import importlib.util, json, os, sys, tempfile

SOURCE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'collect.py')
os.chdir(tempfile.mkdtemp())
spec = importlib.util.spec_from_file_location('collect', SOURCE)
c = importlib.util.module_from_spec(spec); sys.modules['collect'] = c
spec.loader.exec_module(c)
failures = []


def check(cond, label):
    print(("OK   " if cond else "FAIL ") + label)
    if not cond:
        failures.append(label)


ROSTER = {str(1000 + i): {"n": "J%d" % i} for i in range(12)}
FAILING = set()       # the API returns an error for these cps
CALLS = []


def mock(url, retries=3):
    CALLS.append(url)
    if "game-player-stats" not in url:
        return 404, None
    cp = url.split("competition_player_id%5D=")[1].split("&")[0]
    if cp in FAILING:
        return 500, None
    return 200, {"data": [
        {"value": 90, "points": 0, "competition_stat_config": {"name": "Játszott perc"}},
        {"value": 1, "points": 5, "competition_stat_config": {"name": "Gól"}}]}


c.api_get = mock

# --- 1. a file is written for a closed round, not for an open one ---
c.collect_breakdowns([1], set(), ROSTER)
check(os.path.exists("bontasok/1.json"), "a file is written for the closed round")
check(not os.path.exists("bontasok/2.json"), "NO file for the round still in progress")

# --- which round counts as closed? It is decided from the STORED state ---
# (not from the run's `closed` dict - that only knows the rounds fetched in
# this run, so on introduction only the last one would have got a file)
SCHEDULE = {"1": [["A", "B", 50.0, 40.0]], "2": [["A", "B", 60.0, 55.0]],
            "3": [["A", "B", None, None]]}
check(c.closed_rounds(SCHEDULE, []) == [1, 2],
      "closed: every match has a result (%s)" % c.closed_rounds(SCHEDULE, []))
check(c.closed_rounds(SCHEDULE, [2]) == [1],
      "a provisional round is NOT closed (%s)" % c.closed_rounds(SCHEDULE, [2]))

j = json.load(open("bontasok/1.json", encoding="utf-8"))
check(j.get("round") == 1 and len(j.get("bontasok") or {}) == len(ROSTER),
      "the breakdown of all %d players is in" % len(ROSTER))
check(j["bontasok"]["1000"] == [{"n": "Játszott perc", "v": 90, "p": 0},
                                {"n": "Gól", "v": 1, "p": 5}],
      "the rows have the expected shape (n/v/p): %s" % j["bontasok"]["1000"][:1])

# --- ZERO rows are not stored, the minutes row is ---
# MLSZ returns all 22 stat rows, the zero ones too: with 385 players that is
# 141 KB per round. The page shows only the rows worth points + "Jatszott
# perc" (the message is decided from that too).
RAW = [{"n": "Gólok", "v": 1, "p": 5}, {"n": "Sárga lap", "v": 0, "p": 0},
       {"n": "Játszott perc", "v": 90, "p": 0},
       {"n": "Passzpontosság", "v": 0.59, "p": 0}]
check(c.filter_breakdown(RAW) == [{"n": "Gólok", "v": 1, "p": 5},
                                  {"n": "Játszott perc", "v": 90, "p": 0}],
      "the 0-point rows are dropped, Játszott perc stays (%s)"
      % [x["n"] for x in c.filter_breakdown(RAW)])
check(c.filter_breakdown([]) == [], "an empty breakdown stays empty")
check("updated" not in j,
      "there is no timestamp in it (otherwise it would be rewritten on every run)")

# --- 2. the second time it does NOT fetch again ---
CALLS.clear()
c.collect_breakdowns([1], set(), ROSTER)
check(not CALLS, "with an existing file there is not a single request (%d)" % len(CALLS))

# --- 3. but if the round's result CHANGED, it fetches again ---
CALLS.clear()
c.collect_breakdowns([1], {1}, ROSTER)
check(len(CALLS) == len(ROSTER),
      "after an MLSZ correction the whole round is fetched again (%d requests)" % len(CALLS))

# --- 4. an incomplete run does NOT write a half-finished file ---
os.chdir(tempfile.mkdtemp())
FAILING.update(list(ROSTER)[:5])      # 5/12 fail - more than 10%
c.collect_breakdowns([1], set(), ROSTER)
check(not os.path.exists("bontasok/1.json"),
      "with many failed requests the file is NOT written (the next run retries)")

# --- 5. but a few errors are tolerated ---
FAILING.clear(); FAILING.add(list(ROSTER)[0])   # 1/12 - under the threshold
c.collect_breakdowns([1], set(), ROSTER)
check(os.path.exists("bontasok/1.json"), "one or two failed requests do not block the write")
j = json.load(open("bontasok/1.json", encoding="utf-8"))
check(len(j["bontasok"]) == len(ROSTER) - 1,
      "the failed player is left out, the rest are in (%d/%d)"
      % (len(j["bontasok"]), len(ROSTER)))

# --- 6. an empty breakdown is stored too (it is not a missing one!) ---
os.chdir(tempfile.mkdtemp())
FAILING.clear()
c.api_get = lambda url, retries=3: (200, {"data": []}) if "game-player-stats" in url else (404, None)
c.collect_breakdowns([1], set(), ROSTER)
j = json.load(open("bontasok/1.json", encoding="utf-8"))
check(j["bontasok"].get("1000") == [],
      "a player without points is stored with an EMPTY list - that differs from a missing one")

if failures:
    print("\n%d assertions failed." % len(failures))
    sys.exit(1)
print("\nAll %d assertions passed." % 14)
