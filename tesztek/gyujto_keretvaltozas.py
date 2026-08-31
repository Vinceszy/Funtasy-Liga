#!/usr/bin/env python3
"""A "Valtoztatasok" ful adata (collect.py keretvaltozas).

A ful egesz ertelme, hogy a tabellaban allo GUARD-szam LEVEZETHETO legyen.
Ezert itt nem az a fo allitas, hogy "van lista", hanem hogy a tetelek
osszege PONTOSAN a Guardiola mutato - kerekitesi maradek nelkul.

K1: eladott jatekos a MULT HETI szerepevel szamit (kapitany duplan).
K2: megvett jatekos a MOSTANI szerepevel.
K3: aki bent maradt, de valtozott a szerepe, kulon tetel - a ket ertek
    kulonbsegevel.
K4: a magyarszabaly kulonbsege kulon sor (nem egy jatekoson mulik).
K5: A TETELEK OSSZEGE = a guardiola() altal adott `guard`. Ez a leg-
    fontosabb allitas: ha elcsuszik, a ful szama mast mond, mint a tabella.
K6: valtozatlan keretnel nincs tetel, es a mutato 0.
K7: nincs mihez hasonlitani / nincs bontas -> nincs adat.
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
    return {"id": pid, "name": "J%d" % pid, "team": "K", "pos": "KP",
            "hun": hun, "u21": u21, "cap": cap, "sub": sub, "week": 0}


def keret(ids, **kw):
    return [j(pid, sub=(i >= 11), **kw) for i, pid in enumerate(ids)]


ALAP = list(range(1, 16))
NYERS = {str(x): 5 for x in range(1, 30)}
c.nyers_pontok = lambda r: NYERS


def egy(regi, most, r=2):
    return (c.keretvaltozas({"1": {"A": regi}, "2": {"A": most}}, r) or {}).get("A")


print("--- K1-K2: eladott a mult heti, megvett a mostani szerepevel ---")
regi = keret(ALAP)
regi[0]["cap"] = True                      # az 1-es a mult heti kapitany
most = keret([21] + ALAP[1:])
most[0]["cap"] = True                      # a 21-es a mostani kapitany
v = egy(regi, most)
allit(v and len(v["ki"]) == 1 and v["ki"][0]["id"] == 1 and v["ki"][0]["ert"] == 10,
      "K1: az eladott kapitany 5 nyers pontja duplan (10) szamit - kapott: %s"
      % (v and v["ki"]))
allit(v and len(v["be"]) == 1 and v["be"][0]["id"] == 21 and v["be"][0]["ert"] == 10,
      "K2: a megvett kapitany szinten duplan - kapott: %s" % (v and v["be"]))

print("\n--- K3: szerepvaltas kulon tetel ---")
regi = keret(ALAP)
most = keret(ALAP)
most[0]["cap"] = True                      # ugyanaz a keret, mas szerep
v = egy(regi, most)
allit(v and not v["ki"] and not v["be"] and len(v["szerep"]) == 1,
      "K3: nincs csere, egy szerepvaltas - kapott: %s" % (v and v["szerep"]))
allit(v and v["szerep"][0]["szE"] == "kezdo" and v["szerep"][0]["szU"] == "C"
      and v["szerep"][0]["ertE"] == 5 and v["szerep"][0]["ertU"] == 10,
      "K3: kezdo -> kapitany, 5 -> 10 - kapott: %s" % (v and v["szerep"]))

print("\n--- K4: a magyarszabaly kulonbsege kulon sor ---")
# 5 magyar kezdo, kozte 1 U21 -> +10. A mostani keretbol egy magyar kiesik.
regi = keret(ALAP)
for i in range(5):
    regi[i]["hun"] = True
regi[0]["u21"] = True
most = [dict(p) for p in regi]
most[4]["hun"] = False                     # mar csak 4 magyar kezdo
v = egy(regi, most)
allit(v and v["bonusz"] == -10,
      "K4: az elveszett magyarszabaly -10 kulon tetelkent - kapott: %s"
      % (v and v["bonusz"]))

print("\n--- K5: A TETELEK OSSZEGE = a Guardiola mutato ---")


def ellenoriz(regi, most, cimke):
    hist = {"1": {"A": regi}, "2": {"A": most}}
    v = (c.keretvaltozas(hist, 2) or {}).get("A")
    g = (c.guardiola(hist, 2) or {}).get("A")
    ossz = round(sum(x["ert"] for x in v["be"]) - sum(x["ert"] for x in v["ki"])
                 + sum(x["ertU"] - x["ertE"] for x in v["szerep"]) + v["bonusz"], 2)
    allit(v["stimmel"] and ossz == g["guard"] == v["guard"],
          "K5: %s - tetelek %s, guardiola %s, ful %s"
          % (cimke, ossz, g["guard"], v["guard"]))


# vegyes eset: csere + szerepvaltas + kapitanyvaltas + felezes egyszerre
NYERS.update({"1": 3.25, "2": 0.75, "3": 14.25, "21": 5.25, "22": 0.25})
regi = keret(ALAP)
regi[2]["cap"] = True
most = keret([21, 22] + ALAP[2:])
most[0]["cap"] = True
most[3]["sub"] = True                      # kezdobol pados
ellenoriz(regi, most, "csere + szerepvaltas + kapitanyvaltas")

# pados felezes-kerekites (0,75 -> 0,38): itt csuszna el legkonnyebben
regi2 = keret(ALAP)
regi2[1]["sub"] = True
most2 = keret(ALAP)
most2[1]["sub"] = False
ellenoriz(regi2, most2, "pad -> kezdo, felezes-kerekitessel")

# magyarszabaly is mozdul
regi3 = keret(ALAP)
for i in range(5):
    regi3[i]["hun"] = True
regi3[0]["u21"] = True
most3 = keret([21] + ALAP[1:])
for i in range(1, 5):
    most3[i]["hun"] = True
ellenoriz(regi3, most3, "magyarszabaly is elveszik")

print("\n--- K6-K7: hatarhelyzetek ---")
NYERS.clear()
NYERS.update({str(x): 5 for x in range(1, 30)})
v = egy(keret(ALAP), keret(ALAP))
allit(v and not v["ki"] and not v["be"] and not v["szerep"] and v["guard"] == 0,
      "K6: valtozatlan keretnel nincs tetel es a mutato 0 - kapott: %s" % (v,))
allit(c.keretvaltozas({"1": {"A": keret(ALAP)}}, 1) is None,
      "K7: az elso fordulora nincs adat")
c.nyers_pontok = lambda r: None
allit(c.keretvaltozas({"1": {"A": keret(ALAP)}, "2": {"A": keret(ALAP)}}, 2) is None,
      "K7: bontas nelkul (nem lezart fordulo) nincs adat")

if hibak:
    print("\n%d allitas bukott." % len(hibak))
    sys.exit(1)
print("\nMind a %d allitas rendben." % osszes)
