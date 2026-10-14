#!/usr/bin/env python3
"""ONE-OFF probe: can the TWO CLUBS of a LIVE round's match be obtained?

THE ERROR UNDER EXAMINATION: in round 6 the profile row shows "-" in place
of the opponent, although the result is known. Cause: in a live round the
match object of the squad response comes WITHOUT clubs, so "?" goes into
meccsek.json (for all six matches). In a closed round the two teams' full
objects come too - which is why rounds 1-5, downloaded already closed, were
fine.

The question: is there a way to have the two clubs LIVE as well? NOTHING is
claimed UNTIL it is measured. Five questions:

  A) What does the match object contain TODAY, in a live round? (full key
     list)
  B) Do the two teams come if they are requested EXPLICITLY in the include?
     The repository's own experience is that the MLSZ returns some embedded
     fields only on explicit request - current_round itself behaved exactly
     like that in a live round (2026-08-21). Three include forms are tried,
     and the response size is measured too (the closed round's 118 KB comes
     from the base64 club logo).
  C) Is there a SEPARATE match endpoint for the id already known? The
     schedule endpoints were all measured on 2026-08-25 (all 404), but there
     the FUTURE schedule was looked for, as a list - fetching ONE SPECIFIC
     match was not among them.
  D) Can it be derived from our own data? The same match comes with the
     players of BOTH clubs, and every player record carries his own club. If
     there is an owned player on both sides, the two clubs are known - but
     NOT the home/away side. How many matches that would cover is measured.
  E) Does the points breakdown endpoint (game-player-stats) know about the
     match? That call is made for the drop-down anyway, so if it knows, it
     is free.

Reads only; the workflow commits the log.

PRIVACY: the repository is public. No MLSZ user_id goes into the log;
base64 image data is cut.

Environment: PROBE_ROUND (default: the MLSZ's current round, else 6).
"""
import json, os, sys, urllib.parse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import collect

LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mlsz-live-match.txt")
lines = []
out = lines.append


def shorten(v, limit=120):
    if isinstance(v, dict):
        return {k: shorten(x, limit) for k, x in v.items()}
    if isinstance(v, list):
        return [shorten(x, limit) for x in v[:3]]
    if isinstance(v, str) and len(v) > limit:
        return "<text of %d characters>" % len(v)
    return v


def fetch(url):
    """(HTTP, json, size) - the size is estimated from the raw response."""
    st, j = collect.api_get(url)
    size = len(json.dumps(j)) if j is not None else 0
    return st, j, size


# ---- which round is live now? ----
current, _ = collect.competition_rounds()
R = int(os.environ.get("PROBE_ROUND") or current or 6)
out("=== PROBE: live round = %s. (current according to the MLSZ: %s) ===" % (R, current))

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

one_uid = next(iter(ids.values()))

# ---- A) TODAY's match object ----
out("")
out("=== A) live round match object with the CURRENT include ===")
st, j, size = fetch(collect.BASE + "user-team-players-history?include="
                    + urllib.parse.quote(collect.INCLUDE
                        + ",competition_player.current_round.games")
                    + "&filter%5Buser_id%5D=" + str(one_uid)
                    + "&filter%5Bround_id%5D=" + str(collect.rid(R)))
out("HTTP %s, response ~%.1f KB" % (st, size / 1024))
sample_id = None
for d in (j or {}).get("data") or []:
    cr = (d.get("competition_player") or {}).get("current_round") or {}
    for g in cr.get("games") or []:
        if isinstance(g, dict):
            out("ALL keys of the match object: %s" % sorted(g.keys()))
            out(json.dumps(shorten(g), ensure_ascii=False, indent=1))
            sample_id = g.get("id")
            break
    if sample_id:
        break
if not sample_id:
    out("! not a single match object came back")

# ---- B) explicit team include ----
out("")
out("=== B) do the two teams come if requested EXPLICITLY? ===")
G = "competition_player.current_round.games"
for label, extra in [
        ("games.home_team + games.away_team", G + ".home_team," + G + ".away_team"),
        ("games.homeTeam + games.awayTeam", G + ".homeTeam," + G + ".awayTeam"),
        ("games.teams", G + ".teams")]:
    st, j, size = fetch(collect.BASE + "user-team-players-history?include="
                        + urllib.parse.quote(collect.INCLUDE + "," + G + "," + extra)
                        + "&filter%5Buser_id%5D=" + str(one_uid)
                        + "&filter%5Bround_id%5D=" + str(collect.rid(R)))
    present = set()
    for d in (j or {}).get("data") or []:
        cr = (d.get("competition_player") or {}).get("current_round") or {}
        for g in cr.get("games") or []:
            if isinstance(g, dict):
                present |= {k for k in g.keys() if "team" in k.lower()}
    out("  %-34s HTTP %-4s ~%6.1f KB  team fields: %s"
        % (label, st, size / 1024, sorted(present) or "NONE"))

# ---- B2) WHAT is in the team object? (the name is taken from it) ----
out("")
out("=== B2) the team object of the working include: what is in it? ===")
st, j, size = fetch(collect.BASE + "user-team-players-history?include="
                    + urllib.parse.quote(collect.INCLUDE + "," + G
                        + "," + G + ".home_team," + G + ".away_team")
                    + "&filter%5Buser_id%5D=" + str(one_uid)
                    + "&filter%5Bround_id%5D=" + str(collect.rid(R)))
out("HTTP %s, response ~%.1f KB" % (st, size / 1024))
printed = False
for d in (j or {}).get("data") or []:
    cr = (d.get("competition_player") or {}).get("current_round") or {}
    for g in cr.get("games") or []:
        if isinstance(g, dict) and g.get("home_team") and not printed:
            out("the FULL match object (base64 cut):")
            out(json.dumps(shorten(g), ensure_ascii=False, indent=1))
            ht = g.get("home_team") or {}
            out("home_team keys: %s" % sorted(ht.keys()))
            out("is there a logo (it inflated the closed round's response to 118 KB)? %s"
                % ("YES" if ht.get("logo") else "no"))
            out("short_name=%r  name=%r" % (ht.get("short_name"), ht.get("name")))
            printed = True
    if printed:
        break
if not printed:
    out("! no match came with a team object")

# ---- C) a separate match endpoint for the id already known ----
out("")
out("=== C) is there a SEPARATE endpoint for one specific match? (id=%s) ===" % sample_id)
if sample_id:
    for path in ["games/%s", "game/%s", "matches/%s", "match/%s", "fixtures/%s"]:
        for prefix, name in ((collect.ROOT, "root"), (collect.BASE, "competitions/3")):
            u = prefix + (path % sample_id)
            st, j, size = fetch(u)
            out("  %-14s %-22s HTTP %-4s %s"
                % (name, path % sample_id, st,
                   ("~%.1f KB" % (size / 1024)) if st == 200 else ""))
            if st == 200 and j:
                out(json.dumps(shorten(j), ensure_ascii=False, indent=1)[:1200])

# ---- D) can the two clubs be derived from our own squads? ----
out("")
out("=== D) deriving the two clubs from the clubs of the owned players ===")
match_clubs = {}
for name, uid in ids.items():
    st, j = collect.squad(uid, R, with_games=True)
    if st != 200 or not isinstance(j, dict):
        continue
    for d in j.get("data") or []:
        cp = d.get("competition_player") or {}
        club = ((cp.get("team") or {}).get("short_name")
                or (cp.get("team") or {}).get("name"))
        cr = cp.get("current_round") or {}
        for g in cr.get("games") or []:
            if isinstance(g, dict) and g.get("id") is not None and club:
                match_clubs.setdefault(g["id"], set()).add(club)
out("matches we know about: %d" % len(match_clubs))
both = 0
for gid, clubs in sorted(match_clubs.items()):
    if len(clubs) >= 2:
        both += 1
    out("  %s: %s" % (gid, " + ".join(sorted(clubs))))
out("BOTH sides known: in %d / %d matches" % (both, len(match_clubs)))
out("(the home/away side does NOT follow from this)")

# ---- E) does the points breakdown endpoint know the match? ----
out("")
out("=== E) does the game-player-stats response know a match? ===")
cp_id = None
st, j = collect.squad(one_uid, R, with_games=False)
for d in (j or {}).get("data") or []:
    cp_id = (d.get("competition_player") or {}).get("id")
    if cp_id:
        break
if cp_id:
    for inc in ["competition_stat_config", "competition_stat_config,game",
                "competition_stat_config,game.home_team,game.away_team"]:
        u = (collect.ROOT + "game-player-stats?include=" + urllib.parse.quote(inc)
             + "&filter%5Bcompetition_player_id%5D=" + str(cp_id)
             + "&filter%5Bround_id%5D=" + str(collect.rid(R)))
        st, j, size = fetch(u)
        keys = set()
        for s in (j or {}).get("data") or []:
            keys |= set(s.keys())
        out("  include=%-48s HTTP %-4s keys: %s" % (inc, st, sorted(keys)))

open(LOG, "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("\n".join(lines))
