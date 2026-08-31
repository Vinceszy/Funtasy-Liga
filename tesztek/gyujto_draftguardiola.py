#!/usr/bin/env python3
"""A "Guardiola mutato" a PL-en - ugyanaz a definicio, mint az NB1-en:
guard = a MOSTANI keret pontja MINUSZ a MULT HETI kerete UGYANEBBEN a
forduloban. A Draftban nincs kapitany, es a pad pontja nem szamit; viszont
a fordulo vegen AUTOMATIKUS CSERE van, es azt az alternativara is
alkalmazni kell - kulonben a mult heti keretet alulmernenk, es a mutato
szisztematikusan a valtoztatas javara torzulna.

D1: valtozatlan keretnel PONTOSAN 0.
D2: a csere kulonbsege pontos.
D3: AUTOMATIKUS CSERE: a palyara sem lepett kezdo helyere beall az elso
    olyan pados, aki jatszott.
D4: a csere csak ERVENYES formaciot hozhat letre (a kapust csak kapus
    valthatja - ket kapus nem ervenyes).
D5: ha egyetlen pados sem jatszott, nincs csere (a 0 pont marad).
D6: nincs mihez hasonlitani / nincs pont-adat -> nincs ertek.
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


# 15 fos keret: 1 GKP + 4 DEF + 4 MID + 2 FWD kezdo, majd 4 pados
POSZT = {}
def keret(ids, padok):
    sq = [{"e": e, "b": False, "pts": 0} for e in ids]
    sq += [{"e": e, "b": True, "pts": 0} for e in padok]
    return sq

KEZDO = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
PAD = [12, 13, 14, 15]
for e in KEZDO + PAD + [20, 21]:
    POSZT[str(e)] = ("GKP" if e in (1, 12) else "DEF" if e in (2, 3, 4, 5, 13)
                     else "MID" if e in (6, 7, 8, 9, 14) else "FWD")

def pontok(alap=5, perc=90, **kiv):
    """{element: [pont, perc]} - a kiv-ben felulirhato egy-egy jatekos."""
    d = {str(e): [alap, perc] for e in list(POSZT)}
    for k, v in kiv.items():
        d[k.lstrip("j")] = v
    return d


print("--- D1: valtozatlan keret -> pontosan 0 ---")
h = {"1": {"L": keret(KEZDO, PAD)}, "2": {"L": keret(KEZDO, PAD)}}
g = c.draft_guardiola(h, 2, pontok(), POSZT)
allit(g and g["L"]["guard"] == 0,
      "D1: valtozatlan keretnel 0 - kapott: %s" % (g and g["L"]))

print("\n--- D2: csere -> a kulonbseg pontos ---")
uj = keret([20] + KEZDO[1:], PAD)                 # az 1-es (GKP) helyett a 20-as
POSZT["20"] = "GKP"
p = pontok(); p["20"] = [12, 90]
g = c.draft_guardiola({"1": {"L": keret(KEZDO, PAD)}, "2": {"L": uj}}, 2, p, POSZT)
allit(g and g["L"]["guard"] == 7,
      "D2: a 12 pontos jott az 5 pontos helyere -> +7 - kapott: %s" % (g and g["L"]))

print("\n--- D3: automatikus csere a nem jatszo kezdo helyett ---")
# A 11-es (FWD) kezdo 0 percet jatszott. A PAD SORRENDJE szamit: a 12-es
# kapus nem johet (ket kapus nem ervenyes), a 13-as es a 14-es NEM JATSZOTT,
# tehat az elso beallithato a 15-os (8 pont). Igy egyszerre merjuk a
# sorrendet, az ervenyesseget es azt, hogy a nem jatszo padost atugorja.
p = pontok(); p["11"] = [0, 0]; p["13"] = [9, 0]; p["14"] = [9, 0]; p["15"] = [8, 90]
g = c.draft_guardiola(h, 2, p, POSZT)
# 10 jatszo kezdo x 5 + a bejott 15-os 8 = 58
allit(g and g["L"]["teny"] == 58,
      "D3: a nem jatszo padost atugorja, a 15-os all be (58) - kapott: %s" % (g and g["L"]))

# es ha a 13-as JATSZOTT, akkor O jon - o van elorebb a padon
p2 = pontok(); p2["11"] = [0, 0]; p2["13"] = [9, 90]; p2["15"] = [8, 90]
g2 = c.draft_guardiola(h, 2, p2, POSZT)
allit(g2 and g2["L"]["teny"] == 59,
      "D3: a pad SORRENDJE dont - a 13-as jon, nem a 15-os (59) - kapott: %s"
      % (g2 and g2["L"]))

print("\n--- D4: a csere csak ervenyes formaciot hozhat letre ---")
# az 1-es KAPUS nem jatszott. A pad elso jatszo tagja a 13-as (DEF) - ot NEM
# szabad beallitani (0 kapus), csak a 12-es kapust.
p = pontok(); p["1"] = [0, 0]; p["12"] = [3, 90]; p["13"] = [9, 90]
g = c.draft_guardiola(h, 2, p, POSZT)
# 10 kezdo x 5 + a bejott KAPUS 3 = 53 (nem 59, ami a 13-assal jonne ki)
allit(g and g["L"]["teny"] == 53,
      "D4: a kapust csak kapus valthatja (53, nem 59) - kapott: %s" % (g and g["L"]))

print("\n--- D5: ha egy pados sem jatszott, nincs csere ---")
p = pontok(); p["11"] = [0, 0]
for e in PAD:
    p[str(e)] = [0, 0]
g = c.draft_guardiola(h, 2, p, POSZT)
allit(g and g["L"]["teny"] == 50,
      "D5: csere nelkul a 10 jatszo kezdo pontja (50) - kapott: %s" % (g and g["L"]))

print("\n--- D7: a KOZEPPALYAS MINIMUM (jelenleg 2) ---")
# EZ AZ ESET A FORMACIO-KONSTANST ROGZITI. Kezdo: 1 kapus + 5 vedo +
# 3 kozeppalyas + 2 csatar; az egyik kozeppalyas nem jatszott. A pad elso
# jatszo tagja egy VEDO 20 ponttal: vele a felallas 5-2-3 lenne.
#   - ha a kozeppalyas minimum 2 (mostani beallitas): a VEDO beall -> 40
#   - ha 3 lenne: nem allhatna be, es a pados kozeppalyas jonne -> 21
# Ha a Draft szabalya 3-nak bizonyul, a collect_draft.py FORMACIO sora
# valtozik, es ez az allitas fordul meg.
# Kezdo: 1 kapus + 4 vedo + 3 kozeppalyas + 3 csatar (a vedo NEM 5, kulonben
# a csere a VEDO-MAXIMUMON bukna el, nem a kozeppalyas-minimumon - a teszt
# igy nem azt merne, amit hisz).
P7 = {}
K7 = [101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111]
B7 = [112, 113, 114, 115]
for e in K7 + B7:
    P7[str(e)] = ("GKP" if e in (101, 112) else
                  "DEF" if e in (102, 103, 104, 105, 113) else
                  "MID" if e in (106, 107, 108, 114) else "FWD")
h7 = {"1": {"L": keret(K7, B7)}, "2": {"L": keret(K7, B7)}}
p7 = {str(e): [2, 90] for e in K7 + B7}
p7["108"] = [0, 0]        # a harmadik kozeppalyas nem jatszott
p7["113"] = [20, 90]      # pados VEDO, sok pont - NEM johet
p7["114"] = [1, 90]       # pados kozeppalyas - o johet
g = c.draft_guardiola(h7, 2, p7, P7)
# 10 jatszo kezdo x 2 = 20, + a bejott VEDO 20 = 40
allit(g and g["L"]["teny"] == 40,
      "D7: a 20 pontos vedo BEALL (5-2-3 ervenyes, a kozeppalyas minimum 2) "
      "- kapott: %s" % (g and g["L"]))

print("\n--- D6: amikor nincs ertek ---")
allit(c.draft_guardiola({"1": {"L": keret(KEZDO, PAD)}}, 1, pontok(), POSZT) is None,
      "D6: az elso fordulora nincs mutato")
allit(c.draft_guardiola(h, 2, None, POSZT) is None,
      "D6: pont-adat nelkul nincs mutato")

if hibak:
    print("\n%d allitas bukott." % len(hibak))
    sys.exit(1)
print("\nMind a %d allitas rendben." % osszes)
