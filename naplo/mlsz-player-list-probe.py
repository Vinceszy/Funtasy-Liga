#!/usr/bin/env python3
"""EGYSZERI meres - 7. kor: van-e TELJES MENETREND az MLSZ-nel?

A jatekosprofil elore is felsorolja a fordulokat, es ott a KOVETKEZO
ELLENFELNEK latszania kell (csak a pont ures, amig nincs). Ma a
meccsek.json csak azokat a fordulokat ismeri, amiket a gyujto mar
megjart - a jovo ures.

A kerdes: van-e olyan vegpont, ami egy fordulo (vagy az egesz szezon)
meccseit adja, fuggetlenul attol, hogy lejatszottak-e. Ha van, a gyujto
egyszer lehozza az egeszet, es a profil elore is mutatja az ellenfelet.

Tartalek terv, ha nincs: a keret-vegpont fordulonkent VISSZAADJA a
`competition_player.current_round.games` listat - azt a jovobeli
fordulokra is le lehet kerni, fordulonkent egy keresbol.

Csak olvas; a naplot a workflow commitolja.
"""
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import collect

NAPLO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mlsz-jatekoslista.txt")
sorok = []
ki = sorok.append


def rovidit(v, hossz=140):
    if isinstance(v, str) and len(v) > hossz:
        return "<%d karakteres szoveg>" % len(v)
    if isinstance(v, dict):
        return {k: rovidit(x, hossz) for k, x in v.items()}
    if isinstance(v, list):
        return [rovidit(x, hossz) for x in v[:3]] + (["<+%d elem>" % (len(v) - 3)] if len(v) > 3 else [])
    return v


JOVO = 8                                    # egy meg le nem jatszott fordulo
RID = collect.rid(JOVO)
ki("# 12. KOR: van-e teljes menetrend (jovobeli meccsek) az MLSZ-nel?")
ki("# A profil elore is felsorolja a fordulokat - ott az ELLENFELNEK latszania")
ki("# kell, csak a pont ures. Ma a meccsek.json csak a megjart fordulokat ismeri.")
ki("# Probafordulo: %d. (round_id=%d)" % (JOVO, RID))
ki("")

ki("## 1) onallo meccs-vegpontok")
for cimke, ut in [
    ("games?filter[round_id]", "games?filter%%5Bround_id%%5D=%d" % RID),
    ("competitions/N/games", "competitions/%d/games?filter%%5Bround_id%%5D=%d" % (collect.COMPETITION, RID)),
    ("competitions/N/games (szuro nelkul)", "competitions/%d/games" % collect.COMPETITION),
    ("matches?filter[round_id]", "matches?filter%%5Bround_id%%5D=%d" % RID),
    ("fixtures?filter[round_id]", "fixtures?filter%%5Bround_id%%5D=%d" % RID),
    ("competitions/N/rounds", "competitions/%d/rounds" % collect.COMPETITION),
    ("competitions/N/rounds + games", "competitions/%d/rounds?include=games" % collect.COMPETITION),
]:
    st, j = collect.api_get(collect.ROOT + ut)
    if not isinstance(j, dict):
        ki("=== %-38s -> HTTP %s" % (cimke, st))
        continue
    adat = j.get("data")
    n = len(adat) if isinstance(adat, list) else ("dict" if adat else 0)
    meta = j.get("meta") or {}
    ki("=== %-38s -> HTTP %s | data: %s | total=%s" % (cimke, st, n, meta.get("total")))
    if adat:
        minta = adat[0] if isinstance(adat, list) else adat
        ki("    kulcsok: %s" % sorted(minta.keys()))
        ki("    %s" % json.dumps(rovidit(minta), ensure_ascii=False)[:600])

# ---- 2) A jatekos-adatlap MEGVAN, de nem ad ellenfelet ----
# competitions/3/players/{id}: gyoker-szintu mezok (nincs "data" burok!),
# benne `countries` (magyar jelzes), `extended_summary_statistics`, es egy
# `rounds` lista fordulonkenti ARRAL - de a rounds csak az eddigi 6 fordulot
# adja, es NINCS benne ellenfel. A felulet "Kovetkezo merkozesek" tablaja
# tehat mashonnan jon: valoszinuleg a CSAPAT meccseibol.
ki("")
ki("## 2) A csapat meccsei - a team_id-t mar ismerjuk a jatekos-adatlaprol")
CP = 1115
st, j = collect.api_get(collect.ROOT + "competitions/%d/players/%d" % (collect.COMPETITION, CP))
team = ((j or {}).get("team") or {}) if isinstance(j, dict) else {}
tid = team.get("id")
ki("=== a jatekos klubja: %s (id=%s)" % (team.get("short_name"), tid))
if tid:
    for cimke, ut in [
        ("teams/{id}", "competitions/%d/teams/%d" % (collect.COMPETITION, tid)),
        ("teams/{id}/games", "competitions/%d/teams/%d/games" % (collect.COMPETITION, tid)),
        ("teams/{id} + games", "competitions/%d/teams/%d?include=games" % (collect.COMPETITION, tid)),
        ("teams/{id} + rounds", "competitions/%d/teams/%d?include=rounds" % (collect.COMPETITION, tid)),
        ("games?filter[team_id]", "games?filter%%5Bteam_id%%5D=%d" % tid),
        ("competitions/N/games?team", "competitions/%d/games?filter%%5Bteam_id%%5D=%d" % (collect.COMPETITION, tid)),
        ("teams/{id} (gyoker)", "teams/%d" % tid),
        ("teams/{id}/next-games (gyoker)", "teams/%d/next-games" % tid),
    ]:
        st2, j2 = collect.api_get(collect.ROOT + ut)
        if not isinstance(j2, dict):
            ki("=== %-32s -> HTTP %s" % (cimke, st2))
            continue
        ki("=== %-32s -> HTTP %s | gyoker-kulcsok: %s" % (cimke, st2, sorted(j2.keys())))
        for k, v in sorted(j2.items()):
            if isinstance(v, list) and v:
                ki("    %s: %d elem, elso: %s" % (k, len(v),
                   json.dumps(rovidit(v[0], 200), ensure_ascii=False)[:500]))
        d = j2.get("data")
        if isinstance(d, list) and d:
            ki("    data[0]: %s" % json.dumps(rovidit(d[0], 200), ensure_ascii=False)[:500])

ki("")
ki("### Ha ez sem adja, a jovobeli ellenfel csak a frontend-bundle")
ki("### visszafejtesevel talalhato meg - azt kulon kell eldonteni.")

with open(NAPLO, "w", encoding="utf-8") as f:
    f.write("\n".join(sorok) + "\n")
print("\n".join(sorok))
