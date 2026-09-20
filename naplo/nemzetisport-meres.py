#!/usr/bin/env python3
"""Mit enged a nemzetisport.hu, es van-e gepi felhasznalasra szant csatornaja.

MIERT: egy korabbi meres egyetlen konyvtarhivasbol azt allapitotta meg, hogy a
site tiltja a lekerest. Egy "can_fetch" hamis erteke viszont jöhet abbol is,
hogy a robots.txt nem volt olvashato, vagy hogy csak EGY utvonal tiltott -
ezert a tenyleges szabalyokat kell megnezni, nem a verdiktet.

Amit mer:
  1. a robots.txt nyers tartalma (ez nyilvanos, gepi felhasznalasra szant
     szabalyfajl - a naploba is bekerulhet)
  2. utvonalankent kulon: mit enged es mit tilt
  3. van-e hircsatorna (RSS/Atom) - azt kifejezetten gepi olvasasra teszik ki

Cikkszoveget ez sem tarol.
"""
import os
import sys
import time
import urllib.error
import urllib.request
import urllib.robotparser

UGYNOK = "FunTasy-meres (github.com/Vinceszy/Funtasy-Liga)"
HOSZT = "https://www.nemzetisport.hu"
UTAK = ["/", "/foci-nb-i", "/rss", "/rss.xml", "/feed", "/feed/", "/hirek"]
CSATORNAK = ["/rss", "/rss.xml", "/rss/", "/feed", "/feed/", "/atom.xml",
             "/rss/foci-nb-i", "/foci-nb-i/rss"]
NAPLO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "beszamolo-forras.txt")


def kerd(url, fejek=None):
    k = urllib.request.Request(url, headers=fejek or {"User-Agent": UGYNOK})
    t0 = time.time()
    try:
        with urllib.request.urlopen(k, timeout=25) as v:
            return v.status, v.read().decode("utf-8", "replace"), int((time.time() - t0) * 1000)
    except urllib.error.HTTPError as e:
        return e.code, "", int((time.time() - t0) * 1000)
    except Exception as e:                                   # noqa: BLE001
        return 0, "%s: %s" % (type(e).__name__, e), int((time.time() - t0) * 1000)


def main():
    sorok = ["", "=" * 70,
             "MERES: %s UTC | nemzetisport.hu: mit enged" % time.strftime("%Y-%m-%d %H:%M")]

    kod, torzs, ms = kerd(HOSZT + "/robots.txt")
    sorok.append("")
    sorok.append("--- robots.txt (HTTP %s, %d ms) ---" % (kod, ms))
    if kod == 200:
        for sor in torzs.splitlines():
            if sor.strip():
                sorok.append("  | " + sor.rstrip()[:110])
    else:
        sorok.append("  nem olvashato - ilyenkor a korabbi 'tiltja' verdikt"
                     " NEM a site dontese volt, hanem olvasasi hiba")

    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(HOSZT + "/robots.txt")
    try:
        rp.read()
        olvasva = True
    except Exception:                                        # noqa: BLE001
        olvasva = False
    sorok.append("")
    sorok.append("--- utvonalankenti dontes (ugynok: sajat) ---")
    if not olvasva:
        sorok.append("  a robots.txt nem volt beolvashato a konyvtarral")
    else:
        for ut in UTAK:
            sorok.append("  %-16s %s" % (ut, "ENGEDI" if rp.can_fetch(UGYNOK, HOSZT + ut)
                                         else "tiltja"))

    sorok.append("")
    sorok.append("--- hircsatorna keresese ---")
    talalt = []
    for ut in CSATORNAK:
        if olvasva and not rp.can_fetch(UGYNOK, HOSZT + ut):
            sorok.append("  %-18s robots tiltja, nem kerjuk le" % ut)
            continue
        kod, torzs, ms = kerd(HOSZT + ut, {"User-Agent": UGYNOK,
                                           "Accept": "application/rss+xml, application/xml"})
        jel = ""
        if kod == 200:
            eleje = torzs.lstrip()[:200].lower()
            if "<rss" in eleje or "<feed" in eleje or "<?xml" in eleje:
                jel = " | XML-csatorna, %d tetel" % torzs.count("<item")
                talalt.append(ut)
            else:
                jel = " | nem XML (valoszinuleg HTML-oldal)"
        sorok.append("  %-18s HTTP %s (%d ms)%s" % (ut, kod, ms, jel))
    sorok.append("")
    sorok.append("  hasznalhato csatorna: %s" % (", ".join(talalt) if talalt else "nincs"))

    with open(NAPLO, "a", encoding="utf-8") as f:
        f.write("\n".join(sorok) + "\n")
    print("\n".join(sorok))
    return 0


if __name__ == "__main__":
    sys.exit(main())
