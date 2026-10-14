#!/usr/bin/env python3
"""ONE-OFF probe for the PL side of the player profile - round 2.

THE RESULT OF ROUND 1 (naplo/fpl-profile.txt):
  - the Draft's OWN element-summary/{id} endpoint gives a player's whole
    season in one request: per round `event`, `total_points`, every
    statistic, and a `detail` field in the form "AVL (H) 4-0";
  - the classic FPL ids do NOT match the Draft's (1 vs 14 points for one
    player), so that endpoint cannot be used.

THIS ROUND DECIDES A SINGLE QUESTION: in WHAT ORDER is the number pair of
`detail`? Two readings are possible, and for a 4-0 home win they coincide:
  (a) HOME-AWAY (as everywhere else on the site), or
  (b) THE PLAYER'S TEAM - OPPONENT.
Guessing wrong would reverse the result of every away match in the profile -
and exactly that kind of silent error is the worst kind.

The decision is not a guess: the round's matches (event/{gw}/fixtures) are
taken as authoritative - there team_h/team_a and the two scores stand in
separate fields - and the `detail` text is measured against them. AWAY,
NON-DRAWN matches are looked for specifically, because only those tell the
two readings apart.

Reads only; the workflow commits the log.
"""
import json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import collect_draft  # fetch, B

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fpl-profile.txt")
lines = []
out = lines.append

with open(os.path.join(ROOT, "draft_history.json"), encoding="utf-8") as f:
    history = json.load(f)["rounds"]
with open(os.path.join(ROOT, "draft_players.json"), encoding="utf-8") as f:
    roster = json.load(f)
CLUB = roster["teams"]                      # team id -> short name
PLAYER_NAME = roster["players"]

GW = sorted(history, key=int)[0]
elements = sorted({p["e"] for squad in history[GW].values() for p in squad})

out("# PL profile probe, round 2: the ORDER of the `detail` number pair.")
out("# Authoritative source: event/%s/fixtures (team_h, team_a, team_h_score," % GW)
out("# team_a_score in separate fields). The `detail` text is measured against it.")
out("")

st, fx = collect_draft.fetch("event/%s/fixtures" % GW)
if not isinstance(fx, list):
    out("### The fixtures could not be fetched (HTTP %s) - the probe cannot go on." % st)
    with open(LOG, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    sys.exit(0)
fixture = {m.get("id"): m for m in fx}
out("### %d matches in round %s." % (len(fx), GW))
out("")

PATTERN = re.compile(r"^\s*(\S+)\s*\((H|A)\)\s*(\d+)\s*-\s*(\d+)\s*$")
home_away = player_opponent = 0
contradictions = []
examined = 0

for e in elements:
    if examined >= 25:
        break
    st, j = collect_draft.fetch("element-summary/%d" % e)
    if not isinstance(j, dict):
        continue
    for h in (j.get("history") or []):
        if str(h.get("event")) != str(GW):
            continue
        d = (h.get("detail") or "").strip()
        m = PATTERN.match(d)
        fxr = fixture.get(h.get("fixture"))
        if not m or not fxr:
            out("=== element %-4s detail=%r fixture=%s -> NOT INTERPRETABLE"
                % (e, d, h.get("fixture")))
            continue
        opp, venue, a, b = m.group(1), m.group(2), int(m.group(3)), int(m.group(4))
        hs, vs_ = fxr.get("team_h_score"), fxr.get("team_a_score")
        home_club = CLUB.get(str(fxr.get("team_h")), "?")
        away_club = CLUB.get(str(fxr.get("team_a")), "?")
        if hs is None or vs_ is None or hs == vs_:
            continue                        # a draw does not tell them apart
        away = (venue == "A")
        if not away:
            continue                        # nor does a home match
        examined += 1
        # away match: the player's team is the AWAY team
        hv = (a == hs and b == vs_)         # (a) home-away reading
        po = (a == vs_ and b == hs)         # (b) player-opponent reading
        home_away += 1 if hv else 0
        player_opponent += 1 if po else 0
        label = "HOME-AWAY" if hv and not po else ("PLAYER-OPPONENT" if po and not hv else "?!")
        out("=== %-16s detail=%-18r | fixtures: %s %s-%s %s | opponent in the detail: %s -> %s"
            % ((PLAYER_NAME.get(str(e)) or {}).get("n", "#%d" % e), d,
               home_club, hs, vs_, away_club, opp, label))
        if not hv and not po:
            contradictions.append("element %s: detail=%r, fixtures %s-%s" % (e, d, hs, vs_))

out("")
out("### %d away, NON-drawn matches examined." % examined)
out("###   home-away reading holds:        %d" % home_away)
out("###   player-opponent reading holds:  %d" % player_opponent)
if contradictions:
    out("### NEITHER READING HOLDS for the following:")
    for x in contradictions[:10]:
        out("    " + x)
if examined == 0:
    out("### NOT ENOUGH SAMPLES - the question stays undecided.")

with open(LOG, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
print("\n".join(lines))
