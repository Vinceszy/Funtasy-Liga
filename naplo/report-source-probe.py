#!/usr/bin/env python3
"""Elerheto-e meccsbeszamolo-forras mindket ligara, es szabad-e hasznalni.

MIERT: a gol MODJA (fejes, ollozas) es a vitatott itelet nem esemeny-adat,
hanem szoveg. A tervezett feldolgozas TENYT nyer ki a beszamolobol, es azt
csak akkor engedi ki, ha jatekos + perc egyezik egy esemennyel, amit a
strukturalt forrasbol mar tudunk.

Ez a meres NEM szoveget gyujt. Azt meri, hogy:
  1. mit mond a robots.txt - szabad-e egyaltalan lekerni a cikkoldalt
  2. elerheto-e a forras a futorol (HTTP-kod, meret, valaszido)
  3. van-e a valaszban egyaltalan perc-jellegu mintazat (pl. "63.")

A naploba CSAK ezek a szamok kerulnek, a cikkek szovege nem - az atvetel
mas kerdes lenne, mint a belole kinyert teny felhasznalasa.
"""
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser

UGYNOK = "FunTasy-meres (github.com/Vinceszy/Funtasy-Liga)"
NAPLO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "beszamolo-forras.txt")

# (liga, cimke, egy letezo rovat- vagy cikkoldal)
FORRASOK = [
    ("magyar", "nemzetisport", "https://www.nemzetisport.hu/foci-nb-i"),
    ("magyar", "m4sport", "https://m4sport.hu/labdarugas/"),
    ("magyar", "mlsz", "https://www.mlsz.hu/hirek"),
    ("angol", "bbc", "https://www.bbc.com/sport/football/premier-league"),
    ("angol", "guardian", "https://www.theguardian.com/football/premierleague"),
    ("angol", "premierleague", "https://www.premierleague.com/news"),
]
PERC = re.compile(r"\b\d{1,2}\+?\d*\s*(?:\.|')\s")


def robots_engedi(url):
    r = urllib.parse.urlparse(url)
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url("%s://%s/robots.txt" % (r.scheme, r.netloc))
    try:
        rp.read()
    except Exception as e:                                   # noqa: BLE001
        return None, "robots.txt nem olvashato (%s)" % type(e).__name__
    return rp.can_fetch(UGYNOK, url), None


def main():
    sorok = ["", "=" * 70,
             "MERES: %s UTC | beszamolo-forrasok elerhetosege" % time.strftime("%Y-%m-%d %H:%M")]
    for liga, cimke, url in FORRASOK:
        sorok.append("")
        sorok.append("--- %s | %s ---" % (liga, cimke))
        sorok.append("  cim: %s" % url)
        szabad, hiba = robots_engedi(url)
        if hiba:
            sorok.append("  robots.txt: %s" % hiba)
        else:
            sorok.append("  robots.txt: %s" % ("ENGEDI" if szabad else "TILTJA"))
        if szabad is False:
            sorok.append("  -> nem kerjuk le; a tiltast tiszteletben tartjuk")
            continue
        k = urllib.request.Request(url, headers={"User-Agent": UGYNOK,
                                                 "Accept": "text/html"})
        t0 = time.time()
        try:
            with urllib.request.urlopen(k, timeout=25) as v:
                torzs = v.read().decode("utf-8", "replace")
                kod = v.status
        except urllib.error.HTTPError as e:
            sorok.append("  lekeres: HTTP %s (%d ms)" % (e.code, int((time.time() - t0) * 1000)))
            continue
        except Exception as e:                               # noqa: BLE001
            sorok.append("  lekeres: %s: %s" % (type(e).__name__, e))
            continue
        ms = int((time.time() - t0) * 1000)
        sorok.append("  lekeres: HTTP %d, %d kbajt, %d ms" % (kod, len(torzs) // 1024, ms))
        sorok.append("  perc-jellegu mintazat a valaszban: %d db" % len(PERC.findall(torzs)))
    with open(NAPLO, "a", encoding="utf-8") as f:
        f.write("\n".join(sorok) + "\n")
    print("\n".join(sorok))
    return 0


if __name__ == "__main__":
    sys.exit(main())
