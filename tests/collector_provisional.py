#!/usr/bin/env python3
"""A round that is already final must not become provisional from an incomplete run.

Since the rolling check, an old round can also be among the squad fetches (if
MLSZ made a correction). If a single squad request fails there, the round
would be "not closed" - and rated provisional it would DROP OUT of the table.

At the end of the file (C3) it is also checked that with unchanged data
results.json is not rewritten at all - every other output file works this way.
"""
import importlib.util, json, os, sys, tempfile, urllib.parse

SOURCE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'collect.py')
os.chdir(tempfile.mkdtemp())
spec = importlib.util.spec_from_file_location('collect', SOURCE)
c = importlib.util.module_from_spec(spec); sys.modules['collect'] = c
spec.loader.exec_module(c)

NAMES = list(c.MEMBERS); UNAME = {u: n for n, u in c.MEMBERS.items()}
CURRENT = 5
API = {r: {n: 40.0 + r for n in NAMES} for r in range(1, CURRENT + 1)}
API[2]['Bazsa'] = 99.0                      # a later MLSZ correction in round 2
FAILING = ('Csongi', 2)                     # this squad fetch runs into an error


def squad(r, name):
    target = API[r][name] - 10
    return {"data": [{
        "id": 1000 + i, "is_captain": False,
        "type": "starter" if i < 11 else "substitutes",
        "position": {"monogram": "H"},
        "summary_statistics": {"weekly_points": target if i == 0 else 0, "competition_points": 1},
        "competition_player": {"id": 500 + i, "first_name": "J%d" % i, "last_name": name,
            "is_u21": i < 2, "team": {"short_name": "XYZ"}, "countries": [{"code": "HUN"}],
            "current_round": {"is_played": True, "market_price": 5,
                              "first_played_at": "2026-08-01T17:00:00+02:00"}}} for i in range(15)]}


def mock(url, retries=3):
    par = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
    if "rankings" in url:
        name = UNAME[par["filter[search]"][0]]
        rid = par.get("filter[round_id]")
        rr = [x for x in ((int(rid[0]) - 75) // 2 - 1, (int(rid[0]) - 75) // 2) if x in API] \
             if rid else [CURRENT - 1, CURRENT]
        return 200, {"data": [{"user_team": {"user": {"id": NAMES.index(name) + 1, "username": par["filter[search]"][0]},
            "round_statistics": [{"round_number": x, "points": API[x][name]} for x in rr]}}]}
    if "user-team-players-history" in url:
        r = (int(par["filter[round_id]"][0]) - 75) // 2
        name = NAMES[int(par["filter[user_id]"][0]) - 1]
        if (name, r) == FAILING:
            return 500, None                # <-- this is where the fetch fails
        return 200, squad(r, name)
    return 404, None


c.api_get = mock
c.rounds_to_recheck = lambda old, n=4: [2] if 2 in old else []   # round 2 is the one checked

pairs = [(NAMES[0], NAMES[1]), (NAMES[2], NAMES[3]), (NAMES[4], NAMES[5]), (NAMES[6], NAMES[7])]
schedule = {str(r): [[h, v, API[r][h] if r != 2 else 50.0, API[r][v] if r != 2 else 50.0]
                     for h, v in pairs] for r in range(1, CURRENT + 1)}
json.dump({"updated": None, "provisional": [], "schedule": schedule}, open("results.json", "w"))
# the squad history is already complete for every round, so that only the `changed` branch brings in round 2
history = {str(r): {n: [] for n in NAMES} for r in range(1, CURRENT + 1)}
json.dump({"updated": None, "rounds": history}, open("squad_history.json", "w"))
# a ready match list, so that filling in meccsek.json does not interfere (tested by collector_matches.py)
json.dump({"updated": None, "rounds": {str(r): [
    {"id": 900 + r, "h": "XYZ", "v": "ZZZ", "start": "2026-08-01T17:30:00+02:00",
     "hp": 1, "vp": 0, "vege": True}] for r in range(1, 9)}}, open("meccsek.json", "w"))

print("--- collector ---")
c.main()
print("--- checks ---")
prov = json.load(open("results.json"))["provisional"]
print("provisional:", prov)
failures = []
if 2 in prov:
    failures.append("round 2 became provisional because of a failed squad fetch")
    print("FAIL round 2 became provisional because of a failed squad fetch")
else:
    print("OK   the long-closed round 2 did NOT become provisional (despite the squad fetch error)")
bazsa2 = next(m[2] for m in json.load(open("results.json"))["schedule"]["2"] if m[0] == 'Bazsa')
print(("OK   " if bazsa2 == 99.0 else "FAIL ") + "the correction still came through (%.1f)" % bazsa2)
if bazsa2 != 99.0: failures.append("correction")


# ---------------------------------------------------------------- C1
# If the squads of the LIVE round cannot be fetched at all, the earlier
# provisional flag MUST STAY. Otherwise provisional empties, and the live
# round's partial result counts into the table as final.
print("\n--- C1: the squads of the live round do not arrive at all ---")
os.chdir(tempfile.mkdtemp())
json.dump({"updated": None, "provisional": [CURRENT], "schedule": schedule},
          open("results.json", "w"))
json.dump({"updated": None, "rounds": history}, open("squad_history.json", "w"))


def mock2(url, retries=3):
    if "user-team-players-history" in url:
        return 500, None            # EVERY squad fetch fails
    return mock(url, retries)


c.api_get = mock2
c.rounds_to_recheck = lambda old, n=4: []
c.main()
prov2 = json.load(open("results.json"))["provisional"]
print("provisional:", prov2)
if CURRENT in prov2:
    print("OK   the live round stayed provisional (the partial result does not count)")
else:
    failures.append("C1: provisional emptied")
    print("FAIL provisional emptied - the partial result would count as final")

# ---------------------------------------------------------------- C2
# MEASURED: because of a DNS error ONE member's ranking data (and so their
# id) did not arrive -> every target round became "incomplete", and the round
# current-1, already published as final, became provisional: the table showed
# the standings after 4 rounds. The rule: what has already been published as
# final cannot be reopened by an incomplete run.
print("\n--- C2: one member's id does not arrive (network error) ---")
os.chdir(tempfile.mkdtemp())
json.dump({"updated": None, "provisional": [CURRENT], "schedule": schedule},
          open("results.json", "w"))
json.dump({"updated": None, "rounds": history}, open("squad_history.json", "w"))
json.dump({"updated": None, "rounds": {str(r): [
    {"id": 900 + r, "h": "XYZ", "v": "ZZZ", "start": "2026-08-01T17:30:00+02:00",
     "hp": 1, "vp": 0, "vege": True}] for r in range(1, 9)}}, open("meccsek.json", "w"))


def mock3(url, retries=3):
    if "rankings" in url:
        par3 = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        if UNAME[par3["filter[search]"][0]] == NAMES[0]:
            return 500, None            # <-- the network error
    return mock(url, retries)


c.api_get = mock3
c.rounds_to_recheck = lambda old, n=4: []
c.main()
prov3 = json.load(open("results.json"))["provisional"]
print("provisional:", prov3)
if CURRENT - 1 in prov3:
    failures.append("C2: the already final round reopened from a network error")
    print("FAIL round %d, already published as final, became provisional" % (CURRENT - 1))
else:
    print("OK   round %d, already published as final, stayed final" % (CURRENT - 1))
if CURRENT not in prov3:
    failures.append("C2: the live round dropped out of the provisional ones")
    print("FAIL the live round dropped out of the provisional ones")
else:
    print("OK   the live round is still provisional")


# ---------------------------------------------------------------- C3
# results.json may only be rewritten if something REALLY changed.
# MEASURED: the condition compared a list with a set
# (`provisional != old_prov`), which is never equal - so every run rewrote
# the file with a fresh timestamp. In 30 of the last 36 results.json commits
# ONLY the `updated` field changed. (Every other file compares content.)
print("\n--- C3: with unchanged data results.json is not rewritten ---")
os.chdir(tempfile.mkdtemp())
json.dump({"updated": None, "provisional": [], "schedule": schedule},
          open("results.json", "w"))
json.dump({"updated": None, "rounds": history}, open("squad_history.json", "w"))
json.dump({"updated": None, "rounds": {str(r): [
    {"id": 900 + r, "h": "XYZ", "v": "ZZZ", "start": "2026-08-01T17:30:00+02:00",
     "hp": 1, "vp": 0, "vege": True}] for r in range(1, 9)}}, open("meccsek.json", "w"))

# Every result is already in the schedule, and the correction of round 2 is
# not needed here either: the FIRST run sets the final state, the SECOND run
# must not write anything any more.
c.api_get = mock
c.rounds_to_recheck = lambda old, n=4: []
# The timestamp has SECOND precision: two consecutive runs would write the
# same text, and the test would pass even if the file were rewritten. So the
# stamp is replaced by a counter - this way every write SHOWS.
original_stamp, counter = c.stamp, [0]
def counter_stamp():
    counter[0] += 1
    return "WRITE-%d" % counter[0]
c.stamp = counter_stamp
c.main()


def snapshot():
    """The content of EVERY output file - not just results.json.

    The "only if changed" logic is written separately per file (sometimes
    from a counter, sometimes from a dump comparison, sometimes from a flag),
    and exactly this scattering hid the results.json bug. So the test does
    not look at one file, but at ALL of them: any new output is included
    automatically."""
    snap = {}
    for dirpath, _, files in os.walk("."):
        for f in files:
            if not f.endswith(".json"):
                continue
            path = os.path.join(dirpath, f)
            snap[path] = open(path, encoding="utf-8").read()
    return snap


first = snapshot()
c.main()
second = snapshot()
c.stamp = original_stamp
changed = sorted(k for k in first if first[k] != second.get(k))
new_files = sorted(k for k in second if k not in first)
if not changed and not new_files:
    print("OK   the second, unchanged run did not rewrite A SINGLE output file (%d files)"
          % len(first))
else:
    failures.append("C3: an unchanged run rewrote files too")
    print("FAIL the unchanged run rewrote: %s%s"
          % (", ".join(changed), (" | new: " + ", ".join(new_files)) if new_files else ""))
    for k in changed:
        for a, b in zip(first[k].splitlines(), second[k].splitlines()):
            if a != b:
                print("     %s\n     - %s\n     + %s" % (k, a[:90], b[:90]))
                break


# ---------------------------------------------------------------- C4
# The correction of an OLD round must not rewrite squads.json: it only holds
# the squad of the LAST round. The conditional branch of the write is opened
# by a change of the full history - that is, of any round -, and so the file
# went into the repository with a new timestamp and unchanged content. (2 of
# its last 14 changes were like that.)
print("\n--- C4: the correction of an old round does not rewrite squads.json ---")
os.chdir(tempfile.mkdtemp())
json.dump({"updated": None, "provisional": [], "schedule": schedule}, open("results.json", "w"))
json.dump({"updated": None, "rounds": history}, open("squad_history.json", "w"))
json.dump({"updated": None, "rounds": {str(r): [
    {"id": 900 + r, "h": "XYZ", "v": "ZZZ", "start": "2026-08-01T17:30:00+02:00",
     "hp": 1, "vp": 0, "vege": True}] for r in range(1, 9)}}, open("meccsek.json", "w"))
c.api_get = mock
c.rounds_to_recheck = lambda old, n=4: []
c.stamp = counter_stamp
c.main()                                     # run 1: everything is built
sq_before = open("squads.json", encoding="utf-8").read()
sh_before = open("squad_history.json", encoding="utf-8").read()

# now comes the correction of the OLD round (2)
API[2]['Csongi'] = API[2]['Csongi'] + 3.0
c.rounds_to_recheck = lambda old, n=4: [2]
c.main()
c.stamp = original_stamp
sq_after = open("squads.json", encoding="utf-8").read()
sh_after = open("squad_history.json", encoding="utf-8").read()
if sh_before == sh_after:
    failures.append("C4: the correction did not even reach the squad history")
    print("FAIL the correction of round 2 did not appear in squad_history.json")
else:
    print("OK   the correction of the old round reached the squad history")
if sq_before == sq_after:
    print("OK   squads.json (last round) stayed unchanged")
else:
    failures.append("C4: squads.json was rewritten by the correction of an old round")
    print("FAIL squads.json was rewritten, although the squad of the last round did not change")
    print("     - %s\n     + %s" % (sq_before[:110], sq_after[:110]))

sys.exit(1 if failures else 0)
