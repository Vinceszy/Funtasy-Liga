#!/usr/bin/env python3
"""A lezart fordulok teteles bontasanak mentese (collect.py bontasok_gyujtes).

MIERT LETEZIK: a bontast eddig kizarolag a bongeszo kerte le, kattintasra,
elo MLSZ-hivassal - ha az API vagy a kozvetito nem valaszolt, a lenyilo
hibat irt. A lezart fordulo bontasa viszont mar sosem valtozik, tehat
egyszer le lehet kerni es el lehet tenni. Ez a resz fordulonkent EGYSZER
sul el, tehat a teszt az egyetlen hely, ahol lathato, hogy mukodik-e.
"""
import importlib.util, json, os, sys, tempfile

FORRAS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'collect.py')
os.chdir(tempfile.mkdtemp())
spec = importlib.util.spec_from_file_location('collect', FORRAS)
c = importlib.util.module_from_spec(spec); sys.modules['collect'] = c
spec.loader.exec_module(c)
hibak = []


def allit(felt, cimke):
    print(("OK   " if felt else "HIBA ") + cimke)
    if not felt:
        hibak.append(cimke)


TORZS = {str(1000 + i): {"n": "J%d" % i} for i in range(12)}
BUKO = set()          # ezekre a cp-kre hibat ad az API
HIVAS = []


def mock(url, retries=3):
    HIVAS.append(url)
    if "game-player-stats" not in url:
        return 404, None
    cp = url.split("competition_player_id%5D=")[1].split("&")[0]
    if cp in BUKO:
        return 500, None
    return 200, {"data": [
        {"value": 90, "points": 0, "competition_stat_config": {"name": "Játszott perc"}},
        {"value": 1, "points": 5, "competition_stat_config": {"name": "Gól"}}]}


c.api_get = mock

# --- 1. lezart fordulora keszul fajl, nem lezartra nem ---
c.bontasok_gyujtes([1], set(), TORZS)
allit(os.path.exists("bontasok/1.json"), "a lezart fordulohoz keszul fajl")
allit(not os.path.exists("bontasok/2.json"), "a meg tarto fordulohoz NEM keszul")

# --- melyik fordulo szamit lezartnak? A TAROLT allapotbol dol el ---
# (nem a futas `lezart` szotarabol - az csak az ebben a futasban lekert
# fordulokat ismeri, tehat a bevezetesnel csak az utolsohoz keszult volna)
MENETREND = {"1": [["A", "B", 50.0, 40.0]], "2": [["A", "B", 60.0, 55.0]],
             "3": [["A", "B", None, None]]}
allit(c.zart_fordulok(MENETREND, []) == [1, 2],
      "lezart: aminek minden meccse eredmenyes (%s)" % c.zart_fordulok(MENETREND, []))
allit(c.zart_fordulok(MENETREND, [2]) == [1],
      "az ideiglenes fordulo NEM lezart (%s)" % c.zart_fordulok(MENETREND, [2]))

j = json.load(open("bontasok/1.json", encoding="utf-8"))
allit(j.get("round") == 1 and len(j.get("bontasok") or {}) == len(TORZS),
      "mind a %d jatekos bontasa bekerult" % len(TORZS))
allit(j["bontasok"]["1000"] == [{"n": "Játszott perc", "v": 90, "p": 0},
                                {"n": "Gól", "v": 1, "p": 5}],
      "a sorok alakja a vart (n/v/p): %s" % j["bontasok"]["1000"][:1])

# --- a NULLAS sorokat nem taroljuk, a perc-sort viszont igen ---
# Az MLSZ mind a 22 statisztika-sort visszaadja, a nullasokat is: 385
# jatekossal az 141 KB fordulonkent. Az oldal csak a pontot ero sorokat
# mutatja + a "Jatszott perc"-et (abbol dol el az uzenet is).
NYERS = [{"n": "Gólok", "v": 1, "p": 5}, {"n": "Sárga lap", "v": 0, "p": 0},
         {"n": "Játszott perc", "v": 90, "p": 0},
         {"n": "Passzpontosság", "v": 0.59, "p": 0}]
allit(c.bontas_szures(NYERS) == [{"n": "Gólok", "v": 1, "p": 5},
                                 {"n": "Játszott perc", "v": 90, "p": 0}],
      "a 0 pontos sorok kimaradnak, a Játszott perc marad (%s)"
      % [x["n"] for x in c.bontas_szures(NYERS)])
allit(c.bontas_szures([]) == [], "ures bontasbol ures marad")
allit("updated" not in j,
      "nincs benne idobelyeg (kulonben minden futasnal ujrairodna)")

# --- 2. masodszor NEM ker le ujra ---
HIVAS.clear()
c.bontasok_gyujtes([1], set(), TORZS)
allit(not HIVAS, "meglevo fajlnal egyetlen lekeres sincs (%d)" % len(HIVAS))

# --- 3. de ha a fordulo eredmenye VALTOZOTT, ujra lekeri ---
HIVAS.clear()
c.bontasok_gyujtes([1], {1}, TORZS)
allit(len(HIVAS) == len(TORZS),
      "MLSZ-korrekcio utan ujra lekeri az egesz fordulot (%d keres)" % len(HIVAS))

# --- 4. hianyos futas NEM ir ki felig kesz fajlt ---
os.chdir(tempfile.mkdtemp())
BUKO.update(list(TORZS)[:5])          # 5/12 elhasal - tobb, mint 10%
c.bontasok_gyujtes([1], set(), TORZS)
allit(not os.path.exists("bontasok/1.json"),
      "sok hibas keresnel a fajl NEM keszul el (a kovetkezo futas ujraprobal)")

# --- 5. keves hiba viszont belefer ---
BUKO.clear(); BUKO.add(list(TORZS)[0])   # 1/12 - a hatarertek alatt
c.bontasok_gyujtes([1], set(), TORZS)
allit(os.path.exists("bontasok/1.json"), "egy-ket hibas keres nem akadalyozza a kiirast")
j = json.load(open("bontasok/1.json", encoding="utf-8"))
allit(len(j["bontasok"]) == len(TORZS) - 1,
      "a sikertelen jatekos kimarad, a tobbi bekerul (%d/%d)"
      % (len(j["bontasok"]), len(TORZS)))

# --- 6. ures bontas is bekerul (nem hianyzo!) ---
os.chdir(tempfile.mkdtemp())
BUKO.clear()
c.api_get = lambda url, retries=3: (200, {"data": []}) if "game-player-stats" in url else (404, None)
c.bontasok_gyujtes([1], set(), TORZS)
j = json.load(open("bontasok/1.json", encoding="utf-8"))
allit(j["bontasok"].get("1000") == [],
      "a pont nelkuli jatekos URES listaval szerepel - ez mas, mint a hianyzas")

if hibak:
    print("\n%d allitas bukott." % len(hibak))
    sys.exit(1)
print("\nMind a %d allitas rendben." % 14)
