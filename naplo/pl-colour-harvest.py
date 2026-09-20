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

Writes naplo/pl-colour-<event>.json and prints a readable digest.
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
NAGY_XG = 0.3


def keres(url):
    req = urllib.request.Request(url, headers={"User-Agent": AGENT, "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:300]
    except Exception as e:                                   # noqa: BLE001
        return 0, ("%s: %s" % (type(e).__name__, e)).encode()


def js(url):
    c, b = keres(url)
    if c != 200:
        return c, None
    try:
        return c, json.loads(b)
    except Exception:                                        # noqa: BLE001
        return c, None


# Az FPL sajat roviditeseit a FotMob teljes nevere kotjuk. Az elso valtozat
# ellenkezoleg csinalta - kivagta a "united"/"city"/"hotspur" szavakat -, es
# pont a negy legismertebb klubot vesztette el ("Man Utd" vs "Manchester
# United"). Rovidites-tablat kell hasznalni, nem szo-irtast.
ALIAS = {
    "manutd": "manchesterunited", "manunited": "manchesterunited",
    "mancity": "manchestercity",
    "spurs": "tottenhamhotspur",
    "nottmforest": "nottinghamforest", "nottsforest": "nottinghamforest",
    "wolves": "wolverhamptonwanderers",
    "sheffieldutd": "sheffieldunited",
}


def kulcs(nev):
    """Klubnev osszehasonlitashoz: ekezet es irasjel nelkul, kisbetuvel.
       Szot NEM vagunk ki belole - az vesztette el a meccseket."""
    n = unicodedata.normalize("NFKD", nev or "")
    n = "".join(c for c in n if not unicodedata.combining(c)).lower()
    n = re.sub(r"[^a-z]", "", n)
    return ALIAS.get(n, n)


def egyezik(a, b):
    """Ket klubnev ugyanaz-e. A ket forras kulonbozo hosszan irja ugyanazt, es
       a toldalek nem mindig a VEGERE kerul: "Brighton" / "Brighton & Hove
       Albion", de "Bournemouth" / "AFC Bournemouth". Ezert a rovidebbnek
       BARHOL benne kell lennie a hosszabban - legalabb ot betun, kulonben a
       "man" mindenre illeszkedne."""
    if not a or not b:
        return False
    if a == b:
        return True
    rovid, hosszu = (a, b) if len(a) <= len(b) else (b, a)
    return len(rovid) >= 5 and rovid in hosszu


def main():
    sor = []
    def ki(s=""):
        sor.append(s)
        print(s)

    ki("=" * 70)
    ki("HARVEST: %s UTC | Premier League colour, gameweek %s" % (
        time.strftime("%Y-%m-%d %H:%M"), EVENT))

    c, boot = js("https://fantasy.premierleague.com/api/bootstrap-static/")
    if not boot:
        ki("  bootstrap-static: HTTP %s - megallunk" % c)
        return 1
    klub = {t["id"]: t["name"] for t in boot.get("teams", [])}
    ki("  klubok: %d" % len(klub))

    c, fx = js("https://fantasy.premierleague.com/api/fixtures/?event=" + EVENT)
    if not fx:
        ki("  fixtures: HTTP %s - megallunk" % c)
        return 1
    ki("  a(z) %s. fordulo meccsei: %d" % (EVENT, len(fx)))
    napok = sorted({(f.get("kickoff_time") or "")[:10] for f in fx if f.get("kickoff_time")})
    ki("  jatszonapok: %s" % ", ".join(napok))

    # FotMob napi listak, csak a szukseges napokra
    fm = {}
    for d in napok:
        c, j = js("https://www.fotmob.com/api/data/matches?date=" + d.replace("-", ""))
        if not j:
            ki("  fotmob %s: HTTP %s" % (d, c))
            continue
        pl = [lg for lg in j.get("leagues", [])
              if lg.get("ccode") == "ENG" and lg.get("name") == "Premier League"]
        db = 0
        for lg in pl:
            for m in lg.get("matches", []):
                h = (m.get("home") or {}).get("name")
                v = (m.get("away") or {}).get("name")
                fm[str(m.get("id"))] = (kulcs(h), kulcs(v), h, v)
                db += 1
        ki("  fotmob %s: %d PL-meccs" % (d, db))

    eredmeny = {}
    hianyzo = []
    for f in fx:
        h, v = klub.get(f.get("team_h")), klub.get(f.get("team_a"))
        mid = None
        for azon, (fh, fv, nh, nv) in fm.items():
            if egyezik(kulcs(h), fh) and egyezik(kulcs(v), fv):
                mid = azon
                break
        if not mid:
            # A hianyt KIIRJUK a szemkozti nevekkel egyutt: enelkul egy elavult
            # rovidites-tabla csendben tuntetne el egy meccset.
            hianyzo.append("%s - %s (kulcs: %s / %s)" % (h, v, kulcs(h), kulcs(v)))
            continue
        c, j = js("https://www.fotmob.com/api/data/matchDetails?matchId=" + mid)
        if not j:
            hianyzo.append("%s - %s (matchDetails HTTP %s)" % (h, v, c))
            continue
        tart = j.get("content") or {}
        ev = ((tart.get("matchFacts") or {}).get("events") or {}).get("events") or []
        sm = tart.get("shotmap") or {}
        lov = sm.get("shots") if isinstance(sm, dict) else []
        lov = lov if isinstance(lov, list) else []

        # a golhoz a lovest a perc + jatekos parral kotjuk ossze
        lovesek = {}
        for x in lov:
            lovesek.setdefault((x.get("min"), x.get("playerName")), x)

        golok, var = [], []
        for e in ev:
            if e.get("type") == "Goal":
                p = (e.get("player") or {}).get("name")
                l = lovesek.get((e.get("time"), p)) or {}
                golok.append({
                    "perc": e.get("timeStr") if isinstance(e.get("timeStr"), str) else e.get("time"),
                    "jatekos": p,
                    "gólpassz": e.get("assistStr"),
                    "leiras": e.get("goalDescription"),
                    "mód": l.get("shotType"),
                    "helyzet": l.get("situation"),
                    "öngól": bool(l.get("isOwnGoal")),
                    "xG": round(l["expectedGoals"], 3) if l.get("expectedGoals") else None,
                })
            elif e.get("type") == "VAR":
                var.append({"perc": e.get("time"),
                            "jatekos": (e.get("player") or {}).get("name"),
                            "mit": e.get("nameStr") or e.get("reactKey")})

        kihagyott = [{"perc": x.get("min"), "jatekos": x.get("playerName"),
                      "xG": round(x.get("expectedGoals") or 0, 3),
                      "mód": x.get("shotType"), "helyzet": x.get("situation"),
                      "kapura": bool(x.get("isOnTarget"))}
                     for x in lov
                     if (x.get("expectedGoals") or 0) >= NAGY_XG
                     and str(x.get("eventType")) != "Goal"]
        vedes = {}
        for x in lov:
            if str(x.get("eventType")) == "AttemptSaved" and not x.get("isBlocked"):
                vedes[str(x.get("keeperId"))] = vedes.get(str(x.get("keeperId")), 0) + 1

        eredmeny["%s - %s" % (h, v)] = {
            "fotmob": mid, "golok": golok, "var": var,
            "kihagyott_nagy_helyzet": kihagyott,
            "vedesek_kapusonkent": vedes,
            "loves_db": len(lov),
        }

    ki("")
    ki("  feldolgozott meccs: %d / %d" % (len(eredmeny), len(fx)))
    if hianyzo:
        ki("  NEM SIKERULT PAROSITANI (%d):" % len(hianyzo))
        for x in hianyzo:
            ki("    %s" % x)
        ki("    a fotmob oldalan latott nevek: %s" % "; ".join(
            sorted({"%s - %s" % (a[2], a[3]) for a in fm.values()})))
    else:
        ki("  minden meccs parositva")

    for nev, a in eredmeny.items():
        ki("")
        ki("--- %s (%d loves) ---" % (nev, a["loves_db"]))
        for g in a["golok"]:
            ki("   %s' %s | %s / %s%s%s" % (
                g["perc"], g["jatekos"], g["mód"] or "?", g["helyzet"] or "?",
                " | öngól" if g["öngól"] else "",
                (" | gólpassz: %s" % g["gólpassz"]) if g["gólpassz"] else ""))
        for x in a["kihagyott_nagy_helyzet"]:
            ki("   %s' KIHAGYTA %s (xG %.2f, %s / %s, kapura: %s)" % (
                x["perc"], x["jatekos"], x["xG"], x["mód"], x["helyzet"], x["kapura"]))
        for x in a["var"]:
            ki("   %s' VAR: %s %s" % (x["perc"], x["jatekos"] or "", x["mit"] or ""))
        if a["vedesek_kapusonkent"]:
            ki("   vedesek kapusonkent: %s" % a["vedesek_kapusonkent"])

    ut = os.path.join(HERE, "pl-colour-%s.json" % EVENT)
    open(ut, "w", encoding="utf-8").write(
        json.dumps({"event": EVENT, "keszult": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "meccsek": eredmeny}, ensure_ascii=False, indent=1) + "\n")
    ki("")
    ki("  kiirva: %s" % os.path.basename(ut))
    return 0


if __name__ == "__main__":
    sys.exit(main())
