#!/usr/bin/env python3
"""The Premier League's own minute-by-minute commentary for one gameweek.

The probe found it and then nothing used it: the colour harvest pulls
FotMob, which gives the manner of every shot but no prose. So a summary
written from the table alone knows the minute and the foot, and nothing
about how the match felt - which is exactly what a reader notices.

This fetches the league's own text stream for every fixture of a gameweek,
matched to our fixtures through the club names, and prints the entries. The
TEXT goes to the run log only, never into the repository, the same way the
Hungarian reports are handled.

The gameweek comes from the environment variable HARVEST_EVENT, not from an
argument (arguments are ignored). From Actions it is passed through the
`environment` input of .github/workflows/naplo-meres.yml, one NAME=value per
line:

    HARVEST_EVENT=5 python3 naplo/pl-textstream.py
"""
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "pl-colour.txt")
EVENT = os.environ.get("HARVEST_EVENT") or "5"
AGENT = "FunTasy-harvest (github.com/Vinceszy/Funtasy-Liga)"
HEADERS = {"User-Agent": AGENT, "Accept": "application/json",
           "Origin": "https://www.premierleague.com",
           "Referer": "https://www.premierleague.com/"}
# What belongs in a summary: a goal, a disputed moment, a keeper's feat, a big
# miss, a sending-off. The rest of the minute-by-minute commentary is not
# needed for the paper.
INTERESTING = re.compile(
    r"\b(goal|scores?|scored|header|volley|free[- ]kick|penalt|own goal|"
    r"var|offside|disallow|red card|sent off|save[sd]?|denie[sd]|tip|"
    r"post|crossbar|woodwork|miss|wide|blaze|sitter|equalis|winner)\b", re.I)


def fetch(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=40) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:200]
    except Exception as e:                                   # noqa: BLE001
        return 0, ("%s: %s" % (type(e).__name__, e)).encode()


def js(url):
    c, b = fetch(url)
    if c != 200:
        return c, None
    try:
        return c, json.loads(b.decode("utf-8", "replace"))
    except Exception:                                        # noqa: BLE001
        return c, None


# The two sources abbreviate the same club differently, and containment does
# not help: "mancity" is not contained in "manchestercity". The same table the
# FotMob harvest uses - without it, precisely the big matches were missed.
ALIAS = {
    "manutd": "manchesterunited", "manunited": "manchesterunited",
    "mancity": "manchestercity",
    "spurs": "tottenhamhotspur",
    "nottmforest": "nottinghamforest", "nottsforest": "nottinghamforest",
    "wolves": "wolverhamptonwanderers",
    "sheffieldutd": "sheffieldunited",
}


def club_key(name):
    n = unicodedata.normalize("NFKD", name or "")
    n = "".join(c for c in n if not unicodedata.combining(c)).lower()
    n = re.sub(r"[^a-z]", "", n)
    return ALIAS.get(n, n)


def same_club(a, b):
    if not a or not b:
        return False
    if a == b:
        return True
    short, long_ = (a, b) if len(a) <= len(b) else (b, a)
    return len(short) >= 5 and short in long_


def main():
    lines = ["", "=" * 70,
             "TEXTSTREAM: %s UTC | Premier League minute-by-minute commentary, gameweek %s"
             % (time.strftime("%Y-%m-%d %H:%M"), EVENT)]

    c, boot = js("https://fantasy.premierleague.com/api/bootstrap-static/")
    c2, fx = js("https://fantasy.premierleague.com/api/fixtures/?event=" + EVENT)
    if not boot or not fx:
        lines.append("  FPL: bootstrap HTTP %s, fixtures HTTP %s - stopping" % (c, c2))
        print("\n".join(lines))
        return 1
    clubs = {t["id"]: t["name"] for t in boot.get("teams", [])}
    ours = [(clubs.get(f.get("team_h")), clubs.get(f.get("team_a"))) for f in fx]
    lines.append("  matches of gameweek %s: %d" % (EVENT, len(ours)))

    c, seasons = js("https://footballapi.pulselive.com/football/competitions/1/compseasons")
    if not seasons:
        lines.append("  compseasons: HTTP %s - stopping" % c)
        print("\n".join(lines))
        return 1
    sid = str((seasons.get("content") or [{}])[0].get("id")).split(".")[0]
    c, listing = js("https://footballapi.pulselive.com/football/fixtures?comps=1"
                    "&compSeasons=%s&statuses=C&page=0&pageSize=40&sort=desc" % sid)
    if not listing:
        lines.append("  fixtures: HTTP %s - stopping" % c)
        print("\n".join(lines))
        return 1
    pulse = []
    for f in listing.get("content", []):
        names = [(t.get("team") or {}).get("name", "") for t in f.get("teams", [])]
        if len(names) == 2:
            pulse.append((str(f.get("id")).split(".")[0], club_key(names[0]), club_key(names[1]),
                          names[0], names[1]))
    lines.append("  pulselive completed matches: %d" % len(pulse))

    print("\n".join(lines))
    print("")
    print("#" * 70)
    print("# MINUTE-BY-MINUTE COMMENTARY - run log only, never committed to the repository")
    print("#" * 70)

    matched = 0
    for h, v in ours:
        mid = None
        for pulse_id, ph, pv, nh, nv in pulse:
            if same_club(club_key(h), ph) and same_club(club_key(v), pv):
                mid = pulse_id
                break
        if not mid:
            print("\n### %s - %s: no counterpart in the pulselive list" % (h, v))
            continue
        c, j = js("https://footballapi.pulselive.com/football/fixtures/%s/textstream/EN"
                  "?pageSize=200" % mid)
        e = ((j or {}).get("events") or {}).get("content") or []
        print("\n### %s - %s  (%d entries)" % (h, v, len(e)))
        matched += 1
        for x in sorted(e, key=lambda z: z.get("time", {}).get("label") or ""):
            text = (x.get("text") or "").strip()
            if not text or not INTERESTING.search(text):
                continue
            minute = (x.get("time") or {}).get("label") or ""
            print("   %-6s %s" % (minute, text))

    lines2 = ["  matches matched: %d / %d" % (matched, len(ours))]
    print("")
    print("\n".join(lines2))
    with open(LOG, "a", encoding="utf-8") as f:
        f.write("\n".join(lines + lines2) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
