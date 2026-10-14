#!/usr/bin/env python3
"""A karszalag retege: ki kire tette, mikor gondolta meg magat, mennyit ert.

MIERT KELL: az NB1-ben a kapitany az egyetlen kar, amit a jatek a szakvezeto
kezebe ad - egy jatekos heti termese duplan szamit. Hogy ez a kar mukodik-e,
csak tobb fordulon at latszik: egy fordulo kapitanyi listaja onmagaban semmit
nem mond, a negy egymas utani fordulo viszont megmutatja, valaki dont-e vagy
csak ragaszkodik.

MIBOL: squad_history.json, sajat adat, kulso keres nelkul. A tarolt `week` a
kapitanynal MAR duplazva van (lasd nb1/index.html alapPont), a padon ulonel
pedig mar felezve - az alapertekhez tehat vissza kell osztani.

HASZNALAT: python3 naplo/karszalag-harvest.py [elso_fordulo] [utolso_fordulo]
"""
import json
import os
import sys

GYOKER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def alap(p):
    """A jatekos heti termese duplazas es felezes nelkul."""
    return (p.get("week") or 0) / (2 if p.get("cap") else 1) * (2 if p.get("sub") else 1)


def kapitany(keret):
    for p in keret:
        if p.get("cap"):
            return p
    return None


def main():
    with open(os.path.join(GYOKER, "squad_history.json"), encoding="utf-8") as fh:
        tortenet = json.load(fh)["rounds"]
    meglevo = sorted((int(r) for r in tortenet), reverse=False)
    elso = int(sys.argv[1]) if len(sys.argv) > 1 else meglevo[0]
    utolso = int(sys.argv[2]) if len(sys.argv) > 2 else meglevo[-1]
    fordulok = [r for r in meglevo if elso <= r <= utolso]

    print("=" * 70)
    print("NB1 KARSZALAG-RETEG - %d-%d. fordulo" % (elso, utolso))
    print("=" * 70)

    szakvezetok = sorted(tortenet[str(fordulok[0])])
    valtas_ossz = alkalom_ossz = 0

    for mgr in szakvezetok:
        print("\n  %s" % mgr)
        elozo = None
        for r in fordulok:
            keret = tortenet.get(str(r), {}).get(mgr) or []
            k = kapitany(keret)
            if not k:
                print("    %2d. nincs kapitany a tarolt keretben" % r)
                elozo = None
                continue
            # A legjobb valasztas ugyanabbol a keretbol, utolag nezve.
            mezony = sorted(keret, key=lambda p: -alap(p))
            legjobb = mezony[0] if mezony else None
            jel = ""
            if elozo is not None:
                alkalom_ossz += 1
                if k["name"] != elozo:
                    jel = "  << VALTOTT (%s helyett)" % elozo
                    valtas_ossz += 1
                else:
                    jel = "  (marad)"
            print("    %2d. %-26s %5.2f -> duplan %5.2f   legjobb lett volna: "
                  "%-24s %5.2f%s"
                  % (r, k["name"], alap(k), alap(k) * 2,
                     legjobb["name"] if legjobb else "-",
                     alap(legjobb) if legjobb else 0, jel))
            elozo = k["name"]

    print("\n" + "-" * 70)
    print("  ujragondolasi alkalom: %d, ebbol valtas: %d"
          % (alkalom_ossz, valtas_ossz))

    # Kire kerult a szalag fordulonkent - a nyaj merete.
    print("\n  A SZALAG VISELOI FORDULONKENT")
    for r in fordulok:
        szamlalo = {}
        for mgr, keret in (tortenet.get(str(r)) or {}).items():
            k = kapitany(keret)
            if k:
                szamlalo.setdefault(k["name"], []).append((mgr, alap(k)))
        sorok = sorted(szamlalo.items(), key=lambda kv: -len(kv[1]))
        print("    %2d. fordulo:" % r)
        for nev, lista in sorok:
            print("        %-26s %dx  %5.2f  (%s)"
                  % (nev, len(lista), lista[0][1],
                     ", ".join(m for m, _ in lista)))

    # A kar hozama: mennyit adott a duplazas, es mennyit adhatott volna.
    print("\n  A DUPLAZAS HOZAMA SZAKVEZETONKENT (%d-%d.)" % (elso, utolso))
    for mgr in szakvezetok:
        nyert = elszalasztott = 0.0
        for r in fordulok:
            keret = tortenet.get(str(r), {}).get(mgr) or []
            k = kapitany(keret)
            if not k:
                continue
            legjobb = max((alap(p) for p in keret), default=0)
            nyert += alap(k)
            elszalasztott += legjobb - alap(k)
        print("    %-14s a szalag hozott +%.2f-t; a keret legjobbjaval "
              "+%.2f lett volna (elszalasztva %.2f)"
              % (mgr, nyert, nyert + elszalasztott, elszalasztott))
    return 0


if __name__ == "__main__":
    sys.exit(main())
