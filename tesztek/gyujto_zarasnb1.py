#!/usr/bin/env python3
"""NB1 pontigazitas a meccs vege utan (collect.py zaras_valtozas) - 9 allitas.

MIERT LETEZIK: a hivatalos szabalyzat szerint a pont minden meccs utan
meghatarozasra kerul, de a heti osszeg csak a fordulo utolso jateknapjanak
vegen VEGLEGES. A ketto kozott az MLSZ meg igazithat - a gyujto ezt eddig
atvezette, de nem orizte meg, pedig utolag rekonstrualhatatlan.

Ez a resz elesben ritkan sul el, tehat a teszt az EGYETLEN hely, ahol
lathato, hogy mukodik-e.
"""
import importlib.util, os, sys

FORRAS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'collect.py')
spec = importlib.util.spec_from_file_location('collect', FORRAS)
c = importlib.util.module_from_spec(spec); sys.modules['collect'] = c
spec.loader.exec_module(c)
hibak = []


def allit(felt, cimke):
    print(("OK   " if felt else "HIBA ") + cimke)
    if not felt:
        hibak.append(cimke)


def j(nev, week, cp=1, vege=True, cap=False, sub=False):
    return {"name": nev, "id": cp, "week": week, "vege": vege, "cap": cap, "sub": sub}


MA = "2026-08-25"

# --- lement meccs utani valtozas: ez a hir ---
t = []
db = c.zaras_valtozas({"Katyul": [j("A", 5.0)]}, {"Katyul": [j("A", 6.0)]}, t, MA)
allit(db == 1 and t == [{"n": "A", "cp": 1, "e": 5.0, "u": 6.0, "d": MA}],
      "lement meccs utan valtozott pont bekerul (%s)" % t)

# --- meccs KOZBEN nem hir: a pont meg ketyeg ---
t = []
db = c.zaras_valtozas({"Katyul": [j("A", 5.0, vege=False)]},
                      {"Katyul": [j("A", 6.0, vege=False)]}, t, MA)
allit(db == 0 and t == [], "meccs kozbeni valtozas NEM kerul be (a pont meg ketyeg)")

# --- valtozatlan pont nem hir ---
t = []
allit(c.zaras_valtozas({"K": [j("A", 5.0)]}, {"K": [j("A", 5.0)]}, t, MA) == 0
      and t == [], "valtozatlan pontra nem keletkezik bejegyzes")

# --- a KAPITANYI duplazast visszaszamoljuk: ugyanaz a valtozas ---
# regi: kezdo 5,0 -> uj: kapitany 12,0 (alappont 6,0). A valtozas 5 -> 6,
# NEM 5 -> 12: a jatekos sajat pontja valtozott, nem a szerepe miatti szorzo.
t = []
c.zaras_valtozas({"K": [j("A", 5.0)]}, {"K": [j("A", 12.0, cap=True)]}, t, MA)
allit(t and t[0]["e"] == 5.0 and t[0]["u"] == 6.0,
      "a kapitanyi duplazas vissza van szamolva (%s)" % (t[0] if t else None))

# --- a PAD felezeset is, negyedre kerekitve ---
# 0,38 pados ertek = 0,75 alappont (az API a felezes utan ket tizedesre kerekit)
t = []
c.zaras_valtozas({"K": [j("A", 0.38, sub=True)]}, {"K": [j("A", 0.5, sub=True)]}, t, MA)
allit(t and t[0]["e"] == 0.75 and t[0]["u"] == 1.0,
      "a padfelezes vissza van szamolva, negyedre kerekitve (%s)" % (t[0] if t else None))

# --- ugyanaz a jatekos TOBB keretben: egyszer irjuk fel ---
t = []
db = c.zaras_valtozas({"K": [j("A", 5.0)], "B": [j("A", 5.0)], "C": [j("A", 5.0)]},
                      {"K": [j("A", 6.0)], "B": [j("A", 6.0)], "C": [j("A", 6.0)]}, t, MA)
allit(db == 1 and len(t) == 1,
      "ugyanaz a valtozas tobb keretbol csak EGYSZER kerul be (%d)" % len(t))

# --- de a KESOBBI, ujabb igazitas nem veszhet el ---
# ugyanaz a jatekos ujabb futasban ismet valtozik: a tarolo mar tartalmazza
# az elozot, de az ujat is fel kell irni
c.zaras_valtozas({"K": [j("A", 6.0)]}, {"K": [j("A", 5.5)]}, t, "2026-08-26")
allit(len(t) == 2 and t[1]["e"] == 6.0 and t[1]["u"] == 5.5,
      "a kesobbi ujabb igazitas is bekerul, nem nyeli el a dedup (%s)" % t)

# --- hianyzo adat nem ertelmezheto valtozaskent ---
t = []
c.zaras_valtozas({"K": [j("A", None)]}, {"K": [j("A", 6.0)]}, t, MA)
c.zaras_valtozas({"K": [j("A", 5.0)]}, {"K": [{"name": "A", "id": 1, "vege": True}]}, t, MA)
allit(t == [], "hianyzo pont egyik iranyban sem szamit valtozasnak")

# --- akit kicsereltek: nincs par, nincs bejegyzes ---
t = []
c.zaras_valtozas({"K": [j("A", 5.0, cp=1)]}, {"K": [j("B", 9.0, cp=2)]}, t, MA)
allit(t == [], "aki mar nincs a keretben, arrol nem talalunk ki valtozast")

if hibak:
    print("\n%d allitas bukott." % len(hibak))
    sys.exit(1)
print("\nMind a 9 allitas rendben.")
