#!/usr/bin/env python3
"""The Draft bench layer: how much scoring stayed out, and how much of it counted.

WHY IT IS NEEDED: the Draft has no captain, no shared player and no budget -
the manager's only weekly decision is the starting eleven. What the field
does with that decision does not show in a single round; across several
rounds it is measurable.

THREE SEPARATE NUMBERS that are easy to mix up:
  - the score left on the bench: the sum of every bench player. The upper
    bound, not the lever - four men cannot be fielded in eleven places.
  - the surplus a perfect line-up would have won: the difference between the
    best possible VALID starting eleven and the one actually fielded. THIS is
    the real lever. Valid: exactly 1 goalkeeper, 3-5 defenders, 2-5
    midfielders, 1-3 forwards - a goalkeeper on the bench cannot be fielded
    in place of a weak forward, so a pairing that ignores positions would lie
    upwards.
  - the deciding case: the match where the score left on the bench alone
    was more than the margin of the defeat.

FROM WHAT: draft_history.json (squad per round, `b` = sat on the bench,
`pts`), draft.json (fixtures, team names), draft_players.json (positions).
Our own data, no external request.

USAGE: python3 naplo/bench-harvest.py
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(name):
    with open(os.path.join(ROOT, name), encoding="utf-8") as fh:
        return json.load(fh)


# The limits of a valid formation (FPL Draft): the number of goalkeepers is
# fixed, the outfield positions are ranges. Without them every number would
# drift upwards.
LIMITS = {"GKP": (1, 1), "DEF": (3, 5), "MID": (2, 5), "FWD": (1, 3)}
STARTERS = 11


def formations():
    """Every valid split from 1-3-2-1 ... 1-5-5-3 that adds up to eleven."""
    out = []
    for d in range(LIMITS["DEF"][0], LIMITS["DEF"][1] + 1):
        for m in range(LIMITS["MID"][0], LIMITS["MID"][1] + 1):
            for f in range(LIMITS["FWD"][0], LIMITS["FWD"][1] + 1):
                if 1 + d + m + f == STARTERS:
                    out.append({"GKP": 1, "DEF": d, "MID": m, "FWD": f})
    return out


FORMATIONS = formations()


def best_eleven(squad, position):
    """The score of the best VALID eleven that can be fielded from the squad.

    The best per position can be sorted up front, so for every formation it
    is enough to add up the first n, and take the best of the formations.
    """
    by_pos = {}
    for p in squad:
        by_pos.setdefault(position(p), []).append(p["pts"])
    for pts in by_pos.values():
        pts.sort(reverse=True)
    best = None
    for f in FORMATIONS:
        if any(len(by_pos.get(pos, [])) < n for pos, n in f.items()):
            continue
        total = sum(sum(by_pos[pos][:n]) for pos, n in f.items())
        if best is None or total > best:
            best = total
    return best


def surplus(squad, position):
    """How much more the squad would have scored with the best possible eleven."""
    actual = sum(p["pts"] for p in squad if not p["b"])
    possible = best_eleven(squad, position)
    return 0 if possible is None else possible - actual


def main():
    history = load("draft_history.json")["rounds"]
    league = load("draft.json")
    players = load("draft_players.json")["players"]
    name = {str(e["id"]): e["name"] for e in league["entries"]}

    def position(p):
        return (players.get(str(p["e"])) or {}).get("p", "MID")

    rounds = sorted(history, key=int)

    print("=" * 70)
    print("DRAFT BENCH LAYER - rounds %s" % ", ".join(rounds))
    print("=" * 70)

    print("\n  PER ROUND")
    total_bench = total_surplus = 0
    for r in rounds:
        bench = sum(p["pts"] for k in history[r].values() for p in k if p["b"])
        sp = sum(surplus(k, position) for k in history[r].values())
        flawless = sum(1 for k in history[r].values()
                       if not surplus(k, position))
        total_bench += bench
        total_surplus += sp
        print("    round %2s: on the bench %3d, with a better line-up +%3d, "
              "flawless squads %d/%d" % (r, bench, sp, flawless, len(history[r])))
    print("    TOTAL:     on the bench %3d, with a better line-up +%3d"
          % (total_bench, total_surplus))

    print("\n  PER MANAGER")
    per_team = {}
    for r in rounds:
        for team, squad in history[r].items():
            a = per_team.setdefault(team, [0, 0])
            a[0] += sum(p["pts"] for p in squad if p["b"])
            a[1] += surplus(squad, position)
    for team, (bench, sp) in sorted(per_team.items(), key=lambda kv: -kv[1][0]):
        print("    %-24s on the bench %3d, with a better line-up +%3d"
              % (name.get(team, team), bench, sp))

    print("\n  HOW MANY BENCH PLAYERS PLAYED AT ALL")
    print("  (a clean bench can be attention, and it can be an empty squad -")
    print("   if the bench player does not come on, there was nothing to leave out)")
    for team in sorted(per_team, key=lambda c: -per_team[c][0]):
        benched = played = 0
        for r in rounds:
            for p in history[r][team]:
                if p["b"]:
                    benched += 1
                    played += 1 if p["pts"] > 0 else 0
        print("    %-24s %2d/%2d came on, bench score %3d, with a better line-up +%3d"
              % (name.get(team, team), played, benched, per_team[team][0], per_team[team][1]))

    print("\n  WHAT A TEAM'S OWN BENCH WON FOR THE OPPONENT")
    print("  (with a valid line-up the defeat could have been avoided)")
    for r in rounds:
        bench = {team: surplus(k, position) for team, k in history[r].items()}
        for a, b, pa, pb in league["schedule"][r]:
            for own, opp, own_pts, opp_pts in ((a, b, pa, pb), (b, a, pb, pa)):
                margin = opp_pts - own_pts
                if margin > 0 and bench.get(str(own), 0) >= margin:
                    print("    %2s. %-22s %2d:%-2d %-22s  short by %2d, "
                          "the squad held +%2d" % (r, name[str(own)], own_pts, opp_pts,
                                                   name[str(opp)], margin,
                                                   bench[str(own)]))

    print("\n  THE BIGGEST SINGLE SCORES FORGOTTEN ON THE BENCH")
    entries = []
    for r in rounds:
        for team, squad in history[r].items():
            for p in squad:
                if p["b"]:
                    j = players.get(str(p["e"])) or {}
                    entries.append((p["pts"], int(r), name[str(team)],
                                    "%s (%s)" % (j.get("n", "?"), j.get("t", "?"))))
    for pts, r, team, j in sorted(entries, reverse=True)[:10]:
        print("    round %2d  %2d  %-24s %s" % (r, pts, team, j))
    return 0


if __name__ == "__main__":
    sys.exit(main())
