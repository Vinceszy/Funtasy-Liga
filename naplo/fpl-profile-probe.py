#!/usr/bin/env python3
"""EGYSZERI meres a jatekosprofil PL-oldalahoz - 2. kor.

AZ 1. KOR EREDMENYE (naplo/fpl-profil.txt):
  - a Draft SAJAT element-summary/{id} vegpontja egy keresbol adja egy
    jatekos egesz szezonjat: fordulonkent `event`, `total_points`, minden
    statisztika, es egy `detail` mezo "AVL (H) 4-0" alakban;
  - a klasszikus FPL azonositoi NEM egyeznek a Draftéval (egy jatekosnal
    1 vs 14 pont), tehat az a vegpont nem hasznalhato.

EZ A KOR EGYETLEN KERDEST DONT EL: a `detail` szamparja MILYEN SORRENDBEN
all? Ket olvasat lehetseges, es 4-0-s hazai gyozelemnel a ketto egybeesik:
  (a) HAZAI-VENDEG (mint mindenhol maskul az oldalon), vagy
  (b) a JATEKOS CSAPATA - ELLENFEL.
Ha rosszul talalnank el, minden idegenbeli meccs eredmenye megfordulna a
profilban - es pont az ilyen csendes hiba a legrosszabb fajta.

A dontes nem tippbol szuletik: a fordulo meccseit (event/{gw}/fixtures)
tekintjuk hitelesnek - ott team_h/team_a es a ket gol kulon mezoben all -,
es ahhoz mérjük a `detail` szoveget. Kifejezetten IDEGENBELI, NEM dontetlen
meccseket keresunk, mert csak azok valasztjak szet a ket olvasatot.

Csak olvas; a naplot a workflow commitolja.
"""
import json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import collect_draft  # fetch, B

GYOKER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAPLO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fpl-profil.txt")
sorok = []
ki = sorok.append

with open(os.path.join(GYOKER, "draft_history.json"), encoding="utf-8") as f:
    tortenet = json.load(f)["rounds"]
with open(os.path.join(GYOKER, "draft_players.json"), encoding="utf-8") as f:
    torzs = json.load(f)
KLUB = torzs["teams"]                       # csapat-id -> rovidnev
JATEKOSNEV = torzs["players"]

GW = sorted(tortenet, key=int)[0]
elemek = sorted({p["e"] for lista in tortenet[GW].values() for p in lista})

ki("# PL profil-meres, 2. kor: a `detail` szamparjanak SORRENDJE.")
ki("# Hiteles forras: event/%s/fixtures (team_h, team_a, team_h_score," % GW)
ki("# team_a_score kulon mezoben). Ehhez merjuk a `detail` szoveget.")
ki("")

st, fx = collect_draft.fetch("event/%s/fixtures" % GW)
if not isinstance(fx, list):
    ki("### A fixtures nem johetett le (HTTP %s) - a meres nem folytathato." % st)
    with open(NAPLO, "w", encoding="utf-8") as f:
        f.write("\n".join(sorok) + "\n")
    print("\n".join(sorok))
    sys.exit(0)
meccs = {m.get("id"): m for m in fx}
ki("### %d meccs a %s. forduloban." % (len(fx), GW))
ki("")

MINTA = re.compile(r"^\s*(\S+)\s*\((H|A)\)\s*(\d+)\s*-\s*(\d+)\s*$")
hazai_vendeg = jatekos_ellenfel = 0
ellentmondas = []
vizsgalt = 0

for e in elemek:
    if vizsgalt >= 25:
        break
    st, j = collect_draft.fetch("element-summary/%d" % e)
    if not isinstance(j, dict):
        continue
    for h in (j.get("history") or []):
        if str(h.get("event")) != str(GW):
            continue
        d = (h.get("detail") or "").strip()
        m = MINTA.match(d)
        fxr = meccs.get(h.get("fixture"))
        if not m or not fxr:
            ki("=== elem %-4s detail=%r fixture=%s -> NEM ERTELMEZHETO"
               % (e, d, h.get("fixture")))
            continue
        ell, hol, a, b = m.group(1), m.group(2), int(m.group(3)), int(m.group(4))
        hs, vs_ = fxr.get("team_h_score"), fxr.get("team_a_score")
        hazai_klub = KLUB.get(str(fxr.get("team_h")), "?")
        vendeg_klub = KLUB.get(str(fxr.get("team_a")), "?")
        if hs is None or vs_ is None or hs == vs_:
            continue                        # dontetlen nem valaszt szet
        idegenben = (hol == "A")
        if not idegenben:
            continue                        # hazai meccs sem valaszt szet
        vizsgalt += 1
        # idegenbeli meccs: a jatekos csapata a VENDEG
        hv = (a == hs and b == vs_)         # (a) hazai-vendeg olvasat
        je = (a == vs_ and b == hs)         # (b) jatekos-ellenfel olvasat
        hazai_vendeg += 1 if hv else 0
        jatekos_ellenfel += 1 if je else 0
        cimke = "HAZAI-VENDEG" if hv and not je else ("JATEKOS-ELLENFEL" if je and not hv else "?!")
        ki("=== %-16s detail=%-18r | fixtures: %s %s-%s %s | ellenfel a detailben: %s -> %s"
           % ((JATEKOSNEV.get(str(e)) or {}).get("n", "#%d" % e), d,
              hazai_klub, hs, vs_, vendeg_klub, ell, cimke))
        if not hv and not je:
            ellentmondas.append("elem %s: detail=%r, fixtures %s-%s" % (e, d, hs, vs_))

ki("")
ki("### %d idegenbeli, NEM dontetlen meccs vizsgalva." % vizsgalt)
ki("###   hazai-vendeg olvasat stimmel:      %d" % hazai_vendeg)
ki("###   jatekos-ellenfel olvasat stimmel:  %d" % jatekos_ellenfel)
if ellentmondas:
    ki("### EGYIK OLVASAT SEM ALL a kovetkezokre:")
    for x in ellentmondas[:10]:
        ki("    " + x)
if vizsgalt == 0:
    ki("### NEM VOLT ELEGENDO MINTA - a kerdes eldontetlen maradt.")

with open(NAPLO, "w", encoding="utf-8") as f:
    f.write("\n".join(sorok) + "\n")
print("\n".join(sorok))
