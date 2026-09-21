#!/usr/bin/env python3
"""A forduló egyetlen órán: mikor mi történt, és melyik párharcban.

MIERT: a golperceket nem azert gyujtjuk, hogy minden golnal odairjuk, mikor
esett. Azert gyujtjuk, hogy a fordulo egy idovonalra kerulhessen - egyszerre
futo meccsek mellett csak igy latszik, hol fordult meg egy parharc, es mi
tortent kozben egy masik palyan.

A kezdesi ido a szinestablabol jon (`meccsek[...]["kezdes"]`, a
pl-colour-harvest.py irja oda), a perc az allitasok soraibol. A ketto
osszege az esemeny valos ideje; a felido tizenot perce hozzaadodik a
masodik felido perceihez, a hosszabbitas percei pedig a sajat percukhoz.

Ez kozelites: nem a masodpercet keressuk, hanem azt, hogy ket esemeny
ugyanabban a percben tortent-e ket kulon palyan.

Hasznalat: python3 naplo/idovonal.py <fordulo>
"""
import collections
import datetime
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
FELIDO = 15
ERDEKES = ("goal_manner", "goal", "luck", "assist", "disputed", "big_miss")


def betolt(nev):
    with open(os.path.join(ROOT, nev), encoding="utf-8") as f:
        return json.load(f)


def valos_ido(kezdes, perc):
    t = datetime.datetime.strptime(kezdes, "%Y-%m-%dT%H:%M:%SZ")
    p = str(perc).replace(" ", "")
    alap = int(p.split("+")[0])
    rada = int(p.split("+")[1]) if "+" in p else 0
    return t + datetime.timedelta(minutes=alap + rada + (FELIDO if alap > 45 else 0))


def main():
    rnd = sys.argv[1] if len(sys.argv) > 1 else "5"
    szin = json.load(open(os.path.join(HERE, "pl-colour-%s.json" % rnd), encoding="utf-8"))
    meccsek = szin.get("meccsek") or {}
    draft = betolt("draft.json")
    nev = {e["id"]: e["name"] for e in draft["entries"]}
    keretek = betolt("draft_history.json")["rounds"][rnd]
    jatekosok = betolt("draft_players.json")["players"]

    gazda = {}
    for csapat, keret in keretek.items():
        for x in keret:
            j = jatekosok.get(str(x["e"])) or {}
            gazda[(j.get("n"), j.get("t"))] = (nev[int(csapat)], "pad" if x.get("b") else "kezdo")

    ellenfel = {}
    for m in draft["schedule"][rnd]:
        ellenfel[nev[m[0]]], ellenfel[nev[m[1]]] = nev[m[1]], nev[m[0]]

    def kulcs(meccsnev):
        if meccsnev in meccsek:
            return meccsnev
        for k in meccsek:
            h, _, v = k.partition(" - ")
            if meccsnev.startswith(h) and meccsnev.endswith(v):
                return k
        return None

    esemenyek = []
    for s in szin.get("allitasok") or []:
        if s.get("tag") not in ERDEKES or not s.get("perc"):
            continue
        k = kulcs(s.get("meccs"))
        ki = gazda.get((s.get("jatekos"), s.get("klub")))
        if not k or not ki or not meccsek[k].get("kezdes"):
            continue
        esemenyek.append((valos_ido(meccsek[k]["kezdes"], s["perc"]), ki[0], ki[1],
                          s["jatekos"], s["perc"], s["tag"], s["mondat"], k))
    esemenyek.sort()

    parharc = collections.defaultdict(list)
    for e in esemenyek:
        parharc[tuple(sorted((e[1], ellenfel[e[1]])))].append(e)

    print("=" * 70)
    print("A %s. FORDULO IDOVONALA - %d esemeny, %d meccs" % (rnd, len(esemenyek), len(meccsek)))
    print("=" * 70)
    for (a, b), sorok in parharc.items():
        print("")
        print("  %s - %s" % (a, b))
        elozo = None
        for t, csapat, hely, jatekos, perc, tag, mondat, meccs in sorok:
            egyutt = " <<< egyszerre" if elozo and t == elozo else ""
            print("    %s  %-22s %-5s %-15s %4s'  %-12s %s%s" % (
                t.strftime("%a %H:%M"), csapat, hely, jatekos, perc, tag, meccs, egyutt))
            elozo = t
    print("")
    print("  Az ido UTC. Ket azonos idobelyeg ket kulon palyan egyidejuseg.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
