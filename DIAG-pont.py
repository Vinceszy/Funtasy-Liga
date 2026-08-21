#!/usr/bin/env python3
"""Egyszeri diagnosztika, 9. kor (IDEIGLENES): a /game-player-stats vegpont.

A 8. kor kiderítette: a jatekos-modal a /game-player-stats vegpontot
hivja GET-tel, parameterekkel. Ez a kor a parameter-valtozatokat probalja
(433 = DVSC-ETO a 4. fordulobol, 1305 = Umathum), es kiirja a valaszt.

CSAK OLVAS es nyomtat.
"""
import json, sys, time, urllib.error, urllib.request

API = "https://fantasy-api.mlsz.hu/"
HDRS = {"Accept": "application/json", "User-Agent": "funtasy-archiver/1.0",
        "Referer": "https://fantasy.mlsz.hu/"}


def get(url):
    time.sleep(0.3)
    try:
        req = urllib.request.Request(url, headers=HDRS)
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception as e:
        return None, str(e)


def main():
    probak = [
        "game-player-stats?filter%5Bgame_id%5D=433&filter%5Bcompetition_player_id%5D=1305",
        "game-player-stats?filter%5Bcompetition_player_id%5D=1305",
        "game-player-stats?game_id=433&competition_player_id=1305",
        "game-player-stats?filter%5Bgame_id%5D=433",
        "competitions/3/game-player-stats?filter%5Bgame_id%5D=433&filter%5Bcompetition_player_id%5D=1305",
    ]
    for p in probak:
        st, j = get(API + p)
        if st == 200 and isinstance(j, (dict, list)):
            print("GET %s -> 200:" % p)
            print(json.dumps(j, ensure_ascii=False)[:4000])
        else:
            print("GET %s -> HTTP %s" % (p, st))
        print()

    print("Diagnosztika vege - semmit nem irt.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
