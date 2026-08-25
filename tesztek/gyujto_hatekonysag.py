#!/usr/bin/env python3
"""A kezdoallitasi hatekonysag szamitasa (collect.py hatekonysag) - 7 allitas.

A szabaly (Vince, 2026-08-25): a pad kotelezoen 1 kapus + 1 vedo + 1 kozep-
palyas + 1 csatar, tehat az optimum posztonkent a leggyengebb kiultetese;
a kapitany a kezdok legjobbja. A tarolt week mar KESZ ertek (kapitanyi x2,
pad x0.5) - a nyers pontot a cap/sub jelzobol kell visszafejteni.
"""
import importlib.util, json, os, sys

FORRAS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'collect.py')
spec = importlib.util.spec_from_file_location('collect', FORRAS)
c = importlib.util.module_from_spec(spec); sys.modules['collect'] = c
spec.loader.exec_module(c)
hibak = []


def allit(felt, cimke):
    print(("OK   " if felt else "HIBA ") + cimke)
    if not felt:
        hibak.append(cimke)


def j(pos, week, cap=False, sub=False):
    return {"pos": pos, "week": week, "cap": cap, "sub": sub}


# --- tokeletes felallitas: a hatekonysag pontosan 100% ---
# nyers pontok: K 6/1, H 5/4/3/1, KP 7/6/5/4/2, CS 9/3/2/1
# optimalis pad (posztonkenti minimum): K1, H1, KP2, CS1 -> x0.5 = 2.5
# kezdok nyers osszege: (6)+(5+4+3)+(7+6+5+4)+(9+3+2) = 54; kapitany a 9-es
# leheto = 54 + 2.5 + 9 = 65.5
TOKELETES = ([j("K", 6), j("K", 0.5, sub=True)]
             + [j("H", 5), j("H", 4), j("H", 3), j("H", 0.5, sub=True)]
             + [j("KP", 7), j("KP", 6), j("KP", 5), j("KP", 4), j("KP", 1, sub=True)]
             + [j("CS", 18, cap=True), j("CS", 3), j("CS", 2), j("CS", 0.5, sub=True)])
v = c.hatekonysag(TOKELETES)
allit(v is not None and abs(v[1] - 65.5) < 1e-9,
      "leheto: posztonkenti minimum a padra, legjobb kezdo a kapitany (%.2f)" % (v[1] if v else -1))
allit(v is not None and abs(v[0] - v[1]) < 1e-9,
      "a tokeletes felallitas 100%%: szerzett == leheto (%.2f == %.2f)" % (v or (0, 0)))

# --- rossz felallitas: a 9-es nyerspontu csatar a PADON ul (week 4.5),
#     es a kapitanyi szalag az 5-os vedon (week 10) ---
ROSSZ = ([j("K", 6), j("K", 0.5, sub=True)]
         + [j("H", 10, cap=True), j("H", 4), j("H", 3), j("H", 0.5, sub=True)]
         + [j("KP", 7), j("KP", 6), j("KP", 5), j("KP", 4), j("KP", 1, sub=True)]
         + [j("CS", 4.5, sub=True), j("CS", 3), j("CS", 2), j("CS", 1)])
v2 = c.hatekonysag(ROSSZ)
allit(v2 is not None and abs(v2[1] - 65.5) < 1e-9,
      "a leheto NEM fugg a tenyleges felallitastol (%.2f)" % (v2[1] if v2 else -1))
allit(v2 is not None and v2[0] < v2[1],
      "a rossz felallitas szerzettje kisebb a lehetonel (%.2f < %.2f)" % (v2 or (0, 0)))
allit(v2 is not None and abs(v2[0] - sum(p["week"] for p in ROSSZ)) < 1e-9,
      "a szerzett a week-ek osszege (a hivatalos fordulopont)")

# --- hianyos adat: nem 15 fos keret vagy hianyzo poszt -> None ---
allit(c.hatekonysag(TOKELETES[:14]) is None, "14 fos keretre nincs ertek")
allit(c.hatekonysag([j("K", 1)] * 15) is None, "egyposztos (serult) keretre nincs ertek")

if hibak:
    print("\n%d allitas bukott." % len(hibak)); sys.exit(1)
print("\nMind a het allitas rendben.")
