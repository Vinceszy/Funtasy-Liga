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
FEJ = {"User-Agent": AGENT, "Accept": "application/json",
       "Origin": "https://www.premierleague.com",
       "Referer": "https://www.premierleague.com/"}
# Ami egy osszefoglaloba valo: gol, vitatott helyzet, kapusbravur, nagy
# kihagyas, kiallitas. A tobbi perces kommentar a lapnak nem kell.
ERDEKES = re.compile(
    r"\b(goal|scores?|scored|header|volley|free[- ]kick|penalt|own goal|"
    r"var|offside|disallow|red card|sent off|save[sd]?|denie[sd]|tip|"
    r"post|crossbar|woodwork|miss|wide|blaze|sitter|equalis|winner)\b", re.I)


def keres(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=FEJ), timeout=40) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:200]
    except Exception as e:                                   # noqa: BLE001
        return 0, ("%s: %s" % (type(e).__name__, e)).encode()


def js(url):
    c, b = keres(url)
    if c != 200:
        return c, None
    try:
        return c, json.loads(b.decode("utf-8", "replace"))
    except Exception:                                        # noqa: BLE001
        return c, None


def kulcs(nev):
    n = unicodedata.normalize("NFKD", nev or "")
    n = "".join(c for c in n if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z]", "", n)


def egyezik(a, b):
    if not a or not b:
        return False
    if a == b:
        return True
    rovid, hosszu = (a, b) if len(a) <= len(b) else (b, a)
    return len(rovid) >= 5 and rovid in hosszu


def main():
    sor = ["", "=" * 70,
           "TEXTSTREAM: %s UTC | Premier League perces kommentar, %s. fordulo"
           % (time.strftime("%Y-%m-%d %H:%M"), EVENT)]

    c, boot = js("https://fantasy.premierleague.com/api/bootstrap-static/")
    c2, fx = js("https://fantasy.premierleague.com/api/fixtures/?event=" + EVENT)
    if not boot or not fx:
        sor.append("  FPL: bootstrap HTTP %s, fixtures HTTP %s - megallunk" % (c, c2))
        print("\n".join(sor))
        return 1
    klub = {t["id"]: t["name"] for t in boot.get("teams", [])}
    sajat = [(klub.get(f.get("team_h")), klub.get(f.get("team_a"))) for f in fx]
    sor.append("  a(z) %s. fordulo meccsei: %d" % (EVENT, len(sajat)))

    c, sez = js("https://footballapi.pulselive.com/football/competitions/1/compseasons")
    if not sez:
        sor.append("  compseasons: HTTP %s - megallunk" % c)
        print("\n".join(sor))
        return 1
    sid = str((sez.get("content") or [{}])[0].get("id")).split(".")[0]
    c, lista = js("https://footballapi.pulselive.com/football/fixtures?comps=1"
                  "&compSeasons=%s&statuses=C&page=0&pageSize=40&sort=desc" % sid)
    if not lista:
        sor.append("  fixtures: HTTP %s - megallunk" % c)
        print("\n".join(sor))
        return 1
    pulse = []
    for f in lista.get("content", []):
        nevek = [(t.get("team") or {}).get("name", "") for t in f.get("teams", [])]
        if len(nevek) == 2:
            pulse.append((str(f.get("id")).split(".")[0], kulcs(nevek[0]), kulcs(nevek[1]),
                          nevek[0], nevek[1]))
    sor.append("  pulselive lezart meccs: %d" % len(pulse))

    print("\n".join(sor))
    print("")
    print("#" * 70)
    print("# PERCES KOMMENTAR - csak a futasi naploban, a repoba nem kerul be")
    print("#" * 70)

    talalt = 0
    for h, v in sajat:
        mid = None
        for azon, ph, pv, nh, nv in pulse:
            if egyezik(kulcs(h), ph) and egyezik(kulcs(v), pv):
                mid = azon
                break
        if not mid:
            print("\n### %s - %s: nincs parja a pulselive listaban" % (h, v))
            continue
        c, j = js("https://footballapi.pulselive.com/football/fixtures/%s/textstream/EN"
                  "?pageSize=200" % mid)
        e = ((j or {}).get("events") or {}).get("content") or []
        print("\n### %s - %s  (%d bejegyzes)" % (h, v, len(e)))
        talalt += 1
        for x in sorted(e, key=lambda z: z.get("time", {}).get("label") or ""):
            szoveg = (x.get("text") or "").strip()
            if not szoveg or not ERDEKES.search(szoveg):
                continue
            perc = (x.get("time") or {}).get("label") or ""
            print("   %-6s %s" % (perc, szoveg))

    sor2 = ["  parositott meccs: %d / %d" % (talalt, len(sajat))]
    print("")
    print("\n".join(sor2))
    with open(LOG, "a", encoding="utf-8") as f:
        f.write("\n".join(sor + sor2) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
