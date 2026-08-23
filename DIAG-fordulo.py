#!/usr/bin/env python3
"""EGYSZERI felderites, 6. kor: mi lett a KIMARADT meccs jatekosainak
is_played statuszabol, ha a fordulo mar reg lezarult?

A tarolt pillanatkepekbol annyi latszik, hogy a 3. forduloban az ETO
minden jatekosa 0 pontos (ott maradt ki meccs), a 4.-ben viszont mindenki
played=True. A tarolt kep viszont a lekereskori allapot - most azt
kerdezzuk meg, mit mond az API MA a regi fordulokrol. Csak olvas.
"""
import json, urllib.parse, urllib.request

BASE = "https://fantasy-api.mlsz.hu/competitions/3/"
HDRS = {"Accept": "application/json", "User-Agent": "funtasy-diag/1.0",
        "Referer": "https://fantasy.mlsz.hu/"}
INCLUDE = ("position,competition_player,competition_player.team,"
           "competition_player.current_round,competition_player.current_round.games,"
           "summary_statistics")


def hoz(url, timeout=60):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=HDRS), timeout=timeout) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return getattr(e, "code", None) or ("%s: %s" % (type(e).__name__, e)), None


# a verseny aktualis forduloja - viszonyitasnak
st, j = hoz("https://fantasy-api.mlsz.hu/competitions?include=current_round")
comp = next((c for c in ((j or {}).get("data") or []) if c.get("id") == 3), {})
print("=== aktualis fordulo az MLSZ szerint: %s" % json.dumps(comp.get("current_round"), ensure_ascii=False))

# felhasznalo-azonosito
UNAME = "peterkmrs"
st, j = hoz(BASE + "rankings?include=user_team.user.id,summary_statistics,ranking,rounds,"
            "competition_rank&page=1&per_page=5&filter%5Bsearch%5D=" + urllib.parse.quote(UNAME))
rows = (j or {}).get("data") or []
sor = next((d for d in rows
            if ((d.get("user_team") or {}).get("user") or {}).get("username") == UNAME),
           rows[0] if rows else {})
uid = (((sor.get("user_team") or {}).get("user") or {}).get("id"))
print("=== %s user_id = %s (HTTP %s, %d talalat)" % (UNAME, uid, st, len(rows)))

for r_no in (3, 4, 5):
    rid = 75 + 2 * r_no
    url = (BASE + "user-team-players-history?include=" + urllib.parse.quote(INCLUDE)
           + "&filter%5Buser_id%5D=" + str(uid) + "&filter%5Bround_id%5D=" + str(rid))
    st, j = hoz(url)
    sorok = (j or {}).get("data") or []
    print("\n=== %d. fordulo (round_id=%s) -> HTTP %s, %d jatekos" % (r_no, rid, st, len(sorok)))
    print("    %-26s %-8s %-7s %-6s  %s" % ("jatekos", "csapat", "played", "pont", "meccs"))
    for d in sorok:
        cp = d.get("competition_player") or {}
        cr = cp.get("current_round") or {}
        ss = d.get("summary_statistics") or {}
        games = cr.get("games")
        if games is None:
            m = "(nincs games)"
        elif not games:
            m = "NINCS MECCSE"
        else:
            g = games[0] or {}
            m = "%s @ %s" % (g.get("status"), g.get("start_at"))
        print("    %-26s %-8s %-7s %-6s  %s" % (
            (" ".join(x for x in (cp.get("first_name"), cp.get("last_name")) if x))[:26],
            ((cp.get("team") or {}).get("short_name") or "")[:8],
            cr.get("is_played"), ss.get("weekly_points"), m))
    # a fordulo-objektum kulcsai: van-e barmi ujdonsag a regi fordulonal
    d0 = (sorok or [{}])[0]
    cr0 = ((d0.get("competition_player") or {}).get("current_round") or {})
    print("    current_round kulcsok: %s" % sorted(cr0))

print("\n--- vege ---")
