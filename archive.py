#!/usr/bin/env python3
"""FunTasy Liga - heti archivalo.
Lekeri a 8 tag fordulonkenti pontjait az MLSZ fantasy API-bol,
es beirja a results.json-ba azokat az eredmenyeket, amik meg hianyoznak.
Csak akkor ir, ha tenylegesen valtozott valami.
"""
import json, sys, time, urllib.parse, urllib.request

COMPETITION = 3
MEMBERS = {
    "Katyul": "peterkmrs", "Bence": "Dill Dough", "Sámsi": "samsonp",
    "Vince": "HolVanSalah", "Bazsa": "Hoxha98", "Csongi": "szcsngr",
    "Csendi": "cspeti93", "Ádám": "siuu_1885",
}
API = ("https://fantasy-api.mlsz.hu/competitions/{c}/rankings"
       "?include=user_team.user.id,summary_statistics,ranking,rounds,competition_rank"
       "&page=1&per_page=5&filter%5Bsearch%5D={q}")


def fetch(username, retries=3):
    url = API.format(c=COMPETITION, q=urllib.parse.quote(username))
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                "Accept": "application/json",
                "User-Agent": "funtasy-liga-archiver/1.0",
            })
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            if attempt == retries - 1:
                print(f"  ! {username}: {e}", file=sys.stderr)
                return None
            time.sleep(3)


def main():
    with open("results.json", encoding="utf-8") as f:
        data = json.load(f)
    schedule = data["schedule"]

    points = {}   # nev -> {fordulo: pont}
    for name, uname in MEMBERS.items():
        j = fetch(uname)
        if not j:
            continue
        rows = j.get("data") or []
        row = next((d for d in rows
                    if (d.get("user_team") or {}).get("user", {}).get("username") == uname), None)
        if row is None:
            row = rows[0] if rows else None
        if row is None:
            print(f"  ! nincs talalat: {uname}", file=sys.stderr)
            continue
        stats = (row.get("user_team") or {}).get("round_statistics") or []
        points[name] = {int(s["round_number"]): s["points"] for s in stats}
        print(f"  {name}: {sorted(points[name])}")

    filled = 0
    for rnd, matches in schedule.items():
        r = int(rnd)
        for m in matches:
            home, away = m[0], m[1]
            if m[2] is None and points.get(home, {}).get(r) is not None \
                            and points.get(away, {}).get(r) is not None:
                m[2] = points[home][r]
                m[3] = points[away][r]
                filled += 1
                print(f"  + {r}. fordulo: {home} {m[2]} - {m[3]} {away}")

    if filled:
        data["updated"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        with open("results.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=0)
        print(f"Kesz: {filled} uj eredmeny archivalva.")
    else:
        print("Nincs uj archivalando eredmeny.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
