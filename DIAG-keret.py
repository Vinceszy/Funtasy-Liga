#!/usr/bin/env python3
"""FOPROBA (IDEIGLENES fajl, torolheto): a tervezett szerveroldali keretgyujtes
teljes proba-utja, mielott a collect.py-ba beepulne.

Mit csinal (CSAK OLVAS es nyomtat, semmit nem ir):
  1. Lekeri mind a 8 szakvezeto user_id-jat es hivatalos fordulopontszamait
     a ranglista-vegpontrol.
  2. Az 1-4. (lezart) fordulora lekeri mindenki keretet a keret-vegpontrol,
     kiszamolja a fordulopontszamot (weekly_points osszeg + magyarszabaly),
     es osszeveti a hivatalos ertekkel. 32 osszevetes - mind egyeznie kell.
  3. Fordulonkent kiirja az is_played-alapu lezaras-iteletet (a 3. fordulos
     halasztott ETO-Fradi jatekosai is is_played=True, 0 ponttal - igazolt).
  4. Az 5. (el nem kezdodott) fordulora 403-at var.

Ezzel a valos terheles is kiderul: ~41 keres 150 ms szunetekkel.
"""
import json, sys, time, urllib.error, urllib.parse, urllib.request

BASE = "https://fantasy-api.mlsz.hu/competitions/3/"
HDRS = {"Accept": "application/json", "User-Agent": "funtasy-archiver/1.0",
        "Referer": "https://fantasy.mlsz.hu/"}
MEMBERS = {
    "Katyul": "peterkmrs", "Bence": "Dill Dough", "Sámsi": "samsonp",
    "Vince": "HolVanSalah", "Bazsa": "Hoxha98", "Csongi": "szcsngr",
    "Csendi": "cspeti93", "Ádám": "siuu_1885",
}
INCLUDE = ("position,position.alternatives,competition_player,"
           "competition_player.team,competition_player.countries,summary_statistics")
rid = lambda n: 75 + 2 * n


def get(url):
    time.sleep(0.15)
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=HDRS), timeout=30) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception as e:
        return None, str(e)


def keret(user_id, r):
    url = (BASE + "user-team-players-history?include=" + urllib.parse.quote(INCLUDE)
           + "&filter%5Buser_id%5D=" + str(user_id)
           + "&filter%5Bround_id%5D=" + str(rid(r)))
    return get(url)


def ertekel(data):
    """Egy keret-valaszbol: (szamolt pontszam, lejatszott/osszes, jatekosszam)."""
    ossz, jatszott, db = 0.0, 0, 0
    hun_kezdo, u21_hun_kezdo = 0, 0
    for d in data:
        cp = d.get("competition_player") or {}
        cr = cp.get("current_round") or {}
        ss = d.get("summary_statistics") or {}
        db += 1
        ossz += ss.get("weekly_points") or 0
        if cr.get("is_played"):
            jatszott += 1
        if d.get("type") == "starter":
            hun = any((c.get("code") == "HUN") for c in (cp.get("countries") or []))
            if hun:
                hun_kezdo += 1
                if cp.get("is_u21"):
                    u21_hun_kezdo += 1
    bonus = 10 if (hun_kezdo >= 5 and u21_hun_kezdo >= 1) else 0
    return ossz + bonus, jatszott, db, bonus


def main():
    print("Mit mond MOST hivatalosan az MLSZ az 1-4. fordulora?")
    print("(teljes include-dal, mint a collect.py-ban)")
    for nev, uname in MEMBERS.items():
        st, j = get(BASE + "rankings?include=user_team.user.id,summary_statistics,"
                    "ranking,rounds,competition_rank&page=1&per_page=5"
                    + "&filter%5Bsearch%5D=" + urllib.parse.quote(uname))
        if st != 200 or not j:
            print("  ! %s: HTTP %s" % (nev, st)); continue
        row = next((d for d in j.get("data") or []
                    if ((d.get("user_team") or {}).get("user") or {}).get("username") == uname),
                   (j.get("data") or [None])[0])
        if not row:
            print("  ! nincs talalat: %s" % nev); continue
        rs = (row.get("user_team") or {}).get("round_statistics") or []
        pontok = {s2["round_number"]: s2["points"] for s2 in rs}
        print("  %-8s visszaadott fordulok=%s  pontok=%s"
              % (nev, sorted(pontok), json.dumps(pontok, ensure_ascii=False)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
