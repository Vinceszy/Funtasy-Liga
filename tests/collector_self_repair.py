#!/usr/bin/env python3
"""Test of collect.py's self-repair with a mocked API.

It checks two things:
 1. If the official points of an OLD round changed at MLSZ, the collector
    carries them into results.json AND fetches the round's squads again.
 2. If the sum computed from the squad does not match the stored official
    value, the collector fetches the official value again and writes that
    in (it does not just flag it).
"""
import importlib.util, json, os, shutil, sys, tempfile, urllib.parse

SOURCE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'collect.py')
WORKDIR = tempfile.mkdtemp()
os.chdir(WORKDIR)

spec = importlib.util.spec_from_file_location('collect', SOURCE)
c = importlib.util.module_from_spec(spec)
sys.modules['collect'] = c
spec.loader.exec_module(c)

NAMES = list(c.MEMBERS)                      # 8 managers
UNAME = {u: n for n, u in c.MEMBERS.items()}

# the "reality" in the API: round -> name -> official points
API_POINTS = {1: {n: 40.0 for n in NAMES},
              2: {n: 50.0 for n in NAMES},
              3: {n: 60.0 for n in NAMES},
              4: {n: 70.0 for n in NAMES},
              5: {n: 0.0 for n in NAMES}}
API_POINTS[2]['Bazsa'] = 55.0                # <-- a later MLSZ correction
API_POINTS[4]['Katyul'] = 77.0               # the real (corrected) value
DEFAULT_STALE = {(4, 'Katyul'): 70.0}        # the default ranking still gives the old one

SQUAD_CALLS = []                             # which rounds a squad was requested for


def squad(round_no, name):
    """15 players; their sum + the Hungarian rule bonus = the points according to the API."""
    target = API_POINTS[round_no][name] - 10  # the +10 is the Hungarian rule bonus
    players = []
    for i in range(15):
        players.append({
            "id": 1000 + i, "is_captain": False,
            "type": "starter" if i < 11 else "substitutes",
            "position": {"monogram": "H"},
            "summary_statistics": {"weekly_points": target if i == 0 else 0,
                                   "competition_points": 100},
            "competition_player": {
                "id": 500 + i, "first_name": "J%d" % i, "last_name": name,
                "is_u21": i < 2, "team": {"short_name": "XYZ"},
                "countries": [{"code": "HUN"}],
                "current_round": {"is_played": True, "market_price": 5,
                                  "first_played_at": "2026-08-01T17:00:00+02:00",
                                  "games": [{"start_at": "2026-08-01T17:00:00+02:00",
                                             "status": "completed"}]}}})
    return {"data": players}


def mock_api_get(url, retries=3):
    q = urllib.parse.urlparse(url).query
    par = urllib.parse.parse_qs(q)
    if "rankings" in url:
        uname = par["filter[search]"][0]
        name = UNAME[uname]
        rid = par.get("filter[round_id]")
        if rid:
            r = (int(rid[0]) - 75) // 2
            rounds = [x for x in (r - 1, r) if x in API_POINTS]
        else:
            rounds = [4, 5]                   # by default the last two
        def points(x):
            if not rid and (x, name) in DEFAULT_STALE:
                return DEFAULT_STALE[(x, name)]
            return API_POINTS[x][name]
        return 200, {"data": [{
            "user_team": {"user": {"id": NAMES.index(name) + 1, "username": uname},
                          "round_statistics": [
                              {"round_number": x, "points": points(x)}
                              for x in rounds]}}]}
    if "user-team-players-history" in url:
        r = (int(par["filter[round_id]"][0]) - 75) // 2
        uid = int(par["filter[user_id]"][0])
        name = NAMES[uid - 1]
        SQUAD_CALLS.append((r, name))
        return 200, squad(r, name)
    return 404, None


c.api_get = mock_api_get

# ---- starting state: round 2 has its old value, round 4 is stale for Katyul
schedule = {}
for r in range(1, 6):
    pairs = [(NAMES[0], NAMES[1]), (NAMES[2], NAMES[3]),
             (NAMES[4], NAMES[5]), (NAMES[6], NAMES[7])]
    schedule[str(r)] = [[h, v,
                         None if r == 5 else (50.0 if r == 2 else API_POINTS[r][h]),
                         None if r == 5 else (50.0 if r == 2 else API_POINTS[r][v])]
                        for h, v in pairs]
schedule["4"][0][2] = 70.0                    # Katyul's stored value is stale (70), 77 in the API
json.dump({"updated": None, "provisional": [], "schedule": schedule},
          open("results.json", "w"))
json.dump({"updated": None, "rounds": {}}, open("squad_history.json", "w"))
# a ready match list, so that filling in meccsek.json does not interfere (tested by collector_matches.py)
json.dump({"updated": None, "rounds": {str(r): [
    {"id": 900 + r, "h": "XYZ", "v": "ZZZ", "start": "2026-08-01T17:30:00+02:00",
     "hp": 1, "vp": 0, "vege": True}] for r in range(1, 9)}}, open("meccsek.json", "w"))

print("--- running the collector ---")
c.main()
print("--- checks ---")

result = json.load(open("results.json"))
sch = result["schedule"]
failures = []


def check(cond, label):
    print(("OK   " if cond else "FAIL ") + label)
    if not cond:
        failures.append(label)


bazsa2 = next(m[2] for m in sch["2"] if m[0] == 'Bazsa')
check(bazsa2 == 55.0, "the later corrected points of round 2 came through (%.1f)" % bazsa2)
check(any(r == 2 for r, _ in SQUAD_CALLS),
      "the squads of round 2 were fetched again too (the points changed)")
katyul4 = next(m[2] for m in sch["4"] if m[0] == 'Katyul')
check(katyul4 == 77.0,
      "after the mismatch found from the squad the official points were corrected (%.1f)" % katyul4)
stored = json.load(open("squad_history.json"))
check("2" in stored["rounds"] and len(stored["rounds"]["2"]) == len(NAMES),
      "the squad history of round 2 is complete")

# Does the collector write the per-round squad files, and do they match the
# full history? (The page reads from these when a match is opened.)
if os.path.isdir("keretek"):
    files = sorted(os.listdir("keretek"))
    check(len(files) == len(stored["rounds"]),
          "a squad file was written for every round (%d files)" % len(files))
    bad = []
    # the loop variable is NOT "squad": it would shadow the squad function above
    for r, squad_ in stored["rounds"].items():
        try:
            one = json.load(open(os.path.join("keretek", "%s.json" % r)))
        except Exception as e:
            bad.append("%s: %s" % (r, e)); continue
        if one.get("squads") != squad_ or one.get("round") != int(r):
            bad.append(r)
    check(not bad, "the per-round files match the history" + (" (%s)" % bad if bad else ""))
    # there is DELIBERATELY no timestamp in them: otherwise all 33 files would
    # change on every run, and the repository would grow for nothing
    one = json.load(open(os.path.join("keretek", files[0])))
    check("updated" not in one, "there is no timestamp in it (otherwise it would change on every run)")
else:
    check(False, "the collector did not write a keretek/ directory")

print("\nsquad fetches per round:",
      {r: sum(1 for x, _ in SQUAD_CALLS if x == r) for r in sorted({x for x, _ in SQUAD_CALLS})})
shutil.rmtree(WORKDIR, ignore_errors=True)
sys.exit(1 if failures else 0)
