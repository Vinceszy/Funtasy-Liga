#!/usr/bin/env python3
"""Az atigazolasok retege: ki epitett at, mikor szabad, es mit dobott el.

MIERT KELL: az NB1-ben a cserek szama a jatek egyik kemeny korlatja - hetente
HAROM, a teli es a valogatott szunetben viszont KORLATLAN (a hivatalos
szabalyzatbol, lasd a fo README "Amit a hivatalos szabalyzat rogzit"
szakaszat). Ebbol kovetkezik, hogy egy keret NEM barmikor epitheto at: aki
tizenegy embert cserel, az nem szorgalmasabb a tobbinel, hanem egy olyan
fordulot hasznalt ki, amelyikben ez egyaltalan lehetseges volt. Egy
fordulo cserelistaja onmagaban ezert felrevezeto - a korlat ismerete nelkul
ugyanaz a szam jelenthet elszantsagot es puszta alkalmat is.

A szunetes fordulot nem talaljuk ki, de a RESBOL latszik: az elozo fordulo
utolso meccse es a mostani fordulo elso meccse kozott eltelt ido. Rendes
heten ez het nap korul van; a valogatott szunet utan harom hetre nyilik.
NEM a fordulo hosszat merjuk: egy EPPEN FUTO fordulohoz a gyujto meg csak a
mar lement meccseket tarolja, abbol a harom hetes fordulo is ketnaposnak
latszana. A res viszont a lezart mult ket pontja kozott all, tehat stabil.

A fordulo sajat hatarideje (start_at, end_at, closed_transfers_at) az MLSZ
fordulo-objektumaban all - azt ma nem gyujtjuk (lasd naplo/nb1-fordulo-allas.txt),
ezert dolgozunk a meccsnapokbol.

MIBOL: squad_history.json es meccsek.json - sajat adat, kulso keres nelkul.
A tarolt `week` a jatekos VEGSO fordulo-jarulelka (a kapitanyi duplazas es a
padfelezes mar benne van; lasd collect.py keret_osszeg), tehat az eladott
emberek jaruleka kozvetlenul osszeadhato.

HASZNALAT: python3 naplo/atigazolas-harvest.py [elso_fordulo] [utolso_fordulo]
"""
import json
import os
import sys

GYOKER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HETI_KERET = 3          # a szabalyzat szerinti heti cserekeret


def betolt(nev):
    with open(os.path.join(GYOKER, nev), encoding="utf-8") as fh:
        return json.load(fh)


def kulcsolt(keret):
    """A keret AZONOSITO szerint kulcsolva. Nem nev szerint: az MLSZ menet
    kozben javitja a neveket (az 5. fordulora "Artur Horvath"-bol "Horvath
    Artur" lett, ugyanazzal az 1137-es azonositoval), es a nev szerinti
    parositas ezt ket cserenek latta - egy olyan fordulot mutatott a heti
    harmas kereten felul, amelyikben nem tortent semmi. Ugyanaz a szabaly,
    mint a kulonbseg-nezetnel a lapon (lasd a fo README-t).

    Akinek nincs azonositoja (a legregebbi rekordok), az a neven marad: egy
    ilyen rekord parositatlan maradna, ami rosszabb, mint a nev."""
    return {(p.get("id") if p.get("id") is not None else "nev:" + p["name"]): p
            for p in keret}


def kapitany(keret):
    return next((p["name"] for p in keret if p.get("cap")), None)


def ertek(keret):
    """A keret erteke a FORDULOBAN ervenyes arakkal (a rekordban allo `price`),
    nem a mai arral - kulonben egy kesobbi aremelkedes visszamenoleg irna at
    azt, amit a szakvezeto akkor koltott."""
    return sum(p.get("price") or 0 for p in keret)


def alakzat(keret):
    kezdok = [p for p in keret if not p.get("sub")]
    sorrend = ["K", "H", "KP", "CS"]
    db = {x: sum(1 for p in kezdok if p.get("pos") == x) for x in sorrend}
    return "-".join(str(db[x]) for x in sorrend)


def meccsnapok(meccsek, r):
    return sorted(m["start"][:10] for m in (meccsek.get(str(r)) or []) if m.get("start"))


def res(meccsek, elozo_r, r):
    """Hany nap telt el az elozo fordulo UTOLSO es a mostani ELSO meccse
    kozott. None, ha barmelyik oldal hianyzik."""
    a, b = meccsnapok(meccsek, elozo_r), meccsnapok(meccsek, r)
    if not a or not b:
        return None
    from datetime import date
    x, y = (date(*map(int, d.split("-"))) for d in (a[-1], b[0]))
    return (y - x).days


def main():
    tortenet = betolt("squad_history.json")["rounds"]
    meccsek = betolt("meccsek.json").get("rounds") or {}
    meglevo = sorted(int(r) for r in tortenet)
    elso = int(sys.argv[1]) if len(sys.argv) > 1 else meglevo[0]
    utolso = int(sys.argv[2]) if len(sys.argv) > 2 else meglevo[-1]
    fordulok = [r for r in meglevo if elso <= r <= utolso]
    if len(fordulok) < 2:
        print("Legalabb ket tarolt fordulo kell az osszehasonlitashoz.")
        return 1

    print("=" * 72)
    print("NB1 ATIGAZOLAS-RETEG - %d-%d. fordulo" % (fordulok[0], fordulok[-1]))
    print("=" * 72)
    print("A heti cserekeret %d; a teli es a valogatott szunetben korlatlan." % HETI_KERET)

    for r in fordulok[1:]:
        elozo_r = fordulok[fordulok.index(r) - 1]
        r_res = res(meccsek, elozo_r, r)
        jel = ""
        if r_res is not None and r_res > 10:
            jel = ("  << %d NAP RES az elozo fordulo ota: szunet, "
                   "a cserekeret itt nem szorit" % r_res)
        print("\n%s" % ("-" * 72))
        print("%d. fordulo (az elozo a %d.)%s" % (r, elozo_r, jel))
        if r_res is not None and not jel:
            print("  %d nap telt el az elozo fordulo utolso meccse ota" % r_res)
        print("%s" % ("-" * 72))

        sorok = []
        for mgr in sorted(tortenet[str(r)]):
            uj = tortenet[str(r)].get(mgr) or []
            regi = tortenet[str(elozo_r)].get(mgr) or []
            if not uj or not regi:
                continue
            un, rn = kulcsolt(uj), kulcsolt(regi)
            ki = [rn[k] for k in sorted(set(rn) - set(un), key=lambda k: rn[k]["name"])]
            be = [un[k] for k in sorted(set(un) - set(rn), key=lambda k: un[k]["name"])]
            sorok.append((len(ki), mgr, ki, be, regi, uj))

        for db, mgr, ki, be, regi, uj in sorted(sorok, reverse=True):
            tul = "  (a heti kereten FELUL: %d)" % (db - HETI_KERET) if db > HETI_KERET else ""
            print("\n  %-8s %2d csere%s" % (mgr, db, tul))
            print("           keretertek %.1f -> %.1f M | kezdo %s -> %s"
                  % (ertek(regi), ertek(uj), alakzat(regi), alakzat(uj)))
            kr, ku = kapitany(regi), kapitany(uj)
            if kr != ku:
                kr_p = next((p for p in regi if p.get("cap")), None)
                maradt = kr_p is not None and kulcsolt([kr_p]).popitem()[0] in kulcsolt(uj)
                elengedte = " (es EL IS ADTA)" if kr and not maradt else ""
                print("           karszalag: %s -> %s%s" % (kr, ku, elengedte))
            if not db:
                continue
            # Az eladottak jaruleka az ELOZO fordulohoz - ez a "mitol szabadult
            # meg" merteke. A magyarszabaly +10 nem jatekoshoz kotodik, ezert
            # nem szerepel benne; a sor ezert a jatekospontokhoz viszonyit.
            jarulek = sum(p.get("week") or 0 for p in ki)
            jatekospont = sum(p.get("week") or 0 for p in regi)
            nullas = sum(1 for p in ki if not p.get("week"))
            arany = (" (%.0f%%)" % (100 * jarulek / jatekospont)) if jatekospont else ""
            print("           az eladottak a %d. fordulohoz: %.2f pont a %.2f-bol%s, "
                  "koztuk %d nullas"
                  % (elozo_r, jarulek, jatekospont, arany, nullas))
            print("           ELADVA:  " + ", ".join(
                "%s %s" % (p["name"], ("%.2f" % (p.get("week") or 0)).rstrip("0").rstrip("."))
                for p in sorted(ki, key=lambda p: -(p.get("week") or 0))))
            print("           MEGVEVE: " + ", ".join(p["name"] for p in be))
    return 0


if __name__ == "__main__":
    sys.exit(main())
