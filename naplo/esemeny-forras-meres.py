#!/usr/bin/env python3
"""Meccs-esemenyek kulso forrasanak merese: van-e GOLPERC es milyen reszletesseg.

MIERT: a sajat adatunk (MLSZ/FPL) eseményenkenti OSSZEGET ad, idopontot nem -
a gol perce es a gol MODJA csak kulso forrasbol johet. A fejlesztoi kornyezet
halozata minden kulso forrast blokkol, ezert a meres a GitHub futojarol megy.

Amit mer, ket ligara (angol elso osztaly es magyar elso osztaly):
  1. elerheto-e a forras egyaltalan az adott ligara
  2. ad-e PERCET az esemenyekhez
  3. milyen RESZLETESSEG: csak "Goal", vagy "Penalty" / "Own Goal" / fejes stb.
  4. milyen nevalakban adja a jatekost (a sajat kereteinkhez kell parositani)

Kulcs nem kell hozza. Az eredmeny a naplo/esemeny-forras.txt-be kerul.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

ALAP = "https://site.api.espn.com/apis/site/v2/sports/soccer"
LIGAK = [("angol elso osztaly", "eng.1"), ("magyar elso osztaly", "hun.1")]
NAPLO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "esemeny-forras.txt")
FEJ = {"Accept": "application/json", "User-Agent": "FunTasy-meres"}


def kerd(url):
    k = urllib.request.Request(url, headers=FEJ)
    t0 = time.time()
    try:
        with urllib.request.urlopen(k, timeout=25) as v:
            return v.status, v.read().decode("utf-8", "replace"), int((time.time() - t0) * 1000)
    except urllib.error.HTTPError as e:
        return e.code, "", int((time.time() - t0) * 1000)
    except Exception as e:                                   # noqa: BLE001
        return 0, "%s: %s" % (type(e).__name__, e), int((time.time() - t0) * 1000)


def json_kerd(url):
    kod, torzs, ms = kerd(url)
    if kod != 200:
        return None, kod, ms
    try:
        return json.loads(torzs), kod, ms
    except ValueError:
        return None, kod, ms


def liga_meres(nev, slug, sorok):
    sorok.append("")
    sorok.append("--- %s (%s) ---" % (nev, slug))
    # egy LEZAJLOTT nap menetrendje: visszafele keresunk, amig talalunk kesz meccset
    esemeny_id = nap = None
    kodok = set()
    for nap_vissza in range(1, 15):
        d = time.strftime("%Y%m%d", time.gmtime(time.time() - nap_vissza * 86400))
        j, kod, ms = json_kerd("%s/%s/scoreboard?dates=%s" % (ALAP, slug, d))
        kodok.add(kod)
        if j is None:
            sorok.append("  scoreboard %s: HTTP %s (%d ms)" % (d, kod, ms))
            if kod in (0, 404):
                return
            continue
        for e in j.get("events") or []:
            allapot = (((e.get("status") or {}).get("type") or {}).get("state"))
            if allapot == "post":
                esemeny_id, nap = e.get("id"), d
                sorok.append("  talalt lezajlott meccs: %s (%s), id=%s"
                             % (e.get("name"), d, esemeny_id))
                break
        if esemeny_id:
            break
    if not esemeny_id:
        # A 403 ELUTASITAS, nem hiany: a forras nem enged be minket (tipikusan
        # adatkozponti IP-rol). Ezt kulon kell mondani a "nincs ilyen liga"
        # esettol, kulonben a meres rossz kovetkeztetest rogzit.
        if 403 in kodok:
            sorok.append("  A FORRAS ELUTASIT (HTTP 403) - ez hozzaferes, nem"
                         " adathiany; errol a ligarol semmit nem allitottunk meg")
        else:
            sorok.append("  nem talaltam lezajlott meccset 14 napra visszamenoleg"
                         " (kapott valaszkodok: %s)"
                         % ", ".join(str(k) for k in sorted(kodok)))
        return

    j, kod, ms = json_kerd("%s/%s/summary?event=%s" % (ALAP, slug, esemeny_id))
    if j is None:
        sorok.append("  summary: HTTP %s (%d ms) - nincs esemeny-adat" % (kod, ms))
        return
    sorok.append("  summary: HTTP 200 (%d ms), felso kulcsok: %s"
                 % (ms, ", ".join(sorted(j.keys()))))
    kulcs = j.get("keyEvents") or []
    sorok.append("  keyEvents: %d elem" % len(kulcs))
    if not kulcs:
        sorok.append("  ! nincs esemenylista - ez a forras igy nem ad golpercet")
        return
    sorok.append("  egy elem mezoi: %s" % ", ".join(sorted(kulcs[0].keys())))
    for e in kulcs[:8]:
        ora = (e.get("clock") or {}).get("displayValue")
        tip = (e.get("type") or {}).get("text")
        jat = ", ".join((x.get("athlete") or {}).get("displayName", "?")
                        for x in (e.get("participants") or [])) or "-"
        sorok.append("    %-7s | %-22s | %s | %s"
                     % (ora, tip, jat, (e.get("text") or "")[:70]))
    tipusok = sorted({(e.get("type") or {}).get("text") or "?" for e in kulcs})
    sorok.append("  elofordulo tipusok: %s" % ", ".join(tipusok))


# --- kulcsos forras (api-football): csak ha a titok be van allitva ---
AF_ALAP = "https://v3.football.api-sports.io"
AF_LIGAK = [("angol elso osztaly", 39), ("magyar elso osztaly", 271)]


def af_meres(sorok):
    kulcs = os.environ.get("APIFOOTBALL_KULCS") or ""
    if not kulcs:
        sorok.append("")
        sorok.append("--- kulcsos forras: KIHAGYVA (nincs APIFOOTBALL_KULCS titok) ---")
        return
    fej = {"x-apisports-key": kulcs, "Accept": "application/json"}
    evad = time.gmtime().tm_year - (1 if time.gmtime().tm_mon < 7 else 0)
    for nev, lid in AF_LIGAK:
        sorok.append("")
        sorok.append("--- %s (api-football liga=%d, evad=%d) ---" % (nev, lid, evad))
        k = urllib.request.Request(
            "%s/fixtures?league=%d&season=%d&last=1" % (AF_ALAP, lid, evad), headers=fej)
        try:
            with urllib.request.urlopen(k, timeout=25) as v:
                j = json.loads(v.read().decode("utf-8", "replace"))
        except Exception as e:                               # noqa: BLE001
            sorok.append("  fixtures: %s: %s" % (type(e).__name__, e))
            continue
        hibak = j.get("errors")
        if hibak:
            sorok.append("  fixtures hiba: %s" % json.dumps(hibak, ensure_ascii=False))
            continue
        val = j.get("response") or []
        if not val:
            sorok.append("  nincs lejatszott meccs a valaszban - a liga nem elerheto"
                         " ezen a csomagon")
            continue
        fx = val[0]["fixture"]
        csap = val[0]["teams"]
        sorok.append("  utolso meccs: %s - %s (id=%s)"
                     % (csap["home"]["name"], csap["away"]["name"], fx["id"]))
        k2 = urllib.request.Request("%s/fixtures/events?fixture=%s" % (AF_ALAP, fx["id"]),
                                    headers=fej)
        try:
            with urllib.request.urlopen(k2, timeout=25) as v:
                j2 = json.loads(v.read().decode("utf-8", "replace"))
        except Exception as e:                               # noqa: BLE001
            sorok.append("  events: %s: %s" % (type(e).__name__, e))
            continue
        ev = j2.get("response") or []
        sorok.append("  events: %d elem" % len(ev))
        for e in ev[:10]:
            sorok.append("    %3s' | %-12s | %-14s | %s"
                         % ((e.get("time") or {}).get("elapsed"), e.get("type"),
                            e.get("detail"), ((e.get("player") or {}).get("name"))))
        sorok.append("  elofordulo reszletessegek: %s"
                     % ", ".join(sorted({str(e.get("detail")) for e in ev})))


def main():
    sorok = ["", "=" * 70,
             "MERES: %s UTC" % time.strftime("%Y-%m-%d %H:%M")]
    sorok.append("")
    sorok.append("### kulcs nelkuli forras (ESPN)")
    for nev, slug in LIGAK:
        liga_meres(nev, slug, sorok)
    sorok.append("")
    sorok.append("### kulcsos forras (api-football)")
    af_meres(sorok)
    with open(NAPLO, "a", encoding="utf-8") as f:
        f.write("\n".join(sorok) + "\n")
    print("\n".join(sorok))
    return 0


if __name__ == "__main__":
    sys.exit(main())
