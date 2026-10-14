#!/usr/bin/env python3
"""The transfer layer: who rebuilt, when it was allowed, and what was dropped.

WHY: in the NB1 the number of transfers is one of the game's hard limits -
THREE a week, but UNLIMITED in the winter and the international breaks (from
the official rules, see the main README, "Amit a hivatalos szabalyzat
rogzit"). So a squad cannot be rebuilt at any time: a manager who changes
eleven players is not keener than the rest, he used a round in which it was
possible at all. A round's transfer list on its own is therefore misleading -
without the limit the same number can mean resolve or mere opportunity.

The break round is not guessed, it shows in the GAP: the time between the
previous round's last match and this round's first. In a normal week it is
about seven days; after an international break it opens to three weeks. We
do NOT measure the round's length: for a round still RUNNING the collector
stores only the matches already played, so even a three-week round would
look two days long. The gap lies between two points of the closed past, so
it is stable.

The round's own deadlines (start_at, end_at, closed_transfers_at) are in the
MLSZ round object - we do not collect them (see naplo/nb1-round-state.txt),
so we work from the match days.

SOURCES: squad_history.json and meccsek.json - our own data, no requests.
The stored `week` is the player's FINAL contribution to the round (captain
doubling and bench halving already in; see collect.py squad_total), so the
contributions of the players sold add up directly.

Usage: python3 naplo/transfer-harvest.py [first_round] [last_round]
"""
import json
import os
import sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEEKLY_LIMIT = 3          # weekly transfers allowed by the rules


def load(name):
    with open(os.path.join(ROOT, name), encoding="utf-8") as fh:
        return json.load(fh)


def keyed(squad):
    """The squad keyed by player ID. Not by name: the MLSZ corrects names on
    the way (by round 5 "Artur Horvath" became "Horvath Artur", same ID 1137),
    and pairing by name saw that as two transfers - it showed a round over the
    weekly limit in which nothing happened. The same rule as the difference
    view on the page (see the main README).

    A record without an ID (the oldest ones) stays keyed by name: such a
    record would otherwise stay unpaired, which is worse than the name."""
    return {(p.get("id") if p.get("id") is not None else "name:" + p["name"]): p
            for p in squad}


def captain(squad):
    return next((p["name"] for p in squad if p.get("cap")), None)


def value(squad):
    """The squad's value at the prices of THAT round (the `price` in the
    record), not today's - otherwise a later price rise would rewrite what the
    manager spent at the time."""
    return sum(p.get("price") or 0 for p in squad)


def formation(squad):
    starters = [p for p in squad if not p.get("sub")]
    order = ["K", "H", "KP", "CS"]
    n = {x: sum(1 for p in starters if p.get("pos") == x) for x in order}
    return "-".join(str(n[x]) for x in order)


def match_days(matches, r):
    return sorted(m["start"][:10] for m in (matches.get(str(r)) or []) if m.get("start"))


def gap(matches, prev_r, r):
    """Days between the previous round's LAST match and this round's FIRST.
    None if either side is missing."""
    a, b = match_days(matches, prev_r), match_days(matches, r)
    if not a or not b:
        return None
    x, y = (date(*map(int, d.split("-"))) for d in (a[-1], b[0]))
    return (y - x).days


def main():
    history = load("squad_history.json")["rounds"]
    matches = load("meccsek.json").get("rounds") or {}
    stored = sorted(int(r) for r in history)
    first = int(sys.argv[1]) if len(sys.argv) > 1 else stored[0]
    last = int(sys.argv[2]) if len(sys.argv) > 2 else stored[-1]
    rounds = [r for r in stored if first <= r <= last]
    if len(rounds) < 2:
        print("At least two stored rounds are needed for a comparison.")
        return 1

    print("=" * 72)
    print("NB1 TRANSFER LAYER - rounds %d-%d" % (rounds[0], rounds[-1]))
    print("=" * 72)
    print("Weekly limit %d; unlimited in the winter and international breaks." % WEEKLY_LIMIT)

    for r in rounds[1:]:
        prev_r = rounds[rounds.index(r) - 1]
        r_gap = gap(matches, prev_r, r)
        flag = ""
        if r_gap is not None and r_gap > 10:
            flag = ("  << %d-DAY GAP since the previous round: a break, "
                    "the weekly limit does not bind here" % r_gap)
        print("\n%s" % ("-" * 72))
        print("round %d (previous: %d)%s" % (r, prev_r, flag))
        if r_gap is not None and not flag:
            print("  %d days since the previous round's last match" % r_gap)
        print("%s" % ("-" * 72))

        rows = []
        for mgr in sorted(history[str(r)]):
            new = history[str(r)].get(mgr) or []
            old = history[str(prev_r)].get(mgr) or []
            if not new or not old:
                continue
            nk, ok = keyed(new), keyed(old)
            out = [ok[k] for k in sorted(set(ok) - set(nk), key=lambda k: ok[k]["name"])]
            inn = [nk[k] for k in sorted(set(nk) - set(ok), key=lambda k: nk[k]["name"])]
            rows.append((len(out), mgr, out, inn, old, new))

        for n, mgr, out, inn, old, new in sorted(rows, reverse=True):
            over = "  (OVER the weekly limit: %d)" % (n - WEEKLY_LIMIT) if n > WEEKLY_LIMIT else ""
            print("\n  %-8s %2d transfers%s" % (mgr, n, over))
            print("           squad value %.1f -> %.1f M | starting shape %s -> %s"
                  % (value(old), value(new), formation(old), formation(new)))
            co, cn = captain(old), captain(new)
            if co != cn:
                co_p = next((p for p in old if p.get("cap")), None)
                kept = co_p is not None and keyed([co_p]).popitem()[0] in keyed(new)
                sold = " (and SOLD him)" if co and not kept else ""
                print("           armband: %s -> %s%s" % (co, cn, sold))
            if not n:
                continue
            # What the players sold contributed to the PREVIOUS round - the
            # measure of "what he got rid of". The Hungarian-rule +10 belongs
            # to no player, so it is left out; the line compares with player
            # points only.
            contribution = sum(p.get("week") or 0 for p in out)
            player_points = sum(p.get("week") or 0 for p in old)
            zeros = sum(1 for p in out if not p.get("week"))
            share = (" (%.0f%%)" % (100 * contribution / player_points)) if player_points else ""
            print("           the players sold, in round %d: %.2f of %.2f points%s, "
                  "%d of them on zero"
                  % (prev_r, contribution, player_points, share, zeros))
            print("           SOLD:   " + ", ".join(
                "%s %s" % (p["name"], ("%.2f" % (p.get("week") or 0)).rstrip("0").rstrip("."))
                for p in sorted(out, key=lambda p: -(p.get("week") or 0))))
            print("           BOUGHT: " + ", ".join(p["name"] for p in inn))
    return 0


if __name__ == "__main__":
    sys.exit(main())
