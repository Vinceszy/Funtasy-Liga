#!/usr/bin/env python3
"""Ket allitas ellenorzese a gyujtorol.

R1: az ELSO futasnal, amikor meg nincs korabbi provisional bejegyzes, egy
    elhasalt keret-lekeres utan a fordulo veglegesnek irodik-e be.
R2: ha a fordulo utolso meccse MEG TART, de az MLSZ mar mindenkire
    is_played=true-t ad, lezartnak minositi-e a gyujto a fordulot.
"""
import importlib.util, json, os, sys, tempfile, urllib.parse

FORRAS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'collect.py')
os.chdir(tempfile.mkdtemp())
spec = importlib.util.spec_from_file_location('collect', FORRAS)
c = importlib.util.module_from_spec(spec); sys.modules['collect'] = c
spec.loader.exec_module(c)

NEVEK = list(c.MEMBERS); UNAME = {u: n for n, u in c.MEMBERS.items()}
AKT = 5
API = {r: {n: 40.0 + r for n in NEVEK} for r in range(1, AKT + 1)}
parok = [(NEVEK[0], NEVEK[1]), (NEVEK[2], NEVEK[3]), (NEVEK[4], NEVEK[5]), (NEVEK[6], NEVEK[7])]
hibak = []


def keret(r, nev, status):
    """15 jatekos; a meccs status-a allithato (scheduled = meg tart)."""
    return {"data": [{
        "id": 1000 + i, "is_captain": False,
        "type": "starter" if i < 11 else "substitutes",
        "position": {"monogram": "H"},
        "summary_statistics": {"weekly_points": (API[r][nev] - 10) if i == 0 else 0,
                               "competition_points": 1},
        "competition_player": {"id": 500 + i, "first_name": "J%d" % i, "last_name": nev,
            "is_u21": i < 2, "team": {"short_name": "XYZ"}, "countries": [{"code": "HUN"}],
            "current_round": {"is_played": True, "market_price": 5,
                              "first_played_at": "2026-08-23T17:30:00+02:00",
                              "games": [{"start_at": "2026-08-23T17:30:00+02:00",
                                         "status": status}]}}} for i in range(15)]}


def keszit(prov):
    menetrend = {str(r): [[h, v, API[r][h], API[r][v]] for h, v in parok] for r in range(1, AKT + 1)}
    json.dump({"updated": None, "provisional": prov, "schedule": menetrend}, open("results.json", "w"))
    json.dump({"updated": None, "rounds": {str(r): {n: [] for n in NEVEK} for r in range(1, AKT + 1)}},
              open("squad_history.json", "w"))


def futtat(status, bukjon_e, cimke):
    """status: a meccs allapota; bukjon_e: egy keret-lekeres elhasal-e."""
    def mock(url, retries=3):
        par = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        if "rankings" in url:
            nev = UNAME[par["filter[search]"][0]]
            return 200, {"data": [{"user_team": {
                "user": {"id": NEVEK.index(nev) + 1, "username": par["filter[search]"][0]},
                "round_statistics": [{"round_number": x, "points": API[x][nev]} for x in (AKT - 1, AKT)]}}]}
        if "user-team-players-history" in url:
            r = (int(par["filter[round_id]"][0]) - 75) // 2
            nev = NEVEK[int(par["filter[user_id]"][0]) - 1]
            if bukjon_e and (nev, r) == (NEVEK[2], AKT):
                return 500, None
            return 200, keret(r, nev, status)
        return 404, None
    c.api_get = mock
    c.ellenorzendo = lambda regi, db=4: []
    print("\n--- " + cimke + " ---")
    c.main()
    return json.load(open("results.json"))["provisional"]


# ---- R1: elso futas, meg nincs korabbi provisional, egy lekeres elhasal
os.chdir(tempfile.mkdtemp()); keszit([])
prov = futtat("scheduled", True, "R1: elso futas + egy elhasalt keret-lekeres")
print("provisional:", prov)
if AKT in prov:
    print("OK   az elo fordulo ideiglenes lett")
else:
    hibak.append("R1"); print("HIBA veglegeskent irodott be - a reszeredmeny bekerul a tabellaba")

# ---- R2: minden lekeres jo, de a meccs MEG TART (status=scheduled)
os.chdir(tempfile.mkdtemp()); keszit([AKT])
prov = futtat("scheduled", False, "R2: minden keret megjott, de a meccs meg tart")
print("provisional:", prov)
if AKT in prov:
    print("OK   a fordulo ideiglenes maradt, amig a meccs tart")
else:
    hibak.append("R2"); print("HIBA lezartnak minositette - pedig a meccs meg tart (is_played=true)")

# ---- kontroll: ha a meccs LEMENT, akkor viszont lezartnak kell lennie
os.chdir(tempfile.mkdtemp()); keszit([AKT])
prov = futtat("completed", False, "kontroll: a meccs lement")
print("provisional:", prov)
if AKT not in prov:
    print("OK   lement meccs utan a fordulo lezart")
else:
    hibak.append("kontroll"); print("HIBA lement meccs utan is ideiglenes maradt")

sys.exit(1 if hibak else 0)
