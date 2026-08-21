#!/usr/bin/env python3
"""Egyszeri diagnosztika, 12. kor (IDEIGLENES): a "jatszott mar?" jelzo forrasa.

A 11. kor szerint az elo fordulonal a current_round (is_played) hianyzik
az alap include-dal. Ez a kor:
  A) elo fordulo (85) explicit competition_player.current_round include-dal
  B) a fordulo meccslistaja egy hivassal: games?filter[round_id]
  C) FPL: event/1/fixtures - meccs-allapotok a GW-ben

CSAK OLVAS es nyomtat.
"""
import json, sys, time, urllib.error, urllib.parse, urllib.request

M_BASE = "https://fantasy-api.mlsz.hu/competitions/3/"
F_BASE = "https://draft.premierleague.com/api/"
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
    print("========== A) elo fordulo explicit current_round include-dal ==========")
    inc = ("competition_player,competition_player.team,"
           "competition_player.current_round,summary_statistics")
    st, j = get(M_BASE + "user-team-players-history?include=" + urllib.parse.quote(inc)
                + "&filter%5Buser_id%5D=5483&filter%5Bround_id%5D=85")
    if st == 200 and j and j.get("data"):
        for d in j["data"][:15]:
            cp = d.get("competition_player") or {}
            cr = cp.get("current_round") or {}
            print("  %-22s %-8s is_played=%-5s has_stats=%-5s first_played_at=%-25s hetipont=%s"
                  % (cp.get("last_name"), (cp.get("team") or {}).get("short_name"),
                     cr.get("is_played"), cr.get("has_statistics"), cr.get("first_played_at"),
                     (d.get("summary_statistics") or {}).get("weekly_points")))
    else:
        print("HTTP %s" % st)

    print("\n========== B) meccslista-vegpont probak ==========")
    for p in ("games?filter%5Bround_id%5D=85",
              "games?filter%5Bround_id%5D=85&include=home_team,away_team",
              "rounds?filter%5Bid%5D=85&include=games",
              "rounds/85?include=games,games.home_team,games.away_team"):
        st, j = get(M_BASE + p)
        rov = json.dumps(j, ensure_ascii=False)[:900] if st == 200 else ""
        print("GET %s -> HTTP %s %s\n" % (p.split("?")[0], st, rov))

    print("========== C) FPL fixtures ==========")
    for p in ("event/1/fixtures", "fixtures?event=1"):
        st, j = get(F_BASE + p)
        if st == 200 and isinstance(j, list) and j:
            print("GET %s -> 200; elso elem: %s" % (p, json.dumps(j[0], ensure_ascii=False)[:600]))
            print("  osszesen %d meccs; kulcsok: %s" % (len(j), sorted(j[0].keys())))
            break
        print("GET %s -> HTTP %s" % (p, st))

    print("\nDiagnosztika vege - semmit nem irt.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
