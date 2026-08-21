#!/usr/bin/env python3
"""Egyszeri diagnosztika, 8. kor (IDEIGLENES): a pont-bontas modal chunkja.

A 7. kor megtalalta a lazy-chunkokat; a jatekos-modal a
CompetitionPlayerStatsDialog chunkban van. Ez a kor letolti a
PlayerStatsDialog / PlayerCard / Player / GameRules chunkokat, es kiirja:
  A) az ekezetes/magyar sztring-literalokat (cimkek)
  B) az API-hivasok kornyeket (url:`...`)
  C) a game_player_statistics feldolgozasat

CSAK OLVAS es nyomtat.
"""
import re, sys, time, urllib.error, urllib.request

UI = "https://fantasy.mlsz.hu/"
HDRS = {"Accept": "*/*", "User-Agent": "funtasy-archiver/1.0",
        "Referer": "https://fantasy.mlsz.hu/"}
CHUNKOK = ("CompetitionPlayerStatsDialog", "PlayerCard", "Player-", "GameRules")


def get(url):
    time.sleep(0.2)
    try:
        req = urllib.request.Request(url, headers=HDRS)
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception as e:
        return None, str(e)


def main():
    st, html = get(UI)
    fo = ""
    if st == 200:
        for ut in re.findall(r'(?:src|href)="([^"]+\.js[^"]*)"', html):
            teljes = ut if ut.startswith("http") else UI.rstrip("/") + "/" + ut.lstrip("/")
            st2, adat = get(teljes)
            if st2 == 200:
                fo += adat
    utak = sorted(set(re.findall(r'assets/[A-Za-z0-9_\-.]+\.js', fo)))
    kellenek = [u for u in utak if any(c in u for c in CHUNKOK)]
    print("letoltendo chunkok: %s" % kellenek)

    for ut in kellenek:
        st, js = get(UI + ut)
        if st != 200:
            print("\n### %s -> HTTP %s" % (ut, st)); continue
        print("\n### %s (%d bajt)" % (ut, len(js)))

        print("-- magyar/ekezetes sztringek: --")
        for s in sorted(set(re.findall(r'["\'`]([^"\'`]*[áéíóöőúüűÁÉÍÓÖŐÚÜŰ][^"\'`]*)["\'`]', js))):
            if len(s) < 90:
                print("   %r" % s)

        print("-- url: kontextusok: --")
        for m in re.finditer(r'url\s*:\s*`[^`]+`', js):
            print("   ..." + js[max(0, m.start() - 120):m.end() + 60].replace("\n", " ") + "...")

        print("-- game_player_statistics kontextus: --")
        for m in re.finditer(re.escape("game_player_statistics"), js):
            print("   ..." + js[max(0, m.start() - 350):m.end() + 500].replace("\n", " ") + "...")

    print("\nDiagnosztika vege - semmit nem irt.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
