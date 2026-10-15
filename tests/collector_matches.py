#!/usr/bin/env python3
"""The collector's match collection (meccsek.json) - five assertions.

M1: the matches travelling in the squad responses go into meccsek.json per
    round, merged by id, sorted by kick-off.
M2: A RESULT ONLY FROM A FINISHED MATCH: the score of a match still in
    progress is not stored even if the API already sends it - the collector
    running every 3 hours would immortalise a partial score as final.
M3: a match falling back from a LATER round is left out (when an old round is
    fetched, the API falls back to the club's next match).
M9: a RESCHEDULED match (from an earlier round, played NOW) however IS
    INCLUDED, and the club does NOT get a "no match" flag. Measured: MLSZ's
    round 7 had ETO-FTC marked "3F" (the postponed round 3 match), plus
    ETO-HONVED "7F" - the collector flagged all nine ETO players as
    `nogame`, because it only looked at the FIRST item of the list, and its
    round number did not match.
M10: with SEVERAL MATCHES, `start` is the nearest match NOT YET FINISHED, and
    `vege` is true only when ALL of them are finished - until then the
    player's points can change.
M4: the collector fetches a missing round again with the match list (filling
    it in), but once every match is in with a final result, NOT ANY MORE - the
    games response of a closed round is large (it comes with club logos), it
    is not requested for nothing.
M5: a round with a match in progress goes with the match list in the next
    run too, so that the final result gets in.
M6: RESCHEDULED MATCH. The postponed match is not in the list (it is not
    "without a result"), so the condition of M4 would not notice it being
    made up. But when it is played, the round's official points change - in
    that case the collector fetches the round again with the match list, and
    the rescheduled match gets in.
"""
import importlib.util, json, os, sys, tempfile, urllib.parse

SOURCE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'collect.py')
os.chdir(tempfile.mkdtemp())
spec = importlib.util.spec_from_file_location('collect', SOURCE)
c = importlib.util.module_from_spec(spec); sys.modules['collect'] = c
spec.loader.exec_module(c)

NAMES = list(c.MEMBERS)
CURRENT = 2
API = {r: {n: 40.0 + r for n in NAMES} for r in (1, 2)}
pairs = [(NAMES[i], NAMES[i + 1]) for i in range(0, len(NAMES) - 1, 2)]
failures = []


total = 0


def check(cond, label):
    global total
    total += 1
    print(("OK   " if cond else "FAIL ") + label)
    if not cond:
        failures.append(label)


def match(mid, h, v, status, r, hp=None, vp=None):
    g = {"id": mid, "start_at": "2026-08-%02dT17:30:00+02:00" % (10 + mid % 20),
         "status": status, "round_number": "%dF" % r,
         "home_team": {"short_name": h}, "away_team": {"short_name": v}}
    # the trap of M2: the match in progress gets a score TOO - it must not be stored
    g["home_score"], g["away_score"] = (hp if hp is not None else 1), (vp if vp is not None else 1)
    return g


# round -> which match comes in the response per player. The two clubs of
# round 1 give two finished matches (from different players, overlapping -
# the dedup is measured here); in round 2 (live) there is one finished and one
# match still in progress, plus a match falling back from ANOTHER round (M3).
MATCHES = {
    1: [match(11, "AAA", "BBB", "completed", 1, 3, 1),
        match(12, "CCC", "DDD", "completed", 1, 0, 0)],
    2: [match(21, "AAA", "CCC", "completed", 2, 2, 2),
        match(22, "BBB", "DDD", "in_progress", 2),
        match(99, "EEE", "FFF", "completed", 1)],   # falling back: 1F inside round 2
}
player_requests = []
team_requests = []    # (round, whether the two clubs were requested explicitly)


def squad(r, games):
    data = []
    for i in range(15):
        crd = {"is_played": True, "market_price": 5,
               "first_played_at": "2026-08-10T17:30:00+02:00"}
        if games:
            # the matches spread among the players, with overlap (dedup!)
            crd["games"] = [MATCHES[r][i % len(MATCHES[r])]]
        data.append({"id": 1000 + i, "is_captain": False, "type": "starter",
            "position": {"monogram": "H"},
            "summary_statistics": {"weekly_points": 1, "competition_points": 1},
            "competition_player": {"id": 500 + i, "first_name": "J%d" % i,
                "last_name": "X", "is_u21": False, "team": {"short_name": "AAA"},
                "countries": [], "current_round": crd}})
    return {"data": data}


def mock(url, retries=3):
    par = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
    if "competitions?include=rounds" in url:
        return 200, {"data": [{"id": c.COMPETITION, "rounds": [],
                               "current_round": {"round_number": CURRENT}}]}
    if "rankings" in url:
        uname = par["filter[search]"][0]
        real = {u: n for n, u in c.MEMBERS.items()}[uname]
        return 200, {"data": [{"user_team": {
            "user": {"id": NAMES.index(real) + 1, "username": uname},
            "round_statistics": [{"round_number": x, "points": API[x][real]} for x in (1, 2)]}}]}
    if "user-team-players-history" in url:
        r = (int(par["filter[round_id]"][0]) - 75) // 2
        full = urllib.parse.unquote(url)
        games = "current_round.games" in full
        player_requests.append((r, games))
        if games:
            team_requests.append((r, "games.home_team" in full
                                     and "games.away_team" in full))
        return 200, squad(r, games)
    return 404, None


c.api_get = mock
c.rounds_to_recheck = lambda old, n=4: []

schedule = {str(r): [[h, v, API[r][h], API[r][v]] for h, v in pairs] for r in (1, 2)}
json.dump({"updated": None, "provisional": [], "schedule": schedule}, open("results.json", "w"))
json.dump({"updated": None, "rounds": {}}, open("squad_history.json", "w"))

print("--- run 1: empty meccsek.json ---")
c.main()
m = json.load(open("meccsek.json"))

r1 = m["rounds"].get("1") or []
check(len(r1) == 2 and [x["id"] for x in r1] == [11, 12],
      "M1: the two matches of round 1 merged by id, sorted by kick-off")
check(all(x.get("vege") and "hp" in x for x in r1)
      and r1[0]["h"] == "AAA" and r1[0]["hp"] == 3 and r1[0]["vp"] == 1,
      "M1: the finished match has the two clubs and the result")
check(any(x["hp"] == 0 and x["vp"] == 0 and x.get("vege") for x in r1),
      "M1: a FINISHED 0-0 is included - that is the real result, not a placeholder")

r2 = m["rounds"].get("2") or []
running = next((x for x in r2 if x["id"] == 22), None)
check(running is not None and "hp" not in running and "vege" not in running,
      "M2: the match in progress has no result, even though the API sends one")
check(all(x["id"] != 99 for x in r2), "M3: the match falling back from another round was left out")

print("\n--- run 2: round 1 is complete, round 2 has a match in progress ---")
player_requests.clear()
c.main()
first_with_games = [r for r, g in player_requests if g and r == 1]
second_with_games = [r for r, g in player_requests if g and r == 2]
check(not first_with_games,
      "M4: no more (large) fetch with the match list for the already complete round 1")
check(len(second_with_games) > 0,
      "M5: round 2 with a match in progress still goes with the match list")

print("\n--- M6: rescheduled match (the official points change) ---")
# round 1 is complete and every match is finished -> by M4 it would not be
# fetched again. But now MLSZ gives different points for it: that is the
# signal of the rescheduled match.
MATCHES[1].append(match(13, "EEE", "FFF", "completed", 1, 1, 0))
API[1] = {n: 55.0 for n in NAMES}
player_requests.clear()
c.main()
m = json.load(open("meccsek.json"))
first_with_games = [r for r, g in player_requests if g and r == 1]
check(first_with_games, "M6: the round with changed points is fetched again with the match list")
check(any(x["id"] == 13 for x in m["rounds"].get("1") or []),
      "M6: the rescheduled match got in: " + repr([x["id"] for x in m["rounds"]["1"]]))

print("\n--- M7: the fetch with the match list requests the two clubs EXPLICITLY ---")
# MEASURED (naplo/mlsz-live-match.txt): in a live round the match object comes
# WITHOUT the clubs, unless the two teams are requested separately. Without
# it meccsek.json stores "?", and the profile shows a dash in place of the
# opponent.
check(team_requests and all(k for _, k in team_requests),
      "M7: every fetch with the match list requests home_team and away_team"
      + ("" if not team_requests else " (%d requests)" % len(team_requests)))

print("\n--- M8: a match with '?' clubs counts as incomplete too ---")
# If EVERY match of a round is finished, but the club names stayed "?", the
# old condition would have seen it as complete: it drops out of the rounds to
# re-request, and once MLSZ moves on it would never be fetched again - the "?"
# would be stuck for good.
m = json.load(open("meccsek.json"))
m["rounds"]["1"] = [{"id": 11, "h": "?", "v": "?", "start": "2026-08-11T17:30:00+02:00",
                     "hp": 3, "vp": 1, "vege": True}]
json.dump(m, open("meccsek.json", "w"))
player_requests.clear()
c.main()
check([r for r, g in player_requests if g and r == 1],
      "M8: round 1 with '?' clubs is fetched again with the match list")
m = json.load(open("meccsek.json"))
check(all(x.get("h") != "?" and x.get("v") != "?" for x in m["rounds"].get("1") or []),
      "M8: after the new request a real club name stands in place of the '?': "
      + repr([(x.get("h"), x.get("v")) for x in m["rounds"].get("1") or []]))

print()
print("--- M9-M10: rescheduled match (a club has TWO matches in the round) ---")
# The shape of the measurement: the FIRST item of the list is the rescheduled
# match from an earlier round, the second is the round's own match.
RESCHEDULED = {"id": 431, "start_at": "2026-09-03T19:30:00+02:00",
               "status": "scheduled", "round_number": "3F",
               "home_team": {"short_name": "ETO"}, "away_team": {"short_name": "FTC"}}
OWN = {"id": 9, "start_at": "2026-09-06T20:00:00+02:00",
       "status": "scheduled", "round_number": "7F",
       "home_team": {"short_name": "ETO"}, "away_team": {"short_name": "HONVÉD"}}
fields = c.game_fields({"games": [RESCHEDULED, OWN]}, 7)
check(not fields.get("nogame"),
      "M9: the club does NOT get a 'no match' flag - got: %s" % fields)
check(fields.get("start") == RESCHEDULED["start_at"],
      "M10: `start` is the nearest match not yet finished (the rescheduled one) - got: %s"
      % fields.get("start"))
fields2 = c.game_fields({"games": [dict(RESCHEDULED, status="completed"), OWN]}, 7)
check(fields2.get("start") == OWN["start_at"] and not fields2.get("vege"),
      "M10: after the rescheduled one it points to the NEXT match, and there is no 'vege' yet - got: %s"
      % fields2)
fields3 = c.game_fields({"games": [dict(RESCHEDULED, status="completed"),
                                   dict(OWN, status="completed")]}, 7)
check(fields3.get("vege") is True,
      "M10: 'vege' only once BOTH are finished - got: %s" % fields3)
# the fallback still drops out: it belongs to a LATER round
later = {"id": 77, "start_at": "2026-09-20T18:00:00+02:00",
         "status": "scheduled", "round_number": "9F"}
check(c.game_fields({"games": [later]}, 3).get("nogame") is True,
      "M3: a match from a LATER round (falling back) is still 'no match'")
store = {}
c.collect_matches({"data": [{"competition_player":
                             {"current_round": {"games": [RESCHEDULED, OWN]}}}]}, 7, store)
check(sorted(store) == [9, 431],
      "M9: the rescheduled match gets into meccsek.json too - got: %s" % sorted(store))

print()
print("--- M11: the match list fetched NOW overrides the old flag ---")
# MEASURED: after the fix for rescheduled matches the collector correctly said
# that the club HAS a match - but the `nogame` inherited from the previous run
# restored the error. The fix would have BLOCKED ITSELF.
old = {"A": [{"name": "J1", "nogame": True, "start": None, "vege": True}]}
new = {"A": [{"name": "J1", "start": "2026-09-03T19:30:00+02:00"}]}
c.inherit_match_flags(old, new, inherit=False)
check(not new["A"][0].get("nogame") and new["A"][0]["start"],
      "M11: with a fresh match list the old 'nogame' does NOT stick - got: %s" % new["A"][0])
new2 = {"A": [{"name": "J1", "start": "2026-09-03T19:30:00+02:00"}]}
c.inherit_match_flags(old, new2, inherit=True)
check(new2["A"][0].get("nogame") is True and new2["A"][0]["start"] is None,
      "M11: WITHOUT a match list however it is still inherited - got: %s" % new2["A"][0])

if failures:
    print("\n%d assertions failed." % len(failures)); sys.exit(1)
print("\nAll %d assertions passed." % total)
