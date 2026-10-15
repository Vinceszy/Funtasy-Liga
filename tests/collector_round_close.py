#!/usr/bin/env python3
"""Nine assertions about the collector closing a round.

R1: on the FIRST run, when there is no earlier provisional entry yet, whether
    the round is written as final after a failed squad fetch.
R2: if the round's last match is STILL IN PROGRESS, but MLSZ already gives
    is_played=true for everyone, whether the collector rates the round closed.
R3: a player who has NO match in the round (postponement) must not hold up
    the closing - otherwise the round stays provisional until the club's next
    match.
R3b: the same when the round is no longer the current one, so the match
    list is not requested - the "no match" flag comes from the stored squad.
R4: safety net - if the player-level picture does not come together, but
    MLSZ has already moved past the round, it must be closed.
R5: ...but while MLSZ says the round IS THE CURRENT one, the net must not fire.
R6: if the match list returns a match of ANOTHER round (for an old round the
    API falls back to the club's latest match), that is nogame - and the state
    of a match from another round must not hold up the closing.
R7: a squad in the old format (no "played" in it) is fetched again by the
    collector, and the filled-in record has played, id and nogame.
"""
import importlib.util, json, os, sys, tempfile, urllib.parse

SOURCE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'collect.py')
os.chdir(tempfile.mkdtemp())
spec = importlib.util.spec_from_file_location('collect', SOURCE)
c = importlib.util.module_from_spec(spec); sys.modules['collect'] = c
spec.loader.exec_module(c)

NAMES = list(c.MEMBERS); UNAME = {u: n for n, u in c.MEMBERS.items()}
CURRENT = 5
LAST = 6                        # the highest round that has data
API = {r: {n: 40.0 + r for n in NAMES} for r in range(1, LAST + 1)}
pairs = [(NAMES[0], NAMES[1]), (NAMES[2], NAMES[3]), (NAMES[4], NAMES[5]), (NAMES[6], NAMES[7])]
failures = []


def squad(r, name, status, nogame=False, games=True, match_round=None):
    """15 players; the match status can be set (scheduled = still in progress).

    nogame=True: the club has no match in the round - empty match list, and
      MLSZ gives is_played=false (measured).
    games=False: the match list was not requested (not the live round) - then
      the response has no games key at all."""
    if nogame:
        match = {"is_played": False}
        if games:
            match["games"] = []
    else:
        match = {"is_played": True}
        if games:
            match["games"] = [{"start_at": "2026-08-23T17:30:00+02:00", "status": status,
                               "round_number": "%dF" % (match_round or r)}]
    return {"data": [{
        "id": 1000 + i, "is_captain": False,
        "type": "starter" if i < 11 else "substitutes",
        "position": {"monogram": "H"},
        "summary_statistics": {"weekly_points": (API[r][name] - 10) if i == 0 else 0,
                               "competition_points": 1},
        "competition_player": {"id": 500 + i, "first_name": "J%d" % i, "last_name": name,
            "is_u21": i < 2, "team": {"short_name": "XYZ"}, "countries": [{"code": "HUN"}],
            "current_round": dict(market_price=5,
                                  first_played_at="2026-08-23T17:30:00+02:00",
                                  **match)}} for i in range(15)]}


def prepare(prov, current=CURRENT, history=None):
    schedule = {str(r): [[h, v, API[r][h], API[r][v]] for h, v in pairs] for r in range(1, current + 1)}
    json.dump({"updated": None, "provisional": prov, "schedule": schedule}, open("results.json", "w"))
    # A ready match list for every round, so that filling in meccsek.json
    # (tested separately by collector_matches.py) does not request match lists
    # for the old rounds - without it the preconditions of the scenarios here
    # would change.
    json.dump({"updated": None, "rounds": {str(r): [
        {"id": 900 + r, "h": "XYZ", "v": "ZZZ", "start": "2026-08-01T17:30:00+02:00",
         "hp": 1, "vp": 0, "vege": True}] for r in range(1, current + 1)}},
        open("meccsek.json", "w"))
    rounds = {str(r): {n: [] for n in NAMES} for r in range(1, current + 1)}
    for r, squads in (history or {}).items():
        rounds[str(r)] = squads
    json.dump({"updated": None, "rounds": rounds}, open("squad_history.json", "w"))


def run(status, fail_one, label, nogame_names=(), mlsz=None, current=CURRENT, match_round=None):
    """status: the match status; fail_one: whether one squad fetch fails;
    nogame_names: who has no match; mlsz: the current round number according
    to MLSZ (None = the competition endpoint is unreachable)."""
    def mock(url, retries=3):
        par = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        if "competitions?include=rounds" in url:
            if mlsz is None:
                return 500, None
            # the rounds' end dates: all in the past, except the current one
            rounds = [{"round_number": x, "end_at": "2026-08-%02dT10:00:00+02:00" % (10 + x)}
                      for x in range(1, LAST + 1)]
            return 200, {"data": [{"id": c.COMPETITION, "rounds": rounds,
                                   "current_round": {"round_number": mlsz}}]}
        if "rankings" in url:
            name = UNAME[par["filter[search]"][0]]
            return 200, {"data": [{"user_team": {
                "user": {"id": NAMES.index(name) + 1, "username": par["filter[search]"][0]},
                "round_statistics": [{"round_number": x, "points": API[x][name]}
                                     for x in (current - 1, current)]}}]}
        if "user-team-players-history" in url:
            r = (int(par["filter[round_id]"][0]) - 75) // 2
            name = NAMES[int(par["filter[user_id]"][0]) - 1]
            if fail_one and (name, r) == (NAMES[2], current):
                return 500, None
            return 200, squad(r, name, status, nogame=(name in nogame_names),
                              games="current_round.games" in urllib.parse.unquote(url),
                              match_round=match_round)
        return 404, None
    c.api_get = mock
    c.rounds_to_recheck = lambda old, n=4: []
    print("\n--- " + label + " ---")
    c.main()
    return json.load(open("results.json"))["provisional"]


def check(cond, ok_message, fail_message, label):
    if cond:
        print("OK   " + ok_message)
    else:
        failures.append(label); print("FAIL " + fail_message)


# ---- R1: first run, no earlier provisional yet, one fetch fails
os.chdir(tempfile.mkdtemp()); prepare([])
prov = run("scheduled", True, "R1: first run + one failed squad fetch")
print("provisional:", prov)
check(CURRENT in prov, "the live round became provisional",
      "it was written as final - the partial result goes into the table", "R1")

# ---- R2: every fetch is fine, but the match is STILL IN PROGRESS (status=scheduled)
os.chdir(tempfile.mkdtemp()); prepare([CURRENT])
prov = run("scheduled", False, "R2: every squad arrived, but the match is still in progress")
print("provisional:", prov)
check(CURRENT in prov, "the round stayed provisional while the match is in progress",
      "it was rated closed - although the match is still in progress (is_played=true)", "R2")

# ---- control: if the match is FINISHED, then it must be closed
os.chdir(tempfile.mkdtemp()); prepare([CURRENT])
prov = run("completed", False, "control: the match is finished")
print("provisional:", prov)
check(CURRENT not in prov, "after the finished match the round is closed",
      "it stayed provisional even after the finished match", "control")

# ---- R3: one manager's players have NO match (postponement)
#      The flag is written into the history for the previous round too: the
#      collector fetches that again as well, but without a match list (it is
#      not the live round).
os.chdir(tempfile.mkdtemp())
nogame_squad = {NAMES[3]: [{"name": "J%d %s" % (i, NAMES[3]), "nogame": True}
                           for i in range(15)]}
prepare([CURRENT], history={CURRENT - 1: nogame_squad})
prov = run("completed", False, "R3: the 4th manager's players have no match",
           nogame_names=(NAMES[3],))
print("provisional:", prov)
check(CURRENT not in prov, "players without a match do not hold up the closing",
      "it stayed provisional - the round would be stuck until the club's next match", "R3")

# ---- R3b: the same, but the round is no longer the current one (no match list)
#      The "no match" flag then comes only from the STORED squad.
os.chdir(tempfile.mkdtemp())
prepare([CURRENT], current=LAST, history={CURRENT: nogame_squad})
prov = run("completed", False, "R3b: old round, the nogame comes from the stored squad",
           nogame_names=(NAMES[3],), current=LAST)
print("provisional:", prov)
check(CURRENT not in prov, "the stored nogame flag also leaves the player out of the closing",
      "it stayed provisional - the stored nogame flag was lost", "R3b")

# ---- R4: the player-level picture does not come together, but MLSZ has moved on
os.chdir(tempfile.mkdtemp()); prepare([CURRENT])
prov = run("scheduled", False, "R4: match still in progress, but MLSZ is already at round 6",
           mlsz=CURRENT + 1)
print("provisional:", prov)
check(CURRENT not in prov, "the safety net closed the round",
      "it stayed provisional - the round could be stuck for good", "R4")

# ---- R5: the net must NOT fire while MLSZ says the round is the current one
os.chdir(tempfile.mkdtemp()); prepare([CURRENT])
prov = run("scheduled", False, "R5: match still in progress, MLSZ also says this is the current one",
           mlsz=CURRENT)
print("provisional:", prov)
check(CURRENT in prov, "the net did not fire on the running round",
      "it closed the running round - a half-finished result goes into the table", "R5")

# ---- R6: the match list returns a match of ANOTHER round
#      The status is deliberately "scheduled": if the match from the other
#      round were accepted, it has not even been played yet - it would hold
#      up the closing too.
os.chdir(tempfile.mkdtemp()); prepare([CURRENT])
prov = run("scheduled", False, "R6: the match list holds the club's match from another round",
           match_round=CURRENT + 3)
print("provisional:", prov)
check(CURRENT not in prov, "the match of the other round counts as nogame, and does not hold it up",
      "it stayed provisional - the state of the match from the other round misled it", "R6")

# ---- R7: filling in a squad in the old format
#      The earliest records have no "played"/"id"/"start". The collector
#      fetches such a round again, together with the match list.
os.chdir(tempfile.mkdtemp())
old_format = {n: [{"name": "J%d %s" % (i, n), "team": "XYZ", "pos": "H", "week": 0,
                   "total": 1, "hun": True, "u21": i < 2, "cap": False,
                   "sub": i >= 11, "price": 5} for i in range(15)]
              for n in NAMES}
prepare([], history={1: old_format})
run("completed", False, "R7: filling in round 1 in the old format", match_round=CURRENT)
new = json.load(open("squad_history.json"))["rounds"]["1"][NAMES[0]][0]
print("fields of the filled-in record:", sorted(new))
check("played" in new and "id" in new, "the filled-in record has played and id",
      "the round in the old format was not filled in: %s" % sorted(new), "R7")
check(new.get("nogame") is True,
      "nogame from the match list is in too (the match belonged to another round)",
      "nogame did not get into the filled-in record", "R7-nogame")

sys.exit(1 if failures else 0)
