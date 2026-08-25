#!/usr/bin/env python3
"""EGYSZERI meres: van-e az MLSZ-nel JATEKOSLISTA-vegpont?

A jatekosprofil-funkciohoz ket dolog kell, ami ma nincs meg:
  1) a TELJES jatekostorzs (a keresohoz - ma csak azt a ~107-et ismerjuk,
     aki valaha valamelyik keretben volt);
  2) minden jatekos FORDULONKENTI pontja (a profil "ures hetei" - amikor a
     jatekos senkinel sem volt, a pontja sehol nincs eltarolva).

Amit mar tudunk (naplo/mlsz-adat.txt, 2026-08-25):
  - game-player-stats?filter[round_id]=X megy, de a SORBAN NINCS
    jatekos-azonosito, es 50-esevel lapoz (80 lap egy fordulora);
  - az include=competition_player-t a vegpont nemán lenyeli;
  - a stat-szuro 400-at ad.
Tehat a tomeges pont-lekerdezes azon az uton nem jart.

Ez a meres a JATEKOS-vegpontokat probalja: a fantasy piac/bongeszo oldal
biztosan listaz jatekosokat arral es ponttal - a kerdes, melyik uton.
Ha van ilyen, a gyujto fordulozaras utan egyszer lehivja az egeszet
(mint a tabellat), es a profil ingyen lesz.

Csak olvas; a naplot a workflow commitolja.
ADATVEDELEM: a labdarugok neve nyilvanos adat, az mehet a naploba.
"""
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import collect  # api_get, ROOT, BASE, COMPETITION, rid

NAPLO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mlsz-jatekoslista.txt")
R = int(os.environ.get("MERES_FORDULO", "1"))
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


def proba(cimke, ut):
    """Egy vegpont kiprobalasa: statusz, sorszam, lapozas, elso sor."""
    st, j = collect.api_get(collect.ROOT + ut)
    if not isinstance(j, dict):
        ki("=== %-38s -> HTTP %s (nem JSON objektum)" % (cimke, st))
        return None
    adat = j.get("data")
    n = len(adat) if isinstance(adat, list) else ("dict" if adat else 0)
    meta = j.get("meta") or {}
    lap = ""
    if meta:
        lap = " | meta: total=%s per_page=%s last_page=%s" % (
            meta.get("total"), meta.get("per_page"), meta.get("last_page"))
    ki("=== %-38s -> HTTP %s, sorok: %s%s" % (cimke, st, n, lap))
    if st == 200 and isinstance(adat, list) and adat:
        ki("    elso sor kulcsai: %s" % sorted(adat[0].keys()))
        ki(json.dumps(rovidit(adat[0]), ensure_ascii=False, indent=1))
    return j


ki("# 2. KOR: a players vegpont MEGVAN (competitions/N/players, 385 jatekos,")
ki("# 15/lap, 26 lap; a page[size]-t eldobja). Amit ad: klub, poszt, u21,")
ki("# serules, ar, es summary_statistics (competition_points, weekly_points).")
ki("# Amit NEM ad: fordulonkenti pont - a weekly_points az AKTUALIS forduloe.")
ki("#")
ki("# EZ A KOR AZT MERI, POTOLHATO-E A MULT:")
ki("#   a) fogad-e filter[round_id]-t (akkor barmelyik regi fordulo lekerheto)")
ki("#   b) van-e mukodo lapmeret-parameter (26 keres helyett keve sebb)")
ki("#   c) valtozik-e a weekly_points a szurovel - ez a doL kerdes")

ALAP = "competitions/%d/players?include=summary_statistics,team,position" % collect.COMPETITION


def minta(cimke, ut, kulcs="weekly_points"):
    """Egy proba: hany sor, es mit ad az ELSO jatekos weekly_points-a."""
    st, j = collect.api_get(collect.ROOT + ut)
    if not isinstance(j, dict) or not isinstance(j.get("data"), list):
        ki("=== %-44s -> HTTP %s (nincs lista)" % (cimke, st))
        return None
    adat, meta = j["data"], (j.get("meta") or {})
    elso = adat[0] if adat else {}
    ss = (elso.get("summary_statistics") or {})
    cr = (elso.get("current_round") or {})
    ki("=== %-44s -> HTTP %s | sorok=%d total=%s per_page=%s"
       % (cimke, st, len(adat), meta.get("total"), meta.get("per_page")))
    ki("    elso: %s %s | %s=%s comp=%s | current_round.round_id=%s"
       % (elso.get("first_name"), elso.get("last_name"), kulcs, ss.get(kulcs),
          ss.get("competition_points"), cr.get("round_id")))
    return j


# ---- a) fordulo-szuro: potolhato-e a mult? ----
for r_ in (1, 3, 5):
    minta("filter[round_id]=%d (%d. fordulo)" % (collect.rid(r_), r_),
          ALAP + "&filter%%5Bround_id%%5D=%d" % collect.rid(r_))
minta("szuro NELKUL (referencia)", ALAP)

# ---- b) lapmeret-parameterek ----
for cimke, par in [("per_page=100", "per_page=100"), ("limit=100", "limit=100"),
                   ("page[limit]=100", "page%5Blimit%5D=100"),
                   ("page[per_page]=100", "page%5Bper_page%5D=100")]:
    minta("lapmeret: " + cimke, ALAP + "&" + par)

# ---- c) mennyi ido/keres a teljes torzs? ----
st, j = collect.api_get(collect.ROOT + ALAP)
lapok = ((j or {}).get("meta") or {}).get("last_page")
ki("")
ki("### A teljes torzs %s lapbol all (15/lap)." % lapok)

sys.exit(0)

ki("# Jatekoslista-vegpont kereses. Cel: teljes torzs + fordulonkenti pont.")
ki("# ROOT=%s  BASE=%s  round_id(%d)=%d" % (collect.ROOT, collect.BASE, R, collect.rid(R)))

# ---- 1) a legvaloszinubb utak a JSON:API mintabol ----
jeloltek = [
    ("competition-players (gyoker)", "competition-players?filter%%5Bcompetition_id%%5D=%d" % collect.COMPETITION),
    ("competitions/N/competition-players", "competitions/%d/competition-players" % collect.COMPETITION),
    ("competitions/N/players", "competitions/%d/players" % collect.COMPETITION),
    ("players (gyoker)", "players?filter%%5Bcompetition_id%%5D=%d" % collect.COMPETITION),
    ("competitions/N/player-rankings", "competitions/%d/player-rankings" % collect.COMPETITION),
    ("competition-players + round szuro",
     "competition-players?filter%%5Bcompetition_id%%5D=%d&filter%%5Bround_id%%5D=%d"
     % (collect.COMPETITION, collect.rid(R))),
]
talalat = None
for cimke, ut in jeloltek:
    j = proba(cimke, ut)
    if j and isinstance(j.get("data"), list) and j["data"] and talalat is None:
        talalat = (cimke, ut, j)

# ---- 2) ha van talalat: mit tud? include-ok, lapmeret, fordulonkenti pont ----
if talalat:
    cimke, ut, j = talalat
    ki("")
    ki("### MUKODIK: %s" % cimke)
    elval = "&" if "?" in ut else "?"
    for cim2, extra in [
        ("include=team,position", "include=team,position"),
        ("include=current_round", "include=current_round"),
        ("include=summary_statistics", "include=summary_statistics"),
        ("nagy lapmeret (500)", "page%5Bsize%5D=500"),
        ("2. lap", "page%5Bnumber%5D=2"),
    ]:
        proba(cimke + " + " + cim2, ut + elval + extra)
else:
    ki("")
    ki("### EGYIK JELOLT SEM ADOTT LISTAT.")
    ki("# Tartalek terv: a gyujto jatekosonkent kerdez (game-player-stats,")
    ki("# 1 keres/jatekos/fordulo) - de ahhoz is kell egy NEVSOR. Az egyetlen")
    ki("# ismert nevsor-forras a keret-vegpont, ami csak a MI jatekosainkat")
    ki("# adja. Ilyenkor a 'minden jatekos' kovetelmeny nem teljesitheto,")
    ki("# es ezt Vincenek meg kell beszelnunk.")

with open(NAPLO, "w", encoding="utf-8") as f:
    f.write("\n".join(sorok) + "\n")
print("\n".join(sorok))
