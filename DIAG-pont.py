#!/usr/bin/env python3
"""Egyszeri diagnosztika (IDEIGLENES): honnan jon a pont-BONTAS?

1. MLSZ: a felulet jatekos-modalja mutatja, mibol epul a heti pont
   (gyozelem 3, gol 3, percek 2, parharcok, kulcspasszok...). Melyik
   include vagy vegpont adja ki?
2. FPL: az event/{gw}/live elemei milyen statisztikat es 'explain'
   bontast hordoznak, es a bootstrap settings.scoring mit tartalmaz?

CSAK OLVAS es nyomtat.
"""
import json, sys, time, urllib.parse, urllib.request

M_BASE = "https://fantasy-api.mlsz.hu/competitions/3/"
F_BASE = "https://draft.premierleague.com/api/"
HDRS = {"Accept": "application/json", "User-Agent": "funtasy-archiver/1.0",
        "Referer": "https://fantasy.mlsz.hu/"}
ALAP_INC = ("position,position.alternatives,competition_player,"
            "competition_player.team,competition_player.countries,summary_statistics")


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
import urllib.error


def kulcsok(x):
    return sorted(x.keys()) if isinstance(x, dict) else type(x).__name__


def main():
    print("========== 1. MLSZ: pont-bontas keresese ==========")
    # alap: Vince (5483) 4. fordulo (83) - lezart, biztos van statisztika
    alap_url = (M_BASE + "user-team-players-history?include=" + urllib.parse.quote(ALAP_INC)
                + "&filter%5Buser_id%5D=5483&filter%5Bround_id%5D=83")
    st, j = get(alap_url)
    alap_kulcsok = set()
    if st == 200 and j and j.get("data"):
        d = j["data"][0]
        alap_kulcsok = set(d.keys()) | {"cp." + k for k in (d.get("competition_player") or {})}
        print("alap (referencia) HTTP 200; jatekos-kulcsok: %s" % sorted(d.keys()))
        print("  cp-kulcsok: %s" % sorted((d.get("competition_player") or {}).keys()))

    variansok = [
        "statistics",
        "round_statistics",
        "player_statistics",
        "competition_player.statistics",
        "competition_player.round_statistics",
        "competition_player.player_statistics",
        "competition_player.current_round.statistics",
        "competition_player.current_round.player_statistics",
        "competition_player.current_round.round_player_statistic",
        "competition_player.current_round.statistic",
    ]
    for v in variansok:
        url = (M_BASE + "user-team-players-history?include=" + urllib.parse.quote(ALAP_INC + "," + v)
               + "&filter%5Buser_id%5D=5483&filter%5Bround_id%5D=83")
        st, j = get(url)
        if st != 200 or not j or not j.get("data"):
            print("+%s -> HTTP %s" % (v, st)); continue
        d = j["data"][0]
        uj = (set(d.keys()) | {"cp." + k for k in (d.get("competition_player") or {})}) - alap_kulcsok
        cr = ((d.get("competition_player") or {}).get("current_round") or {})
        print("+%s -> 200; UJ kulcsok: %s | current_round kulcsai: %s"
              % (v, sorted(uj) or "-", sorted(cr.keys())))
        for k in uj:
            ertek = d.get(k) if not k.startswith("cp.") else (d.get("competition_player") or {}).get(k[3:])
            print("    %s = %s" % (k, json.dumps(ertek, ensure_ascii=False)[:400]))

    # kulon vegpont-jeloltek (1305 = Umathum)
    print("\n--- kulon vegpont-jeloltek ---")
    for utvonal in ("player-statistics?filter%5Bcompetition_player_id%5D=1305&filter%5Bround_id%5D=83",
                    "competition-player-statistics?filter%5Bcompetition_player_id%5D=1305&filter%5Bround_id%5D=83",
                    "statistics?filter%5Bcompetition_player_id%5D=1305&filter%5Bround_id%5D=83",
                    "round-player-statistics?filter%5Bcompetition_player_id%5D=1305&filter%5Bround_id%5D=83",
                    "competition-players/1305?include=current_round.statistics",
                    "competition-players/1305/statistics?filter%5Bround_id%5D=83"):
        st, j = get(M_BASE + utvonal)
        rov = json.dumps(j, ensure_ascii=False)[:300] if isinstance(j, (dict, list)) else str(j)[:120]
        print("GET %s -> HTTP %s %s" % (utvonal.split("?")[0], st, rov if st == 200 else ""))

    print("\n========== 2. FPL: live statisztika es scoring ==========")
    st, j = get(F_BASE + "event/1/live")
    if st == 200 and isinstance(j, dict):
        el = j.get("elements") or {}
        # egy olyan elem, akinek mar van pontja, ha letezik
        valasztott = None
        if isinstance(el, dict):
            for k, v in el.items():
                if ((v or {}).get("stats") or {}).get("total_points"):
                    valasztott = (k, v); break
            if not valasztott and el:
                k = next(iter(el)); valasztott = (k, el[k])
        if valasztott:
            k, v = valasztott
            print("live elem #%s kulcsai: %s" % (k, kulcsok(v)))
            print("  stats: %s" % json.dumps(v.get("stats"), ensure_ascii=False)[:500])
            print("  explain: %s" % json.dumps(v.get("explain"), ensure_ascii=False)[:600])
        else:
            print("live: nincs elem")
    else:
        print("live HTTP %s" % st)

    st, j = get(F_BASE + "bootstrap-static")
    if st == 200 and isinstance(j, dict):
        se = j.get("settings") or {}
        print("settings kulcsai: %s" % kulcsok(se))
        print("  scoring: %s" % json.dumps(se.get("scoring"), ensure_ascii=False)[:600])

    print("\nDiagnosztika vege - semmit nem irt.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
