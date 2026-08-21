#!/usr/bin/env python3
"""Egyszeri diagnosztika, 10. kor (IDEIGLENES): a bontas cimkei II.

A 9. kor igazolta a /game-player-stats szurest, de a sorokban nincs nev.
Ez a kor:
  A) kiirja a TELJES CompetitionPlayerStatsDialog chunkot (3.2 KB)
  B) include-okat probal a /game-player-stats vegponton

CSAK OLVAS es nyomtat.
"""
import json, re, sys, time, urllib.error, urllib.request

API = "https://fantasy-api.mlsz.hu/"
UI = "https://fantasy.mlsz.hu/"
HDRS = {"Accept": "*/*", "User-Agent": "funtasy-archiver/1.0",
        "Referer": "https://fantasy.mlsz.hu/"}


def get(url, szoveg=False):
    time.sleep(0.3)
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
    print("========== A) CompetitionPlayerStatsDialog teljes kodja ==========")
    st, html = get(UI, szoveg=True)
    fo = ""
    if st == 200:
        for ut in re.findall(r'(?:src|href)="([^"]+\.js[^"]*)"', html):
            teljes = ut if ut.startswith("http") else UI.rstrip("/") + "/" + ut.lstrip("/")
            st2, adat = get(teljes, szoveg=True)
            if st2 == 200:
                fo += adat
    for ut in sorted(set(re.findall(r'assets/CompetitionPlayerStatsDialog[A-Za-z0-9_\-.]*\.js', fo))):
        st, js = get(UI + ut, szoveg=True)
        print("--- %s (HTTP %s) ---" % (ut, st))
        if st == 200:
            print(js)

    print("\n========== B) include-probak a game-player-stats-on ==========")
    for inc in ("stat", "statistic", "stat_config", "game_statistic", "statistic_type", "stat.type"):
        url = (API + "game-player-stats?filter%5Bgame_id%5D=433"
               "&filter%5Bcompetition_player_id%5D=1305&include=" + inc)
        st, j = get(url)
        if st == 200 and isinstance(j, dict) and j.get("data"):
            print("+%s -> 200; elso 2 sor: %s" % (inc, json.dumps(j["data"][:2], ensure_ascii=False)[:500]))
        else:
            print("+%s -> HTTP %s" % (inc, st))

    print("\nDiagnosztika vege - semmit nem irt.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
