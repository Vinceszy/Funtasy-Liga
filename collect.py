#!/usr/bin/env python3
"""FunTasy Liga - H2H eredmenyek automatikus archivalasa.

A ranglista-vegpont adatkozponti IP-rol is elerheto, ezert ez a resz teljesen automata.
A KERETEK gyujtese NEM itt tortenik: azt a vegpontot az MLSZ 403-mal tiltja szerverrol,
arra a bongeszos konyvjelzo valo (lasd KERET-MENTES.md).
"""
import json, os, sys, time, urllib.parse, urllib.request

COMPETITION = 3
MEMBERS = {
    "Katyul": "peterkmrs", "Bence": "Dill Dough", "Sámsi": "samsonp",
    "Vince": "HolVanSalah", "Bazsa": "Hoxha98", "Csongi": "szcsngr",
    "Csendi": "cspeti93", "Ádám": "siuu_1885",
}
API = ("https://fantasy-api.mlsz.hu/competitions/%d/rankings?include=user_team.user.id,"
       "summary_statistics,ranking,rounds,competition_rank&page=1&per_page=5&filter%%5Bsearch%%5D=")
HDRS = {"Accept": "application/json", "User-Agent": "funtasy-archiver/1.0",
        "Referer": "https://fantasy.mlsz.hu/"}


def fetch(username, retries=3):
    url = (API % COMPETITION) + urllib.parse.quote(username)
    for i in range(retries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=HDRS), timeout=30) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            if i == retries - 1:
                print("  ! %s: %s" % (username, e), file=sys.stderr)
                return None
            time.sleep(3)


def main():
    with open("results.json", encoding="utf-8") as f:
        data = json.load(f)
    schedule = data["schedule"]

    points = {}
    for name, uname in MEMBERS.items():
        j = fetch(uname)
        rows = (j or {}).get("data") or []
        row = next((d for d in rows
                    if ((d.get("user_team") or {}).get("user") or {}).get("username") == uname),
                   rows[0] if rows else None)
        if not row:
            print("  ! nincs talalat: %s" % uname, file=sys.stderr)
            continue
        stats = (row.get("user_team") or {}).get("round_statistics") or []
        points[name] = {int(s["round_number"]): s["points"] for s in stats}
        print("  %s: fordulok=%s" % (name, sorted(points[name])))

    filled = 0
    for rnd, matches in schedule.items():
        r = int(rnd)
        for m in matches:
            if m[2] is not None:
                continue
            hp, vp = points.get(m[0], {}).get(r), points.get(m[1], {}).get(r)
            if hp is None or vp is None:
                continue
            if not hp and not vp:          # 0-0 = a fordulo meg nem zarult le
                print("  . %d. fordulo meg nem lezart (%s-%s)" % (r, m[0], m[1]))
                continue
            m[2], m[3] = hp, vp
            filled += 1
            print("  + %d. fordulo: %s %s - %s %s" % (r, m[0], hp, vp, m[1]))

    if filled:
        data["updated"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        with open("results.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=0)
    print("Kesz: %d uj eredmeny." % filled)
    return 0


if __name__ == "__main__":
    sys.exit(main())
