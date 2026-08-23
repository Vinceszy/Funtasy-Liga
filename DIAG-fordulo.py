#!/usr/bin/env python3
"""EGYSZERI felderites, 2. kor: hol van a FORDULO-SZINTU allapot?

Az elso kor: nincs onallo rounds-vegpont (404). Viszont a ranglista-valaszban
ott a user_team.round_played_player_count. Most a verseny-objektumot es a
kapcsolodo include-okat nezzuk - ott lenne a helye egy "aktualis / lezart
fordulo" jelzesnek. Csak olvas.
"""
import json, urllib.parse, urllib.request

BASE = "https://fantasy-api.mlsz.hu/"
HDRS = {"Accept": "application/json", "User-Agent": "funtasy-diag/1.0",
        "Referer": "https://fantasy.mlsz.hu/"}


def get(ut):
    try:
        with urllib.request.urlopen(urllib.request.Request(BASE + ut, headers=HDRS), timeout=30) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return getattr(e, "code", None) or str(e), None


def kiir(ut, hossz=1500):
    st, j = get(ut)
    print("\n=== %s  ->  HTTP %s" % (ut[:120], st))
    if isinstance(j, dict):
        print("    %s" % json.dumps(j, ensure_ascii=False)[:hossz])
    return j


# 1) maga a verseny - itt lehet "aktualis fordulo" / "lezart fordulo"
kiir("competitions/3")
kiir("competitions/3?include=current_round,next_round,last_round,rounds")
kiir("competitions")

# 2) a ranglista teljes user_team resze: mit ad a round_played_player_count?
st, j = get("competitions/3/rankings?include=user_team.user.id,summary_statistics,"
            "ranking,rounds,competition_rank&page=1&per_page=3")
print("\n=== rankings (per_page=3) -> HTTP %s" % st)
for d in ((j or {}).get("data") or [])[:3]:
    ut_ = d.get("user_team") or {}
    print("    %-14s round_played_player_count=%s  utolso ket fordulo: %s"
          % ((ut_.get("user") or {}).get("username"),
             ut_.get("round_played_player_count"),
             [(s.get("round_number"), s.get("points")) for s in (ut_.get("round_statistics") or [])]))

# 3) a keret-valaszban van-e fordulo-objektum, nem csak jatekos-szintu mezo?
st, j = get("competitions/3/user-team-players-history?include=competition_player.current_round"
            "&filter%5Buser_id%5D=5299&filter%5Bround_id%5D=85&per_page=1")
print("\n=== keret-valasz teteje -> HTTP %s" % st)
if isinstance(j, dict):
    print("    valasz kulcsok: %s" % sorted(j))
    for k in ("meta", "links", "round", "competition_round"):
        if k in j:
            print("    %s: %s" % (k, json.dumps(j[k], ensure_ascii=False)[:600]))
    d0 = ((j.get("data") or [None])[0] or {})
    cr = ((d0.get("competition_player") or {}).get("current_round") or {})
    print("    current_round kulcsok: %s" % sorted(cr))
    print("    current_round: %s" % json.dumps(cr, ensure_ascii=False)[:600])

print("\n--- vege ---")
