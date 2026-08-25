#!/usr/bin/env python3
"""EGYSZERI meres a jatekosprofil-funkciohoz.

EDDIGI EREDMENY (naplo/mlsz-jatekoslista.txt):
  1. kor: MEGVAN a teljes jatekostorzs - competitions/3/players
     (385 jatekos, klub, poszt, u21, serules, ar, competition_points).
  2. kor: a torzs NEM fogad filter[round_id]-t (400), tehat a
     fordulonkenti pontot nem adja vissza; a per_page=100 viszont MEGY
     (26 lap helyett 4).

3. KOR - a fordulonkenti pont utolso eselye. A pontbontas-vegpont
(/game-player-stats, competitions elotag NELKUL) ma is ket szuroval megy:
filter[competition_player_id] ES filter[round_id]. A kerdes:
  a) elhagyhato-e a fordulo-szuro (akkor egy keres = egy jatekos EGESZ
     szezonja, es a mult potolhato 385 keressel, egyszer);
  b) fogad-e vesszos azonosito-listat (akkor meg olcsobb);
  c) a tomeges (csak fordulora szurt) valasz soraiban tenyleg nincs-e
     jatekos-azonosito - ezt a nyers sor teljes kiirasaval ellenorizzuk,
     mert egy elnezett mezo itt az egesz funkciot eldonti;
  d) van-e a torzsvegponton fordulonkenti include (round_statistics stb.),
     es elfér-e mind a 385 jatekos egy lapon (per_page=500).

Csak olvas; a naplot a workflow commitolja.
ADATVEDELEM: a labdarugok neve nyilvanos adat, az mehet a naploba.
"""
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import collect  # api_get, ROOT, BASE, COMPETITION, rid

NAPLO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mlsz-jatekoslista.txt")
sorok = []
ki = sorok.append

# Ket ismert competition_player azonosito a mentett keretbol - nem kell
# hozza kerés, es igy a meres nem fugg attol, ki van eppen valakinek a
# kereteben.
GYOKER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JATEKOS = [1237]
try:
    with open(os.path.join(GYOKER, "keretek", "5.json"), encoding="utf-8") as f:
        mind = [p for lista in json.load(f)["squads"].values() for p in lista]
    JATEKOS = [p["id"] for p in mind if p.get("id")][:2]
except Exception as e:                                    # pragma: no cover
    ki("# (a keret-fajl nem olvashato: %s - beepitett azonosito)" % e)
    JATEKOS = [1237]


def rovidit(v, hossz=200):
    if isinstance(v, str) and len(v) > hossz:
        return "<%d karakteres szoveg>" % len(v)
    if isinstance(v, dict):
        return {k: rovidit(x, hossz) for k, x in v.items()}
    if isinstance(v, list):
        return [rovidit(x, hossz) for x in v[:3]] + (["<+%d elem>" % (len(v) - 3)] if len(v) > 3 else [])
    return v


def proba(cimke, ut, elso_sor=False):
    """Egy keres: statusz, sorszam, lapozas - es keresre az elso nyers sor."""
    st, j = collect.api_get(collect.ROOT + ut)
    if not isinstance(j, dict):
        ki("=== %-52s -> HTTP %s (nem JSON objektum)" % (cimke, st))
        return None
    adat = j.get("data")
    meta = j.get("meta") or {}
    n = len(adat) if isinstance(adat, list) else ("dict" if adat else 0)
    ki("=== %-52s -> HTTP %s | sorok=%s total=%s per_page=%s last_page=%s"
       % (cimke, st, n, meta.get("total"), meta.get("per_page"), meta.get("last_page")))
    if elso_sor and isinstance(adat, list) and adat:
        ki("    elso sor (RÖVIDÍTVE, de MINDEN mezo):")
        ki(json.dumps(rovidit(adat[0]), ensure_ascii=False, indent=1))
    return j


def fordulok_a_valaszban(j):
    """Hany kulonbozo round_id van a valaszban? Ez donti el, hogy a
    fordulo-szuro elhagyasa tenyleg az EGESZ szezont adja-e."""
    adat = (j or {}).get("data")
    if not isinstance(adat, list):
        return
    talalt = set()
    for sor in adat:
        for kulcs in ("round_id", "roundId"):
            if sor.get(kulcs) is not None:
                talalt.add(sor[kulcs])
        r = sor.get("round") or {}
        if isinstance(r, dict) and r.get("id") is not None:
            talalt.add(r["id"])
    ki("    -> %d sorban %d kulonbozo fordulo: %s"
       % (len(adat), len(talalt), sorted(talalt)[:12]))


ki("# 3. KOR - a fordulonkenti pont utolso eselye (pontbontas-vegpont).")
ki("# Elozmeny: a torzs (competitions/3/players) megvan, de fordulora nem")
ki("# szurheto (400). Itt a /game-player-stats vegpontot meritjuk ki.")
ki("# Merott jatekos-azonositok: %s" % JATEKOS)
ki("")

GPS = "game-player-stats"
CP = "&filter%5Bcompetition_player_id%5D="
RD = "&filter%5Bround_id%5D="
KONF = "?include=competition_stat_config"
j1 = JATEKOS[0]

# ---- a) elhagyhato-e a fordulo-szuro? ----
ki("## a) EGY jatekos, fordulo-szuro NELKUL - megjon-e az egesz szezon?")
j = proba("csak jatekos-szuro", GPS + KONF + CP + str(j1), elso_sor=True)
fordulok_a_valaszban(j)
j = proba("csak jatekos-szuro + per_page=100", GPS + KONF + CP + str(j1) + "&per_page=100")
fordulok_a_valaszban(j)
ki("")
ki("## referencia: ugyanaz a jatekos, EGY fordulora (a mai mukodo hivas)")
j = proba("jatekos + 5. fordulo", GPS + KONF + CP + str(j1) + RD + str(collect.rid(5)))
fordulok_a_valaszban(j)
ki("")

# ---- b) vesszos azonosito-lista ----
ki("## b) fogad-e TOBB azonositot egyszerre?")
if len(JATEKOS) > 1:
    lista = ",".join(str(x) for x in JATEKOS[:2])
    j = proba("jatekos-lista (%s)" % lista, GPS + KONF + CP + lista + RD + str(collect.rid(5)))
    fordulok_a_valaszban(j)
    proba("jatekos-lista szogletes ([]=)", GPS + KONF
          + "&filter%5Bcompetition_player_id%5D%5B%5D=" + str(JATEKOS[0])
          + "&filter%5Bcompetition_player_id%5D%5B%5D=" + str(JATEKOS[1])
          + RD + str(collect.rid(5)))
ki("")

# ---- c) a tomeges valasz sora: tenyleg nincs benne jatekos? ----
ki("## c) TOMEGES hivas (csak fordulora szurve) - a nyers sor MINDEN mezoje.")
ki("#    Ha van benne barmilyen jatekos-azonosito, az egesz mult potolhato")
ki("#    par keressel. Az 1. kor szerint nincs - ezt ellenorizzuk ujra.")
j = proba("csak fordulo-szuro + per_page=500", GPS + "?filter%5Bround_id%5D="
          + str(collect.rid(5)) + "&per_page=500", elso_sor=True)
adat = (j or {}).get("data")
if isinstance(adat, list) and adat:
    kulcsok = set()
    for sor in adat[:50]:
        kulcsok |= set(sor.keys())
    ki("    az elso 50 sor OSSZES mezoneve: %s" % sorted(kulcsok))
    gyanus = [k for k in sorted(kulcsok) if "player" in k.lower() or k.endswith("_id") or k == "id"]
    ki("    azonositonak tuno mezok: %s" % gyanus)
    for k in gyanus:
        ertekek = {sor.get(k) for sor in adat[:50]}
        ki("      %-32s -> %d kulonbozo ertek az elso 50 sorban, pl. %s"
           % (k, len(ertekek), sorted(str(x) for x in ertekek)[:5]))
ki("")

# ---- d) a torzsvegpont vegso lehetosegei ----
ki("## d) a torzsvegpont: fordulonkenti include, es elfér-e egy lapon?")
ALAP = "competitions/%d/players" % collect.COMPETITION
for cimke, extra in [
    ("per_page=500 (mind a 385 egy lapon?)", "?per_page=500"),
    ("include=round_statistics", "?include=round_statistics"),
    ("include=statistics", "?include=statistics"),
    ("include=rounds", "?include=rounds"),
    ("include=game_player_stats", "?include=game_player_stats"),
]:
    proba("torzs: " + cimke, ALAP + extra)
proba("egy jatekos reszletes lapja", ALAP + "/" + str(j1)
      + "?include=summary_statistics,team,position", elso_sor=True)

with open(NAPLO, "w", encoding="utf-8") as f:
    f.write("\n".join(sorok) + "\n")
print("\n".join(sorok))
