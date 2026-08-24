#!/usr/bin/env python3
"""Az FPL fordulo-allapotanak FOLYAMATOS naplozasa.

Miert: 2026/27-tol az FPL a fordulot az utolso meccs utani nap 09:00 UK-kor
zarja le ("lockdown"), es azt allitja, hogy NAPI zaras nincs. Ezt nem
elhisszuk, hanem megnezzuk az adatfolyamon: ha megis van napi zaras, annak
latszania kell abban, hogy egy nap mezoi a sajat estejen billennek at, nem a
fordulo vegen.

Mit naplozunk (naplo/fpl-allapot.txt), es CSAK VALTOZASKOR egy sort:
  - naponkent: points ("" / l / p / r) es bonus_added
  - meccsenkent: - / M (elindult) / P (finished_provisional) / F (finished)
  - a fordulo szintjen: current_event_finished, processing_status, leagues

A "points" jelenteset a Draft frontendjenek forrasabol olvastuk ki:
  {"": ures, l: Live, p: Provisional, r: Confirmed}

Ez ideiglenes megfigyeles. Ha kiderult, amit tudni akartunk, torolheto:
ez a fajl, a naplo/ konyvtar es a .github/workflows/fpl-naplo.yml.
"""
import datetime, json, os, sys, urllib.request

NAPLO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fpl-allapot.txt")
HDRS = {"Accept": "application/json", "User-Agent": "Mozilla/5.0 funtasy-figyelo/1.0"}


def hoz(url, timeout=30):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=HDRS), timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return {"__hiba": "%s: %s" % (type(e).__name__, e)}


game = hoz("https://draft.premierleague.com/api/game")
gw = game.get("current_event")
nap = hoz("https://fantasy.premierleague.com/api/event-status/")
if not gw or "__hiba" in nap:
    sys.exit(0)          # halozati hiba nem allapotvaltozas
fx = hoz("https://draft.premierleague.com/api/event/%s/fixtures" % gw)

napok = " ".join("%s=%s%s" % (n.get("date", "")[5:], n.get("points") or "_",
                              "/Added" if n.get("bonus_added") else "")
                 for n in (nap.get("status") or []) if isinstance(n, dict))
meccsek = " ".join("%s%s" % (m.get("id"),
                             "F" if m.get("finished") else
                             ("P" if m.get("finished_provisional") else
                              ("M" if m.get("started") else "-")))
                   for m in (fx if isinstance(fx, list) else []))
allapot = "GW%s kesz=%s ps=%s ligak=%r | NAP %s | MECCS %s" % (
    gw, game.get("current_event_finished"), game.get("processing_status"),
    nap.get("leagues"), napok, meccsek)

elozo = None
if os.path.exists(NAPLO):
    for sor in open(NAPLO, encoding="utf-8"):
        if " | NAP " in sor:
            elozo = sor.split("  ", 1)[-1].rstrip("\n")
if elozo == allapot:
    sys.exit(0)

fejlec = not os.path.exists(NAPLO)
with open(NAPLO, "a", encoding="utf-8") as f:
    if fejlec:
        f.write("# Az FPL fordulo-allapota. Egy sor = egy VALTOZAS (UTC).\n"
                "# points: _ = meg nem jatszottak, l = Live, p = Provisional, r = Confirmed\n"
                "# meccs:  - = meg nem kezdodott, M = megy, P = lefujva, F = finished\n")
    f.write("%s  %s\n" % (datetime.datetime.now(datetime.timezone.utc)
                          .strftime("%Y-%m-%d %H:%M"), allapot))
print("uj allapot: %s" % allapot)
