#!/usr/bin/env python3
"""Collect the colourful facts of a closed round from our own stored data.

This is the raw material a round summary would be written from. Everything
here comes from the repository - no external source - so it is available
today, for every closed round.

Usage: python3 naplo/round-colour-harvest.py [round]
"""
import json
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


def load(name):
    with open(os.path.join(ROOT, name), encoding="utf-8") as f:
        return json.load(f)


def hungarian_bonus(starters):
    hun = sum(1 for p in starters if p.get("hun"))
    u21 = sum(1 for p in starters if p.get("hun") and p.get("u21"))
    return 10 if (hun >= 5 and u21 >= 1) else 0, hun, u21


NOTABLE = {
    "Kihagyott büntető": "missed a penalty",
    "Tizenegyes hárítások": "saved a penalty",
    "Öngól": "own goal",
    "Piros lap": "sent off",
}


def main():
    rnd = sys.argv[1] if len(sys.argv) > 1 else None
    results = load("results.json")
    schedule = results["schedule"]
    if rnd is None:
        closed = [k for k in sorted(schedule, key=int)
                  if all(m[2] is not None for m in schedule[k])
                  and os.path.exists(os.path.join(ROOT, "bontasok", k + ".json"))]
        rnd = closed[-1]
    squads = load("squad_history.json")["rounds"][rnd]
    games = sorted(load("meccsek.json")["rounds"][rnd], key=lambda g: g["start"])
    detail = load(os.path.join("bontasok", rnd + ".json"))["bontasok"]

    club_game = {}
    for i, g in enumerate(games):
        club_game.setdefault(g["h"], []).append(i)
        club_game.setdefault(g["v"], []).append(i)

    print("=" * 72)
    print("ROUND %s - colour harvest from our own data" % rnd)
    print("=" * 72)
    print("\nMATCHES IN ORDER")
    for i, g in enumerate(games):
        print("  %d. %s  %s %s-%s %s" % (i, g["start"][:16].replace("T", " "),
                                         g["h"], g["hp"], g["vp"], g["v"]))

    def running(name):
        """Points after each match of the round, bonus counted from the start.

        EVERY player counts, bench included: the stored round total is the
        sum of all fifteen plus the bonus, and an earlier version of this
        script that summed only the starters came out short by exactly the
        bench's contribution in all eight cases. The starter/bench split
        only decides the Hungarian bonus."""
        squad = squads[name]
        starters = [p for p in squad if not p.get("sub")]
        bonus, hun, u21 = hungarian_bonus(starters)
        per = [0.0] * len(games)
        for p in squad:
            idx = club_game.get(p["team"])
            if idx:
                per[idx[-1]] += p.get("week") or 0
        out, acc = [], bonus
        for x in per:
            acc += x
            out.append(round(acc, 2))
        return bonus, hun, u21, out

    def notes(name):
        squad = squads[name]
        lines = []
        for p in squad:
            rows = detail.get(str(p.get("id"))) or []
            for r in rows:
                for key, text in NOTABLE.items():
                    if key in r["n"] and (r.get("v") or 0) > 0:
                        lines.append("%s (%s) %s" % (p["name"], p["team"], text))
            saves = next((r for r in rows if "Védett lövések" in r["n"]), None)
            if saves and (saves.get("v") or 0) >= 5:
                lines.append("%s (%s) made %d saves" % (p["name"], p["team"], saves["v"]))
        return lines

    print("\nFIXTURES")
    for m in schedule[rnd]:
        a, b, pa, pb = m[0], m[1], m[2], m[3]
        print("\n  %s %s : %s %s" % (a, pa, pb, b))
        for name in (a, b):
            bonus, hun, u21, run = running(name)
            squad = squads[name]
            cap = next((p for p in squad if p.get("cap")), None)
            bench = sum(p.get("week") or 0 for p in squad if p.get("sub"))
            total = round(sum(p.get("week") or 0 for p in squad) + bonus, 2)
            best = max(squad, key=lambda p: p.get("week") or 0, default=None)
            blanks = sum(1 for p in squad if not (p.get("week") or 0))
            print("    %-7s bonus %2d (hun %d, u21 %d) | captain %s (%s)"
                  % (name, bonus, hun, u21,
                     cap["name"] if cap else "-", (cap.get("week") if cap else "-")))
            print("            best %s (%s, %s) | bench gave %.2f | blanks %d"
                  " | check %s vs stored %s"
                  % (best["name"], best["team"], best.get("week"), bench, blanks,
                     total, pa if name == a else pb))
            print("            running: %s" % "  ".join(str(x) for x in run))
        sa = {p["name"] for p in squads[a]}
        sb = {p["name"] for p in squads[b]}
        both = sorted(sa & sb)
        if both:
            print("    shared players: %s" % ", ".join(both))
        for name in (a, b):
            for line in notes(name):
                print("    note (%s): %s" % (name, line))
    return 0


if __name__ == "__main__":
    sys.exit(main())
