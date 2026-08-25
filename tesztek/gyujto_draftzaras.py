#!/usr/bin/env python3
"""A draft-gyujto fordulo-veglegesitese - negy allitas.

MIERT KELL: az FPL a fordulo vegen AUTOMATIKUS CSEREKET hajt vegre (a nem
jatszo kezdo helyere beall az elso befero padrol), es ilyenkor ATIRJA a pick
"position" mezojet. Merve (2026-08-25): ez a "lockdown"-kor tortenik, a
jelzese a game vegpont "current_event_finished" mezoje - es EKKOR A
current_event MEG A REGI FORDULO. Ha a gyujto a zaras utan nem keri le
megegyszer a fordulot, a keret veglegesen a csere elotti allapotban fagy be.

D1: amig a fordulo nincs lezarva (current_event_finished=false), minden
    futas ujra lekeri - akkor is, ha a keret mar teljes.
D2: a zaras utani futas lekeri megegyszer, es a CSERE UTANI allapot kerul be
    (a "b" jelzo a friss position-bol szamolodik).
D3: a lezart fordulo bekerul a "veglegesek" listaba - de amig O AZ AKTUALIS,
    tovabbra is minden korben lekerjuk (az utolagos FPL-korrekciok igy
    jonnek at); csak amikor a current_event tovabblep, akkor hagyjuk el.
D4: ha a lekeres elhasal, a fordulo NEM jelolodik veglegesnek - kulonben a csere
    elotti allapotot rogzitenenk veglegesnek.
D5: ...es akkor sem, ha a TAROLT adat mar teljes egy korabbi futasbol. A
    gyujto osszefesuli a regit az ujjal, tehat a tarolt allapotbol nem
    latszik, hogy MOST bejott-e minden csapat. Ez a valodi eset: a keret mar
    megvan a zaras elottrol, a zaras utani lekeres viszont elhasal - a csere
    igy pont attol a csapattol hianyozna.
"""
import importlib.util, json, os, sys, tempfile

FORRAS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'collect_draft.py')
os.chdir(tempfile.mkdtemp())
spec = importlib.util.spec_from_file_location('collect_draft', FORRAS)
c = importlib.util.module_from_spec(spec); sys.modules['collect_draft'] = c
spec.loader.exec_module(c)

hibak = []
LIGAK = [101, 102]
ENTRY = {201: 101, 202: 102}
# a kezdo 11 + 4 pad; a 15-os elem (id 15) a 0 perces kezdo, a 12-es a pad elso
KEZDOK = list(range(1, 12))
PAD = [12, 13, 14, 15]

allapot = {"zarva": False, "akt": 1}
keresek = []          # (gw, entry) parok, hogy szamolhassuk a lekereseket


def allit(felt, cimke):
    print(("OK   " if felt else "HIBA ") + cimke)
    if not felt:
        hibak.append(cimke)


def picks(csere):
    """csere=True: az FPL mar beallitotta a 12-est a 11-es helyere."""
    kezdo = KEZDOK[:] if not csere else KEZDOK[:10] + [12]
    pad = PAD[:] if not csere else [11, 13, 14, 15]
    return ([{"element": e, "position": i + 1} for i, e in enumerate(kezdo)]
            + [{"element": e, "position": 12 + i} for i, e in enumerate(pad)])


def mock(path, retries=3):
    if path == "game":
        return 200, {"current_event": allapot["akt"],
                     "current_event_finished": allapot["zarva"]}
    if path.startswith("league/") and "details" in path:
        return 200, {"league": {"id": 1, "name": "T"},
                     "league_entries": [{"id": l, "entry_id": e, "player_first_name": "A",
                                         "player_last_name": "B", "entry_name": "C"}
                                        for e, l in ENTRY.items()],
                     "matches": [], "standings": [{"league_entry": l} for l in LIGAK]}
    if "element-status" in path:
        return 200, {"element_status": []}
    if path.startswith("bootstrap-static"):
        return 200, {"elements": [], "teams": [], "element_types": []}
    if "/live" in path:
        gw = int(path.split("/")[1])
        return 200, {"elements": {str(e): {"stats": {"total_points": 1}} for e in range(1, 16)}}
    if path.startswith("entry/"):
        reszek = path.split("/")
        entry, gw = int(reszek[1]), int(reszek[3])
        keresek.append((gw, entry))
        if allapot.get("bukjon") == entry:
            return 500, None
        return 200, {"picks": picks(allapot["zarva"])}
    return 404, None


c.fetch = mock

print("--- 1. futas: a fordulo MEG TART ---")
c.main()
h = json.load(open("draft_history.json"))
allit(len(h["rounds"].get("1") or {}) == 2, "az 1. fordulo keretei bekerultek")
allit(not h.get("veglegesek"), "D1: a meg tarto fordulo NEM kesz: " + repr(h.get("veglegesek")))
padE = {x["e"] for x in h["rounds"]["1"]["101"] if x["b"]}
allit(padE == set(PAD), "a pad a csere ELOTTI allapot: " + repr(sorted(padE)))

print("\n--- 2. futas: meg mindig tart, a keret mar teljes ---")
keresek.clear()
c.main()
allit(len(keresek) == 2,
      "D1: a le nem zart fordulot teljes keret mellett is ujra lekeri (%d keres)" % len(keresek))

print("\n--- 3. futas: LOCKDOWN, az FPL vegrehajtotta a cseret ---")
allapot["zarva"] = True
keresek.clear()
c.main()
h = json.load(open("draft_history.json"))
padE = {x["e"] for x in h["rounds"]["1"]["101"] if x["b"]}
allit(len(keresek) == 2, "a zaras utan meg egyszer lekeri (%d keres)" % len(keresek))
allit(padE == {11, 13, 14, 15},
      "D2: a CSERE UTANI allapot kerult be - a 0 perces kezdo a padra: " + repr(sorted(padE)))
allit(h.get("veglegesek") == [1], "D3: a fordulo bekerult a veglegesek listaba: " + repr(h.get("veglegesek")))

print("\n--- 4. futas: lezart, DE MEG AKTUALIS fordulo ---")
keresek.clear()
c.main()
allit(len(keresek) == 2,
      "D3: amig a fordulo az aktualis, a zaras utan is lekerjuk - igy jon at egy "
      "utolagos FPL-korrekcio (%d keres)" % len(keresek))

print("\n--- 5. futas: a current_event tovabblepett ---")
allapot["akt"] = 2
allapot["zarva"] = False        # a 2. fordulo mar tart
keresek.clear()
c.main()
elso = [x for x in keresek if x[0] == 1]
allit(not elso, "D3: a mar NEM aktualis, lezart fordulot nem kerdezzuk tobbe (%d keres)" % len(elso))
allit([x for x in keresek if x[0] == 2], "a 2. fordulot viszont igen")

print("\n--- 6. eset: zaraskor elhasal az egyik lekeres (ures elozmeny) ---")
os.chdir(tempfile.mkdtemp())
allapot["akt"] = 1
allapot["zarva"] = True
allapot["bukjon"] = 202
c.main()
h = json.load(open("draft_history.json"))
allit(not h.get("veglegesek"),
      "D4: hianyos lekeres utan NEM jelolodik veglegesnek: " + repr(h.get("veglegesek")))

print("\n--- 7. eset: a TAROLT adat mar teljes, de a zarasi lekeres elhasal ---")
os.chdir(tempfile.mkdtemp())
allapot["akt"] = 1
allapot["zarva"] = False
allapot["bukjon"] = None
c.main()                                   # elso kor: teljes keret, csere elott
h = json.load(open("draft_history.json"))
allit(len(h["rounds"]["1"]) == 2 and not h.get("veglegesek"),
      "eloallt a teljes, csere ELOTTI allapot")
allapot["zarva"] = True                    # lockdown...
allapot["bukjon"] = 202                    # ...de az egyik lekeres elhasal
c.main()
h = json.load(open("draft_history.json"))
padE = {x["e"] for x in h["rounds"]["1"]["102"] if x["b"]}
allit(padE == set(PAD),
      "a 102-es csapatnal a csere NEM jott be (a lekeres elhasalt): " + repr(sorted(padE)))
allit(not h.get("veglegesek"),
      "D5: teljes tarolt adat + hianyos mostani lekeres -> NEM veglegesitunk: "
      + repr(h.get("veglegesek")))

if hibak:
    print("\n%d allitas bukott." % len(hibak)); sys.exit(1)
print("\nMind a tizenharom allitas rendben.")
