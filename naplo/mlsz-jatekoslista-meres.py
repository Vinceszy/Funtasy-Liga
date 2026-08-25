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
ki("# 10. KOR: van-e teljes menetrend (jovobeli meccsek) az MLSZ-nel?")
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

# ---- 2) A JATEKOS-ADATLAP: a felulet MUTATJA a kovetkezo merkozeseket ----
# A fantasy.mlsz.hu/fantasy/3/jatekosok/{id} oldalon ott a "KOVETKEZO
# MERKOZESEK" tabla, egesz szezonra elore (hazai/vendeg, idopont, ellenfel).
# Tehat a vegpont LETEZIK - eddig csak nem talaltam el. Itt a nyers valaszt
# irjuk ki, nem feltetelezve, hogy a "data" lista.
ki("")
ki("## 2) A jatekos-adatlap vegpontja (a felulet ezt mutatja)")
CP = 1115                                   # a felulet peldajaban ez a jatekos
UTAK = [
    ("players/{id}", "competitions/%d/players/%d" % (collect.COMPETITION, CP)),
    ("players/{id} + team.games", "competitions/%d/players/%d?include=team.games" % (collect.COMPETITION, CP)),
    ("players/{id} + games", "competitions/%d/players/%d?include=games" % (collect.COMPETITION, CP)),
    ("players/{id} + next_games", "competitions/%d/players/%d?include=next_games" % (collect.COMPETITION, CP)),
    ("players/{id} + upcoming_games", "competitions/%d/players/%d?include=upcoming_games" % (collect.COMPETITION, CP)),
    ("players/{id} + fixtures", "competitions/%d/players/%d?include=fixtures" % (collect.COMPETITION, CP)),
    ("players/{id}/games", "competitions/%d/players/%d/games" % (collect.COMPETITION, CP)),
    ("players/{id}/next-games", "competitions/%d/players/%d/next-games" % (collect.COMPETITION, CP)),
]
for cimke, ut in UTAK:
    st, j = collect.api_get(collect.ROOT + ut)
    if not isinstance(j, dict):
        ki("=== %-32s -> HTTP %s (nem JSON objektum)" % (cimke, st))
        continue
    ki("=== %-32s -> HTTP %s | felso kulcsok: %s" % (cimke, st, sorted(j.keys())))
    d = j.get("data")
    if isinstance(d, dict):
        ki("    data kulcsai: %s" % sorted(d.keys()))
        for k, v in sorted(d.items()):
            if isinstance(v, list) and v:
                ki("    %s: %d elem, elso: %s" % (k, len(v),
                   json.dumps(rovidit(v[0]), ensure_ascii=False)[:400]))
    elif isinstance(d, list):
        ki("    data: %d elemu lista" % len(d))
        if d:
            ki("    %s" % json.dumps(rovidit(d[0]), ensure_ascii=False)[:400])

# ---- 3) a fordulo-lista lapozasa: elso korben csak 6 fordulo jott ----
ki("")
ki("## 3) Hany fordulot ismer az API? (elso meresre csak 6-ot adott)")
for cimke, ut in [
    ("competitions?include=rounds", "competitions?include=rounds"),
    ("+ per_page=100", "competitions?include=rounds&per_page=100"),
    ("rounds?filter[competition_id]", "rounds?filter%%5Bcompetition_id%%5D=%d&per_page=100" % collect.COMPETITION),
]:
    st, j = collect.api_get(collect.ROOT + ut)
    adat = (j or {}).get("data") if isinstance(j, dict) else None
    if isinstance(adat, list) and adat and "rounds" in (adat[0] or {}):
        comp = next((c for c in adat if c.get("id") == collect.COMPETITION), adat[0])
        r = comp.get("rounds") or []
        ki("=== %-32s -> HTTP %s | %d fordulo (utolso: %s)"
           % (cimke, st, len(r), (r[-1] or {}).get("round_number") if r else None))
    else:
        n = len(adat) if isinstance(adat, list) else ("dict" if adat else 0)
        ki("=== %-32s -> HTTP %s | data: %s" % (cimke, st, n))
        if isinstance(adat, list) and adat:
            ki("    %s" % json.dumps(rovidit(adat[0]), ensure_ascii=False)[:300])

ki("")
ki("### A felulet biztosan tudja a jovobeli parositasokat - ha egyik ut sem")
ki("### adja, a kovetkezo lepes a frontend-bundle visszafejtese.")

with open(NAPLO, "w", encoding="utf-8") as f:
    f.write("\n".join(sorok) + "\n")
print("\n".join(sorok))
