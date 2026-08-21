#!/usr/bin/env python3
"""Egyszeri diagnosztika, 11. kor (IDEIGLENES): vegso ellenorzes.

A 10. kor dekodolta a modalt: /game-player-stats +
include=competition_stat_config adja a cimkezett bontast.
Ez a kor igazolja, es a "jatszott mar?" jelzot meri:
  A) game-player-stats cimkekkel (Umathum, 4. fordulo)
  B) elo fordulo (85): is_played / first_played_at / has_statistics
     nehany jatekosnal, akiknek MA volt meccse vs. vasarnap lesz
  C) FPL: explain ures-e a meg nem jatszott jatekosoknal (GW1 elo)

CSAK OLVAS es nyomtat.
"""
import json, sys, time, urllib.error, urllib.parse, urllib.request

API = "https://fantasy-api.mlsz.hu/"
M_BASE = API + "competitions/3/"
F_BASE = "https://draft.premierleague.com/api/"
HDRS = {"Accept": "application/json", "User-Agent": "funtasy-archiver/1.0",
        "Referer": "https://fantasy.mlsz.hu/"}
ALAP_INC = ("position,competition_player,competition_player.team,"
            "competition_player.countries,summary_statistics")


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
    print("========== A) game-player-stats cimkekkel ==========")
    st, j = get(API + "game-player-stats?include=competition_stat_config"
                "&filter%5Bcompetition_player_id%5D=1305&filter%5Bround_id%5D=83")
    if st == 200 and j and j.get("data"):
        for sor in j["data"]:
            cfg = (sor.get("competition_stat_config") or {})
            print("  %-40s value=%-6s points=%s" % (cfg.get("name"), sor.get("value"), sor.get("points")))
    else:
        print("HTTP %s" % st)

    print("\n========== B) elo fordulo (85): jatszott-jelzok ==========")
    st, j = get(M_BASE + "user-team-players-history?include=" + urllib.parse.quote(ALAP_INC)
                + "&filter%5Buser_id%5D=5483&filter%5Bround_id%5D=85")
    if st == 200 and j and j.get("data"):
        for d in j["data"]:
            cp = d.get("competition_player") or {}
            cr = cp.get("current_round") or {}
            print("  %-22s %-8s is_played=%-5s has_stats=%-5s first_played_at=%s  hetipont=%s"
                  % (cp.get("last_name"), (cp.get("team") or {}).get("short_name"),
                     cr.get("is_played"), cr.get("has_statistics"), cr.get("first_played_at"),
                     (d.get("summary_statistics") or {}).get("weekly_points")))
    else:
        print("HTTP %s" % st)

    print("\n========== C) FPL: explain ures-e nem jatszottnal ==========")
    st, j = get(F_BASE + "event/1/live")
    if st == 200 and isinstance(j, dict):
        el = j.get("elements") or {}
        jatszott = nem = None
        for k, v in el.items():
            mins = ((v or {}).get("stats") or {}).get("minutes") or 0
            if mins > 0 and jatszott is None:
                jatszott = (k, v)
            if mins == 0 and nem is None:
                nem = (k, v)
            if jatszott and nem:
                break
        for cimke, valasztott in (("JATSZOTT", jatszott), ("NEM JATSZOTT", nem)):
            if not valasztott:
                print("  %s: nincs ilyen elem" % cimke); continue
            k, v = valasztott
            print("  %s (#%s): minutes=%s total=%s explain=%s"
                  % (cimke, k, (v.get("stats") or {}).get("minutes"),
                     (v.get("stats") or {}).get("total_points"),
                     json.dumps(v.get("explain"), ensure_ascii=False)[:200]))
    else:
        print("live HTTP %s" % st)

    print("\nDiagnosztika vege - semmit nem irt.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
