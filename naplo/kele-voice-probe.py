#!/usr/bin/env python3
"""Az utanzott hang FORRASA: a szerzo sajat futballos szovegei.

MIERT: a rovat egy letezo publicista hangjat imitalja. A hangot nem talalgatni
kell, hanem elolvasni - a jellegzetes fogasok csak a valodi szovegbol latszanak.

A LEKERT SZOVEG A `tartalek/kele/` ALA KERUL. A meres eredmenye addig letezik,
amig le van irva: egy futasi naplo par nap mulva elerhetetlen, es akkor vagy
ujra le kell kerni ugyanazt, vagy - ami rosszabb - emlekezetbol ir az ember.
A `tartalek/` a repo azon resze, amit a lap nem szolgal ki es a D9 sem nez.

BYLINE-ELLENORZES. A szerzoi oldalon a lap sajat "legfrissebb hirek" savja is
ott all, tele idegen cikkel. Egy puszta "datumos cikk-link" minta ezeket is
osszeszedi, es a meres ugy jon vissza tele idojaras-elorejelzessel, hogy
kozben sikeresnek latszik. Ezert minden letoltott lapnal megnezzuk, ott
all-e rajta a SZERZO sajat hivatkozasa; ami nem allja ki, azt eldobjuk, es a
vegen kiirjuk, hany ilyen volt.

Kornyezet: KELE_OLDAL (hany archivum-oldal, alap 6), KELE_CIKK (legfeljebb
hany cikket toltsunk le, alap 40).
"""
import html
import os
import re
import sys
import time
import urllib.request

FEJ = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                     "(KHTML, like Gecko) Chrome/124 Safari/537.36",
       "Accept": "text/html,application/xhtml+xml"}
# MERVE: a Substack elott allo vedelem adatkozponti cimrol MINDENT 403-mal
# utasit el - a feedet es az archivum-API-t is -, a masik kiado szerzoi
# oldala viszont atmegy. Onnan jon a lista, es onnan a cikkek torzse is.
SZERZO = "https://24.hu/author/kelejanos/"
BYLINE = "/author/kelejanos"
GYOKER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CEL = os.path.join(GYOKER, "tartalek", "kele")
OLDAL_DB = int(os.environ.get("KELE_OLDAL", "6"))
CIKK_DB = int(os.environ.get("KELE_CIKK", "40"))


def hoz(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=FEJ),
                                    timeout=45) as r:
            return r.read().decode("utf-8", "replace")
    except Exception as e:                                    # noqa: BLE001
        return "__HIBA__ %s: %s" % (type(e).__name__, e)


def szoveg(h):
    """A torzsszoveg, jelolok nelkul. Nem tokeletes - olvasasra eleg."""
    h = re.sub(r"(?is)<(script|style|nav|footer|svg|aside)[^>]*>.*?</\1>", " ", h)
    h = re.sub(r"(?is)<br\s*/?>", "\n", h)
    h = re.sub(r"(?is)</(p|h1|h2|h3|li|div)>", "\n", h)
    h = re.sub(r"(?s)<[^>]+>", " ", h)
    h = html.unescape(h)
    sorok = [re.sub(r"[ \t ]+", " ", x).strip() for x in h.split("\n")]
    return [x for x in sorok if len(x) > 40]


def cim(h):
    m = re.search(r"(?is)<title>(.*?)</title>", h)
    return html.unescape(m.group(1)).strip() if m else ""


def szelet(nev):
    return re.sub(r"[^a-z0-9]+", "-", nev.lower()).strip("-")[:70]


def main():
    os.makedirs(CEL, exist_ok=True)
    jeloltek = []
    for lap in range(1, OLDAL_DB + 1):
        u = SZERZO if lap == 1 else "%spage/%d/" % (SZERZO, lap)
        h = hoz(u)
        if h.startswith("__HIBA__"):
            print("archivum %d.: %s" % (lap, h))
            continue
        uj = [x for x in dict.fromkeys(re.findall(
            r'href="(https://24\.hu/[a-z-]+/20\d\d/\d\d/\d\d/[^"#?]+)"', h))]
        print("archivum %d. oldal: %d hivatkozas" % (lap, len(uj)))
        jeloltek += [x for x in uj if x not in jeloltek]
    print("\nosszes jelolt: %d" % len(jeloltek))

    ove = idegen = hibas = 0
    for c in jeloltek:
        if ove >= CIKK_DB:
            break
        ch = hoz(c)
        time.sleep(0.4)
        if ch.startswith("__HIBA__"):
            hibas += 1
            print("  HIBA   %s  %s" % (c, ch))
            continue
        # A byline dont, nem az, hogy a szerzoi oldalrol jott a hivatkozas.
        if BYLINE not in ch:
            idegen += 1
            continue
        sorok = szoveg(ch)
        if len(sorok) < 5:
            hibas += 1
            print("  URES   %s" % c)
            continue
        ove += 1
        nev = szelet(c.rstrip("/").split("/")[-1]) or ("cikk-%02d" % ove)
        ut = os.path.join(CEL, "%s.txt" % nev)
        with open(ut, "w", encoding="utf-8") as f:
            f.write("# %s\n# %s\n\n%s\n" % (cim(ch), c, "\n\n".join(sorok)))
        print("  MENTVE %s  (%d bekezdes)  -> tartalek/kele/%s.txt"
              % (c, len(sorok), nev))

    print("\n%d sajat cikk mentve, %d idegen eldobva (byline nem egyezett), "
          "%d hibas" % (ove, idegen, hibas))
    if not ove:
        print("EGYETLEN sajat cikk sem jott meg - a meres NEM sikerult.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
