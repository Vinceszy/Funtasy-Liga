#!/usr/bin/env python3
"""Egyszeri diagnosztika, 6. kor (IDEIGLENES): honnan jon a pont-BONTAS?

Az 5. kor kihozta a stat-configs neveket, de a players/{id} valasz
elejet a log-vagas elvitte. Ez a kor a kep-mezok MELLETT a
meccslistakat (games, next_game) is kidobja, es tomoren irja ki a
players/1305 teljes maradek szerkezetet. Ha van benne fordulonkenti
statisztika pontokkal, megvan a bontas forrasa.

CSAK OLVAS es nyomtat.
"""
import json, sys, time, urllib.error, urllib.request

M_BASE = "https://fantasy-api.mlsz.hu/competitions/3/"
HDRS = {"Accept": "application/json", "User-Agent": "funtasy-archiver/1.0",
        "Referer": "https://fantasy.mlsz.hu/"}
DOBANDO = {"profile_picture", "logo", "media", "background", "src", "srcset",
           "icon", "games", "next_game"}


def get(url):
    time.sleep(0.2)
    try:
        req = urllib.request.Request(url, headers=HDRS)
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception as e:
        return None, str(e)


def szur(x):
    if isinstance(x, dict):
        return {k: szur(v) for k, v in x.items() if k not in DOBANDO}
    if isinstance(x, list):
        return [szur(v) for v in x]
    return x


def main():
    print("========== players/1305 (kepek es meccslistak nelkul) ==========")
    st, j = get(M_BASE + "players/1305")
    if st == 200:
        print(json.dumps(szur(j), ensure_ascii=False)[:12000])
    else:
        print("HTTP %s" % st)
    print("\nDiagnosztika vege - semmit nem irt.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
