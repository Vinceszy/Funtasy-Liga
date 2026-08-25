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
ki("# 9. KOR: van-e teljes menetrend (jovobeli meccsek) az MLSZ-nel?")
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

# ---- 2) a keret-vegpont jovobeli fordulora: MERVE, ures listat ad ----
ki("")
ki("## 2) a keret-vegpont jovobeli fordulora: HTTP 200, de URES lista")
ki("#    (kimerve: 8., 13. es 33. fordulo, valodi user.id-val - a keret")
ki("#     csak a mar elindult fordulokra letezik, tehat ez az ut sem jar)")

# ---- 3) csapat-alapu vegpontok es a fordulo-objektum ----
ki("")
ki("## 3) csapat-alapu vegpontok es a fordulo-objektum")
for cimke, ut in [
    ("competitions/N/teams", "competitions/%d/teams" % collect.COMPETITION),
    ("competitions/N/teams + games", "competitions/%d/teams?include=games" % collect.COMPETITION),
    ("teams?filter[competition_id]", "teams?filter%%5Bcompetition_id%%5D=%d" % collect.COMPETITION),
    ("competitions/N/schedule", "competitions/%d/schedule" % collect.COMPETITION),
    ("competitions/N/fixtures", "competitions/%d/fixtures" % collect.COMPETITION),
    ("competitions/N/game-days", "competitions/%d/game-days" % collect.COMPETITION),
]:
    st, j = collect.api_get(collect.ROOT + ut)
    if not isinstance(j, dict):
        ki("=== %-34s -> HTTP %s" % (cimke, st))
        continue
    adat = j.get("data")
    n = len(adat) if isinstance(adat, list) else ("dict" if adat else 0)
    ki("=== %-34s -> HTTP %s | data: %s" % (cimke, st, n))
    if adat:
        minta = adat[0] if isinstance(adat, list) else adat
        ki("    kulcsok: %s" % sorted(minta.keys()))
        ki("    %s" % json.dumps(rovidit(minta), ensure_ascii=False)[:400])

ki("")
ki("## 4) a fordulo-objektum (amit a gyujto amugy is lekér)")
st, j = collect.api_get(collect.ROOT + "competitions?include=rounds,current_round")
adat = (j or {}).get("data") if isinstance(j, dict) else None
comp = None
if isinstance(adat, list):
    comp = next((c for c in adat if c.get("id") == collect.COMPETITION), adat[0] if adat else None)
if comp:
    rounds = comp.get("rounds") or []
    ki("=== competitions?include=rounds -> HTTP %s | %d fordulo" % (st, len(rounds)))
    if rounds:
        ki("    egy fordulo kulcsai: %s" % sorted(rounds[0].keys()))
        ki("    %s" % json.dumps(rovidit(rounds[0]), ensure_ascii=False)[:400])
        jovo_r = next((r for r in rounds if (r.get("round_number") or 0) == JOVO), None)
        if jovo_r:
            ki("    a %d. fordulo: %s" % (JOVO, json.dumps(rovidit(jovo_r), ensure_ascii=False)[:400]))
else:
    ki("=== competitions?include=rounds -> HTTP %s (nincs adat)" % st)

ki("")
ki("### Ha egyik sem adja a jovobeli parositasokat, akkor az NB1-profil")
ki("### jovobeli soraiban nem tudunk ellenfelet mutatni - csak a fordulot.")

with open(NAPLO, "w", encoding="utf-8") as f:
    f.write("\n".join(sorok) + "\n")
print("\n".join(sorok))
