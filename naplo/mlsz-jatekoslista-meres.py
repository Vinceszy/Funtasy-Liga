#!/usr/bin/env python3
"""EGYSZERI meres - 6. kor: van-e AR-ELOZMENY az MLSZ-nel?

Elozmeny: a torzs (competitions/3/players) a `current_round.market_price`
mezoben a MOSTANI arat adja. Ha az arak valtozasat kovetni akarjuk, ket ut
van: vagy mi naplozzuk futasonkent (amit visszamenoleg mar nem lehet
potolni), vagy az API maga adja a multat.

Ez a kor az utobbit keresi. A legigeretesebb, hogy a torzs fogad valamilyen
fordulonkenti include-ot: akkor MINDEN jatekos ARMULTJA egy keresbol
megjonne, es a sajat naplozas felesleges (vagy legalabb visszamenoleg
potolhato) lenne.

Ha nincs ilyen, az is ertekes valasz: akkor a naplozas az EGYETLEN ut, es
amit ma nem irunk fel, az orokre elveszett.

Csak olvas; a naplot a workflow commitolja.
"""
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import collect

NAPLO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mlsz-jatekoslista.txt")
sorok = []
ki = sorok.append


def rovidit(v, hossz=160):
    if isinstance(v, str) and len(v) > hossz:
        return "<%d karakteres szoveg>" % len(v)
    if isinstance(v, dict):
        return {k: rovidit(x, hossz) for k, x in v.items()}
    if isinstance(v, list):
        return [rovidit(x, hossz) for x in v[:4]] + (["<+%d elem>" % (len(v) - 4)] if len(v) > 4 else [])
    return v


ki("# 6. KOR: van-e AR-ELOZMENY az MLSZ-nel?")
ki("# Ha van, nem kell sajat naplo (es a mult is potolhato). Ha nincs, a")
ki("# naplozas az egyetlen ut - amit ma nem irunk fel, az elveszett.")
ki("")

# ---- 1) a torzs include-jai: hoz-e barmelyik fordulonkenti arat? ----
ALAP = "competitions/%d/players?per_page=3" % collect.COMPETITION
ki("## 1) A torzs include-jai (per_page=3, hogy a valasz olvashato legyen)")
for inc in ("rounds", "player_rounds", "competition_player_rounds", "market_prices",
            "price_history", "prices", "current_round", "statistics"):
    st, j = collect.api_get(collect.ROOT + ALAP + "&include=" + inc)
    adat = (j or {}).get("data") if isinstance(j, dict) else None
    if not isinstance(adat, list) or not adat:
        ki("=== include=%-28s -> HTTP %s (nincs lista)" % (inc, st))
        continue
    elso = adat[0]
    # az include akkor "hatott", ha uj kulcs jelent meg a soron
    ki("=== include=%-28s -> HTTP %s | sor-kulcsok: %s"
       % (inc, st, sorted(elso.keys())))
    for k in sorted(elso.keys()):
        if k in ("id", "first_name", "last_name", "birth_date", "is_u21", "injury_status"):
            continue
        ert = elso[k]
        if isinstance(ert, list) and ert:
            ki("    %s: %d elem, elso: %s" % (k, len(ert),
               json.dumps(rovidit(ert[0]), ensure_ascii=False)[:300]))

# ---- 2) kulon vegpontok az arra ----
ki("")
ki("## 2) Onallo ar-vegpontok")
CP = 1299                                   # egy ismert competition_player
for cimke, ut in [
    ("players/{id} (reszletes lap)", "competitions/%d/players/%d" % (collect.COMPETITION, CP)),
    ("market-prices", "market-prices?filter%%5Bcompetition_player_id%%5D=%d" % CP),
    ("player-market-prices", "player-market-prices?filter%%5Bcompetition_player_id%%5D=%d" % CP),
    ("competition-player-rounds", "competition-player-rounds?filter%%5Bcompetition_player_id%%5D=%d" % CP),
    ("player-rounds", "player-rounds?filter%%5Bcompetition_player_id%%5D=%d" % CP),
    ("price-history", "price-history?filter%%5Bcompetition_player_id%%5D=%d" % CP),
]:
    st, j = collect.api_get(collect.ROOT + ut)
    if not isinstance(j, dict):
        ki("=== %-30s -> HTTP %s" % (cimke, st))
        continue
    adat = j.get("data")
    n = len(adat) if isinstance(adat, list) else ("dict" if adat else 0)
    ki("=== %-30s -> HTTP %s | data: %s" % (cimke, st, n))
    if adat:
        minta = adat[0] if isinstance(adat, list) else adat
        ki("    %s" % json.dumps(rovidit(minta), ensure_ascii=False)[:500])

ki("")
ki("### Ha egyik sem ad fordulonkenti/idobeli arat, marad a sajat naplozas.")

with open(NAPLO, "w", encoding="utf-8") as f:
    f.write("\n".join(sorok) + "\n")
print("\n".join(sorok))
