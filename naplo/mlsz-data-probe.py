#!/usr/bin/env python3
"""ONE-OFF probe: what does the MLSZ API give from which the NB1 could get the
data that already works on the PL side (minutes played, whether he started,
match result)?

Four questions, each deciding whether to build it in - NOTHING is claimed
UNTIL then:

  1) Does the match object in a CLOSED round's squad response carry a RESULT
     (and opponent)? According to the collector's docstring, for a finished
     match the API also includes the two teams (response 17->118 KB) - but
     the score field has never been looked at. If it is there, the score
     line above the breakdown can be built for the NB1 too.
  2) Does the game-player-stats endpoint work with ONLY a round_id filter
     (no player)? If so, the minutes played come in one request for ALL the
     round's players -> they can be a column in the squad list. If not, the
     minutes can stay only in the drop-down (where they are today).
  3) Is there "did he start" data anywhere? The full name list of the stat
     config and ALL raw rows of one player (the nought-point ones too) are
     printed.
  4) The full key list of the current_round object - in case there is a
     field not used so far (e.g. a starter flag).

The functions of collect.py are imported (api_get, squad, MEMBERS, rankings),
not copied. Reads only; the workflow commits the log.

PRIVACY: the repository is public. No MLSZ user_id goes into the log (the
user names are in the repository anyway, but the id is not written either);
the footballers' names are public data. Base64 image data (club logo) is cut.

Environment: PROBE_ROUND (a closed round, default 1).
"""
import json, os, sys, urllib.parse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import collect  # api_get, squad, MEMBERS, rankings, rid, ROOT

LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mlsz-data.txt")
R = int(os.environ.get("PROBE_ROUND", "1"))       # a closed round
lines = []
out = lines.append


def shorten(v, limit=160):
    """Cuts a long value (base64 logo!), keeps the structure."""
    if isinstance(v, str) and len(v) > limit:
        return "<text of %d characters>" % len(v)
    if isinstance(v, dict):
        return {k: shorten(x, limit) for k, x in v.items()}
    if isinstance(v, list):
        return [shorten(x, limit) for x in v[:4]] + (["<+%d items>" % (len(v) - 4)] if len(v) > 4 else [])
    return v


def dump(title, obj):
    out("--- %s ---" % title)
    out(json.dumps(shorten(obj), ensure_ascii=False, indent=1))


# ---- one participant's user_id (in memory only, never in the log) ----
uid = None
for name, uname in collect.MEMBERS.items():
    row = collect.rankings(uname)
    if row:
        uid = ((row.get("user_team") or {}).get("user") or {}).get("id")
        if uid:
            break
if not uid:
    out("! no participant available - the rankings did not answer")

# ---- 1+4) squad of a closed round with the match list ----
if uid:
    st, j = collect.squad(uid, R, with_games=True)
    out("=== 1) squad response for round %d (with match list) -> HTTP %s" % (R, st))
    found_match = found_cr = False
    for d in (j or {}).get("data") or []:
        cp = d.get("competition_player") or {}
        cr = cp.get("current_round") or {}
        games = cr.get("games") or []
        if not found_cr and cr:
            out("=== 4) ALL keys of current_round: %s" % sorted(cr.keys()))
            found_cr = True
        if not found_match and games:
            pname = " ".join(x for x in (cp.get("first_name"), cp.get("last_name")) if x)
            out("    (the match at player %s)" % pname)
            dump("FULL content of the match object", games[0])
            found_match = True
        if found_match and found_cr:
            break
    if not found_match:
        out("! no player has a match list in the response")

# ---- 2) game-player-stats bulk query - SECOND ROUND ----
# The first probe showed: the round-only query WORKS (200), but the row has no
# player id, and it pages by 50 rows. Now what a column would need is measured:
# (a) whether include=competition_player adds the player, (b) whether the stat
# filter works (only the "Jatszott perc" rows), (c) whether there is paging
# control, (d) whether the nought-point players are in the bulk response.
rid_ = collect.rid(R)
# the config id of "Jatszott perc" from the rows of a SCORING player
# (the player is taken from the stored squad, not a hard-coded id)
minutes_conf = None
try:
    with open(os.path.join(os.path.dirname(LOG), "..", "squad_history.json"), encoding="utf-8") as f:
        _hist = json.load(f)
    _candidate = next(p for sq in (_hist["rounds"].get(str(R)) or {}).values()
                      for p in sq if p.get("id") and (p.get("week") or 0) > 0)
except Exception as e:
    _candidate = None
    out("! no candidate player for the config id: %s" % e)
st, j = collect.api_get(collect.ROOT + "game-player-stats?include=competition_stat_config"
                        + "&filter%%5Bround_id%%5D=%d&filter%%5Bcompetition_player_id%%5D=%s"
                        % (rid_, _candidate["id"] if _candidate else 0))
for s2 in (j or {}).get("data") or []:
    cfg = s2.get("competition_stat_config") or {}
    if cfg.get("name") == "Játszott perc":
        minutes_conf = cfg.get("id")
out("=== 2) the 'Jatszott perc' stat-config id: %s" % minutes_conf)
attempts = [
    ("round + player include",
     "game-player-stats?include=competition_stat_config,competition_player"
     "&filter%%5Bround_id%%5D=%d" % rid_),
    ("round + stat filter",
     "game-player-stats?include=competition_player"
     "&filter%%5Bround_id%%5D=%d&filter%%5Bcompetition_stat_config_id%%5D=%s" % (rid_, minutes_conf)),
    ("round + stat filter + large page",
     "game-player-stats?include=competition_player"
     "&filter%%5Bround_id%%5D=%d&filter%%5Bcompetition_stat_config_id%%5D=%s"
     "&page%%5Bsize%%5D=500" % (rid_, minutes_conf)),
    ("round + stat filter + page 2",
     "game-player-stats?include=competition_player"
     "&filter%%5Bround_id%%5D=%d&filter%%5Bcompetition_stat_config_id%%5D=%s"
     "&page%%5Bnumber%%5D=2" % (rid_, minutes_conf)),
]
for label, path in attempts:
    st, j = collect.api_get(collect.ROOT + path)
    data = (j or {}).get("data") or [] if isinstance(j, dict) else []
    out("=== 2) %s -> HTTP %s, rows: %s" % (label, st, len(data)))
    if st == 200 and data:
        dump("first row", data[0])
        # paging information from the top of the response (meta/links, if any)
        for k in ("meta", "links"):
            if isinstance(j, dict) and k in j:
                dump("the response's '%s' field" % k, j[k])
        # whether the nought-point players are in: how many DIFFERENT players are on the page
        players = set()
        for s2 in data:
            cp = s2.get("competition_player") or {}
            if cp.get("id"):
                players.add((cp.get("id"), cp.get("last_name")))
        out("    different players on the page: %d %s" % (len(players), sorted(players)[:6]))

# ---- 3) ALL raw rows of a player with many minutes and one with none ----
try:
    with open(os.path.join(os.path.dirname(LOG), "..", "squad_history.json"), encoding="utf-8") as f:
        hist = json.load(f)
    squads = hist["rounds"].get(str(R)) or {}
    candidates = []
    for sq in squads.values():
        for p in sq:
            if p.get("id"):
                candidates.append(p)
    many_minutes = next((p for p in candidates if (p.get("week") or 0) > 0), None)
    zero = next((p for p in candidates if not p.get("week")), None)
except Exception as e:
    many_minutes = zero = None
    out("! squad_history not readable: %s" % e)

stat_names = set()
for p in (many_minutes, zero):
    if not p:
        continue
    url = (collect.ROOT + "game-player-stats?include=competition_stat_config"
           + "&filter%%5Bcompetition_player_id%%5D=%s&filter%%5Bround_id%%5D=%d"
           % (p["id"], collect.rid(R)))
    st, j = collect.api_get(url)
    out("=== 3) %s (%s, %s points) -> HTTP %s" % (p.get("name"), p.get("team"), p.get("week"), st))
    for s in (j or {}).get("data") or []:
        sname = (s.get("competition_stat_config") or {}).get("name") or "?"
        stat_names.add(sname)
        out("    %-45s value=%-6s points=%s" % (sname, s.get("value"), s.get("points")))

out("=== stat names in total: %s" % sorted(stat_names))

with open(LOG, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
print("\n".join(lines))
