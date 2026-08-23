#!/usr/bin/env python3
"""Ot allitas ellenorzese a gyujto fordulo-lezarasarol.

R1: az ELSO futasnal, amikor meg nincs korabbi provisional bejegyzes, egy
    elhasalt keret-lekeres utan a fordulo veglegesnek irodik-e be.
R2: ha a fordulo utolso meccse MEG TART, de az MLSZ mar mindenkire
    is_played=true-t ad, lezartnak minositi-e a gyujto a fordulot.
R3: akinek NINCS meccse a forduloban (halasztas), az nem akaszthatja meg a
    lezarast - kulonben a fordulo a klub kovetkezo meccseig ideiglenes marad.
R3b: ugyanez akkor is, ha a fordulo mar nem az aktualis, tehat a meccslistat
    nem kerjuk le - a "nincs meccse" jelzes a tarolt keretbol jon.
R4: biztonsagi halo - ha a jatekos-szintu kep nem all ossze, de az MLSZ mar
    tovabblepett a fordulon, lezartnak kell lennie.
R5: ...de amig az MLSZ szerint a fordulo AZ AKTUALIS, a halo nem sulhet el.
"""
import importlib.util, json, os, sys, tempfile, urllib.parse

FORRAS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'collect.py')
os.chdir(tempfile.mkdtemp())
spec = importlib.util.spec_from_file_location('collect', FORRAS)
c = importlib.util.module_from_spec(spec); sys.modules['collect'] = c
spec.loader.exec_module(c)

NEVEK = list(c.MEMBERS); UNAME = {u: n for n, u in c.MEMBERS.items()}
AKT = 5
VEGSO = 6                       # a legnagyobb fordulo, amire adat letezik
API = {r: {n: 40.0 + r for n in NEVEK} for r in range(1, VEGSO + 1)}
parok = [(NEVEK[0], NEVEK[1]), (NEVEK[2], NEVEK[3]), (NEVEK[4], NEVEK[5]), (NEVEK[6], NEVEK[7])]
hibak = []


def keret(r, nev, status, nogame=False, games=True):
    """15 jatekos; a meccs status-a allithato (scheduled = meg tart).

    nogame=True: a klubnak nincs meccse a forduloban - ures meccslista, es az
      MLSZ is_played=false-t ad (2026-08-23-i meres).
    games=False: a meccslistat nem kertuk (nem az elo fordulo) - ilyenkor a
      valaszban egyaltalan nincs games kulcs."""
    if nogame:
        meccs = {"is_played": False}
        if games:
            meccs["games"] = []
    else:
        meccs = {"is_played": True}
        if games:
            meccs["games"] = [{"start_at": "2026-08-23T17:30:00+02:00", "status": status}]
    return {"data": [{
        "id": 1000 + i, "is_captain": False,
        "type": "starter" if i < 11 else "substitutes",
        "position": {"monogram": "H"},
        "summary_statistics": {"weekly_points": (API[r][nev] - 10) if i == 0 else 0,
                               "competition_points": 1},
        "competition_player": {"id": 500 + i, "first_name": "J%d" % i, "last_name": nev,
            "is_u21": i < 2, "team": {"short_name": "XYZ"}, "countries": [{"code": "HUN"}],
            "current_round": dict(market_price=5,
                                  first_played_at="2026-08-23T17:30:00+02:00",
                                  **meccs)}} for i in range(15)]}


def keszit(prov, akt=AKT, tortenet=None):
    menetrend = {str(r): [[h, v, API[r][h], API[r][v]] for h, v in parok] for r in range(1, akt + 1)}
    json.dump({"updated": None, "provisional": prov, "schedule": menetrend}, open("results.json", "w"))
    rounds = {str(r): {n: [] for n in NEVEK} for r in range(1, akt + 1)}
    for r, keretek in (tortenet or {}).items():
        rounds[str(r)] = keretek
    json.dump({"updated": None, "rounds": rounds}, open("squad_history.json", "w"))


def futtat(status, bukjon_e, cimke, nogame_nevek=(), mlsz=None, akt=AKT):
    """status: a meccs allapota; bukjon_e: egy keret-lekeres elhasal-e;
    nogame_nevek: kiknek nincs meccsuk; mlsz: az MLSZ szerinti aktualis
    fordulo szama (None = a verseny-vegpont nem elerheto)."""
    def mock(url, retries=3):
        par = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        if "competitions?include=rounds" in url:
            if mlsz is None:
                return 500, None
            # a fordulok vegdatuma: mind a multban, a jelenlegi kivetelevel
            fordulok = [{"round_number": x, "end_at": "2026-08-%02dT10:00:00+02:00" % (10 + x)}
                        for x in range(1, VEGSO + 1)]
            return 200, {"data": [{"id": c.COMPETITION, "rounds": fordulok,
                                   "current_round": {"round_number": mlsz}}]}
        if "rankings" in url:
            nev = UNAME[par["filter[search]"][0]]
            return 200, {"data": [{"user_team": {
                "user": {"id": NEVEK.index(nev) + 1, "username": par["filter[search]"][0]},
                "round_statistics": [{"round_number": x, "points": API[x][nev]} for x in (akt - 1, akt)]}}]}
        if "user-team-players-history" in url:
            r = (int(par["filter[round_id]"][0]) - 75) // 2
            nev = NEVEK[int(par["filter[user_id]"][0]) - 1]
            if bukjon_e and (nev, r) == (NEVEK[2], akt):
                return 500, None
            return 200, keret(r, nev, status, nogame=(nev in nogame_nevek),
                              games="current_round.games" in urllib.parse.unquote(url))
        return 404, None
    c.api_get = mock
    c.ellenorzendo = lambda regi, db=4: []
    print("\n--- " + cimke + " ---")
    c.main()
    return json.load(open("results.json"))["provisional"]


def allit(felt, jo_uzenet, rossz_uzenet, cimke):
    if felt:
        print("OK   " + jo_uzenet)
    else:
        hibak.append(cimke); print("HIBA " + rossz_uzenet)


# ---- R1: elso futas, meg nincs korabbi provisional, egy lekeres elhasal
os.chdir(tempfile.mkdtemp()); keszit([])
prov = futtat("scheduled", True, "R1: elso futas + egy elhasalt keret-lekeres")
print("provisional:", prov)
allit(AKT in prov, "az elo fordulo ideiglenes lett",
    "veglegeskent irodott be - a reszeredmeny bekerul a tabellaba", "R1")

# ---- R2: minden lekeres jo, de a meccs MEG TART (status=scheduled)
os.chdir(tempfile.mkdtemp()); keszit([AKT])
prov = futtat("scheduled", False, "R2: minden keret megjott, de a meccs meg tart")
print("provisional:", prov)
allit(AKT in prov, "a fordulo ideiglenes maradt, amig a meccs tart",
    "lezartnak minositette - pedig a meccs meg tart (is_played=true)", "R2")

# ---- kontroll: ha a meccs LEMENT, akkor viszont lezartnak kell lennie
os.chdir(tempfile.mkdtemp()); keszit([AKT])
prov = futtat("completed", False, "kontroll: a meccs lement")
print("provisional:", prov)
allit(AKT not in prov, "lement meccs utan a fordulo lezart",
    "lement meccs utan is ideiglenes maradt", "kontroll")

# ---- R3: egy szakvezeto jatekosainak NINCS meccsuk (halasztas)
#      Az elozo fordulohoz is beirjuk a jelzest a tortenetbe: azt a gyujto
#      szinten ujra lekeri, de meccslista nelkul (nem az az elo fordulo).
os.chdir(tempfile.mkdtemp())
nogame_keret = {NEVEK[3]: [{"name": "J%d %s" % (i, NEVEK[3]), "nogame": True}
                           for i in range(15)]}
keszit([AKT], tortenet={AKT - 1: nogame_keret})
prov = futtat("completed", False, "R3: a 4. szakvezeto jatekosainak nincs meccsuk",
              nogame_nevek=(NEVEK[3],))
print("provisional:", prov)
allit(AKT not in prov, "a meccs nelkuli jatekosok nem akasztjak meg a lezarast",
    "ideiglenes maradt - a fordulo a klub kovetkezo meccseig beragadna", "R3")

# ---- R3b: ugyanez, de a fordulo mar nem az aktualis (nincs meccslista)
#      A "nincs meccse" jelzes ilyenkor csak a TAROLT keretbol jon.
os.chdir(tempfile.mkdtemp())
keszit([AKT], akt=VEGSO, tortenet={AKT: nogame_keret})
prov = futtat("completed", False, "R3b: regi fordulo, a nogame a tarolt keretbol jon",
              nogame_nevek=(NEVEK[3],), akt=VEGSO)
print("provisional:", prov)
allit(AKT not in prov, "a tarolt nogame jelzes is kihagyja a jatekost a lezarasbol",
    "ideiglenes maradt - a tarolt nogame jelzes elveszett", "R3b")

# ---- R4: a jatekos-szintu kep nem all ossze, de az MLSZ tovabblepett
os.chdir(tempfile.mkdtemp()); keszit([AKT])
prov = futtat("scheduled", False, "R4: meccs meg tart, de az MLSZ mar a 6. fordulonal jar",
              mlsz=AKT + 1)
print("provisional:", prov)
allit(AKT not in prov, "a biztonsagi halo lezarta a fordulot",
    "ideiglenes maradt - a fordulo orokre bent ragadhat", "R4")

# ---- R5: a halo NEM sulhet el, amig az MLSZ szerint a fordulo az aktualis
os.chdir(tempfile.mkdtemp()); keszit([AKT])
prov = futtat("scheduled", False, "R5: meccs meg tart, az MLSZ szerint is ez az aktualis",
              mlsz=AKT)
print("provisional:", prov)
allit(AKT in prov, "a halo nem sult el a futo fordulora",
    "lezarta a futo fordulot - felig kesz eredmeny kerul a tabellaba", "R5")

sys.exit(1 if hibak else 0)
