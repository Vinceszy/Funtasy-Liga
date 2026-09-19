#!/usr/bin/env python3
"""A Worker "utolso ismert allas" tarolojanak vegpontrol-vegpontig merese.

MIERT ITT: a fejlesztoi kornyezet halozata nem enged ki a workers.dev-re
(merve: azonnali kapcsolathiba), a Worker logikajat tehat csak hamis KV-vel
lehet ott tesztelni (tesztek/workertarolo.teszt.js). Az ELES viselkedest -
hogy a masodik latogato tenyleg a tarolt allast kapja-e - csak kintrol lehet
megmerni; a GitHub Actions futtatoja kimegy a netre, tehat innen megy.

Amit mer:
  1. /tarolt a lekeres ELOTT  - van-e mar tarolt allas, es mikori
  2. rendes proxy-keres       - ez az, ami eltarolja a valaszt
  3. /tarolt a lekeres UTAN   - megvan-e, es MENNYI IDO alatt jon
  4. ugyanez megismetelve     - valtozatlan adatnal nem valt-e az idobelyeg
                                (vagyis tenyleg csak valtozaskor irunk)

Az eredmenyt a naplo/tarolo-meres.txt-be irja, hozzafuzve.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

PROXY = os.environ.get("PROXY_URL", "https://funtasy-liga.swick00.workers.dev")
EREDET = "https://vinceszy.github.io"
VERSENY = 3
# Egy valodi szakvezeto - a lap is pontosan ezt az URL-t keri le
UNAME = os.environ.get("MERES_UNAME", "HolVanSalah")
CEL = (f"https://fantasy-api.mlsz.hu/competitions/{VERSENY}/rankings"
       "?include=user_team.user.id,summary_statistics,ranking,rounds,"
       "competition_rank&page=1&per_page=5"
       f"&filter%5Bsearch%5D={urllib.parse.quote(UNAME)}")
NAPLO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tarolo-meres.txt")


def kerd(url):
    """(HTTP-kod, torzs, eltelt ms). Halozati hiba: (0, hibauzenet, ms)."""
    keres = urllib.request.Request(url, headers={
        "Accept": "application/json", "Origin": EREDET,
        "User-Agent": "FunTasy-meres (github.com/Vinceszy/Funtasy-Liga)"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(keres, timeout=25) as v:
            return v.status, v.read().decode("utf-8", "replace"), int((time.time() - t0) * 1000)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace"), int((time.time() - t0) * 1000)
    except Exception as e:                                   # noqa: BLE001
        return 0, "%s: %s" % (type(e).__name__, e), int((time.time() - t0) * 1000)


def tarolt():
    kod, torzs, ms = kerd(PROXY + "/tarolt?url=" + urllib.parse.quote(CEL, safe=""))
    if kod != 200:
        return None, ms, "HTTP %s" % kod
    try:
        j = json.loads(torzs)
    except ValueError:
        return None, ms, "nem JSON"
    return j.get(CEL), ms, None


def main():
    sorok = ["", "=" * 62,
             "MERES: %s UTC | szakvezeto: %s" % (time.strftime("%Y-%m-%d %H:%M"), UNAME)]

    elotte, ms, hiba = tarolt()
    sorok.append("1. /tarolt a lekeres ELOTT: %s (%d ms)%s" % (
        ("van, ido=%s, %d bajt" % (elotte.get("ido"), len(elotte.get("adat") or ""))
         if elotte else "meg nincs tarolva"), ms, " [%s]" % hiba if hiba else ""))

    kod, torzs, ms2 = kerd(PROXY + "/?url=" + urllib.parse.quote(CEL, safe=""))
    sorok.append("2. rendes proxy-keres: HTTP %d, %d bajt, %d ms" % (kod, len(torzs), ms2))
    if kod != 200:
        sorok.append("   ! a lekeres nem sikerult, a tobbi lepes ertelmetlen")
        ir(sorok)
        return 1

    time.sleep(3)                       # a waitUntil-os iras befejezodesere
    utana, ms3, hiba3 = tarolt()
    sorok.append("3. /tarolt a lekeres UTAN: %s (%d ms)%s" % (
        ("van, ido=%s, %d bajt" % (utana.get("ido"), len(utana.get("adat") or ""))
         if utana else "NINCS - a tarolas nem mukodik"), ms3, " [%s]" % hiba3 if hiba3 else ""))
    if utana:
        sorok.append("   egyezik a proxy valaszaval: %s"
                     % ("IGEN" if utana.get("adat") == torzs else "NEM"))
        if ms3:
            sorok.append("   a tarolt valasz %.1fx gyorsabban jott, mint a friss lekeres"
                         % (ms2 / ms3))

    # 4. ugyanaz megegyszer: VALTOZATLAN adatnal nem szabad ujra irni
    kerd(PROXY + "/?url=" + urllib.parse.quote(CEL, safe=""))
    time.sleep(3)
    megegyszer, _, _ = tarolt()
    if utana and megegyszer:
        azonos = utana.get("ido") == megegyszer.get("ido")
        sorok.append("4. valtozatlan adat utan az idobelyeg: %s"
                     % ("VALTOZATLAN - csak valtozaskor irunk, ahogy kell" if azonos
                        else "MEGVALTOZOTT - minden keres ir, ez a napi kvotat enne"))
    ir(sorok)
    return 0


def ir(sorok):
    with open(NAPLO, "a", encoding="utf-8") as f:
        f.write("\n".join(s for s in sorok if s is not None) + "\n")
    print("\n".join(s for s in sorok if s is not None))


if __name__ == "__main__":
    sys.exit(main())
