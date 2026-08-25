#!/usr/bin/env python3
"""A jatekostorzs es az arnaplo (collect.py) - 10 allitas.

MIERT: a torzs a fooldali lista es kereses forrasa, az arnaplo pedig az
EGYETLEN ut az arak valtozasanak kovetesehez - kimertuk, hogy az MLSZ sehol
nem ad ar-elozmenyt (naplo/mlsz-jatekoslista.txt, 6. kor: minden include-ot
nemán elnyel, a kulon vegpontok 404-esek). Amit a naplo ma nem ir fel, az
visszamenoleg pototlhatatlan - ezert erdemel sajat tesztet.
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


# ---------------- 1) a torzs lekepezese ----------------
VALASZ = {"data": [
    {"id": 915, "first_name": "Áron", "last_name": "Alaxai", "is_u21": False,
     "position": {"monogram": "H", "name": "Hátvéd"},
     "team": {"short_name": "NYÍREGY", "name": "Nyíregyháza"},
     "current_round": {"market_price": 4.2},
     "summary_statistics": {"competition_points": 12.5}},
    # hianyos sor: nincs monogram, nincs short_name, nincs ar
    {"id": 916, "first_name": "", "last_name": "Teszt", "is_u21": True,
     "position": {"name": "Csatár"}, "team": {"name": "MTK"},
     "current_round": {}, "summary_statistics": {}},
    {"first_name": "Nincs", "last_name": "Azonosító"},          # id nelkul: kimarad
]}
kert = {}
c.api_get = lambda url, retries=3: (kert.setdefault("url", url), (200, VALASZ))[1]
t = c.jatekostorzs()

allit(t is not None and len(t) == 2, "az azonosito nelkuli sor kimarad (%s sor)" % (len(t) if t else None))
allit("per_page=500" in kert["url"], "egy keres, nagy lapmerettel (per_page=500)")
allit(t["915"] == {"n": "Áron Alaxai", "t": "NYÍREGY", "p": "H", "u21": False,
                   "pts": 12.5, "ar": 4.2}, "a teljes sor minden mezoje a helyere kerul")
allit(t["916"]["p"] == "Csatár" and t["916"]["t"] == "MTK",
      "monogram/rovidnev hianyaban a teljes nev a tartalek")
allit(t["916"]["pts"] == 0 and t["916"]["ar"] is None,
      "hianyzo pont -> 0, hianyzo ar -> None (nem 0: az arvaltozasnak latszana)")

c.api_get = lambda url, retries=3: (500, None)
allit(c.jatekostorzs() is None, "hibas valasznal None jon (a fajl valtozatlan marad)")

# ---------------- 2) az arnaplo ----------------
os.chdir(os.path.dirname(FORRAS))                # a naplo a repo gyokerebol olvas

def naplo(torzs, mai, elozo=None):
    """Az arnaplo egy lepese - a lemezen levo arak.json HELYETT a megadott
    elozmennyel, hogy a teszt ne fuggjon a repo aktualis adatatol."""
    import builtins, io
    eredeti = builtins.open           # a modul a beepitett open-t hasznalja
    def nyit(nev, *a, **k):
        if nev == "arak.json":
            if elozo is None:
                raise FileNotFoundError(nev)
            return io.StringIO(json.dumps({"arak": elozo}))
        return eredeti(nev, *a, **k)
    c.open = nyit                     # a modul globalisa arnyekolja a beepitettet
    try:
        return c.arnaplo_frissit(torzs, mai)
    finally:
        del c.open


T1 = {"1": {"ar": 5.0}, "2": {"ar": 8.0}}
n, db = naplo(T1, "2026-08-25")
allit(db == 2 and n == {"1": [["2026-08-25", 5.0]], "2": [["2026-08-25", 8.0]]},
      "elso futas: minden ar bekerul")

# valtozatlan ar -> NEM ir be uj sort (3 oraankent futunk, kulonben hizna)
n2, db2 = naplo(T1, "2026-08-26", elozo=n)
allit(db2 == 0 and n2 == n, "valtozatlan arnal nem keletkezik uj bejegyzes")

# valtozas -> csak az erintett jatekoshoz kerul uj sor, a regi MEGMARAD
n3, db3 = naplo({"1": {"ar": 5.5}, "2": {"ar": 8.0}}, "2026-08-27", elozo=n)
allit(db3 == 1 and n3["1"] == [["2026-08-25", 5.0], ["2026-08-27", 5.5]]
      and n3["2"] == [["2026-08-25", 8.0]],
      "valtozasnal uj sor kerul be, a korabbi ertek megmarad")

# hianyzo/nulla ar NEM szamit valtozasnak - kulonben egy API-hiba hamis
# "0-ra esett" bejegyzest irna be, amit utolag nem lehet megkulonboztetni
n4, db4 = naplo({"1": {"ar": None}, "2": {"ar": 0}}, "2026-08-28", elozo=n)
allit(db4 == 0 and n4 == n,
      "hianyzo vagy nulla ar nem kerul be (API-hiba nem ir hamis arzuhanast)")

if hibak:
    print("\n%d allitas bukott." % len(hibak))
    sys.exit(1)
print("\nMind a %d allitas rendben." % 10)
