#!/usr/bin/env python3
"""The fantasy layer of one Draft round, from our own stored data.

The NB1 has had this since the paper started (round-colour-harvest.py); the
Draft did not, so its summaries were written by reading four files by hand.
Everything here comes from the repository - no external source - and it is
the first of the three layers a summary is built from (see round-pipeline.md).

What a Draft round turns on is not what an NB1 round turns on. There is no
captain and no shared player: a footballer belongs to exactly one squad, and
the bench scores nothing. So the levers are the line-up (a big score left on
the bench is lost outright, not halved) and the week's waiver and free-agent
moves, which is what `guard` measures.

Usage: python3 naplo/draft-round-harvest.py [round]
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")


def load(name):
    with open(os.path.join(ROOT, name), encoding="utf-8") as f:
        return json.load(f)


def main():
    rnd = os.environ.get("HARVEST_ROUND") or (sys.argv[1] if len(sys.argv) > 1 else None)
    draft = load("draft.json")
    hist = load("draft_history.json")
    if rnd is None:
        kesz = [int(r) for r in hist.get("rounds", {})]
        rnd = str(max(kesz)) if kesz else "1"
    rnd = str(int(rnd))

    nev = {e["id"]: e["name"] for e in draft.get("entries", [])}
    jatekos = load("draft_players.json").get("players", {})
    pontok = (load("draft_pontok.json").get("rounds", {}) or {}).get(rnd, {})
    keretek = (hist.get("rounds", {}) or {}).get(rnd, {})
    valtozas = (load("draft_keretvaltozasok.json").get("rounds", {}) or {}).get(rnd, {})
    menetrend = (draft.get("schedule", {}) or {}).get(rnd, [])
    vegleges = int(rnd) in [int(x) for x in (hist.get("veglegesek") or [])]

    def jnev(e):
        j = jatekos.get(str(e)) or {}
        return j.get("n") or j.get("name") or ("#%s" % e)

    def jklub(e):
        j = jatekos.get(str(e)) or {}
        return j.get("t") or j.get("team") or "?"

    print("=" * 70)
    print("DRAFT %s. FORDULO - a sajat adatunkbol%s" % (
        rnd, "" if vegleges else "   [MEG NEM VEGLEGES: a bonusz mozoghat]"))
    print("=" * 70)

    for m in menetrend:
        h, v, hp, vp = m[0], m[1], m[2], m[3]
        print("")
        print("  %s %s : %s %s" % (nev.get(h, h), hp, vp, nev.get(v, v)))
        for csapat in (h, v):
            keret = keretek.get(str(csapat)) or []
            kezdo = [p for p in keret if not p.get("b")]
            pad = [p for p in keret if p.get("b")]
            ossz = sum(p.get("pts") or 0 for p in kezdo)
            padon = sum(p.get("pts") or 0 for p in pad)
            nullak = [p for p in kezdo if not (p.get("pts") or 0)]
            legjobb = max(kezdo, key=lambda p: p.get("pts") or 0) if kezdo else None
            padlegjobb = max(pad, key=lambda p: p.get("pts") or 0) if pad else None
            vz = valtozas.get(str(csapat)) or {}
            print("    %-24s kezdok %s pont | padon maradt %s pont | nulla: %d"
                  % (nev.get(csapat, csapat), ossz, padon, len(nullak)))
            if legjobb:
                print("        legjobb kezdo: %s (%s) %s" % (
                    jnev(legjobb["e"]), jklub(legjobb["e"]), legjobb.get("pts")))
            if padlegjobb and (padlegjobb.get("pts") or 0) > 0:
                print("        legjobb pados: %s (%s) %s  <- ez a pont ELVESZETT"
                      % (jnev(padlegjobb["e"]), jklub(padlegjobb["e"]), padlegjobb.get("pts")))
            if vz:
                print("        heti merleg (guard): %s" % vz.get("guard"))
                for x in vz.get("ki") or []:
                    print("          KI  %-22s %-5s pont: %s" % (
                        jnev(x["e"]), x.get("sz"), x.get("pont")))
                for x in vz.get("be") or []:
                    print("          BE  %-22s %-5s pont: %s" % (
                        jnev(x["e"]), x.get("sz"), x.get("pont")))
                for x in vz.get("szerep") or []:
                    print("          SZ  %-22s %s -> %s  pont: %s" % (
                        jnev(x["e"]), x.get("szE"), x.get("szU"), x.get("pont")))
            if nullak:
                print("        nullan zart kezdo: %s" % ", ".join(
                    "%s (%s)" % (jnev(p["e"]), jklub(p["e"])) for p in nullak))
        # A ket keret kozott a Draftban NINCS atfedes - a kerdes az, ki mennyit
        # hagyott a padon, es mit hozott a heti mozgas.
    print("")
    print("  A jatekosok PERCEI es golszerzese: draft_pontok.json (%d jatekos)" % len(pontok))
    return 0


if __name__ == "__main__":
    sys.exit(main())
