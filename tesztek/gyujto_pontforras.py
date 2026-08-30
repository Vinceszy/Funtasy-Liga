#!/usr/bin/env python3
"""A MENTETT fordulo-pont a TETELES BONTASBOL all ossze, nem az FPL
osszesitojebol - ugyanaz a szabaly, mint az oldalon.

MIERT: az FPL a stats.total_points-ot es az explain esemenylistat KULON
tartja, es az osszesito be tud ragadni (2026-08-30, GW2: a sor 1 pontot
mutatott, a bontas 90 percet es golt, osszesen 8-at; ugyanez a hivatalos
FPL-appban is). A lezart fordulot a gyujto SOHA TOBBE nem keri le, es az
oldal onnantol a MENTETT szamot mutatja - ami a lezaraskor bekerult, az
orokre bent marad.

P1: beragadt osszesito mellett a bontas osszege kerul a tarolt adatba.
P2: ha nincs explain (nem lepett palyara), a stats marad a forras -
    egy API-valtozas igy a REGI viselkedest adja vissza, nem nullakat.
P3: dupla fordulonal a ket meccs bontasa OSSZEADODIK.
P4: elteresnel a futas HANGOSAN szol (a naplobol latszik, ha rendszeres).
"""
import io, os, sys, contextlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import collect_draft as c

hibak, osszes = [], 0


def allit(felt, cimke):
    global osszes
    osszes += 1
    print(("OK   " if felt else "HIBA ") + cimke)
    if not felt:
        hibak.append(cimke)


def sor(stat, pont, ertek=0):
    return {"name": stat, "stat": stat, "points": pont, "value": ertek}


print("--- P1: beragadt osszesito mellett a bontas nyer ---")
beragadt = {"stats": {"total_points": 1, "minutes": 9},
            "explain": [[[sor("minutes", 2, 90), sor("goals_scored", 4, 1),
                          sor("bonus", 2, 2)], 12]]}
p, bontasbol = c.jatekos_pont(beragadt)
allit(p == 8, "P1: a tarolt pont a bontas osszege (8), nem a beragadt 1 - kapott: %s" % p)
allit(bontasbol, "P1: a fuggveny jelzi, hogy a bontasbol jott")

print("\n--- P2: nincs bontas -> a stats marad ---")
for cimke, v in (("ures explain", {"stats": {"total_points": 3}, "explain": []}),
                 ("nincs explain kulcs", {"stats": {"total_points": 3}}),
                 ("ismeretlen szerkezet", {"stats": {"total_points": 3},
                                           "explain": [{"fixture": 1, "stats": []}]})):
    p, bontasbol = c.jatekos_pont(v)
    allit(p == 3 and not bontasbol,
          "P2: %s -> a stats osszesitoje marad (3) - kapott: %s" % (cimke, p))

print("\n--- P3: dupla fordulo: a ket meccs osszeadodik ---")
dupla = {"stats": {"total_points": 0},
         "explain": [[[sor("minutes", 2, 90), sor("goals_scored", 4, 1)], 12],
                     [[sor("minutes", 2, 90), sor("assists", 3, 1)], 15]]}
p, _ = c.jatekos_pont(dupla)
allit(p == 11, "P3: a ket meccs bontasa osszeadodik (2+4+2+3 = 11) - kapott: %s" % p)

print("\n--- P4: hianyzo mezok nem dontik el ---")
for cimke, v in (("ures dict", {}), ("None", None),
                 ("explain=None", {"stats": {"total_points": 5}, "explain": None})):
    try:
        p, _ = c.jatekos_pont(v)
        allit(True, "P4: %s -> nem hasal el (%s pont)" % (cimke, p))
    except Exception as e:
        allit(False, "P4: %s -> KIVETEL: %r" % (cimke, e))

if hibak:
    print("\n%d allitas bukott." % len(hibak))
    sys.exit(1)
print("\nMind a %d allitas rendben." % osszes)
