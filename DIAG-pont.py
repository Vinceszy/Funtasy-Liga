#!/usr/bin/env python3
"""Egyszeri diagnosztika, 4. kor (IDEIGLENES): honnan jon a pont-BONTAS?

A 3. kor megtalalta a jatekos-vegpontot a bundle-ben:
`${Qn}/${e}/players/${t}` -> competitions/3/players/{player_id}.
A magyar cimkek (Kulcspassz, Gyozelem...) NINCSENEK a kliensben,
tehat a bontas nevei az API-bol jonnek.

Ez a kor:
  A) a bundle-bol kiszedi a players/${t} hivas kornyeki kodot
     (ott a pontos include-lista es a parameterek)
  B) rogton meg is hivja a players/1305 vegpontot: eloszor
     csupaszon, majd a talalt include-okkal es round-szurovel

CSAK OLVAS es nyomtat.
"""
import json, re, sys, time, urllib.error, urllib.parse, urllib.request

M_BASE = "https://fantasy-api.mlsz.hu/competitions/3/"
UI = "https://fantasy.mlsz.hu/"
HDRS = {"Accept": "application/json", "User-Agent": "funtasy-archiver/1.0",
        "Referer": "https://fantasy.mlsz.hu/"}


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
    st, html = get(UI, szoveg=True)
    js = ""
    if st == 200:
        for ut in re.findall(r'(?:src|href)="([^"]+\.js[^"]*)"', html):
            teljes = ut if ut.startswith("http") else UI.rstrip("/") + "/" + ut.lstrip("/")
            st2, adat = get(teljes, szoveg=True)
            if st2 == 200 and isinstance(adat, str):
                js += adat

    print("========== A) a players/${t} hivas kornyeke ==========")
    for m in re.finditer(re.escape("players/${t}"), js):
        print("..." + js[max(0, m.start() - 700):m.end() + 900].replace("\n", " ") + "...")
        print("-" * 70)

    print("\n========== B) players/1305 probak ==========")
    probak = [
        "players/1305",
        "players/1305?include=" + urllib.parse.quote(
            "round_statistics,round_statistics.details"),
        "players/1305?include=" + urllib.parse.quote(
            "statistics,round_statistics,summary_statistics,current_round"),
        "players/1305?filter%5Bround_id%5D=83",
    ]
    for p in probak:
        st, j = get(M_BASE + p)
        if st == 200 and isinstance(j, dict):
            print("GET %s -> 200:" % p)
            print(json.dumps(j, ensure_ascii=False)[:3000])
        else:
            print("GET %s -> HTTP %s" % (p, st))
        print()

    print("Diagnosztika vege - semmit nem irt.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
