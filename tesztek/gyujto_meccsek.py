#!/usr/bin/env python3
"""A gyujto meccsgyujtese (meccsek.json) - ot allitas.

M1: a keret-valaszokban utazo meccsek fordulonkent, id szerint osszevonva
    kerulnek a meccsek.json-ba, kezdes szerint rendezve.
M2: EREDMENY CSAK LEZART MECCSROL: a meg futo meccs pontszamai akkor sem
    kerulnek be, ha az API mar kuldi oket - a 3 orankent futo gyujto egy
    reszallast veglegeskent orokitene meg.
M3: a KESOBBI fordulobol visszaeso meccs kimarad (regi fordulo lekeresekor
    az API a klub kovetkezo meccsere esik vissza).
M9: a POTOLT (korabbi fordulos, MOST jatszott) meccs viszont BEKERUL, es a
    klub NEM kap "nincs meccse" jelolest. 2026-09-03: az MLSZ 7. fordulojaban
    ott allt az ETO-FTC "3F" jelolessel (a halasztott 3. fordulos meccs),
    plusz az ETO-HONVED "7F" - a gyujto mind a kilenc ETO-jatekost
    `nogame`-nek jelolte, mert csak a lista ELSO elemet nezte, es annak a
    fordulo-szama nem egyezett.
M10: TOBB MECCSNEL a `start` a legkozelebbi MEG NEM LEMENT meccs, es a `vege`
    csak akkor igaz, ha MINDEGYIK lement - a jatekos pontja addig valtozhat.
M4: a hianyzo fordulot a gyujto meccslistaval keri ujra (potlas), de ha mar
    minden meccs lezart eredmennyel bent van, TOBBE NEM - a lezart fordulos
    games-valasz nagy (klublogokkal jon), feleslegesen nem kerjuk.
M5: futo meccsu fordulo a kovetkezo korben is meccslistaval megy, hogy a
    vegeredmeny bekeruljon.
M6: POTOLT MECCS. Az elhalasztott meccs nincs benne a listaban (nem
    "eredmeny nelkuli"), tehat az M4 feltetele nem venne eszre a potlasat.
    Viszont a lejatszasakor a fordulo hivatalos pontja valtozik - ilyenkor a
    gyujto meccslistaval keri ujra a fordulot, es a potolt meccs bekerul.
"""
import importlib.util, json, os, sys, tempfile, urllib.parse

FORRAS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'collect.py')
os.chdir(tempfile.mkdtemp())
spec = importlib.util.spec_from_file_location('collect', FORRAS)
c = importlib.util.module_from_spec(spec); sys.modules['collect'] = c
spec.loader.exec_module(c)

NEVEK = list(c.MEMBERS)
AKT = 2
API = {r: {n: 40.0 + r for n in NEVEK} for r in (1, 2)}
parok = [(NEVEK[i], NEVEK[i + 1]) for i in range(0, len(NEVEK) - 1, 2)]
hibak = []


osszes = 0


def allit(felt, cimke):
    global osszes
    osszes += 1
    print(("OK   " if felt else "HIBA ") + cimke)
    if not felt:
        hibak.append(cimke)


def meccs(mid, h, v, status, r, hp=None, vp=None):
    g = {"id": mid, "start_at": "2026-08-%02dT17:30:00+02:00" % (10 + mid % 20),
         "status": status, "round_number": "%dF" % r,
         "home_team": {"short_name": h}, "away_team": {"short_name": v}}
    # M2 csapdaja: a futo meccsnek IS adunk pontszamot - nem szabad eltarolni
    g["home_score"], g["away_score"] = (hp if hp is not None else 1), (vp if vp is not None else 1)
    return g


# fordulo -> jatekosonkent milyen meccs jon a valaszban. Az 1. fordulo ket
# klubja ket kesz meccset ad (kulon jatekosoktol, atfedessel - a dedup itt
# merodik); a 2. (elo) forduloban egy kesz es egy meg futo meccs van, plusz
# egy visszaeso meccs egy MASIK fordulobol (M3).
MECCSEK = {
    1: [meccs(11, "AAA", "BBB", "completed", 1, 3, 1),
        meccs(12, "CCC", "DDD", "completed", 1, 0, 0)],
    2: [meccs(21, "AAA", "CCC", "completed", 2, 2, 2),
        meccs(22, "BBB", "DDD", "in_progress", 2),
        meccs(99, "EEE", "FFF", "completed", 1)],   # visszaeso: 1F a 2-ben
}
jatekos_keresek = []
csapat_keresek = []   # (fordulo, kertuk-e explicit a ket klubot)


def keret(r, games):
    adatok = []
    for i in range(15):
        crd = {"is_played": True, "market_price": 5,
               "first_played_at": "2026-08-10T17:30:00+02:00"}
        if games:
            # a meccsek szetosztva a jatekosok kozott, atfedessel (dedup!)
            crd["games"] = [MECCSEK[r][i % len(MECCSEK[r])]]
        adatok.append({"id": 1000 + i, "is_captain": False, "type": "starter",
            "position": {"monogram": "H"},
            "summary_statistics": {"weekly_points": 1, "competition_points": 1},
            "competition_player": {"id": 500 + i, "first_name": "J%d" % i,
                "last_name": "X", "is_u21": False, "team": {"short_name": "AAA"},
                "countries": [], "current_round": crd}})
    return {"data": adatok}


def mock(url, retries=3):
    par = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
    if "competitions?include=rounds" in url:
        return 200, {"data": [{"id": c.COMPETITION, "rounds": [],
                               "current_round": {"round_number": AKT}}]}
    if "rankings" in url:
        nev = par["filter[search]"][0]
        valodi = {u: n for n, u in c.MEMBERS.items()}[nev]
        return 200, {"data": [{"user_team": {
            "user": {"id": NEVEK.index(valodi) + 1, "username": nev},
            "round_statistics": [{"round_number": x, "points": API[x][valodi]} for x in (1, 2)]}}]}
    if "user-team-players-history" in url:
        r = (int(par["filter[round_id]"][0]) - 75) // 2
        teljes = urllib.parse.unquote(url)
        games = "current_round.games" in teljes
        jatekos_keresek.append((r, games))
        if games:
            csapat_keresek.append((r, "games.home_team" in teljes
                                      and "games.away_team" in teljes))
        return 200, keret(r, games)
    return 404, None


c.api_get = mock
c.ellenorzendo = lambda regi, db=4: []

menetrend = {str(r): [[h, v, API[r][h], API[r][v]] for h, v in parok] for r in (1, 2)}
json.dump({"updated": None, "provisional": [], "schedule": menetrend}, open("results.json", "w"))
json.dump({"updated": None, "rounds": {}}, open("squad_history.json", "w"))

print("--- 1. futas: ures meccsek.json ---")
c.main()
m = json.load(open("meccsek.json"))

r1 = m["rounds"].get("1") or []
allit(len(r1) == 2 and [x["id"] for x in r1] == [11, 12],
      "M1: az 1. fordulo ket meccse id szerint osszevonva, kezdes szerint rendezve")
allit(all(x.get("vege") and "hp" in x for x in r1)
      and r1[0]["h"] == "AAA" and r1[0]["hp"] == 3 and r1[0]["vp"] == 1,
      "M1: a kesz meccsnel ott a ket klub es az eredmeny")
allit(any(x["hp"] == 0 and x["vp"] == 0 and x.get("vege") for x in r1),
      "M1: a LEZART 0-0 bekerul - az a valodi eredmeny, nem helyorzo")

r2 = m["rounds"].get("2") or []
futo = next((x for x in r2 if x["id"] == 22), None)
allit(futo is not None and "hp" not in futo and "vege" not in futo,
      "M2: a futo meccsnek nincs eredmenye, hiaba kuldi az API")
allit(all(x["id"] != 99 for x in r2), "M3: a masik fordulobol visszaeso meccs kimaradt")

print("\n--- 2. futas: az 1. fordulo mar teljes, a 2.-ban futo meccs van ---")
jatekos_keresek.clear()
c.main()
elso_gamesszel = [r for r, g in jatekos_keresek if g and r == 1]
masodik_gamesszel = [r for r, g in jatekos_keresek if g and r == 2]
allit(not elso_gamesszel,
      "M4: a mar teljes 1. fordulora NEM megy tobbe meccslistas (nagy) lekeres")
allit(len(masodik_gamesszel) > 0,
      "M5: a futo meccsu 2. fordulo tovabbra is meccslistaval megy")

print("\n--- M6: potolt meccs (a hivatalos pont valtozik) ---")
# az 1. fordulo teljes es minden meccse lezart -> az M4 szerint nem kernenk
# ujra. Most viszont az MLSZ mas pontot ad ra: ez a potolt meccs jelzese.
MECCSEK[1].append(meccs(13, "EEE", "FFF", "completed", 1, 1, 0))
API[1] = {n: 55.0 for n in NEVEK}
jatekos_keresek.clear()
c.main()
m = json.load(open("meccsek.json"))
elso_gamesszel = [r for r, g in jatekos_keresek if g and r == 1]
allit(elso_gamesszel, "M6: a valtozott pontu fordulot meccslistaval keri ujra")
allit(any(x["id"] == 13 for x in m["rounds"].get("1") or []),
      "M6: a potolt meccs bekerult: " + repr([x["id"] for x in m["rounds"]["1"]]))

print("\n--- M7: a meccslistas lekeres EXPLICIT keri a ket klubot ---")
# MERVE (2026-08-30, naplo/mlsz-elo-meccs.txt): elo fordulonal a meccs-
# objektum klub NELKUL jon, hacsak a ket csapatot kulon nem kerjuk. Enelkul
# a meccsek.json "?"-et tarol, es a profilban kotojel all az ellenfel helyen.
allit(csapat_keresek and all(k for _, k in csapat_keresek),
      "M7: minden meccslistas lekeres keri a home_team-et es az away_team-et"
      + ("" if not csapat_keresek else " (%d keres)" % len(csapat_keresek)))

print("\n--- M8: a '?' klubu meccs is hianyosnak szamit ---")
# Ha egy fordulo MINDEN meccse lement, de a klubnevek "?"-ek maradtak, a regi
# feltetel teljesnek latta volna: kikerul az ujrakerendok kozul, es amint az
# MLSZ tovabblep, soha tobbe nem kernenk le - a "?" veglegesen bent ragadna.
m = json.load(open("meccsek.json"))
m["rounds"]["1"] = [{"id": 11, "h": "?", "v": "?", "start": "2026-08-11T17:30:00+02:00",
                     "hp": 3, "vp": 1, "vege": True}]
json.dump(m, open("meccsek.json", "w"))
jatekos_keresek.clear()
c.main()
allit([r for r, g in jatekos_keresek if g and r == 1],
      "M8: a '?' klubu 1. fordulot ujra lekeri meccslistaval")
m = json.load(open("meccsek.json"))
allit(all(x.get("h") != "?" and x.get("v") != "?" for x in m["rounds"].get("1") or []),
      "M8: az ujrakeres utan valodi klubnev all a '?' helyen: "
      + repr([(x.get("h"), x.get("v")) for x in m["rounds"].get("1") or []]))

print()
print("--- M9-M10: potolt meccs (egy klubnak KET meccse van a forduloban) ---")
# A 2026-09-03-i meres alakja: a lista ELSO eleme a potolt, korabbi fordulos
# meccs, a masodik a fordulo sajat meccse.
POTOLT = {"id": 431, "start_at": "2026-09-03T19:30:00+02:00",
          "status": "scheduled", "round_number": "3F",
          "home_team": {"short_name": "ETO"}, "away_team": {"short_name": "FTC"}}
SAJAT = {"id": 9, "start_at": "2026-09-06T20:00:00+02:00",
         "status": "scheduled", "round_number": "7F",
         "home_team": {"short_name": "ETO"}, "away_team": {"short_name": "HONVÉD"}}
mez = c.jatek_mezok({"games": [POTOLT, SAJAT]}, 7)
allit(not mez.get("nogame"),
      "M9: a klub NEM kap 'nincs meccse' jelolest - kapott: %s" % mez)
allit(mez.get("start") == POTOLT["start_at"],
      "M10: a `start` a legkozelebbi meg le nem ment meccs (a potolt) - kapott: %s"
      % mez.get("start"))
mez2 = c.jatek_mezok({"games": [dict(POTOLT, status="completed"), SAJAT]}, 7)
allit(mez2.get("start") == SAJAT["start_at"] and not mez2.get("vege"),
      "M10: a potolt utan a KOVETKEZO meccsre mutat, es meg nincs 'vege' - kapott: %s" % mez2)
mez3 = c.jatek_mezok({"games": [dict(POTOLT, status="completed"),
                                dict(SAJAT, status="completed")]}, 7)
allit(mez3.get("vege") is True,
      "M10: csak MINDKETTO lementevel lesz 'vege' - kapott: %s" % mez3)
# a visszaeses tovabbra is kiesik: az KESOBBI fordulohoz tartozik
kesoi = {"id": 77, "start_at": "2026-09-20T18:00:00+02:00",
         "status": "scheduled", "round_number": "9F"}
allit(c.jatek_mezok({"games": [kesoi]}, 3).get("nogame") is True,
      "M3: a KESOBBI fordulos (visszaeso) meccs tovabbra is 'nincs meccse'")
tarolo = {}
c.meccsek_gyujtes({"data": [{"competition_player":
                             {"current_round": {"games": [POTOLT, SAJAT]}}}]}, 7, tarolo)
allit(sorted(tarolo) == [9, 431],
      "M9: a potolt meccs is bekerul a meccsek.json-ba - kapott: %s" % sorted(tarolo))

if hibak:
    print("\n%d allitas bukott." % len(hibak)); sys.exit(1)
print("\nMind a %d allitas rendben." % osszes)
