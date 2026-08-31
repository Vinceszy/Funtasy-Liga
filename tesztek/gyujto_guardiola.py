#!/usr/bin/env python3
"""A "Guardiola mutato": mennyivel lett tobb/kevesebb pont a keretvaltoztatas
utan. guard = a MOSTANI keret pontja - a MULT HETI kerete UGYANEBBEN a
forduloban. Negativ: a valtoztatas pontba kerult.

G1: VALTOZATLAN keretnel PONTOSAN 0. (Ez a legkonnyebben elromlo allitas: ha
    a ket oldal maskepp szamol - az egyik a tarolt `week`-bol, a masik a
    bontasbol -, a pados jatekos felezese 0,01-et csuszik, es a mutato
    "+0,01"-et irna, holott a szakvezeto hozza sem nyult a kerethez.)
G2: jobb csere -> pozitiv, rosszabb csere -> negativ, a kulonbseg pontos.
G3: a MULT HETI SZEREPEK szamitanak, nem a mostaniak (kapitany, pad).
G4: a magyarszabaly az alternativara is jar - ha a kicserelt magyar miatt
    esik ki, az a mutatoban latszik.
G5: nincs mihez hasonlitani (elso fordulo) -> nincs ertek.
G6: nincs meg a fordulo bontasa (nem lezart) -> nincs ertek.
G7: aki mar nincs a bontasban (kikerult a torzsbol), 0 pontot ad.
G8: a bontas-gyujtes a VALAHA BIRTOKOLT jatekosokra is kiterjed (`extra`) -
    enelkul a bajnoksagbol kikerult jatekos 0-val szamitott, es a mutato
    annak a javara csuszott, aki eppen megvalt tole.
G9: a MEGLEVO bontas-fajlt csak KIEGESZITJUK (a hianyzo nehany jatekossal),
    nem kerjuk le ujra mind a 385-ot.
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import collect as c

hibak, osszes = [], 0


def allit(felt, cimke):
    global osszes
    osszes += 1
    print(("OK   " if felt else "HIBA ") + cimke)
    if not felt:
        hibak.append(cimke)


def j(pid, hun=False, u21=False, cap=False, sub=False):
    return {"id": pid, "name": "J%d" % pid, "hun": hun, "u21": u21,
            "cap": cap, "sub": sub, "pos": "KP", "week": 0}


def keret(ids, **kw):
    """15 fos keret: az elso 11 kezdo, az utolso 4 pados."""
    sq = []
    for i, pid in enumerate(ids):
        sq.append(j(pid, sub=(i >= 11), **kw))
    return sq


ALAP = list(range(1, 16))
# minden jatekos 5 pontot szerez ebben a forduloban
NYERS = {str(x): 5 for x in range(1, 40)}
c.nyers_pontok = lambda r: NYERS

print("--- G1: valtozatlan keret -> pontosan 0 ---")
h = {"1": {"A": keret(ALAP)}, "2": {"A": keret(ALAP)}}
g = c.guardiola(h, 2)
allit(g and g["A"]["guard"] == 0,
      "G1: valtozatlan keretnel a mutato pontosan 0 - kapott: %s" % (g and g["A"]))

print("\n--- G1b: PADOS jatekosnal is pontosan 0 (a felezes kerekitese) ---")
# 0,75 nyers pont -> a pad felezve 0,38 (az API kerekit) - a ket oldalnak
# ugyanabbol kell szamolnia, kulonben itt 0,01 jonne ki
NYERS_TORT = {str(x): 0.75 for x in range(1, 40)}
c.nyers_pontok = lambda r: NYERS_TORT
g = c.guardiola(h, 2)
allit(g and g["A"]["guard"] == 0,
      "G1b: tort pontnal is pontosan 0 - kapott: %s" % (g and g["A"]))
c.nyers_pontok = lambda r: NYERS

print("\n--- G2: csere -> a kulonbseg pontos ---")
# a 12-es (pados, 5 pont) helyett a 20-as jon, aki 9-et szerez
NYERS2 = dict(NYERS); NYERS2["20"] = 9
c.nyers_pontok = lambda r: NYERS2
uj = keret(ALAP[:1] + [20] + ALAP[2:])          # a 2-es KEZDO helyere a 20-as
h2 = {"1": {"A": keret(ALAP)}, "2": {"A": uj}}
g = c.guardiola(h2, 2)
allit(g and g["A"]["guard"] == 4,
      "G2: a 9 pontos jott a 5 pontos helyere -> +4 - kapott: %s" % (g and g["A"]))
h3 = {"1": {"A": uj}, "2": {"A": keret(ALAP)}}
g = c.guardiola(h3, 2)
allit(g and g["A"]["guard"] == -4,
      "G2: forditva -4 - kapott: %s" % (g and g["A"]))
c.nyers_pontok = lambda r: NYERS

print("\n--- G3: a MULT HETI szerepek szamitanak ---")
# mult hete a 3-as volt a kapitany, most a 4-es. Az alternativaban a 3-asnak
# kell duplaznia. Adjunk a 3-asnak 10-et, a tobbinek 5-ot.
NYERS3 = dict(NYERS); NYERS3["3"] = 10
c.nyers_pontok = lambda r: NYERS3
regi = keret(ALAP); regi[2]["cap"] = True        # 3-as a kapitany
most = keret(ALAP); most[3]["cap"] = True        # 4-es a kapitany
g = c.guardiola({"1": {"A": regi}, "2": {"A": most}}, 2)
# teny: 10 + 5x10 + 5(dupla 4-es) + pad... a KULONBSEG a lenyeg:
# alternativa = +10 (a 3-as duplaz), teny = +5 (a 4-es duplaz) -> -5
allit(g and g["A"]["guard"] == -5,
      "G3: a mult heti kapitany duplaz az alternativaban -> -5 - kapott: %s"
      % (g and g["A"]))
c.nyers_pontok = lambda r: NYERS

print("\n--- G4: a magyarszabaly az alternativara is jar ---")
# mult hete 5 magyar kezdo (koztuk egy U21) -> +10. Most az egyiket lecsereltuk
# kulfoldire, tehat a teny NEM kap +10-et, az alternativa igen.
regi = keret(ALAP)
for i in range(5):
    regi[i]["hun"] = True
regi[0]["u21"] = True
most = keret(ALAP)
for i in range(1, 5):                            # csak 4 magyar marad
    most[i]["hun"] = True
most[1]["u21"] = True
g = c.guardiola({"1": {"A": regi}, "2": {"A": most}}, 2)
allit(g and g["A"]["guard"] == -10,
      "G4: az elvesztett magyarszabaly -10-et mutat - kapott: %s" % (g and g["A"]))

print("\n--- G5/G6: amikor nincs ertek ---")
allit(c.guardiola({"1": {"A": keret(ALAP)}}, 1) is None,
      "G5: az elso fordulora nincs mutato")
c.nyers_pontok = lambda r: None
allit(c.guardiola(h, 2) is None,
      "G6: bontas nelkul (nem lezart fordulo) nincs mutato")
c.nyers_pontok = lambda r: NYERS

print("\n--- G7: aki mar nincs a bontasban, 0 pontot ad ---")
SZUK = {str(x): 5 for x in range(1, 15)}         # a 15-os hianyzik
c.nyers_pontok = lambda r: SZUK
regi = keret(ALAP)                                # 15-os: PADOS
most = keret(ALAP[:14] + [21])                    # helyette a 21-es, szinten pados
SZUK["21"] = 5
g = c.guardiola({"1": {"A": regi}, "2": {"A": most}}, 2)
# a 15-os 0-t ad (pad: 0), a 21-es 5-ot (pad: 2,5) -> +2,5
allit(g and g["A"]["guard"] == 2.5,
      "G7: a bontasbol hianyzo jatekos 0 pontot ad -> +2,5 - kapott: %s"
      % (g and g["A"]))

print("\n--- G8-G9: a bontas-gyujtes kiterjed a valaha birtokoltakra ---")
import json as _json, shutil, tempfile

_munka = tempfile.mkdtemp()
_regi_cwd = os.getcwd()
_regi_api = c.api_get
_kert = []


def _api(url):
    _kert.append(url.split("competition_player_id%5D=")[1].split("&")[0])
    return 200, {"data": [{"competition_stat_config": {"name": "Gol"},
                           "value": 1, "points": 5}]}


try:
    os.chdir(_munka)
    c.api_get = _api
    TORZS = {"1": {}, "2": {}}
    # a 99-es mar nincs a torzsben, de valaha birtokolta valaki
    c.bontasok_gyujtes([2], set(), TORZS, {"99"})
    with open("bontasok/2.json", encoding="utf-8") as f:
        b = _json.load(f)["bontasok"]
    allit(set(b) == {"1", "2", "99"},
          "G8: a kikerult, de birtokolt jatekos is bekerult a bontasba - kapott: %s"
          % sorted(b))

    # G9: mar letezo fajl, amibol csak a 99-es hianyzik
    c.kompakt_iras("bontasok/2.json", {"round": 2, "bontasok": {"1": [], "2": []}})
    del _kert[:]
    c.bontasok_gyujtes([2], set(), TORZS, {"99"})
    with open("bontasok/2.json", encoding="utf-8") as f:
        b = _json.load(f)["bontasok"]
    allit(_kert == ["99"],
          "G9: csak a hianyzo jatekost kertuk le, a tobbit nem - kapott: %s" % _kert)
    allit(set(b) == {"1", "2", "99"},
          "G9: a meglevo sorok megmaradtak a potlas utan - kapott: %s" % sorted(b))

    # ha mar semmi nem hianyzik, egyetlen keres sem megy ki
    del _kert[:]
    c.bontasok_gyujtes([2], set(), TORZS, {"99"})
    allit(_kert == [], "G9: teljes fajlnal nincs keres - kapott: %s" % _kert)
finally:
    c.api_get = _regi_api
    os.chdir(_regi_cwd)
    shutil.rmtree(_munka, ignore_errors=True)

if hibak:
    print("\n%d allitas bukott." % len(hibak))
    sys.exit(1)
print("\nMind a %d allitas rendben." % osszes)
