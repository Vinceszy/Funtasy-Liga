#!/usr/bin/env python3
"""Colour for one Premier League gameweek, as facts rather than prose.

The probe established that FotMob carries the manner of every shot. This
script turns that into the raw material a round summary is written from:
for every fixture of a gameweek, the goals with their minute and how they
were struck, the saves, the VAR moments and the big chances that were not
taken.

It matches OUR gameweek (the fantasy side) to real fixtures through the
FPL fixture list, then those to FotMob's day list by club name. Every
unmatched fixture is reported loudly: a silent gap here would become a
summary that talks about a match that is not there.

Writes naplo/pl-colour-<event>.json and prints a readable digest. The
gameweek comes from the environment, not from an argument:

    HARVEST_EVENT=5 python3 naplo/pl-colour-harvest.py
"""
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.request

AGENT = "FunTasy-harvest (github.com/Vinceszy/Funtasy-Liga)"
HERE = os.path.dirname(os.path.abspath(__file__))
EVENT = os.environ.get("HARVEST_EVENT") or "4"
BIG_XG = 0.3


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": AGENT, "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:300]
    except Exception as e:                                   # noqa: BLE001
        return 0, ("%s: %s" % (type(e).__name__, e)).encode()


def js(url):
    c, b = fetch(url)
    if c != 200:
        return c, None
    try:
        return c, json.loads(b)
    except Exception:                                        # noqa: BLE001
        return c, None


# FPL's own abbreviations are mapped to FotMob's full names. Doing it the other
# way round - cutting the words "united"/"city"/"hotspur" out - loses exactly
# the four best-known clubs ("Man Utd" vs "Manchester United"). An
# abbreviation table is needed, not word stripping.
ALIAS = {
    "manutd": "manchesterunited", "manunited": "manchesterunited",
    "mancity": "manchestercity",
    "spurs": "tottenhamhotspur",
    "nottmforest": "nottinghamforest", "nottsforest": "nottinghamforest",
    "wolves": "wolverhamptonwanderers",
    "sheffieldutd": "sheffieldunited",
}


def club_key(name):
    """A club name for comparison: no accents, no punctuation, lower case.
       No word is cut out of it - that is what lost the matches."""
    n = unicodedata.normalize("NFKD", name or "")
    n = "".join(c for c in n if not unicodedata.combining(c)).lower()
    n = re.sub(r"[^a-z]", "", n)
    return ALIAS.get(n, n)


def same_club(a, b):
    """Whether two club names are the same. The two sources write the same
       club at different lengths, and the extra part is not always at the END:
       "Brighton" / "Brighton & Hove Albion", but "Bournemouth" / "AFC
       Bournemouth". So the shorter one has to occur ANYWHERE in the longer
       one - with at least five letters, otherwise "man" would match anything."""
    if not a or not b:
        return False
    if a == b:
        return True
    short, long_ = (a, b) if len(a) <= len(b) else (b, a)
    return len(short) >= 5 and short in long_


def main():
    lines = []
    def out(s=""):
        lines.append(s)
        print(s)

    out("=" * 70)
    out("HARVEST: %s UTC | Premier League colour, gameweek %s" % (
        time.strftime("%Y-%m-%d %H:%M"), EVENT))

    c, boot = js("https://fantasy.premierleague.com/api/bootstrap-static/")
    if not boot:
        out("  bootstrap-static: HTTP %s - stopping" % c)
        return 1
    clubs = {t["id"]: t["name"] for t in boot.get("teams", [])}
    out("  clubs: %d" % len(clubs))

    c, fx = js("https://fantasy.premierleague.com/api/fixtures/?event=" + EVENT)
    if not fx:
        out("  fixtures: HTTP %s - stopping" % c)
        return 1
    out("  matches of gameweek %s: %d" % (EVENT, len(fx)))
    days = sorted({(f.get("kickoff_time") or "")[:10] for f in fx if f.get("kickoff_time")})
    out("  match days: %s" % ", ".join(days))

    # FotMob day lists, only for the days needed
    fm = {}
    for d in days:
        c, j = js("https://www.fotmob.com/api/data/matches?date=" + d.replace("-", ""))
        if not j:
            out("  fotmob %s: HTTP %s" % (d, c))
            continue
        pl = [lg for lg in j.get("leagues", [])
              if lg.get("ccode") == "ENG" and lg.get("name") == "Premier League"]
        count = 0
        for lg in pl:
            for m in lg.get("matches", []):
                h = (m.get("home") or {}).get("name")
                v = (m.get("away") or {}).get("name")
                fm[str(m.get("id"))] = (club_key(h), club_key(v), h, v)
                count += 1
        out("  fotmob %s: %d PL matches" % (d, count))

    result = {}
    missing = []
    for f in fx:
        h, v = clubs.get(f.get("team_h")), clubs.get(f.get("team_a"))
        mid = None
        for fm_id, (fh, fv, nh, nv) in fm.items():
            if same_club(club_key(h), fh) and same_club(club_key(v), fv):
                mid = fm_id
                break
        if not mid:
            # The gap is PRINTED together with the names on the other side:
            # without it an outdated abbreviation table would silently drop
            # a match.
            missing.append("%s - %s (key: %s / %s)" % (h, v, club_key(h), club_key(v)))
            continue
        c, j = js("https://www.fotmob.com/api/data/matchDetails?matchId=" + mid)
        if not j:
            missing.append("%s - %s (matchDetails HTTP %s)" % (h, v, c))
            continue
        content = j.get("content") or {}
        ev = ((content.get("matchFacts") or {}).get("events") or {}).get("events") or []
        sm = content.get("shotmap") or {}
        shot_list = sm.get("shots") if isinstance(sm, dict) else []
        shot_list = shot_list if isinstance(shot_list, list) else []

        # a goal is tied to its shot through the minute + player pair
        shots = {}
        for x in shot_list:
            shots.setdefault((x.get("min"), x.get("playerName")), x)

        goals, var = [], []
        for e in ev:
            if e.get("type") == "Goal":
                p = (e.get("player") or {}).get("name")
                l = shots.get((e.get("time"), p)) or {}
                goals.append({
                    "minute": e.get("timeStr") if isinstance(e.get("timeStr"), str) else e.get("time"),
                    "player": p,
                    "assist": e.get("assistStr"),
                    "description": e.get("goalDescription"),
                    "manner": l.get("shotType"),
                    "situation": l.get("situation"),
                    "own_goal": bool(l.get("isOwnGoal")),
                    "xG": round(l["expectedGoals"], 3) if l.get("expectedGoals") else None,
                })
            elif e.get("type") == "VAR":
                var.append({"minute": e.get("time"),
                            "player": (e.get("player") or {}).get("name"),
                            "decision": e.get("nameStr") or e.get("reactKey")})

        missed = [{"minute": x.get("min"), "player": x.get("playerName"),
                   "xG": round(x.get("expectedGoals") or 0, 3),
                   "manner": x.get("shotType"), "situation": x.get("situation"),
                   "on_target": bool(x.get("isOnTarget"))}
                  for x in shot_list
                  if (x.get("expectedGoals") or 0) >= BIG_XG
                  and str(x.get("eventType")) != "Goal"]
        saves = {}
        for x in shot_list:
            if str(x.get("eventType")) == "AttemptSaved" and not x.get("isBlocked"):
                saves[str(x.get("keeperId"))] = saves.get(str(x.get("keeperId")), 0) + 1

        result["%s - %s" % (h, v)] = {
            # Without the kick-off the goal minutes are mere decoration: only
            # with it can they go on a common timeline, and only with it can
            # a turn in the score be computed from them.
            "kickoff": f.get("kickoff_time"),
            "fotmob": mid, "goals": goals, "var": var,
            "big_chances_missed": missed,
            "saves_by_keeper": saves,
            "shots": len(shot_list),
        }

    out("")
    out("  matches processed: %d / %d" % (len(result), len(fx)))
    if missing:
        out("  COULD NOT BE MATCHED (%d):" % len(missing))
        for x in missing:
            out("    %s" % x)
        out("    names seen on the fotmob side: %s" % "; ".join(
            sorted({"%s - %s" % (a[2], a[3]) for a in fm.values()})))
    else:
        out("  every match matched")

    for name, a in result.items():
        out("")
        out("--- %s (%d shots) ---" % (name, a["shots"]))
        for g in a["goals"]:
            out("   %s' %s | %s / %s%s%s" % (
                g["minute"], g["player"], g["manner"] or "?", g["situation"] or "?",
                " | own goal" if g["own_goal"] else "",
                (" | assist: %s" % g["assist"]) if g["assist"] else ""))
        for x in a["big_chances_missed"]:
            out("   %s' MISSED %s (xG %.2f, %s / %s, on target: %s)" % (
                x["minute"], x["player"], x["xG"], x["manner"], x["situation"], x["on_target"]))
        for x in a["var"]:
            out("   %s' VAR: %s %s" % (x["minute"], x["player"] or "", x["decision"] or ""))
        if a["saves_by_keeper"]:
            out("   saves by keeper: %s" % a["saves_by_keeper"])

    # The round's table also holds rows entered BY HAND (a manager's statement
    # told to us) - the harvest must not overwrite them. What the machine
    # knows is refreshed; the rest stays.
    path = os.path.join(HERE, "pl-colour-%s.json" % EVENT)
    old = {}
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                old = json.load(f)
        except Exception:                                    # noqa: BLE001
            old = {}
    old.update({"event": EVENT, "round": int(EVENT), "league": "pl",
                "created": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "matches": result})
    old.setdefault("claims", [])
    open(path, "w", encoding="utf-8").write(
        json.dumps(old, ensure_ascii=False, indent=1) + "\n")
    out("  hand-entered rows kept: %d" % len(old.get("claims") or []))
    out("")
    out("  written: %s" % os.path.basename(path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
