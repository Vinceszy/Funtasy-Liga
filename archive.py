#!/usr/bin/env python3
"""FunTasy Liga - archivalo + keret-pillanatkep.

1) results.json : a lejatszott fordulok eredmenyei (archivum, nem vesz el)
2) squads.json  : a 8 tag aktualis kerete nevekkel, pontokkal (az oldal ebbol tolt -> gyors)
"""
import json, sys, time, urllib.parse, urllib.request

COMPETITION = 3
MEMBERS = {
    "Katyul": "peterkmrs", "Bence": "Dill Dough", "Sámsi": "samsonp",
    "Vince": "HolVanSalah", "Bazsa": "Hoxha98", "Csongi": "szcsngr",
    "Csendi": "cspeti93", "Ádám": "siuu_1885",
}
BASE = "https://fantasy-api.mlsz.hu/competitions/{c}".format(c=COMPETITION)
HDRS = {"Accept": "application/json", "User-Agent": "funtasy-liga-archiver/1.0",
        "Referer": "https://fantasy.mlsz.hu/"}


def get(url, retries=3):
    for i in range(retries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=HDRS), timeout=45) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            if i == retries - 1:
                print("  ! %s -> %s" % (url[:80], e), file=sys.stderr)
                return None
            time.sleep(4)


def deep_name(o, depth=0):
    """Nevet keres a valasz beagyazott szerkezeteben, barhol is legyen."""
    if not isinstance(o, dict) or depth > 6:
        return None
    f = o.get("first_name") or o.get("firstname")
    l = o.get("last_name") or o.get("lastname")
    if f or l:
        return " ".join(x for x in (f, l) if x)
    for k in ("name", "short_name", "display_name"):
        v = o.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    for v in o.values():
        if isinstance(v, dict):
            r = deep_name(v, depth + 1)
            if r:
                return r
    return None


def ranking_row(username):
    url = (BASE + "/rankings?include=user_team.user.id,summary_statistics,ranking,rounds,"
           "competition_rank&page=1&per_page=5&filter%5Bsearch%5D=" + urllib.parse.quote(username))
    j = get(url)
    if not j:
        return None
    rows = j.get("data") or []
    for d in rows:
        if ((d.get("user_team") or {}).get("user") or {}).get("username") == username:
            return d
    return rows[0] if rows else None


def squad_of(user_id):
    url = (BASE + "/user-team-players-history?include=competition_player.player,"
           "competition_player.team&filter%5Buser_id%5D=" + str(user_id))
    j = get(url)
    if not j or not isinstance(j.get("data"), list):
        j = get(BASE + "/user-team-players-history?filter%5Buser_id%5D=" + str(user_id))
    if not j or not isinstance(j.get("data"), list):
        return None
    out = []
    for d in j["data"]:
        cp = d.get("competition_player") or {}
        team = cp.get("team") or {}
        stats = d.get("summary_statistics") or {}
        out.append({
            "name": deep_name(cp) or ("#%s" % (d.get("competition_player_id") or d.get("id"))),
            "team": team.get("short_name") or team.get("name") or "",
            "cap": bool(d.get("is_captain")),
            "sub": d.get("type") == "substitutes",
            "week": stats.get("weekly_points", 0),
            "total": stats.get("competition_points", 0),
        })
    return out


def main():
    with open("results.json", encoding="utf-8") as f:
        data = json.load(f)
    schedule = data["schedule"]

    points, squads = {}, {}
    for name, uname in MEMBERS.items():
        row = ranking_row(uname)
        if not row:
            print("  ! nincs talalat: %s" % uname, file=sys.stderr)
            continue
        ut = row.get("user_team") or {}
        points[name] = {int(s["round_number"]): s["points"]
                        for s in (ut.get("round_statistics") or [])}
        uid = (ut.get("user") or {}).get("id")
        if uid:
            sq = squad_of(uid)
            if sq:
                squads[name] = sq
        print("  %s: fordulok=%s, keret=%d fo" % (name, sorted(points.get(name, {})), len(squads.get(name, []))))

    filled = 0
    for rnd, matches in schedule.items():
        r = int(rnd)
        for m in matches:
            if m[2] is None and points.get(m[0], {}).get(r) is not None \
                            and points.get(m[1], {}).get(r) is not None:
                m[2], m[3] = points[m[0]][r], points[m[1]][r]
                filled += 1
                print("  + %d. fordulo: %s %s - %s %s" % (r, m[0], m[2], m[3], m[1]))

    stamp = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    if filled:
        data["updated"] = stamp
        with open("results.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=0)
    if squads:
        with open("squads.json", "w", encoding="utf-8") as f:
            json.dump({"updated": stamp, "squads": squads}, f, ensure_ascii=False, indent=0)
    print("Kesz: %d uj eredmeny, %d keret mentve." % (filled, len(squads)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
