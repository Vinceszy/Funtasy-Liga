#!/usr/bin/env python3
"""Egyszeri diagnosztika, 2. kor (IDEIGLENES): honnan jon a pont-BONTAS?

Az 1. kor eredmenye: egyik include-varians sem adja a teteles bontast,
a kulon statisztika-vegpontok 404-esek. Viszont a current_round-ban van
has_statistics es first_played_at (a "jatszott mar?" jelzeshez), az FPL
event/{gw}/live 'explain' mezoje pedig kesz bontas.

Ez a kor a fantasy.mlsz.hu frontend JS-bundle-jeibol olvassa ki, milyen
vegpontokat es include-okat hasznal a felulet jatekos-modalja, es
kiirja egy jatekos TELJES rekordjat (summary_statistics tartalommal).

CSAK OLVAS es nyomtat.
"""
import json, re, sys, time, urllib.error, urllib.parse, urllib.request

M_BASE = "https://fantasy-api.mlsz.hu/competitions/3/"
UI = "https://fantasy.mlsz.hu/"
HDRS = {"Accept": "application/json", "User-Agent": "funtasy-archiver/1.0",
        "Referer": "https://fantasy.mlsz.hu/"}
ALAP_INC = ("position,position.alternatives,competition_player,"
            "competition_player.team,competition_player.countries,summary_statistics")


def get(url, szoveg=False):
    time.sleep(0.2)
    try:
        req = urllib.request.Request(url, headers=HDRS)
        with urllib.request.urlopen(req, timeout=30) as r:
            adat = r.read().decode("utf-8", "replace")
            return r.status, adat if szoveg else json.loads(adat)
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception as e:
        return None, str(e)


def main():
    print("========== A) egy jatekos TELJES rekordja (4. fordulo) ==========")
    url = (M_BASE + "user-team-players-history?include=" + urllib.parse.quote(ALAP_INC)
           + "&filter%5Buser_id%5D=5483&filter%5Bround_id%5D=83")
    st, j = get(url)
    if st == 200 and j and j.get("data"):
        print(json.dumps(j["data"][0], ensure_ascii=False, indent=1)[:4000])
    else:
        print("HTTP %s" % st)

    print("\n========== B) frontend JS-bundle-ok atvizsgalasa ==========")
    st, html = get(UI, szoveg=True)
    if st != 200:
        print("fooldal HTTP %s - nem megy tovabb" % st)
        return 0
    js_utak = re.findall(r'(?:src|href)="([^"]+\.js[^"]*)"', html)
    print("talalt bundle-ok: %s" % js_utak)

    minta_vegpont = re.compile(r'["\'`]([a-z0-9_\-]*(?:statistic|round|player|user-team)[a-z0-9_\-./${}]*)["\'`]')
    minta_include = re.compile(r'["\'`]((?:[a-z_]+\.)*[a-z_]*statistic[a-z_.]*)["\'`]')
    minta_api = re.compile(r'[a-z0-9_\-/${}.]*(?:fantasy-api|/competitions/)[a-zA-Z0-9_\-/${}.%\[\]?&=]*')
    vegpontok, includeok, apik = set(), set(), set()
    for ut in js_utak:
        teljes = ut if ut.startswith("http") else UI.rstrip("/") + "/" + ut.lstrip("/")
        st, js = get(teljes, szoveg=True)
        if st != 200 or not isinstance(js, str):
            print("  %s -> HTTP %s" % (ut, st)); continue
        print("  %s -> %d bajt" % (ut, len(js)))
        vegpontok |= set(minta_vegpont.findall(js))
        includeok |= set(minta_include.findall(js))
        apik |= set(minta_api.findall(js))

    print("\n-- 'statistic/round/player' szo-szeru sztringek (max 120): --")
    for s in sorted(vegpontok)[:120]:
        print("  %s" % s)
    print("\n-- statisztika-include jeloltek: --")
    for s in sorted(includeok):
        print("  %s" % s)
    print("\n-- API-hivatkozasok: --")
    for s in sorted(apik)[:60]:
        print("  %s" % s)

    print("\nDiagnosztika vege - semmit nem irt.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
