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
           + "&filter%5Buser_id%5D=%d&filter%5Bround_id%5D=%d" % (user_id, rid(r)))
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
    print("FOPROBA: szerveroldali keretgyujtes, 8 szakvezeto x 4 fordulo")

    # ---- 1. azonositok es hivatalos pontok ----
    ids, hivatalos = {}, {}
    for nev, uname in MEMBERS.items():
        st, j = get(BASE + "rankings?include=user_team.user.id,rounds&per_page=5"
                    + "&filter%5Bsearch%5D=" + urllib.parse.quote(uname))
        if st != 200 or not j:
            print("  ! ranglista-hiba: %s (HTTP %s)" % (nev, st)); continue
        row = next((d for d in j.get("data") or []
                    if ((d.get("user_team") or {}).get("user") or {}).get("username") == uname),
                   (j.get("data") or [None])[0])
        if not row:
            print("  ! nincs talalat: %s" % nev); continue
        ids[nev] = row["user_team"]["user"]["id"]
        hivatalos[nev] = {s["round_number"]: s["points"]
                          for s in (row["user_team"].get("round_statistics") or [])}
    print("  azonositok: %d/8 megvan" % len(ids))

    # ---- 2-3. keretek + osszevetes fordulonkent ----
    egyezik, osszes_proba = 0, 0
    for r in (1, 2, 3, 4):
        print("\n=== %d. fordulo (round_id=%d) ===" % (r, rid(r)))
        mind_jatszott, mind_megvan = True, True
        for nev, uid in ids.items():
            st, j = keret(uid, r)
            if st != 200 or not isinstance(j, dict):
                print("  ! %-8s HTTP %s" % (nev, st)); mind_megvan = False; continue
            szamolt, jatszott, db, bonus = ertekel(j.get("data") or [])
            hiv = hivatalos.get(nev, {}).get(r)
            osszes_proba += 1
            if hiv is not None and abs(szamolt - hiv) < 0.01:
                egyezik += 1; jel = "OK"
            else:
                jel = "ELTER!"
            if jatszott < db:
                mind_jatszott = False
            print("  %-8s szamolt=%-7.2f hivatalos=%-7s bonus=%-3d jatszott=%d/%d  %s"
                  % (nev, szamolt, hiv, bonus, jatszott, db, jel))
        print("  -> lezaras-itelet: %s"
              % ("LEZART (minden jatekos jatszott)" if (mind_megvan and mind_jatszott)
                 else "MEG TART / hianyos"))

    # ---- 4. el nem kezdodott fordulo ----
    if ids:
        st, _ = keret(next(iter(ids.values())), 5)
        print("\n=== 5. fordulo (meg el sem kezdodott): HTTP %s — %s ==="
              % (st, "vart 403, rendben" if st == 403 else "VARATLAN!"))

    print("\nOSSZEGZES: %d/%d pontszam egyezik a hivatalossal." % (egyezik, osszes_proba))
    print("Ez a szkript semmit nem irt es nem modositott.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
