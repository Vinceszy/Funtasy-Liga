#!/usr/bin/env python3
"""IDOVONAL: mikor vált at az FPL napi allapota?

Egy mintavetel keveset er: a meccs alatti "l" mindket feltevessel osszefer.
A kerdes az, hogy mi tortenik a LEFUJAS UTANI ablakban:
  - ha meg "l", es kesobb valt "p"-re -> a "p" a zaras jelzese
  - ha rogton "p"                     -> a "p" csak annyi, hogy lement a meccs

A szkript egy mintat vesz, es CSAK AKKOR ir sort, ha valtozott valami az
elozohoz kepest. Igy a naplo egy tiszta atmenet-idovonal lesz.
Csak olvas (a git-be irast a workflow vegzi).
"""
import datetime, json, os, sys, urllib.request

NAPLO = "DIAG-FPL-idovonal.txt"
HDRS = {"Accept": "application/json", "User-Agent": "Mozilla/5.0 funtasy-diag/1.0"}


def hoz(url, timeout=30):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=HDRS), timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return {"__hiba": "%s: %s" % (type(e).__name__, e)}


game = hoz("https://draft.premierleague.com/api/game")
gw = game.get("current_event")
nap = hoz("https://fantasy.premierleague.com/api/event-status/")
fx = hoz("https://draft.premierleague.com/api/event/%s/fixtures" % gw) if gw else []

# Ha maga a lekeres hasalt el, NEM irunk sort: egy halozati hiba nem atmenet,
# es a naploban ugy nezne ki, mintha valtozott volna valami.
if not gw or "__hiba" in nap:
    sys.exit(0)

napok = " | ".join("%s:%s%s" % (n.get("date", "")[5:], n.get("points") or "-",
                                "+B" if n.get("bonus_added") else "")
                   for n in (nap.get("status") or []) if isinstance(n, dict))
meccsek = " ".join("%s:%s" % (m.get("id"),
                              "F" if m.get("finished") else
                              ("P" if m.get("finished_provisional") else
                               ("M" if m.get("started") else "-")))
                   for m in (fx if isinstance(fx, list) else []))
allapot = "gw=%s kesz=%s ps=%s || NAPOK %s || MECCSEK %s" % (
    gw, game.get("current_event_finished"), game.get("processing_status"), napok, meccsek)

# csak valtozasra irunk
elozo = None
if os.path.exists(NAPLO):
    for sor in open(NAPLO, encoding="utf-8"):
        if "||" in sor:
            elozo = sor.split("  ", 1)[-1].strip()
if elozo == allapot:
    sys.exit(0)
print("%s  %s" % (datetime.datetime.now(datetime.timezone.utc).strftime("%m-%d %H:%M:%S"), allapot))
