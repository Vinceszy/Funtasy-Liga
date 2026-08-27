#!/usr/bin/env python3
"""Egy mar vegleges fordulo nem valhat ideiglenesse egy hianyos futastol.

A rolling ellenorzes ota egy regi fordulo is bekerulhet a keret-lekeresek
koze (ha az MLSZ korrigalt). Ha ott egyetlen keret-keres hibara fut, a
fordulo "nem lezart" lenne - es ideiglenesse minositve KIESNE a tabellabol.

A fajl vegen (C3) az is szerepel, hogy valtozatlan adatnal a results.json
egyaltalan nem irodik ujra - a tobbi kimeneti fajl mind igy mukodik.
"""
import importlib.util, json, os, sys, tempfile, urllib.parse

FORRAS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'collect.py')
os.chdir(tempfile.mkdtemp())
spec = importlib.util.spec_from_file_location('collect', FORRAS)
c = importlib.util.module_from_spec(spec); sys.modules['collect'] = c
spec.loader.exec_module(c)

NEVEK = list(c.MEMBERS); UNAME = {u: n for n, u in c.MEMBERS.items()}
AKTUALIS = 5
API = {r: {n: 40.0 + r for n in NEVEK} for r in range(1, AKTUALIS + 1)}
API[2]['Bazsa'] = 99.0                      # utolagos MLSZ-korrekcio a 2. fordulon
BUKO = ('Csongi', 2)                        # ennek a keret-lekerese hibara fut


def keret(r, nev):
    cel = API[r][nev] - 10
    return {"data": [{
        "id": 1000 + i, "is_captain": False,
        "type": "starter" if i < 11 else "substitutes",
        "position": {"monogram": "H"},
        "summary_statistics": {"weekly_points": cel if i == 0 else 0, "competition_points": 1},
        "competition_player": {"id": 500 + i, "first_name": "J%d" % i, "last_name": nev,
            "is_u21": i < 2, "team": {"short_name": "XYZ"}, "countries": [{"code": "HUN"}],
            "current_round": {"is_played": True, "market_price": 5,
                              "first_played_at": "2026-08-01T17:00:00+02:00"}}} for i in range(15)]}


def mock(url, retries=3):
    par = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
    if "rankings" in url:
        nev = UNAME[par["filter[search]"][0]]
        rid = par.get("filter[round_id]")
        rr = [x for x in ((int(rid[0]) - 75) // 2 - 1, (int(rid[0]) - 75) // 2) if x in API] \
             if rid else [AKTUALIS - 1, AKTUALIS]
        return 200, {"data": [{"user_team": {"user": {"id": NEVEK.index(nev) + 1, "username": par["filter[search]"][0]},
            "round_statistics": [{"round_number": x, "points": API[x][nev]} for x in rr]}}]}
    if "user-team-players-history" in url:
        r = (int(par["filter[round_id]"][0]) - 75) // 2
        nev = NEVEK[int(par["filter[user_id]"][0]) - 1]
        if (nev, r) == BUKO:
            return 500, None                # <-- itt hasal el a lekeres
        return 200, keret(r, nev)
    return 404, None


c.api_get = mock
c.ellenorzendo = lambda regi, db=4: [2] if 2 in regi else []   # a 2. fordulot nezzuk

parok = [(NEVEK[0], NEVEK[1]), (NEVEK[2], NEVEK[3]), (NEVEK[4], NEVEK[5]), (NEVEK[6], NEVEK[7])]
menetrend = {str(r): [[h, v, API[r][h] if r != 2 else 50.0, API[r][v] if r != 2 else 50.0]
                      for h, v in parok] for r in range(1, AKTUALIS + 1)}
json.dump({"updated": None, "provisional": [], "schedule": menetrend}, open("results.json", "w"))
# a keret-elozmeny mar teljes minden fordulora, hogy csak a `valtozott` ag hozza be a 2-est
tortenet = {str(r): {n: [] for n in NEVEK} for r in range(1, AKTUALIS + 1)}
json.dump({"updated": None, "rounds": tortenet}, open("squad_history.json", "w"))
# kesz meccslista, hogy a meccsek.json-potlas ne szoljon bele (gyujto_meccsek.py tesztje)
json.dump({"updated": None, "rounds": {str(r): [
    {"id": 900 + r, "h": "XYZ", "v": "ZZZ", "start": "2026-08-01T17:30:00+02:00",
     "hp": 1, "vp": 0, "vege": True}] for r in range(1, 9)}}, open("meccsek.json", "w"))

print("--- gyujto ---")
c.main()
print("--- ellenorzes ---")
prov = json.load(open("results.json"))["provisional"]
print("provisional:", prov)
hibak = []
if 2 in prov:
    hibak.append("a 2. fordulo ideiglenesse valt egy elhasalt keret-lekeres miatt")
    print("HIBA a 2. fordulo ideiglenesse valt egy elhasalt keret-lekeres miatt")
else:
    print("OK   a reg lezart 2. fordulo NEM lett ideiglenes (a keret-lekeres hibaja ellenere)")
bazsa2 = next(m[2] for m in json.load(open("results.json"))["schedule"]["2"] if m[0] == 'Bazsa')
print(("OK   " if bazsa2 == 99.0 else "HIBA ") + "a korrekcio ettol meg atjott (%.1f)" % bazsa2)
if bazsa2 != 99.0: hibak.append("korrekcio")


# ---------------------------------------------------------------- C1
# Ha az ELO fordulo kereteit egyaltalan nem tudjuk lekerni, a korabbi
# ideiglenes-jelolesnek MEG KELL MARADNIA. Kulonben a provisional kiurul, es
# az elo fordulo reszeredmenye veglegeskent szamit be a tabellaba.
print("\n--- C1: az elo fordulo keretei egyaltalan nem jonnek meg ---")
os.chdir(tempfile.mkdtemp())
json.dump({"updated": None, "provisional": [AKTUALIS], "schedule": menetrend},
          open("results.json", "w"))
json.dump({"updated": None, "rounds": tortenet}, open("squad_history.json", "w"))


def mock2(url, retries=3):
    if "user-team-players-history" in url:
        return 500, None            # MINDEN keret-lekeres elhasal
    return mock(url, retries)


c.api_get = mock2
c.ellenorzendo = lambda regi, db=4: []
c.main()
prov2 = json.load(open("results.json"))["provisional"]
print("provisional:", prov2)
if AKTUALIS in prov2:
    print("OK   az elo fordulo ideiglenes maradt (a reszeredmeny nem szamit be)")
else:
    hibak.append("C1: a provisional kiurult")
    print("HIBA a provisional kiurult - a reszeredmeny veglegeskent szamitana")

# ---------------------------------------------------------------- C2
# MEGTORTENT (2026-08-25 21:47): egy DNS-hiba miatt EGY tag ranglista-adata
# (es igy az azonositoja) nem jott meg -> minden cel-fordulo "hianyos" lett,
# es a mar veglegeskent kozolt aktualis-1 fordulo ideiglenesse valt: a
# tabella a 4 fordulos allast mutatta. A szabaly: amit mar veglegeskent
# kozoltunk, azt hianyos futas nem nyithatja ujra.
print("\n--- C2: egy tag azonositoja nem jon meg (halozati hiba) ---")
os.chdir(tempfile.mkdtemp())
json.dump({"updated": None, "provisional": [AKTUALIS], "schedule": menetrend},
          open("results.json", "w"))
json.dump({"updated": None, "rounds": tortenet}, open("squad_history.json", "w"))
json.dump({"updated": None, "rounds": {str(r): [
    {"id": 900 + r, "h": "XYZ", "v": "ZZZ", "start": "2026-08-01T17:30:00+02:00",
     "hp": 1, "vp": 0, "vege": True}] for r in range(1, 9)}}, open("meccsek.json", "w"))


def mock3(url, retries=3):
    if "rankings" in url:
        par3 = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        if UNAME[par3["filter[search]"][0]] == NEVEK[0]:
            return 500, None            # <-- a halozati hiba
    return mock(url, retries)


c.api_get = mock3
c.ellenorzendo = lambda regi, db=4: []
c.main()
prov3 = json.load(open("results.json"))["provisional"]
print("provisional:", prov3)
if AKTUALIS - 1 in prov3:
    hibak.append("C2: a mar vegleges fordulo ujranyilt egy halozati hibatol")
    print("HIBA a mar veglegeskent kozolt %d. fordulo ideiglenesse valt" % (AKTUALIS - 1))
else:
    print("OK   a mar veglegeskent kozolt %d. fordulo vegleges maradt" % (AKTUALIS - 1))
if AKTUALIS not in prov3:
    hibak.append("C2: az elo fordulo kikerult az ideiglenesek kozul")
    print("HIBA az elo fordulo kikerult az ideiglenesek kozul")
else:
    print("OK   az elo fordulo tovabbra is ideiglenes")


# ---------------------------------------------------------------- C3
# A results.json csak akkor irodhat ujra, ha TENYLEG valtozott valami.
# MEGTORTENT: a feltetel egy listat hasonlitott halmazhoz
# (`provisional != regi_prov`), ami sosem egyenlo - igy minden futas friss
# idobelyeggel ujrairta a fajlt. A 36 utolso results.json-commitbol 30-ban
# CSAK az `updated` mezo valtozott. (A tobbi fajl mind tartalmat hasonlit.)
print("\n--- C3: valtozatlan adatnal a results.json nem irodik ujra ---")
os.chdir(tempfile.mkdtemp())
json.dump({"updated": None, "provisional": [], "schedule": menetrend},
          open("results.json", "w"))
json.dump({"updated": None, "rounds": tortenet}, open("squad_history.json", "w"))
json.dump({"updated": None, "rounds": {str(r): [
    {"id": 900 + r, "h": "XYZ", "v": "ZZZ", "start": "2026-08-01T17:30:00+02:00",
     "hp": 1, "vp": 0, "vege": True}] for r in range(1, 9)}}, open("meccsek.json", "w"))

# A menetrendben mar minden eredmeny benne van, es a 2. fordulo korrekcioja
# sem kell ide: az ELSO futas beallitja a vegallapotot, a MASODIK futasnak
# mar semmit nem szabad irnia.
c.api_get = mock
c.ellenorzendo = lambda regi, db=4: []
# Az idobelyeg MASODPERC-pontossagu: ket egymas utani futas ugyanazt a
# szoveget irna, es a teszt akkor is atmenne, ha a fajl ujrairodik. Ezert a
# stamp() helyere szamlalo kerul - igy minden iras LATSZIK.
eredeti_stamp, szamlalo = c.stamp, [0]
def szamlalo_stamp():
    szamlalo[0] += 1
    return "IRAS-%d" % szamlalo[0]
c.stamp = szamlalo_stamp
c.main()


def pillanatkep():
    """MINDEN kimeneti fajl tartalma - nem csak a results.json.

    A "csak ha valtozott" logika fajlonkent kulon van megirva (hol
    szamlalobol, hol dump-osszehasonlitasbol, hol jelzobol), es pont ez a
    szethuzottsag rejtette el a results.json hibajat. Ezert a teszt nem egy
    fajlt nez, hanem az OSSZESET: barmelyik uj kimenet automatikusan
    bekerul."""
    kep = {}
    for gy, _, fajlok in os.walk("."):
        for f in fajlok:
            if not f.endswith(".json"):
                continue
            ut = os.path.join(gy, f)
            kep[ut] = open(ut, encoding="utf-8").read()
    return kep


elso = pillanatkep()
c.main()
masodik = pillanatkep()
c.stamp = eredeti_stamp
valtozott = sorted(k for k in elso if elso[k] != masodik.get(k))
uj_fajl = sorted(k for k in masodik if k not in elso)
if not valtozott and not uj_fajl:
    print("OK   a masodik, valtozatlan futas EGYETLEN kimeneti fajlt sem irt ujra (%d fajl)"
          % len(elso))
else:
    hibak.append("C3: valtozatlan futas is ujrairt fajlokat")
    print("HIBA a valtozatlan futas ujrairta: %s%s"
          % (", ".join(valtozott), (" | uj: " + ", ".join(uj_fajl)) if uj_fajl else ""))
    for k in valtozott:
        for a, b in zip(elso[k].splitlines(), masodik[k].splitlines()):
            if a != b:
                print("     %s\n     - %s\n     + %s" % (k, a[:90], b[:90]))
                break


# ---------------------------------------------------------------- C4
# Egy REGI fordulo korrekcioja nem irhatja ujra a squads.json-t: az csak az
# UTOLSO fordulo keretet tartalmazza. A kiiras felteteles agat a teljes
# elozmeny valtozasa nyitja - vagyis barmelyik fordulo -, es igy a fajl uj
# idobelyeggel, valtozatlan tartalommal kerult a repoba. (Az utolso 14
# valtozasabol 2 volt ilyen.)
print("\n--- C4: regi fordulo korrekcioja nem irja ujra a squads.json-t ---")
os.chdir(tempfile.mkdtemp())
json.dump({"updated": None, "provisional": [], "schedule": menetrend}, open("results.json", "w"))
json.dump({"updated": None, "rounds": tortenet}, open("squad_history.json", "w"))
json.dump({"updated": None, "rounds": {str(r): [
    {"id": 900 + r, "h": "XYZ", "v": "ZZZ", "start": "2026-08-01T17:30:00+02:00",
     "hp": 1, "vp": 0, "vege": True}] for r in range(1, 9)}}, open("meccsek.json", "w"))
c.api_get = mock
c.ellenorzendo = lambda regi, db=4: []
c.stamp = szamlalo_stamp
c.main()                                     # 1. futas: minden felepul
sq_elotte = open("squads.json", encoding="utf-8").read()
sh_elotte = open("squad_history.json", encoding="utf-8").read()

# most jon a REGI (2.) fordulo korrekcioja
API[2]['Csongi'] = API[2]['Csongi'] + 3.0
c.ellenorzendo = lambda regi, db=4: [2]
c.main()
c.stamp = eredeti_stamp
sq_utana = open("squads.json", encoding="utf-8").read()
sh_utana = open("squad_history.json", encoding="utf-8").read()
if sh_elotte == sh_utana:
    hibak.append("C4: a korrekcio at sem ment a keret-elozmenyre")
    print("HIBA a 2. fordulo korrekcioja nem jelent meg a squad_history.json-ban")
else:
    print("OK   a regi fordulo korrekcioja atment a keret-elozmenyre")
if sq_elotte == sq_utana:
    print("OK   a squads.json (utolso fordulo) valtozatlan maradt")
else:
    hibak.append("C4: a squads.json ujraírodott egy regi fordulo korrekciojatol")
    print("HIBA a squads.json ujraírodott, pedig az utolso fordulo kerete nem valtozott")
    print("     - %s\n     + %s" % (sq_elotte[:110], sq_utana[:110]))

sys.exit(1 if hibak else 0)
