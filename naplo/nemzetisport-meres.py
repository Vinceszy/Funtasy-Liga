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
CSATORNAK = ["/publicapi/hu/rss/", "/publicapi/hu/rss/index",
             "/publicapi/hu/rss/all", "/publicapi/hu/rss/labdarugas",
             "/publicapi/hu/rss/foci-nb-i", "/rss", "/rss.xml", "/feed"]
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
        # URES SOROKKAL EGYUTT irjuk ki: a csoportokat azok valasztjak el, es
        # eppen ezen mult a korabbi teves verdikt.
        for sor in torzs.splitlines():
            sorok.append("  | " + sor.rstrip()[:110])
    else:
        sorok.append("  nem olvashato - ilyenkor a korabbi 'tiltja' verdikt"
                     " NEM a site dontese volt, hanem olvasasi hiba")

    def sajat_dontes(txt, ut):
        """A `*` csoport szabalyai alapjan dont, csoporthatart is tartva.

        A konyvtar a csoportokat osszevonta, amikor a fajlban nem volt ures
        sor a kettö kozott, es igy egy MASIK ugynoknek szolo `Disallow: /`
        rank is ervenyesnek latszott. A leghosszabb illeszkedo szabaly nyer,
        egyezo hossznal az Allow."""
        aktiv, szabalyok, ugynokok = False, [], []
        for sor in txt.splitlines():
            t = sor.split("#", 1)[0].strip()
            if not t:
                ugynokok = []
                continue
            if ":" not in t:
                continue
            kulcs, ertek = (x.strip() for x in t.split(":", 1))
            k = kulcs.lower()
            if k == "user-agent":
                ugynokok.append(ertek)
                aktiv = "*" in ugynokok
            elif k in ("allow", "disallow") and aktiv and ertek:
                szabalyok.append((k == "allow", ertek))
        legjobb = None
        for enged, minta in szabalyok:
            if ut.startswith(minta) and (legjobb is None or len(minta) > len(legjobb[1])
                                         or (len(minta) == len(legjobb[1]) and enged)):
                legjobb = (enged, minta)
        return (True, "nincs ra szabaly") if legjobb is None else (legjobb[0], legjobb[1])

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
            konyvtar = rp.can_fetch(UGYNOK, HOSZT + ut)
            enged, mi = sajat_dontes(torzs, ut)
            sorok.append("  %-18s sajat: %-6s (%s) | konyvtar: %s"
                         % (ut, "ENGEDI" if enged else "tiltja", mi,
                            "engedi" if konyvtar else "tiltja"))

    # MIERT TERT EL A KONYVTAR: a RobotFileParser a sajat lekeresehez az
    # alapertelmezett urllib-ugynokot hasznalja. Ha arra a site 401/403-at ad,
    # a parser "mindent tilt"-ra all - a verdikt tehat a sajat elutasitasabol
    # jott, nem a fajl szabalyaibol. Ezt kulon megmerjuk.
    sorok.append("")
    sorok.append("--- miert tert el a konyvtar ---")
    kod2, _, ms2 = kerd(HOSZT + "/robots.txt", {"User-Agent": "Python-urllib/3.11"})
    sorok.append("  robots.txt az alapertelmezett urllib-ugynokkel: HTTP %s (%d ms)"
                 % (kod2, ms2))
    sorok.append("  (401/403 eseten a RobotFileParser mindent tiltottnak vesz)")

    sorok.append("")
    sorok.append("--- sitemap: a cikkek gepi jegyzeke ---")
    kod3, sm, ms3 = kerd(HOSZT + "/sitemapindex.xml")
    sorok.append("  sitemapindex.xml: HTTP %s, %d kbajt (%d ms)"
                 % (kod3, len(sm) // 1024, ms3))
    import re as _re
    gyerekek = _re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", sm)
    sorok.append("  hivatkozott terkepek: %d" % len(gyerekek))
    for g in gyerekek[:5]:
        sorok.append("    %s" % g)
    if gyerekek:
        # a legutolso altalaban a legfrissebb
        cel = gyerekek[-1]
        kod4, gy, ms4 = kerd(cel)
        cimek = _re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", gy)
        sorok.append("  legutolso terkep (%s): HTTP %s, %d cim (%d ms)"
                     % (cel.rsplit("/", 1)[-1], kod4, len(cimek), ms4))
        # SZURES NELKUL is mutatunk mintat: a korabbi futas a sajat szurojere
        # nulla talalatot adott, es abbol nem derult ki, hogy rossz-e a szuro
        # vagy tenyleg nincs foci a jegyzekben.
        sorok.append("  minta a cimekbol (szures nelkul):")
        for c in cimek[:10]:
            sorok.append("    %s" % c[:110])
        from collections import Counter
        elotag = Counter()
        for c in cimek:
            r = c.split("//", 1)[-1].split("/")[1:]
            elotag[r[0] if r else "(gyoker)"] += 1
        sorok.append("  utvonal-elotagok: %s"
                     % ", ".join("%s (%d)" % (k, v) for k, v in elotag.most_common(8)))

    sorok.append("")
    sorok.append("--- hircsatorna keresese ---")
    talalt = []
    for ut in CSATORNAK:
        enged, mi = sajat_dontes(torzs, ut)
        if not enged:
            sorok.append("  %-26s a robots tiltja (%s), nem kerjuk le" % (ut, mi))
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
        sorok.append("  %-26s HTTP %s (%d ms)%s" % (ut, kod, ms, jel))
    sorok.append("")
    sorok.append("  hasznalhato csatorna: %s" % (", ".join(talalt) if talalt else "nincs"))

    with open(NAPLO, "a", encoding="utf-8") as f:
        f.write("\n".join(sorok) + "\n")
    print("\n".join(sorok))
    return 0


if __name__ == "__main__":
    sys.exit(main())
