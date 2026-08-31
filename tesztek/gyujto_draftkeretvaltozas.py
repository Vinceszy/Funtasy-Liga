#!/usr/bin/env python3
"""A "Valtoztatasok" ful adata a PL-en (collect_draft.py draft_keretvaltozas).

A ful azt vezeti le, hogy mibol jott ki a Guardiola mutato - es a Draftban
ehhez KETTE KELL VALASZTANI, mit csinalt az EMBER, es mit javitott rajta a
GEP. Az FPL a fordulo vegen automatikus cseret hajt vegre; ha egyben
mutatnank, ugy tunne, hogy a szakvezeto variált jol, holott a gep tette
helyre a keretet (vagy forditva).

P1: elengedett jatekos a MULT HETI megnevezett szerepevel szamit (pad = 0).
P2: megszerzett jatekos a MOSTANI megnevezett szerepevel.
P3: kezdo <-> pad valtas kulon tetel.
P4: A GEP KULON: az automatikus csere hozadeka nem a jatekos-tetelek kozott
    all, hanem sajat sorban (gepE -> gepU).
P5: A TETELEK OSSZEGE (ember + gep) = a draft_guardiola altal adott `guard`.
P6: valtozatlan keretnel nincs tetel es a mutato 0.
P7: nincs mihez hasonlitani / nincs pont-adat -> nincs adat.
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import collect_draft as c

hibak, osszes = [], 0


def allit(felt, cimke):
    global osszes
    osszes += 1
    print(("OK   " if felt else "HIBA ") + cimke)
    if not felt:
        hibak.append(cimke)


POSZT = {}
KEZDO = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
PAD = [12, 13, 14, 15]
for e in KEZDO + PAD + [20, 21]:
    POSZT[str(e)] = ("GKP" if e in (1, 12) else "DEF" if e in (2, 3, 4, 5, 13, 20)
                     else "MID" if e in (6, 7, 8, 9, 14, 21) else "FWD")


def keret(ids, padok):
    return ([{"e": e, "b": False, "pts": 0} for e in ids]
            + [{"e": e, "b": True, "pts": 0} for e in padok])


def pontok(alap=5, perc=90, **kiv):
    d = {str(e): [alap, perc] for e in POSZT}
    for k, v in kiv.items():
        d[k.lstrip("j")] = v
    return d


def egy(regi, most, p, gw=2):
    return (c.draft_keretvaltozas({"1": {"L": regi}, "2": {"L": most}}, gw, p, POSZT)
            or {}).get("L")


print("--- P1-P3: az EMBER tetelei a megnevezett szerep szerint ---")
p = pontok()
p["20"] = [9, 90]
v = egy(keret(KEZDO, PAD), keret([20] + KEZDO[1:], PAD), p)
allit(v and len(v["ki"]) == 1 and v["ki"][0]["e"] == 1 and v["ki"][0]["ert"] == 5
      and v["ki"][0]["sz"] == "kezdo",
      "P1: az elengedett kezdo 5 pontja szamit - kapott: %s" % (v and v["ki"]))
allit(v and len(v["be"]) == 1 and v["be"][0]["e"] == 20 and v["be"][0]["ert"] == 9,
      "P2: a megszerzett kezdo 9 pontja szamit - kapott: %s" % (v and v["be"]))

# a 11-es (FWD) padra kerul, helyette a 15-os (FWD) all be kezdokent
v = egy(keret(KEZDO, PAD), keret(KEZDO[:10] + [15], PAD[:3] + [11]), pontok())
allit(v and not v["ki"] and not v["be"] and len(v["szerep"]) == 2,
      "P3: nincs csere, ket szerepvaltas - kapott: %s" % (v and v["szerep"]))
allit(v and sorted((x["szE"], x["szU"], x["ertE"], x["ertU"]) for x in v["szerep"])
      == [("kezdo", "pad", 5, 0), ("pad", "kezdo", 0, 5)],
      "P3: kezdo->pad 5->0 es pad->kezdo 0->5 - kapott: %s" % (v and v["szerep"]))

print("\n--- P4: a GEP kulon all ---")
# A 11-es kezdo 0 percet jatszott; a 15-os (FWD, pad) 12 pontot hozott, tehat
# az automatikus csere beallitja - ez NEM a szakvezeto erdeme.
p = pontok()
p["11"] = [0, 0]                       # a FWD kezdo palyara sem lepett
for e in ("12", "13", "14"):           # rajta kivul csak a 15-os jatszott a padrol
    p[e] = [0, 0]
p["15"] = [12, 90]
v = egy(keret(KEZDO, PAD), keret(KEZDO, PAD), p)
allit(v and not v["ki"] and not v["be"] and not v["szerep"],
      "P4: az ember semmit nem valtoztatott - kapott: %s"
      % ((v and (v["ki"], v["be"], v["szerep"])),))
allit(v and v["gepE"] == 12 and v["gepU"] == 12 and v["guard"] == 0,
      "P4: a csere hozadeka mindket oldalon 12, a mutato 0 - kapott: %s"
      % ((v and (v["gepE"], v["gepU"], v["guard"])),))

# most a szakvezeto atrendezi a padot: a 12 pontos 15-os elore kerul a padon,
# de a 13-as (DEF) nem allhatna be a FWD helyere - a sorrend szamit
v2 = egy(keret(KEZDO, PAD), keret(KEZDO, [15] + PAD[:3]), p)
allit(v2 and v2["gepU"] == 12 and v2["guard"] == 0,
      "P4: a pad atrendezese itt nem valtoztat (a 15-os igy is beall) - kapott: %s"
      % ((v2 and (v2["gepU"], v2["guard"])),))

print("\n--- P5: EMBER + GEP = a Guardiola mutato ---")


def ellenoriz(regi, most, p, cimke):
    hist = {"1": {"L": regi}, "2": {"L": most}}
    v = (c.draft_keretvaltozas(hist, 2, p, POSZT) or {}).get("L")
    g = (c.draft_guardiola(hist, 2, p, POSZT) or {}).get("L")
    ember = round(sum(x["ert"] for x in v["be"]) - sum(x["ert"] for x in v["ki"])
                  + sum(x["ertU"] - x["ertE"] for x in v["szerep"]), 2)
    gep = round(v["gepU"] - v["gepE"], 2)
    allit(v["stimmel"] and round(ember + gep, 2) == g["guard"] == v["guard"],
          "P5: %s - ember %s + gep %s = %s, guardiola %s"
          % (cimke, ember, gep, round(ember + gep, 2), g["guard"]))


p = pontok()
p["11"] = [0, 0]
p["15"] = [12, 90]
p["20"] = [9, 90]
ellenoriz(keret(KEZDO, PAD), keret([20] + KEZDO[1:], PAD),
          p, "csere + automatikus csere egyszerre")
ellenoriz(keret(KEZDO, PAD), keret(KEZDO[:10] + [15], PAD[:3] + [11]),
          p, "szerepvaltas + automatikus csere")
p2 = pontok()
p2["1"] = [0, 0]          # a kapus nem jatszott -> csak kapus valthatja
p2["12"] = [7, 90]
ellenoriz(keret(KEZDO, PAD), keret(KEZDO, PAD[1:] + [12]), p2,
          "a pad sorrendje valtozik, kapus-csere")

print("\n--- P6-P7: hatarhelyzetek ---")
v = egy(keret(KEZDO, PAD), keret(KEZDO, PAD), pontok())
allit(v and not v["ki"] and not v["be"] and not v["szerep"] and v["guard"] == 0,
      "P6: valtozatlan keretnel nincs tetel es a mutato 0 - kapott: %s" % (v,))
allit(c.draft_keretvaltozas({"1": {"L": keret(KEZDO, PAD)}}, 1, pontok(), POSZT) is None,
      "P7: az elso fordulora nincs adat")
allit(c.draft_keretvaltozas({"1": {"L": keret(KEZDO, PAD)},
                             "2": {"L": keret(KEZDO, PAD)}}, 2, None, POSZT) is None,
      "P7: pont-adat nelkul nincs adat")

if hibak:
    print("\n%d allitas bukott." % len(hibak))
    sys.exit(1)
print("\nMind a %d allitas rendben." % osszes)
