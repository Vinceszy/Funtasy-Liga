#!/usr/bin/env python3
"""A collect.py onjavitasanak tesztje mockolt API-val.

Ket dolgot ellenoriz:
 1. Ha egy REGI fordulo hivatalos pontja megvaltozott az MLSZ-nel, a
    gyujto atvezeti a results.json-ba ES ujra lekeri a fordulo kereteit.
 2. Ha a keretbol szamolt osszeg nem egyezik a tarolt hivatalossal, a
    gyujto ujra lekeri a hivatalos erteket, es azt irja be (nem csak jelez).
"""
import importlib.util, json, os, shutil, sys, tempfile, urllib.parse

FORRAS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'collect.py')
MUNKA = tempfile.mkdtemp()
os.chdir(MUNKA)

spec = importlib.util.spec_from_file_location('collect', FORRAS)
c = importlib.util.module_from_spec(spec)
sys.modules['collect'] = c
spec.loader.exec_module(c)

NEVEK = list(c.MEMBERS)                      # 8 szakvezeto
UNAME = {u: n for n, u in c.MEMBERS.items()}

# a "valosag" az API-ban: fordulo -> nev -> hivatalos pont
API_PONT = {1: {n: 40.0 for n in NEVEK},
            2: {n: 50.0 for n in NEVEK},
            3: {n: 60.0 for n in NEVEK},
            4: {n: 70.0 for n in NEVEK},
            5: {n: 0.0 for n in NEVEK}}
API_PONT[2]['Bazsa'] = 55.0                  # <-- utolagos MLSZ-korrekcio
API_PONT[4]['Katyul'] = 77.0                 # a valos (javitott) ertek
ALAP_ELAVULT = {(4, 'Katyul'): 70.0}         # az alap ranglista meg a regit adja

KERET_HIVAS = []                             # melyik fordulora kertunk keretet


def keret(round_no, nev):
    """15 jatekos; az osszeguk + magyarszabaly = az API szerinti pont."""
    cel = API_PONT[round_no][nev] - 10        # a +10 a magyarszabaly
    jatekosok = []
    for i in range(15):
        jatekosok.append({
            "id": 1000 + i, "is_captain": False,
            "type": "starter" if i < 11 else "substitutes",
            "position": {"monogram": "H"},
            "summary_statistics": {"weekly_points": cel if i == 0 else 0,
                                   "competition_points": 100},
            "competition_player": {
                "id": 500 + i, "first_name": "J%d" % i, "last_name": nev,
                "is_u21": i < 2, "team": {"short_name": "XYZ"},
                "countries": [{"code": "HUN"}],
                "current_round": {"is_played": True, "market_price": 5,
                                  "first_played_at": "2026-08-01T17:00:00+02:00",
                                  "games": [{"start_at": "2026-08-01T17:00:00+02:00",
                                             "status": "completed"}]}}})
    return {"data": jatekosok}


def mock_api_get(url, retries=3):
    q = urllib.parse.urlparse(url).query
    par = urllib.parse.parse_qs(q)
    if "rankings" in url:
        uname = par["filter[search]"][0]
        nev = UNAME[uname]
        rid = par.get("filter[round_id]")
        if rid:
            r = (int(rid[0]) - 75) // 2
            fordulok = [x for x in (r - 1, r) if x in API_PONT]
        else:
            fordulok = [4, 5]                 # alapbol az utolso ketto
        def pont(x):
            if not rid and (x, nev) in ALAP_ELAVULT:
                return ALAP_ELAVULT[(x, nev)]
            return API_PONT[x][nev]
        return 200, {"data": [{
            "user_team": {"user": {"id": NEVEK.index(nev) + 1, "username": uname},
                          "round_statistics": [
                              {"round_number": x, "points": pont(x)}
                              for x in fordulok]}}]}
    if "user-team-players-history" in url:
        r = (int(par["filter[round_id]"][0]) - 75) // 2
        uid = int(par["filter[user_id]"][0])
        nev = NEVEK[uid - 1]
        KERET_HIVAS.append((r, nev))
        return 200, keret(r, nev)
    return 404, None


c.api_get = mock_api_get

# ---- kiindulo allapot: a 2. fordulo regi erteke, a 4. Katyulnal elavult
menetrend = {}
for r in range(1, 6):
    parok = [(NEVEK[0], NEVEK[1]), (NEVEK[2], NEVEK[3]),
             (NEVEK[4], NEVEK[5]), (NEVEK[6], NEVEK[7])]
    menetrend[str(r)] = [[h, v,
                          None if r == 5 else (50.0 if r == 2 else API_PONT[r][h]),
                          None if r == 5 else (50.0 if r == 2 else API_PONT[r][v])]
                         for h, v in parok]
menetrend["4"][0][2] = 70.0                   # Katyul tarolt erteke elavult (70), az API-ban 77
json.dump({"updated": None, "provisional": [], "schedule": menetrend},
          open("results.json", "w"))
json.dump({"updated": None, "rounds": {}}, open("squad_history.json", "w"))

print("--- gyujto futtatasa ---")
c.main()
print("--- ellenorzes ---")

eredmeny = json.load(open("results.json"))
sch = eredmeny["schedule"]
hibak = []


def all(felt, cimke):
    print(("OK   " if felt else "HIBA ") + cimke)
    if not felt:
        hibak.append(cimke)


bazsa2 = next(m[2] for m in sch["2"] if m[0] == 'Bazsa')
all(bazsa2 == 55.0, "a 2. fordulo utolag korrigalt pontja atjott (%.1f)" % bazsa2)
all(any(r == 2 for r, _ in KERET_HIVAS),
    "a 2. fordulo keretei is ujra lekerve (a pont valtozott)")
katyul4 = next(m[2] for m in sch["4"] if m[0] == 'Katyul')
all(katyul4 == 77.0,
    "a keretbol kiderult elteres utan a hivatalos pont javitva (%.1f)" % katyul4)
kesz = json.load(open("squad_history.json"))
all("2" in kesz["rounds"] and len(kesz["rounds"]["2"]) == len(NEVEK),
    "a 2. fordulo keret-elozmenye teljes")

# A gyujto irja-e a fordulonkenti keret-fajlokat, es egyeznek-e a teljes
# elozmennyel? (Az oldal egy meccs megnyitasakor ezekbol olvas.)
if os.path.isdir("keretek"):
    fajlok = sorted(os.listdir("keretek"))
    all(len(fajlok) == len(kesz["rounds"]),
        "minden fordulohoz keszult keret-fajl (%d db)" % len(fajlok))
    baj = []
    for r, keret in kesz["rounds"].items():
        try:
            egy = json.load(open(os.path.join("keretek", "%s.json" % r)))
        except Exception as e:
            baj.append("%s: %s" % (r, e)); continue
        if egy.get("squads") != keret or egy.get("round") != int(r):
            baj.append(r)
    all(not baj, "a fordulonkenti fajlok egyeznek az elozmennyel" + (" (%s)" % baj if baj else ""))
    # az idobelyeg SZANDEKOSAN nincs bennuk: kulonben minden futasnal
    # valtozna mind a 33 fajl, es feleslegesen hizna a repo
    egy = json.load(open(os.path.join("keretek", fajlok[0])))
    all("updated" not in egy, "nincs benne idobelyeg (kulonben minden futasnal valtozna)")
else:
    all(False, "a gyujto nem irt keretek/ konyvtarat")

print("\nkeret-lekeresek fordulonkent:",
      {r: sum(1 for x, _ in KERET_HIVAS if x == r) for r in sorted({x for x, _ in KERET_HIVAS})})
shutil.rmtree(MUNKA, ignore_errors=True)
sys.exit(1 if hibak else 0)
