#!/usr/bin/env python3
"""A fordulo szinestablajanak ellenorzese - halozat nelkul, a sajat adatunkbol.

Ket dolgot allit:

1. Minden `event` es `record` sor megtalalja a parjat ugyanannak a fajlnak a
   strukturalt blokkjaban (gol, golpassz, VAR-dontes, nagy helyzet). Ha nem,
   akkor vagy a perc rossz, vagy a jatekos, vagy az allitas nem tortent meg.
2. Minden jatekos benne van valakinek a kereteben azon a fordulon. Aki nincs,
   annak a horgonya csak `record` lehet: rola nincs sajat adatunk.

A ket forras percei nem mindig egyeznek a hosszabbitasban (a szoveges
kozvetites "45+2"-t ir oda, ahol a lovesterkep 45-ot), ezert az alapperc
szamit; a nev elotti kezdobetu-rovidites ("N.Jackson") le van vagva.

A ket liga strukturalt blokkja mas alaku: az NB1-e a magyar beszamolo
formalis reszebol jon (golok `ki` nevvel, nincs benne VAR-lista es
lovesterkep), a PL-e a FotMobbol. Amit egy blokk nem tartalmaz, azt nem is
ellenorizzuk - a hamis biztonsagnal jobb a bevallott hatar. A kezdesi idot
csak a PL-tablatol varjuk el, mert csak ott gyujtjuk.

Hasznalat: python3 naplo/colour-check.py <liga> <fordulo>
"""
import json
import os
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")


def sima(s):
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    elso = s.split(".")[0]
    return s.split(".")[-1].strip() if 0 < len(elso) <= 2 else s


def alap(p):
    return str(p).replace(" ", "").split("+")[0]


def meccskulcs(nev, meccsek):
    """'Man City 5-3 Sunderland' -> 'Man City - Sunderland'."""
    if nev in meccsek:
        return nev
    for k in meccsek:
        h, _, v = k.partition(" - ")
        if nev.startswith(h) and nev.endswith(v):
            return k
    return None


def keretek(rnd):
    """(nev, klub) parok, akik azon a fordulon barmelyik keretben benne voltak."""
    hist = json.load(open(os.path.join(ROOT, "draft_history.json"), encoding="utf-8"))
    jat = json.load(open(os.path.join(ROOT, "draft_players.json"), encoding="utf-8"))["players"]
    ki = set()
    for keret in (hist.get("rounds", {}).get(str(rnd), {}) or {}).values():
        for x in keret:
            j = jat.get(str(x["e"])) or {}
            ki.add((j.get("n"), j.get("t")))
    return ki


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    liga, rnd = sys.argv[1], sys.argv[2]
    ut = os.path.join(HERE, "%s-colour-%s.json" % (liga, rnd))
    d = json.load(open(ut, encoding="utf-8"))
    meccsek = d.get("meccsek") or {}
    sorok = d.get("allitasok") or []
    keret = keretek(rnd) if liga == "pl" else set()

    baj = []
    for s in sorok:
        horgony, tag = s.get("horgony"), s.get("tag")
        if horgony == "nyilatkozat":
            if not s.get("kitol"):
                baj.append("nyilatkozat beszelo nelkul: %s" % s.get("mondat"))
            continue

        if keret and s.get("klub"):
            van = (s.get("jatekos"), s.get("klub")) in keret
            if van and horgony == "record":
                baj.append("%s (%s): keretben van, megis record" % (s["jatekos"], s["klub"]))
            if not van and horgony != "record":
                baj.append("%s (%s): nincs keretben, megis %s" % (s["jatekos"], s["klub"], horgony))

        if horgony not in ("event", "record"):
            continue
        k = meccskulcs(s.get("meccs"), meccsek)
        if not k:
            baj.append("ismeretlen meccs: %s" % s.get("meccs"))
            continue
        m, p, nev = meccsek[k], alap(s.get("perc")), sima(s.get("jatekos"))

        def golban(mezo="jatekos"):
            return any(alap(g.get("perc")) == p and nev in sima(g.get(mezo) or g.get("ki"))
                       for g in m.get("golok") or [])

        if tag in ("goal", "goal_manner", "luck"):
            talalt = golban()
        elif tag == "assist":
            # Golpasszt csak az a blokk tart szamon, amelyikben van ilyen mezo:
            # a magyar beszamolo formalis resze a golszerzot irja, mast nem.
            van_mezo = any("gólpassz" in g for g in m.get("golok") or [])
            talalt = golban("gólpassz") if van_mezo else True
        elif tag == "disputed":
            talalt = golban() or any(
                alap(v.get("perc")) == p and nev in sima(v.get("jatekos"))
                for v in m.get("var") or [])
        elif tag == "big_miss":
            # Nagy helyzetek listaja csak ott van, ahol lovesterkepet gyujtunk.
            talalt = ("kihagyott_nagy_helyzet" not in m) or any(
                alap(h.get("perc")) == p and nev in sima(h.get("jatekos"))
                for h in m["kihagyott_nagy_helyzet"])
        else:
            # card, sub, milestone, history, match_picture: a blokk nem tartja
            # szamon oket, tehat nincs mihez mernunk.
            talalt = True
        if not talalt:
            baj.append("nincs fedezet: %s %s' %s (%s)" % (s.get("jatekos"), s.get("perc"), tag, k))

    hiany = [k for k, m in meccsek.items() if not m.get("kezdes")] if liga == "pl" else []
    if hiany:
        baj.append("kezdesi ido nelkuli meccs: %s" % ", ".join(sorted(hiany)))

    print("%s %s. fordulo: %d sor, %d meccs" % (liga, rnd, len(sorok), len(meccsek)))
    if baj:
        for b in baj:
            print("  - %s" % b)
        return 1
    print("  rendben")
    return 0


if __name__ == "__main__":
    sys.exit(main())
