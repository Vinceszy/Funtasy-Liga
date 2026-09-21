#!/usr/bin/env python3
"""A Draft kispadjanak retege: mennyi termes maradt kint, es mennyi szamitott.

MIERT KELL: a Draftban nincs kapitany, nincs kozos jatekos es nincs arkeret -
a szakvezeto egyetlen heti dontese a kezdo tizenegy. Hogy ezzel a dontessel
mit kezd a mezony, egyetlen fordulobol nem latszik; tobb fordulon at viszont
szamszeru.

HAROM KULON SZAM, amit konnyu osszekeverni:
  - a padon maradt termes: minden padon ulo osszege. A felso korlat, nem a
    kar - tizenegy helyre negy embert nem lehet beallitani.
  - a tokeletes kezdovel nyerheto tobblet: a lehetseges legjobb SZABALYOS
    kezdo tizenegy es a tenylegesen kiallitott kulonbsege. EZ a valodi kar.
    Szabalyos: pontosan 1 kapus, 3-5 vedo, 2-5 kozeppalyas, 1-3 csatar - egy
    padon ulo kapus nem allithato be egy gyenge csatar helyere, tehat a
    poziciot figyelmen kivul hagyo parositas felfele hazudna.
  - a fordito eset: az a merkozes, ahol a padon maradt termes onmagaban
    tobb volt, mint a vereseg kulonbsege.

MIBOL: draft_history.json (fordulonkenti keret, `b` = padon ult, `pts`),
draft.json (sorsolas, csapatnevek), draft_players.json (poziciok). Sajat adat,
kulso keres nelkul.
"""
import json
import os
import sys

GYOKER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def betolt(nev):
    with open(os.path.join(GYOKER, nev), encoding="utf-8") as fh:
        return json.load(fh)


# A szabalyos felallas hatarai (FPL Draft): a kapus szama kotott, a
# mezonyjatekosoke sav. Ezek nelkul minden szam felfele csuszna.
KERET = {"GKP": (1, 1), "DEF": (3, 5), "MID": (2, 5), "FWD": (1, 3)}
KEZDO = 11


def felallasok():
    """Minden szabalyos 1-3-2-1 ... 1-5-5-3 osztas, ami tizenegyet ad ki."""
    ki = []
    for d in range(KERET["DEF"][0], KERET["DEF"][1] + 1):
        for m in range(KERET["MID"][0], KERET["MID"][1] + 1):
            for f in range(KERET["FWD"][0], KERET["FWD"][1] + 1):
                if 1 + d + m + f == KEZDO:
                    ki.append({"GKP": 1, "DEF": d, "MID": m, "FWD": f})
    return ki


FELALLASOK = felallasok()


def legjobb_kezdo(keret, pozicio):
    """A keretbol kiallithato legjobb SZABALYOS tizenegy termese.

    Posztonkent a legjobbak eleve sorba rakhatok, tehat minden felallasra
    eleg az elso n-et osszeadni, es a felallasok kozul a legjobbat venni.
    """
    rend = {}
    for p in keret:
        rend.setdefault(pozicio(p), []).append(p["pts"])
    for lista in rend.values():
        lista.sort(reverse=True)
    legjobb = None
    for f in FELALLASOK:
        if any(len(rend.get(poz, [])) < db for poz, db in f.items()):
            continue
        ossz = sum(sum(rend[poz][:db]) for poz, db in f.items())
        if legjobb is None or ossz > legjobb:
            legjobb = ossz
    return legjobb


def tobblet(keret, pozicio):
    """Mennyivel zart volna tobbet a keret a lehetseges legjobb tizenegygyel."""
    volt = sum(p["pts"] for p in keret if not p["b"])
    lehetett = legjobb_kezdo(keret, pozicio)
    return 0 if lehetett is None else lehetett - volt


def main():
    tortenet = betolt("draft_history.json")["rounds"]
    liga = betolt("draft.json")
    jatekosok = betolt("draft_players.json")["players"]
    nev = {str(e["id"]): e["name"] for e in liga["entries"]}

    def pozicio(p):
        return (jatekosok.get(str(p["e"])) or {}).get("p", "MID")

    fordulok = sorted(tortenet, key=int)

    print("=" * 70)
    print("DRAFT KISPAD-RETEG - %s. fordulo" % ", ".join(fordulok))
    print("=" * 70)

    print("\n  FORDULONKENT")
    ossz_pad = ossz_tobblet = 0
    for r in fordulok:
        pad = sum(p["pts"] for k in tortenet[r].values() for p in k if p["b"])
        tb = sum(tobblet(k, pozicio) for k in tortenet[r].values())
        hibatlan = sum(1 for k in tortenet[r].values()
                       if not tobblet(k, pozicio))
        ossz_pad += pad
        ossz_tobblet += tb
        print("    %2s. fordulo: a padon %3d, jobb kezdovel +%3d, "
              "hibatlan keret %d/%d" % (r, pad, tb, hibatlan, len(tortenet[r])))
    print("    OSSZESEN:    a padon %3d, jobb kezdovel +%3d"
          % (ossz_pad, ossz_tobblet))

    print("\n  SZAKVEZETONKENT")
    sor = {}
    for r in fordulok:
        for cs, keret in tortenet[r].items():
            a = sor.setdefault(cs, [0, 0])
            a[0] += sum(p["pts"] for p in keret if p["b"])
            a[1] += tobblet(keret, pozicio)
    for cs, (pad, tb) in sorted(sor.items(), key=lambda kv: -kv[1][0]):
        print("    %-24s a padon %3d, jobb kezdovel +%3d"
              % (nev.get(cs, cs), pad, tb))

    print("\n  HANY PADON ULO JATSZOTT EGYALTALAN")
    print("  (a tiszta kispad lehet figyelem is, es lehet ures keret is -")
    print("   ha a padon ulo be sem all, nem is volt mit kihagyni)")
    for cs in sorted(sor, key=lambda c: -sor[c][0]):
        volt = jatszott = 0
        for r in fordulok:
            for p in tortenet[r][cs]:
                if p["b"]:
                    volt += 1
                    jatszott += 1 if p["pts"] > 0 else 0
        print("    %-24s %2d/%2d allt be, padtermes %3d, jobb kezdovel +%3d"
              % (nev.get(cs, cs), jatszott, volt, sor[cs][0], sor[cs][1]))

    print("\n  AMIT A SAJAT KISPAD NYERT MEG AZ ELLENFELNEK")
    print("  (szabalyos felallitassal a vereseg elkerulheto lett volna)")
    for r in fordulok:
        pad = {cs: tobblet(k, pozicio) for cs, k in tortenet[r].items()}
        for a, b, pa, pb in liga["schedule"][r]:
            for en, ell, sajat, ove in ((a, b, pa, pb), (b, a, pb, pa)):
                kul = ove - sajat
                if kul > 0 and pad.get(str(en), 0) >= kul:
                    print("    %2s. %-22s %2d:%-2d %-22s  hianyzott %2d, "
                          "a keretben allt +%2d" % (r, nev[str(en)], sajat, ove,
                                                    nev[str(ell)], kul,
                                                    pad[str(en)]))

    print("\n  A LEGNAGYOBB EGYENI PADON FELEJTES")
    lista = []
    for r in fordulok:
        for cs, keret in tortenet[r].items():
            for p in keret:
                if p["b"]:
                    j = jatekosok.get(str(p["e"])) or {}
                    lista.append((p["pts"], int(r), nev[str(cs)],
                                  "%s (%s)" % (j.get("n", "?"), j.get("t", "?"))))
    for pts, r, cs, j in sorted(lista, reverse=True)[:10]:
        print("    %2d. fordulo  %2d  %-24s %s" % (r, pts, cs, j))
    return 0


if __name__ == "__main__":
    sys.exit(main())
