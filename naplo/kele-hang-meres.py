#!/usr/bin/env python3
"""Az utanzott hang FORRASA: a szerzo sajat futballos szovegei.

MIERT: a rovat egy letezo publicista hangjat imitalja. A hangot nem talalgatni
kell, hanem elolvasni - a jellegzetes fogasok (onkorrekcio a masodik mondatban,
retorikai kerdes sajat valasszal, harmas engedmeny, ritka szavak) csak a valodi
szovegbol latszanak. A ket kezzel bemasolt irasa mediapolitikai volt; a
rovathoz a FUTBALLOS regiszter kell.

A szoveg CSAK a futasi naploba kerul, a repoba nem - ugyanaz a szabaly, mint a
magyar meccsbeszamoloknal es a PL perces kozvetitesenel. Amit megtartunk belole,
az a naplo/kele-janek.md-be irt SZABALY, nem a mondatai.

Cimek: KELE_URLS, soronkent egy (vagy vesszovel). Alapbol az archivum.
"""
import html
import json
import os
import re
import sys
import urllib.request

FEJ = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                     "(KHTML, like Gecko) Chrome/124 Safari/537.36",
       "Accept": "text/html,application/xhtml+xml"}
# A HTML-oldalt a Substack elott allo vedelem 403-mal utasitja el egy
# adatkozponti IP-rol; a FEED es az archivum JSON-ja viszont gepi utak, azokat
# atengedi. Ezert a feed az elsodleges: abban a bejegyzesek TELJES szovege all.
ALAP = ["https://kelejanek.substack.com/feed",
        "https://kelejanek.substack.com/api/v1/archive?sort=new&limit=50",
        "https://kelejanek.substack.com/p/itt-mindenki-hulye",
        "https://24.hu/szerzo/kele-janos",
        "https://24.hu/author/kelejanos/"]


def hoz(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=FEJ), timeout=45) as r:
            return r.read().decode("utf-8", "replace")
    except Exception as e:                                    # noqa: BLE001
        return "__HIBA__ %s: %s" % (type(e).__name__, e)


def szoveg(h):
    """A torzsszoveg, jelolok nelkul. Nem tokeletes - olvasasra eleg."""
    h = re.sub(r"(?is)<(script|style|nav|footer|svg)[^>]*>.*?</\1>", " ", h)
    h = re.sub(r"(?is)<br\s*/?>", "\n", h)
    h = re.sub(r"(?is)</(p|h1|h2|h3|li|div)>", "\n", h)
    h = re.sub(r"(?s)<[^>]+>", " ", h)
    h = html.unescape(h)
    sorok = [re.sub(r"[ \t ]+", " ", x).strip() for x in h.split("\n")]
    return [x for x in sorok if len(x) > 40]


def main():
    urlok = [u.strip() for u in re.split(r"[,\n]", os.environ.get("KELE_URLS", "")) if u.strip()]
    urlok = urlok or ALAP
    for u in urlok:
        print("")
        print("=" * 70)
        print("### %s" % u)
        print("=" * 70)
        h = hoz(u)
        if h.startswith("__HIBA__"):
            print("  %s" % h)
            continue
        # A feed es az archivum-API gepi alak: azokbol a CIM + a torzs kell,
        # nem a lap keretei.
        if "/feed" in u or "/api/" in u:
            for cim in re.findall(r"<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>", h)[:40]:
                print("  CIM: %s" % html.unescape(cim).strip())
            for m in re.findall(r'"title"\s*:\s*"([^"]{5,200})"', h)[:40]:
                print("  CIM: %s" % m)
        sorok = szoveg(h)
        print("  bekezdes: %d" % len(sorok))
        for x in sorok[:200]:
            print("  %s" % x)
        # Az archivumnal a POSZT-CIMEK a hasznosak, azokat kulon is kiirjuk.
        for m in sorted(set(re.findall(r'href="(https://kelejanek\.substack\.com/p/[^"#?]+)"', h))):
            print("  -> %s" % m)
    return 0


if __name__ == "__main__":
    sys.exit(main())
