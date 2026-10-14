#!/usr/bin/env python3
"""ONE-OFF probe: what does the MLSZ send when a club has TWO matches in one
fantasy round?

THE ERROR UNDER EXAMINATION: the MLSZ fantasy's round 7 is NOT only match day
7 - it also holds a POSTPONED, rescheduled match (Fradi-Gyor, 3 Sept). The
collector does not know this: round 7 of meccsek.json knows six matches
(4-6 Sept), not the one on 3 Sept at all, and ALL NINE ETO players were
marked `nogame: True` - so according to the collector ETO has NO match in
the round, when it has TWO.

THE SUSPICION in the code (collect.py, the per-round game fields function):
the function looks only at `games[0]`, and if its round_number is not the
round asked for, it says "no match" at once. If the rescheduled match carries
the number of its ORIGINAL round (e.g. "2F") and stands at the head of the
list, ALL the club's other matches are lost.

BUT NOTHING IS CLAIMED UNTIL IT IS MEASURED. Questions:

  A) How many items are in an ETO player's current_round.games list, and
     what are each item's round_number / start_at / status values?
  B) The same for an FTC player (the other club concerned).
  C) The same for a player of a club NOT concerned (control: is there one
     item there).
  D) What does the CURRENT game-fields function say for these responses?
  E) Does the rescheduled match carry the two clubs (home_team/away_team),
     and is it in the list at all?

Reads only; the workflow commits the log.

PRIVACY: the repository is public. No MLSZ user_id goes into the log;
base64 image data is cut.

Environment: PROBE_ROUND (default: the MLSZ's current round, else 7).
"""
import json, os, sys, urllib.parse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import collect

LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mlsz-double-match.txt")
lines = []
out = lines.append


def shorten(v, limit=80):
    if isinstance(v, dict):
        return {k: shorten(x, limit) for k, x in v.items()}
    if isinstance(v, list):
        return [shorten(x, limit) for x in v]
    if isinstance(v, str) and len(v) > limit:
        return "<text of %d characters>" % len(v)
    return v


current, _ = collect.competition_rounds()
R = int(os.environ.get("PROBE_ROUND") or current or 7)
out("=== PROBE: club with TWO matches in one round - round %s ===" % R)
out("(current round according to the MLSZ: %s)" % current)

ids = {}
for name, uname in collect.MEMBERS.items():
    row = collect.rankings(uname)
    uid = (((row or {}).get("user_team") or {}).get("user") or {}).get("id")
    if uid:
        ids[name] = uid
out("participants reached: %d / %d" % (len(ids), len(collect.MEMBERS)))
if not ids:
    out("! the rankings did not answer - the probe cannot run")
    open(LOG, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    raise SystemExit(0)

GAMES = collect.GAMES
inc = (collect.INCLUDE + "," + GAMES + "," + GAMES + ".home_team,"
       + GAMES + ".away_team")

# Every participant's squad is gone through, and one player is chosen per club.
club_sample = {}         # short club name -> (player name, games list)
for name, uid in ids.items():
    st, j = collect.api_get(
        collect.BASE + "user-team-players-history?include=" + urllib.parse.quote(inc)
        + "&filter%5Buser_id%5D=" + str(uid)
        + "&filter%5Bround_id%5D=" + str(collect.rid(R)))
    if st != 200 or not j:
        continue
    for d in (j.get("data") or []):
        cp = d.get("competition_player") or {}
        team = (cp.get("team") or {}).get("short_name") or ""
        cr = cp.get("current_round") or {}
        if team and team not in club_sample:
            club_sample[team] = (cp.get("last_name") or "?", cr.get("games"))

out("")
out("=== A-C) the current_round.games list per club ===")
for team in sorted(club_sample):
    pname, games = club_sample[team]
    if games is None:
        out("%-8s %-22s games: NONE (the field did not come back)" % (team, pname))
        continue
    out("%-8s %-22s games: %d items" % (team, pname, len(games)))
    for g in games:
        g = g or {}
        h = (g.get("home_team") or {}).get("short_name") or "?"
        v = (g.get("away_team") or {}).get("short_name") or "?"
        out("           round_number=%-6s start=%-26s status=%-12s %s - %s"
            % (g.get("round_number"), g.get("start_at"), g.get("status"), h, v))
    # D) what the current logic says
    out("           CURRENT game_fields(round=%s) -> %s"
        % (R, collect.game_fields({"games": games}, R)))

out("")
out("=== E) is there a match on 3 Sept in ANY club's list? ===")
found = []
for team, (pname, games) in club_sample.items():
    for g in (games or []):
        s = (g or {}).get("start_at") or ""
        if s[:10] == "2026-09-03":
            found.append((team, shorten(g)))
if found:
    for team, g in found:
        out("%s: %s" % (team, json.dumps(g, ensure_ascii=False)))
else:
    out("NO match on 3 Sept in any club's list.")

out("")
out("=== CONCLUSION ===")
several = [t for t, (_, g) in club_sample.items() if g and len(g) > 1]
out("clubs with several matches in the list: %s" % (", ".join(sorted(several)) or "none"))
nogame = [t for t, (_, g) in club_sample.items()
          if g is not None and collect.game_fields({"games": g}, R).get("nogame")]
out("'no match' according to the current logic: %s" % (", ".join(sorted(nogame)) or "none"))

open(LOG, "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("\n".join(lines))
