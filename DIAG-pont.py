#!/usr/bin/env python3
"""Egyszeri diagnosztika (IDEIGLENES): ki NEM jatszik a heten?

A kerdes: a Honved jatekosainal (5. fordulo) a first_played_at
2026-08-29 00:00 - egy hettel kesobb, ejfelkor. Van-e a keret-valaszban
olyan adat, amibol BIZTOSAN latszik, hogy a klubnak nincs meccse ebben
a forduloban (a datum-osszehasonlitas helyett)?

A jelolt: competition_player.current_round.games - fordulonkenti
meccslista. Ez a kor megmeri:
  A) mit ad a games a Honved jatekosaira es a tobbiekre az 5. fordulon
  B) mekkora a valasz a logo-include-ok NELKUL (a korabbi probanal a
     games.home_team logoja hizlalta fel)
  C) mit ad egy LEZART fordulon (4.), hogy a status-ertekeket lassuk

CSAK OLVAS es nyomtat.
"""
import json, sys, time, urllib.error, urllib.parse, urllib.request

BASE = "https://fantasy-api.mlsz.hu/competitions/3/"
HDRS = {"Accept": "application/json", "User-Agent": "funtasy-archiver/1.0",
        "Referer": "https://fantasy.mlsz.hu/"}
ALAP = ("position,position.alternatives,competition_player,"
        "competition_player.team,competition_player.countries,"
        "competition_player.current_round,summary_statistics")


def get(url):
    time.sleep(0.2)
    try:
        req = urllib.request.Request(url, headers=HDRS)
        with urllib.request.urlopen(req, timeout=30) as r:
            nyers = r.read().decode("utf-8")
            return r.status, json.loads(nyers), len(nyers)
    except urllib.error.HTTPError as e:
        return e.code, None, 0
    except Exception as e:
        return None, str(e), 0


def keret(inc, round_id):
    return get(BASE + "user-team-players-history?include=" + urllib.parse.quote(inc)
               + "&filter%5Buser_id%5D=5483&filter%5Bround_id%5D=" + str(round_id))


def main():
    for cimke, rid in (("5. fordulo (elo)", 85), ("4. fordulo (lezart)", 83)):
        print("\n========== %s ==========" % cimke)
        st, alap, m1 = keret(ALAP, rid)
        st2, j, m2 = keret(ALAP + ",competition_player.current_round.games", rid)
        print("valasz-meret: alap %d bajt -> games-szel %d bajt (+%d)" % (m1, m2, m2 - m1))
        if st2 != 200 or not j or not j.get("data"):
            print("HTTP %s" % st2); continue
        for d in j["data"]:
            cp = d.get("competition_player") or {}
            cr = cp.get("current_round") or {}
            games = cr.get("games")
            rov = []
            for g in (games or []):
                rov.append({"fordulo": g.get("round_number"), "kezdes": g.get("start_at"),
                            "status": g.get("status"),
                            "H": (g.get("home_team") or {}).get("short_name"),
                            "V": (g.get("away_team") or {}).get("short_name")})
            print("  %-22s %-8s is_played=%-5s first_played_at=%-26s games=%s"
                  % (cp.get("last_name"), (cp.get("team") or {}).get("short_name"),
                     cr.get("is_played"), cr.get("first_played_at"),
                     json.dumps(rov, ensure_ascii=False) if games is not None else "NINCS MEZO"))

    print("\nDiagnosztika vege - semmit nem irt.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
