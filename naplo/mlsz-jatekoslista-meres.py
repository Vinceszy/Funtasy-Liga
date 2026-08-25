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
ki("# 11. KOR: van-e teljes menetrend (jovobeli meccsek) az MLSZ-nel?")
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

# ---- 2) A JATEKOS-ADATLAP TARTALMA ----
# MEGVAN: competitions/3/players/{id}. Az elozo korben azert latszott
# uresnek, mert a valasznak NINCS "data" burka - a mezok a gyokerben
# allnak -, en pedig csak a j["data"]-t irtam ki. Itt a teljes szerkezetet
# dumpoljuk, kulonos tekintettel a `rounds` kulcsra: a felulet abbol
# rajzolja a "KOVETKEZO MERKOZESEK" tablat.
ki("")
ki("## 2) competitions/N/players/{id} - a TELJES szerkezet")
CP = 1115
st, j = collect.api_get(collect.ROOT + "competitions/%d/players/%d" % (collect.COMPETITION, CP))
if not isinstance(j, dict):
    ki("=== HTTP %s - nincs objektum" % st)
else:
    ki("=== HTTP %s | gyoker-kulcsok: %s" % (st, sorted(j.keys())))
    ki("    nev: %s %s | klub: %s | poszt: %s"
       % (j.get("first_name"), j.get("last_name"),
          (j.get("team") or {}).get("short_name"), (j.get("position") or {}).get("monogram")))
    ki("    countries: %s" % json.dumps(rovidit(j.get("countries")), ensure_ascii=False)[:300])
    for kulcs in ("fantasy_summary_statistics", "extended_summary_statistics"):
        ki("    %s: %s" % (kulcs, json.dumps(rovidit(j.get(kulcs)), ensure_ascii=False)[:400]))
    r = j.get("rounds")
    if isinstance(r, list):
        ki("")
        ki("### rounds: %d elem" % len(r))
        ki("    egy elem kulcsai: %s" % (sorted(r[0].keys()) if r else None))
        for x in r[:3]:
            ki("    %s" % json.dumps(rovidit(x, 200), ensure_ascii=False)[:700])
        ki("    ...")
        for x in r[-2:]:
            ki("    %s" % json.dumps(rovidit(x, 200), ensure_ascii=False)[:700])
        # van-e benne JOVOBELI fordulo, es abban ellenfel?
        szamok = [x.get("round_number") for x in r if isinstance(x, dict)]
        ki("    a fordulo-szamok: %s" % szamok[:40])
    else:
        ki("### rounds: %r" % rovidit(r))

with open(NAPLO, "w", encoding="utf-8") as f:
    f.write("\n".join(sorok) + "\n")
print("\n".join(sorok))
