#!/usr/bin/env python3
"""ONE-OFF probe - round 7: does the MLSZ have a FULL SCHEDULE?

The player profile lists the rounds ahead as well, and the NEXT OPPONENT has
to show there (only the points stay empty until there are any). Today
meccsek.json knows only the rounds the collector has already been through -
the future is empty.

The question: is there an endpoint that gives the matches of a round (or of
the whole season), whether played or not. If so, the collector fetches the
lot once, and the profile shows the opponent ahead as well.

Fallback plan if there is none: the squad endpoint RETURNS the
`competition_player.current_round.games` list per round - that can be
requested for future rounds too, one request per round.

Reads only; the workflow commits the log.
"""
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import collect

LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mlsz-player-list.txt")
lines = []
out = lines.append


def shorten(v, limit=140):
    if isinstance(v, str) and len(v) > limit:
        return "<text of %d characters>" % len(v)
    if isinstance(v, dict):
        return {k: shorten(x, limit) for k, x in v.items()}
    if isinstance(v, list):
        return [shorten(x, limit) for x in v[:3]] + (["<+%d items>" % (len(v) - 3)] if len(v) > 3 else [])
    return v


FUTURE = 8                                  # a round not played yet
RID = collect.rid(FUTURE)
out("# ROUND 12: does the MLSZ have a full schedule (future matches)?")
out("# The profile lists the rounds ahead as well - the OPPONENT has to show")
out("# there, only the points are empty. Today meccsek.json knows only the rounds already seen.")
out("# Test round: %d. (round_id=%d)" % (FUTURE, RID))
out("")

out("## 1) standalone match endpoints")
for label, path in [
    ("games?filter[round_id]", "games?filter%%5Bround_id%%5D=%d" % RID),
    ("competitions/N/games", "competitions/%d/games?filter%%5Bround_id%%5D=%d" % (collect.COMPETITION, RID)),
    ("competitions/N/games (no filter)", "competitions/%d/games" % collect.COMPETITION),
    ("matches?filter[round_id]", "matches?filter%%5Bround_id%%5D=%d" % RID),
    ("fixtures?filter[round_id]", "fixtures?filter%%5Bround_id%%5D=%d" % RID),
    ("competitions/N/rounds", "competitions/%d/rounds" % collect.COMPETITION),
    ("competitions/N/rounds + games", "competitions/%d/rounds?include=games" % collect.COMPETITION),
]:
    st, j = collect.api_get(collect.ROOT + path)
    if not isinstance(j, dict):
        out("=== %-38s -> HTTP %s" % (label, st))
        continue
    data = j.get("data")
    n = len(data) if isinstance(data, list) else ("dict" if data else 0)
    meta = j.get("meta") or {}
    out("=== %-38s -> HTTP %s | data: %s | total=%s" % (label, st, n, meta.get("total")))
    if data:
        sample = data[0] if isinstance(data, list) else data
        out("    keys: %s" % sorted(sample.keys()))
        out("    %s" % json.dumps(shorten(sample), ensure_ascii=False)[:600])

# ---- 2) The player data sheet EXISTS, but gives no opponent ----
# competitions/3/players/{id}: root-level fields (no "data" wrapper!), with
# `countries` (the Hungarian flag), `extended_summary_statistics`, and a
# `rounds` list with the PRICE per round - but rounds gives only the 6 rounds
# so far, and there is NO opponent in it. So the interface's "Kovetkezo
# merkozesek" table comes from somewhere else: probably from the TEAM's matches.
out("")
out("## 2) The team's matches - the team_id is already known from the player data sheet")
CP = 1115
st, j = collect.api_get(collect.ROOT + "competitions/%d/players/%d" % (collect.COMPETITION, CP))
team = ((j or {}).get("team") or {}) if isinstance(j, dict) else {}
tid = team.get("id")
out("=== the player's club: %s (id=%s)" % (team.get("short_name"), tid))
if tid:
    for label, path in [
        ("teams/{id}", "competitions/%d/teams/%d" % (collect.COMPETITION, tid)),
        ("teams/{id}/games", "competitions/%d/teams/%d/games" % (collect.COMPETITION, tid)),
        ("teams/{id} + games", "competitions/%d/teams/%d?include=games" % (collect.COMPETITION, tid)),
        ("teams/{id} + rounds", "competitions/%d/teams/%d?include=rounds" % (collect.COMPETITION, tid)),
        ("games?filter[team_id]", "games?filter%%5Bteam_id%%5D=%d" % tid),
        ("competitions/N/games?team", "competitions/%d/games?filter%%5Bteam_id%%5D=%d" % (collect.COMPETITION, tid)),
        ("teams/{id} (root)", "teams/%d" % tid),
        ("teams/{id}/next-games (root)", "teams/%d/next-games" % tid),
    ]:
        st2, j2 = collect.api_get(collect.ROOT + path)
        if not isinstance(j2, dict):
            out("=== %-32s -> HTTP %s" % (label, st2))
            continue
        out("=== %-32s -> HTTP %s | root keys: %s" % (label, st2, sorted(j2.keys())))
        for k, v in sorted(j2.items()):
            if isinstance(v, list) and v:
                out("    %s: %d items, first: %s" % (k, len(v),
                    json.dumps(shorten(v[0], 200), ensure_ascii=False)[:500]))
        d = j2.get("data")
        if isinstance(d, list) and d:
            out("    data[0]: %s" % json.dumps(shorten(d[0], 200), ensure_ascii=False)[:500])

out("")
out("### If this does not give it either, the future opponent can only be found")
out("### by reverse-engineering the frontend bundle - that is a separate decision.")

with open(LOG, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
print("\n".join(lines))
