#!/usr/bin/env python3
"""A kovetkezo Draft-fordulo beharangozojanak sajat retege.

MIERT KULON A BEHARANGOZONAK: az osszefoglalo azt nezi, mi tortent; a
beharangozoba viszont csak az kerulhet, ami a KOVETKEZO fordulo eredmenyet
befolyasolja. A ketto nem ugyanaz az adat. Ami elore szol, az a keret alakja
es a szakvezeto szokasai - nem a mult heti pontszam.

A Draftban nincs kapitany es nincs kozos jatekos, tehat a karok, amiket egy
szakvezeto huzhat: a kezdo tizenegy, a heti igazolas, es a pad - amelyik nem
tartalek, hanem biztositas. A fordulo vegen ugyanis a gep az elso olyan
padost allitja be a palyara sem lepett kezdo helyere, aki jatszott. Akinek
ures a padja, annak egy kimarado kezdo egy ures hely.

Ezert amit kiir: hanyszor kellett eddig a gepnek beugrania es mit mentett,
hanyszor nem tudott (mert a padon sem jatszott senki), mennyi pont ragadt a
padon, mennyit hoztak a heti mozgasok, mennyi ballaszt van a kezdoben, es
mennyire fugg a csapat egyetlen embertol.

Minden a sajat adatunkbol jon, halozat nelkul.

Hasznalat: python3 naplo/draft-preview-harvest.py [fordulo]
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")


def load(nev):
    with open(os.path.join(ROOT, nev), encoding="utf-8") as f:
        return json.load(f)


def main():
    draft = load("draft.json")
    hist = load("draft_history.json")
    keszek = sorted(int(r) for r in (hist.get("rounds") or {}))
    rnd = int(sys.argv[1]) if len(sys.argv) > 1 else (max(keszek) + 1 if keszek else 1)

    nev = {e["id"]: e["name"] for e in draft.get("entries", [])}
    rang = {s["id"]: s for s in draft.get("standings", [])}
    jatekos = load("draft_players.json").get("players", {})
    pontok = load("draft_pontok.json").get("rounds", {})
    zaras = load("zarasok.json").get("rounds", {})
    valtozas = load("draft_keretvaltozasok.json").get("rounds", {})
    menetrend = (draft.get("schedule") or {}).get(str(rnd)) or []
    mult = [r for r in keszek if r < rnd]
    # A percadat nem minden fordulora all rendelkezesre (az elso fordulot a
    # gyujto meg nem ugy mentette). Ahol nincs, ott nem szamolunk palyara sem
    # lepett kezdot - kulonben az egesz kezdo tizenegy annak latszana.
    percesek = [r for r in mult if str(r) in pontok]

    def jnev(e):
        return (jatekos.get(str(e)) or {}).get("n") or ("#%s" % e)

    def jklub(e):
        return (jatekos.get(str(e)) or {}).get("t") or "?"

    def perc(r, e):
        return ((pontok.get(str(r)) or {}).get(str(e)) or [None, None])[1]

    def profil(cs):
        p = {"csere": 0, "cserepont": 0, "potolatlan": 0, "padon_ragadt": 0,
             "mozgas": 0, "guard": 0, "ballaszt": 0, "kezdo_db": 0,
             "legjobb": None, "fuggoseg": 0.0, "hetek": []}
        for r in mult:
            keret = ((hist.get("rounds") or {}).get(str(r)) or {}).get(str(cs)) or []
            kezdo = [x for x in keret if not x.get("b")]
            pad = [x for x in keret if x.get("b")]
            ossz = sum(x.get("pts") or 0 for x in kezdo)
            p["hetek"].append(ossz)
            p["kezdo_db"] += len(kezdo)
            p["ballaszt"] += sum(1 for x in kezdo if (x.get("pts") or 0) <= 2)
            z = (zaras.get(str(r)) or {}).get(str(cs)) or {}
            p["csere"] += len(z.get("be") or [])
            p["cserepont"] += sum(x.get("pts") or 0 for x in (z.get("be") or []))
            if r in percesek:
                p["potolatlan"] += sum(1 for x in kezdo if not (perc(r, x["e"]) or 0))
            # A tarolt pad a ZARAS UTANI allapot, tehat amit itt latunk, az
            # mar tenyleg kint maradt - a csereben beallt embert a kezdok
            # kozott talaljuk. Ezert minden fordulo padja beleszamit.
            p["padon_ragadt"] += sum(x.get("pts") or 0 for x in pad)
            v = valtozas.get(str(r), {}).get(str(cs)) or {}
            p["mozgas"] += len(v.get("ki") or []) + len(v.get("be") or [])
            p["guard"] += v.get("guard") or 0
        # kitol fugg: az idei legtobb pontot hozo embere, es az aranya
        egyen = {}
        for r in mult:
            for x in ((hist.get("rounds") or {}).get(str(r)) or {}).get(str(cs)) or []:
                if not x.get("b"):
                    egyen[x["e"]] = egyen.get(x["e"], 0) + (x.get("pts") or 0)
        if egyen:
            e = max(egyen, key=lambda k: egyen[k])
            p["legjobb"] = (jnev(e), jklub(e), egyen[e])
            osszes = sum(p["hetek"]) or 1
            p["fuggoseg"] = 100.0 * egyen[e] / osszes
        return p

    def maiKeret(cs):
        """A LEGUTOBBI zart fordulo kerete - ezzel varja a kovetkezot."""
        if not mult:
            return [], []
        keret = ((hist.get("rounds") or {}).get(str(mult[-1])) or {}).get(str(cs)) or []
        return ([x for x in keret if not x.get("b")], [x for x in keret if x.get("b")])

    print("=" * 70)
    print("DRAFT %d. FORDULO - BEHARANGOZO-RETEG (%d lezart fordulo alapjan)"
          % (rnd, len(mult)))
    print("=" * 70)
    for m in menetrend:
        print("")
        print("  %s  -  %s" % (nev.get(m[0], m[0]), nev.get(m[1], m[1])))
        for cs in (m[0], m[1]):
            p, s = profil(cs), rang.get(cs) or {}
            kezdo, pad = maiKeret(cs)
            print("    %-24s %d. hely, %d pont, %d:%d"
                  % (nev.get(cs, cs), s.get("rank", 0), s.get("total", 0),
                     s.get("for", 0), s.get("against", 0)))
            print("        heti termes: %s" % " ".join(str(x) for x in p["hetek"]))
            print("        gep beugrott %dx (%d pontot mentett); potolatlan hely: %d (%d fordulobol)"
                  % (p["csere"], p["cserepont"], p["potolatlan"], len(percesek)))
            print("        a padon kint maradt osszesen: %d pont" % p["padon_ragadt"])
            print("        keretmozgas: %d lepes, merleg %+d" % (p["mozgas"], p["guard"]))
            if p["kezdo_db"]:
                print("        ballaszt: a kezdok %d%%-a zart ket pont alatt vagy azon"
                      % round(100.0 * p["ballaszt"] / p["kezdo_db"]))
            if p["legjobb"]:
                print("        legjobb embere: %s (%s) %d pont - a termes %d%%-a"
                      % (p["legjobb"][0], p["legjobb"][1], p["legjobb"][2],
                         round(p["fuggoseg"])))
            print("        a padja most: %s" % ", ".join(
                "%s (%s)" % (jnev(x["e"]), jklub(x["e"])) for x in pad) or "ures")
    print("")
    print("  FIGYELEM: ez a legutobb lezart fordulo kerete, NEM a kovetkezoe.")
    print("  A heti igazolasok meg hatra vannak, a kezdo tizenegy pedig a")
    print("  fordulo elso kezdorugasaig atirhato. Aki most a padon ul, arrol")
    print("  csak annyit tudunk, hogy a szakvezetonek dontenie kell rola.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
