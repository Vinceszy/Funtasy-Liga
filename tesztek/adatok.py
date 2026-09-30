#!/usr/bin/env python3
"""A TAROLT LIGA-ADAT belso ellentmondasai - halozat nelkul, a repobol.

MIERT KELL: a gyujtok haromoranként felulirjak ezeket a fajlokat egy kulso
API valaszabol. A gyujtok sajat tesztjei (gyujto_*.py) azt nezik, hogy a
gyujto jol dolgozza-e fel, amit kap; azt nem, hogy az EREDMENY ertelmes-e.
Egy fel keret, egy eltunt kapitany vagy ket keretben szereplo ugyanaz a
draft-jatekos a lapon csak annyit jelent, hogy valami furcsa szam all ki -
es a szoveg, ami ezekbol az adatokbol keszul, csendben hazudik.

A szabalyok a ket jatek sajat szabalyai, nem a mi valasztasaink:
  NB1 (salary cap): nyolc szakvezeto, tizenot fos keret, tizenegy kezdo,
    pontosan egy kapitany - a kapitany az egyetlen kar a jatekban.
  Draft: tizenot fos keret, tizenegy kezdo, es EGY jatekos EGY keretben -
    a draft egesz lenyege, hogy a jatekosok el vannak osztva.
Ha ezek valamelyike serul, az adat rossz, nem a szabaly valtozott.
"""
import json
import os
import re
import sys
from collections import Counter

GYOKER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
hibak = []
allitasok = []


def allit(felt, cimke):
    print(("OK   " if felt else "HIBA ") + cimke)
    allitasok.append(cimke)
    if not felt:
        hibak.append(cimke)


def J(nev):
    with open(os.path.join(GYOKER, nev), encoding="utf-8") as f:
        return json.load(f)


# ---- NB1: keretek ----
gond = []
for r, keretek in sorted(J("squad_history.json")["rounds"].items(), key=lambda kv: int(kv[0])):
    if len(keretek) != 8:
        gond.append("%s. fordulo: %d keret a nyolcbol" % (r, len(keretek)))
    for mgr, keret in keretek.items():
        kezdo = [p for p in keret if not p.get("sub")]
        cap = [p for p in kezdo if p.get("cap")]
        if len(keret) != 15:
            gond.append("%s. %s: %d fos keret" % (r, mgr, len(keret)))
        if len(kezdo) != 11:
            gond.append("%s. %s: %d kezdo" % (r, mgr, len(kezdo)))
        if len(cap) != 1:
            gond.append("%s. %s: %d kapitany a kezdoben" % (r, mgr, len(cap)))
allit(not gond, "A1: az NB1 keretei teljesek (15 fo, 11 kezdo, 1 kapitany)"
      + ("" if not gond else " - " + "; ".join(gond[:3])))

# ---- Draft: keretek es a kozos jatekos tilalma ----
gond = []
for r, keretek in sorted(J("draft_history.json")["rounds"].items(), key=lambda kv: int(kv[0])):
    mind = []
    for cs, keret in keretek.items():
        kezdo = [p for p in keret if not p.get("b")]
        if len(keret) != 15:
            gond.append("%s. %s: %d fos keret" % (r, cs, len(keret)))
        if len(kezdo) != 11:
            gond.append("%s. %s: %d kezdo" % (r, cs, len(kezdo)))
        mind += [p["e"] for p in keret]
    ketszer = [e for e, c in Counter(mind).items() if c > 1]
    if ketszer:
        gond.append("%s. fordulo: %d jatekos tobb keretben is" % (r, len(ketszer)))
allit(not gond, "A2: a Draft keretei teljesek, es egy jatekos egy keretben van"
      + ("" if not gond else " - " + "; ".join(gond[:3])))

# ---- NB1 sorsolas: fordulonkent negy meccs, nyolc kulonbozo csapat ----
gond = []
for r, meccsek in J("results.json")["schedule"].items():
    nevek = [x for m in meccsek for x in m[:2]]
    if len(meccsek) != 4:
        gond.append("%s. fordulo: %d meccs" % (r, len(meccsek)))
    if len(set(nevek)) != len(nevek):
        gond.append("%s. fordulo: valaki ketszer szerepel" % r)
allit(not gond, "A3: az NB1 sorsolasa fordulonkent negy meccs, nyolc csapat"
      + ("" if not gond else " - " + "; ".join(gond[:3])))

# ---- A megjelent irasok valodi parharcra mutatnak ----
# Egy elirt nev vagy egy rossz fordulo nem tuno el: a cikk egyszeruen nem
# jelenik meg annal a meccsnel, es csak az veszi eszre, aki kereste.
art = J("articles.json")
res = J("results.json")["schedule"]
dr = J("draft.json")
pl_azon = {e["name"]: str(e["id"]) for e in dr["entries"]}
gond = []
for liga, fordulok in (art.get("leagues") or {}).items():
    menetrend = res if liga == "nb1" else dr["schedule"]
    for r, fajtak in fordulok.items():
        if r not in menetrend:
            gond.append("%s %s.: nincs ilyen fordulo" % (liga, r))
            continue
        parok = {frozenset((str(a), str(b))) for a, b, *_ in menetrend[r]}
        for fajta, irasok in fajtak.items():
            for kulcs in irasok:
                if fajta == "elemzes":
                    # A rovat a fordulohoz tartozik, nem parharchoz: a kulcsa
                    # a sajat cime. Fuggoleges vonal nem lehet benne, mert
                    # abbol a lap ket csapatnevet olvasna ki.
                    if "|" in kulcs:
                        gond.append("%s %s. rovat: | a cimben (%s)" % (liga, r, kulcs))
                    continue
                felek = kulcs.split("|")
                if len(felek) != 2:
                    gond.append("%s %s. %s: rossz parositas (%s)" % (liga, r, fajta, kulcs))
                    continue
                if liga == "pl":
                    felek = [pl_azon.get(x, "") for x in felek]
                if frozenset(felek) not in parok:
                    gond.append("%s %s. %s: %s nem egymas ellen jatszott"
                                % (liga, r, fajta, kulcs))
allit(not gond, "A4: minden iras valodi, abban a forduloban lejatszott parharcra mutat"
      + ("" if not gond else " - " + "; ".join(gond[:3])))

print("\n" + ("Mind a %d allitas rendben." % len(allitasok) if not hibak
              else "%d allitas bukott a %d-bol." % (len(hibak), len(allitasok))))
sys.exit(1 if hibak else 0)
