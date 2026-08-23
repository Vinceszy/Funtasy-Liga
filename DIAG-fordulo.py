#!/usr/bin/env python3
"""EGYSZERI felderites, 7. kor: mit mond az MLSZ a 3. fordulos ETO-rol?

Az oldal a regi fordulo bontasanal ELOBEN keri le a keretet (a tarolt
rekordban nincs id/played), es a current_round.first_played_at-bol irja ki a
kezdesi idot. Egy ETO-jatekosnal ez "aug. 15. (idopont meg nincs kituzve)"
lett - vagyis ejfeles helyorzo. Most megnezzuk, pontosan mit ad az API:
first_played_at, has_statistics, es a meccslista - a 3. es a 4. fordulora,
egy ETO- es egy kontroll-jatekosra. Csak olvas.
"""
import json, urllib.parse, urllib.request

BASE = "https://fantasy-api.mlsz.hu/competitions/3/"
HDRS = {"Accept": "application/json", "User-Agent": "funtasy-diag/1.0",
        "Referer": "https://fantasy.mlsz.hu/"}
# ugyanaz az include, amit az oldal hasznal a bontasnal (games NELKUL),
# es egy masodik, amiben a meccslista is benne van
INC1 = ("position,competition_player,competition_player.team,"
        "competition_player.current_round,summary_statistics")
INC2 = INC1 + ",competition_player.current_round.games"


def hoz(url, timeout=60):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=HDRS), timeout=timeout) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return getattr(e, "code", None) or ("%s: %s" % (type(e).__name__, e)), None


st, j = hoz(BASE + "rankings?include=user_team.user.id,summary_statistics,ranking,rounds,"
            "competition_rank&page=1&per_page=5&filter%5Bsearch%5D=" + urllib.parse.quote("peterkmrs"))
rows = (j or {}).get("data") or []
uid = ((((rows or [{}])[0].get("user_team") or {}).get("user") or {}).get("id"))
print("=== user_id = %s" % uid)

for cimke, inc in (("az oldal include-ja (games nelkul)", INC1), ("meccslistaval", INC2)):
    for r_no in (3, 4):
        url = (BASE + "user-team-players-history?include=" + urllib.parse.quote(inc)
               + "&filter%5Buser_id%5D=" + str(uid) + "&filter%5Bround_id%5D=" + str(75 + 2 * r_no))
        st, j = hoz(url)
        print("\n=== %d. fordulo, %s -> HTTP %s" % (r_no, cimke, st))
        for d in ((j or {}).get("data") or []):
            cp = d.get("competition_player") or {}
            team = (cp.get("team") or {}).get("short_name") or ""
            if team not in ("ETO", "MTK"):      # egy erintett + egy kontroll klub
                continue
            cr = cp.get("current_round") or {}
            g = cr.get("games")
            print("    %-22s %-5s is_played=%-5s has_statistics=%-5s pont=%-6s"
                  % ((" ".join(x for x in (cp.get("first_name"), cp.get("last_name")) if x))[:22],
                     team, cr.get("is_played"), cr.get("has_statistics"),
                     (d.get("summary_statistics") or {}).get("weekly_points")))
            print("        first_played_at = %s" % cr.get("first_played_at"))
            print("        round_id a valaszban = %s | games = %s"
                  % (cr.get("round_id"),
                     "nem kertuk" if g is None else (json.dumps(g, ensure_ascii=False)[:200] or "[]")))

print("\n--- vege ---")
