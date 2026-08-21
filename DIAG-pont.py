#!/usr/bin/env python3
"""Egyszeri diagnosztika, 7. kor (IDEIGLENES): a bontas cimkei.

A 6. kor megtalalta a bontast: players/{id} -> team.previous_games[]
.game_player_statistics[] = {competition_player_id, value, points},
DE nev nelkul. Ez a kor kideriti, hogyan cimkezi a kliens:
  A) kodkontextus a game_player_statistics korul a bundle-ben
  B) i18n/forditas nyomok (locale, translation, hu.json, chunk-nevek)
  C) van-e tovabbi include a statisztika tipusahoz

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

    print("========== A) game_player_statistics a kodban ==========")
    for m in re.finditer(re.escape("game_player_statistics"), js):
        print("..." + js[max(0, m.start() - 500):m.end() + 700].replace("\n", " ") + "...")
        print("-" * 70)

    print("\n========== B) i18n / chunk nyomok ==========")
    for minta in (r'["\'][^"\']*(?:locale|lang|translation|i18n)[^"\']*\.(?:json|js)["\']',
                  r'assets/[A-Za-z0-9_\-.]+\.js', r'["\']hu["\']'):
        talalatok = sorted(set(re.findall(minta, js)))
        print("%s -> %s" % (minta, talalatok[:25]))

    print("\n========== C) statisztika-tipus include probak ==========")
    for inc in ("team.previous_games.game_player_statistics",
                "team.previous_games.game_player_statistics.statistic",
                "team.previous_games.game_player_statistics.stat_config",
                "team.previous_games.game_player_statistics.type"):
        st, j = get(M_BASE + "players/1305?include=" + urllib.parse.quote(inc))
        if st != 200 or not isinstance(j, dict):
            print("+%s -> HTTP %s" % (inc, st)); continue
        elozok = ((j.get("team") or {}).get("previous_games") or [])
        gps = (elozok[0].get("game_player_statistics") if elozok else None) or []
        print("+%s -> 200; elso meccs elso 3 statja: %s"
              % (inc, json.dumps(gps[:3], ensure_ascii=False)[:400]))

    print("\nDiagnosztika vege - semmit nem irt.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
