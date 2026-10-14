#!/usr/bin/env python3
"""The armband layer: who put it on whom, when they changed their mind, what it was worth.

WHY IT IS NEEDED: in the NB1 the captain is the only lever the game puts in
the manager's hands - one player's weekly score counts double. Whether that
lever works shows only across several rounds: one round's list of captains
says nothing by itself, but four rounds in a row show whether somebody
decides or merely holds on.

FROM WHAT: squad_history.json, our own data, no external request. The stored
`week` is ALREADY doubled for the captain (see the base-point calculation in
nb1/index.html) and already halved for a bench player - so it has to be
divided back to the base value.

USAGE: python3 naplo/armband-harvest.py [first_round] [last_round]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def base(p):
    """The player's weekly score without doubling and halving."""
    return (p.get("week") or 0) / (2 if p.get("cap") else 1) * (2 if p.get("sub") else 1)


def captain(squad):
    for p in squad:
        if p.get("cap"):
            return p
    return None


def main():
    with open(os.path.join(ROOT, "squad_history.json"), encoding="utf-8") as fh:
        history = json.load(fh)["rounds"]
    available = sorted((int(r) for r in history), reverse=False)
    first = int(sys.argv[1]) if len(sys.argv) > 1 else available[0]
    last = int(sys.argv[2]) if len(sys.argv) > 2 else available[-1]
    rounds = [r for r in available if first <= r <= last]

    print("=" * 70)
    print("NB1 ARMBAND LAYER - rounds %d-%d" % (first, last))
    print("=" * 70)

    managers = sorted(history[str(rounds[0])])
    total_changes = total_chances = 0

    for mgr in managers:
        print("\n  %s" % mgr)
        previous = None
        for r in rounds:
            squad = history.get(str(r), {}).get(mgr) or []
            k = captain(squad)
            if not k:
                print("    %2d. no captain in the stored squad" % r)
                previous = None
                continue
            # The best choice from the same squad, in hindsight.
            field = sorted(squad, key=lambda p: -base(p))
            best = field[0] if field else None
            mark = ""
            if previous is not None:
                total_chances += 1
                if k["name"] != previous:
                    mark = "  << CHANGED (instead of %s)" % previous
                    total_changes += 1
                else:
                    mark = "  (kept)"
            print("    %2d. %-26s %5.2f -> doubled %5.2f   best would have been: "
                  "%-24s %5.2f%s"
                  % (r, k["name"], base(k), base(k) * 2,
                     best["name"] if best else "-",
                     base(best) if best else 0, mark))
            previous = k["name"]

    print("\n" + "-" * 70)
    print("  chances to reconsider: %d, of which changes: %d"
          % (total_chances, total_changes))

    # Whom the armband went to per round - the size of the herd.
    print("\n  ARMBAND WEARERS PER ROUND")
    for r in rounds:
        counter = {}
        for mgr, squad in (history.get(str(r)) or {}).items():
            k = captain(squad)
            if k:
                counter.setdefault(k["name"], []).append((mgr, base(k)))
        rows = sorted(counter.items(), key=lambda kv: -len(kv[1]))
        print("    round %2d:" % r)
        for name, entries in rows:
            print("        %-26s %dx  %5.2f  (%s)"
                  % (name, len(entries), entries[0][1],
                     ", ".join(m for m, _ in entries)))

    # The lever's yield: what the doubling gave, and what it could have given.
    print("\n  YIELD OF THE DOUBLING PER MANAGER (%d-%d.)" % (first, last))
    for mgr in managers:
        gained = missed = 0.0
        for r in rounds:
            squad = history.get(str(r), {}).get(mgr) or []
            k = captain(squad)
            if not k:
                continue
            best = max((base(p) for p in squad), default=0)
            gained += base(k)
            missed += best - base(k)
        print("    %-14s the armband brought +%.2f; with the squad's best it "
              "would have been +%.2f (missed %.2f)"
              % (mgr, gained, gained + missed, missed))
    return 0


if __name__ == "__main__":
    sys.exit(main())
