#!/usr/bin/env python3
"""NB1 pontigazitas a meccs vege utan (collect.py zaras_valtozas) - 10 allitas.

MIERT LETEZIK: a hivatalos szabalyzat szerint a pont minden meccs utan
meghatarozasra kerul, de a heti osszeg csak a fordulo utolso jateknapjanak
vegen VEGLEGES. A ketto kozott az MLSZ meg igazithat - a gyujto ezt eddig
atvezette, de nem orizte meg, pedig utolag rekonstrualhatatlan.

A tarolo alakja a PL zarasok.json-jat koveti, hogy az oldal ugyanazt a
megjelenitest hasznalhassa:  {szakvezeto: {"pont": [{n,cp,pos,tm,elott,utan,d}]}}

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


def j(nev, week, cp=1, vege=True, cap=False, sub=False, pos="MF", team="MTK"):
    return {"name": nev, "id": cp, "week": week, "vege": vege, "cap": cap,
            "sub": sub, "pos": pos, "team": team}


def sorok(t, mgr="Katyul"):
    return (t.get(mgr) or {}).get("pont") or []


MA = "2026-08-25"

# --- lement meccs utani valtozas: ez a hir ---
t = {}
db = c.zaras_valtozas({"Katyul": [j("A", 5.0)]}, {"Katyul": [j("A", 6.0)]}, t, MA)
allit(db == 1 and sorok(t) == [{"n": "A", "cp": 1, "pos": "MF", "tm": "MTK",
                                "elott": 5.0, "utan": 6.0, "d": MA}],
      "lement meccs utan valtozott pont bekerul (%s)" % t)

# --- meccs KOZBEN nem hir: a pont meg ketyeg ---
t = {}
db = c.zaras_valtozas({"Katyul": [j("A", 5.0, vege=False)]},
                      {"Katyul": [j("A", 6.0, vege=False)]}, t, MA)
allit(db == 0 and t == {}, "meccs kozbeni valtozas NEM kerul be (a pont meg ketyeg)")

# --- valtozatlan pont nem hir ---
t = {}
allit(c.zaras_valtozas({"Katyul": [j("A", 5.0)]}, {"Katyul": [j("A", 5.0)]}, t, MA) == 0
      and t == {}, "valtozatlan pontra nem keletkezik bejegyzes")

# --- a KAPITANYI duplazast visszaszamoljuk: ugyanaz a valtozas ---
# regi: kezdo 5,0 -> uj: kapitany 12,0 (alappont 6,0). A valtozas 5 -> 6,
# NEM 5 -> 12: a jatekos sajat pontja valtozott, nem a szerepe miatti szorzo.
t = {}
c.zaras_valtozas({"Katyul": [j("A", 5.0)]}, {"Katyul": [j("A", 12.0, cap=True)]}, t, MA)
s = sorok(t)
allit(s and s[0]["elott"] == 5.0 and s[0]["utan"] == 6.0,
      "a kapitanyi duplazas vissza van szamolva (%s)" % (s[0] if s else None))

# --- a PAD felezeset is, negyedre kerekitve ---
# 0,38 pados ertek = 0,75 alappont (az API a felezes utan ket tizedesre kerekit)
t = {}
c.zaras_valtozas({"Katyul": [j("A", 0.38, sub=True)]},
                 {"Katyul": [j("A", 0.5, sub=True)]}, t, MA)
s = sorok(t)
allit(s and s[0]["elott"] == 0.75 and s[0]["utan"] == 1.0,
      "a padfelezes vissza van szamolva, negyedre kerekitve (%s)" % (s[0] if s else None))

# --- ugyanaz a jatekos TOBB keretben: mindegyik szakvezetonel ott a sor ---
# A PL-panellel egyezoen szakvezeto szerint csoportositunk: akinel ott volt a
# jatekos, annak a blokkjaban latnia kell a valtozast.
t = {}
db = c.zaras_valtozas({"Katyul": [j("A", 5.0)], "Bazsa": [j("A", 5.0)], "Csendi": [j("A", 5.0)]},
                      {"Katyul": [j("A", 6.0)], "Bazsa": [j("A", 6.0)], "Csendi": [j("A", 6.0)]},
                      t, MA)
allit(db == 3 and sorted(t) == ["Bazsa", "Csendi", "Katyul"]
      and all(len(sorok(t, m)) == 1 for m in t),
      "ugyanaz a valtozas mindharom szakvezetonel megjelenik (%s)" % sorted(t))

# --- ugyanaz a futas ketszer: a dedup nem duplaz ---
c.zaras_valtozas({"Katyul": [j("A", 5.0)]}, {"Katyul": [j("A", 6.0)]}, t, MA)
allit(len(sorok(t)) == 1, "ugyanaz az igazitas nem kerul be ketszer (%s)" % sorok(t))

# --- de a KESOBBI, ujabb igazitas nem veszhet el ---
c.zaras_valtozas({"Katyul": [j("A", 6.0)]}, {"Katyul": [j("A", 5.5)]}, t, "2026-08-26")
s = sorok(t)
allit(len(s) == 2 and s[1]["elott"] == 6.0 and s[1]["utan"] == 5.5,
      "a kesobbi ujabb igazitas is bekerul, nem nyeli el a dedup (%s)" % s)

# --- hianyzo adat nem ertelmezheto valtozaskent ---
t = {}
c.zaras_valtozas({"Katyul": [j("A", None)]}, {"Katyul": [j("A", 6.0)]}, t, MA)
c.zaras_valtozas({"Katyul": [j("A", 5.0)]},
                 {"Katyul": [{"name": "A", "id": 1, "vege": True}]}, t, MA)
allit(t == {}, "hianyzo pont egyik iranyban sem szamit valtozasnak")

# --- akit kicsereltek: nincs par, nincs bejegyzes ---
t = {}
c.zaras_valtozas({"Katyul": [j("A", 5.0, cp=1)]}, {"Katyul": [j("B", 9.0, cp=2)]}, t, MA)
allit(t == {}, "aki mar nincs a keretben, arrol nem talalunk ki valtozast")

if hibak:
    print("\n%d allitas bukott." % len(hibak))
    sys.exit(1)
print("\nMind a 10 allitas rendben.")
