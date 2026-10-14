#!/usr/bin/env python3
"""The own layer of the preview of the next Draft round.

WHY A SEPARATE ONE FOR THE PREVIEW: the summary looks at what happened; a
preview may only carry what influences the result of the NEXT round. The two
are not the same data. What speaks forward is the shape of the squad and the
manager's habits - not last week's score.

The Draft has no captain and no shared player, so the levers a manager can
pull are: the starting eleven, the weekly transfers, and the bench - which is
not a reserve but insurance. At the end of the round the machine puts the
first bench player who played in place of a starter who never took the
field. With an empty bench, a starter who misses out is an empty place.

So it prints: how often the machine had to step in so far and what it saved,
how often it could not (because nobody on the bench played either), how many
points were stuck on the bench, what the weekly moves brought, how much
ballast is in the starting eleven, and how much the team depends on a single
man.

Everything comes from our own data, offline.

Usage: python3 naplo/draft-preview-harvest.py [round]
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
    draft = load("draft.json")
    hist = load("draft_history.json")
    done = sorted(int(r) for r in (hist.get("rounds") or {}))
    rnd = int(sys.argv[1]) if len(sys.argv) > 1 else (max(done) + 1 if done else 1)

    name = {e["id"]: e["name"] for e in draft.get("entries", [])}
    standing = {s["id"]: s for s in draft.get("standings", [])}
    players = load("draft_players.json").get("players", {})
    points = load("draft_pontok.json").get("rounds", {})
    closes = load("zarasok.json").get("rounds", {})
    changes = load("draft_keretvaltozasok.json").get("rounds", {})
    fixtures = (draft.get("schedule") or {}).get(str(rnd)) or []
    past = [r for r in done if r < rnd]
    # Minute data is not available for every round (the collector did not
    # save the first round that way). Where it is missing, no starter is
    # counted as not having played - otherwise the whole eleven would look so.
    with_minutes = [r for r in past if str(r) in points]

    def pname(e):
        return (players.get(str(e)) or {}).get("n") or ("#%s" % e)

    def pclub(e):
        return (players.get(str(e)) or {}).get("t") or "?"

    def minutes(r, e):
        return ((points.get(str(r)) or {}).get(str(e)) or [None, None])[1]

    def profile(team):
        p = {"subs": 0, "sub_points": 0, "unfilled": 0, "stuck_on_bench": 0,
             "moves": 0, "guard": 0, "ballast": 0, "starter_count": 0,
             "best": None, "dependence": 0.0, "weeks": []}
        for r in past:
            squad = ((hist.get("rounds") or {}).get(str(r)) or {}).get(str(team)) or []
            starters = [x for x in squad if not x.get("b")]
            bench = [x for x in squad if x.get("b")]
            total = sum(x.get("pts") or 0 for x in starters)
            p["weeks"].append(total)
            p["starter_count"] += len(starters)
            p["ballast"] += sum(1 for x in starters if (x.get("pts") or 0) <= 2)
            z = (closes.get(str(r)) or {}).get(str(team)) or {}
            p["subs"] += len(z.get("be") or [])
            p["sub_points"] += sum(x.get("pts") or 0 for x in (z.get("be") or []))
            if r in with_minutes:
                p["unfilled"] += sum(1 for x in starters if not (minutes(r, x["e"]) or 0))
            # The stored bench is the state AFTER THE CLOSE, so what is seen
            # here really stayed out - a man brought on by a substitution is
            # found among the starters. So every round's bench counts.
            p["stuck_on_bench"] += sum(x.get("pts") or 0 for x in bench)
            v = changes.get(str(r), {}).get(str(team)) or {}
            p["moves"] += len(v.get("ki") or []) + len(v.get("be") or [])
            p["guard"] += v.get("guard") or 0
        # whom it depends on: the man with the most points this season, and his share
        per_player = {}
        for r in past:
            for x in ((hist.get("rounds") or {}).get(str(r)) or {}).get(str(team)) or []:
                if not x.get("b"):
                    per_player[x["e"]] = per_player.get(x["e"], 0) + (x.get("pts") or 0)
        if per_player:
            e = max(per_player, key=lambda k: per_player[k])
            p["best"] = (pname(e), pclub(e), per_player[e])
            overall = sum(p["weeks"]) or 1
            p["dependence"] = 100.0 * per_player[e] / overall
        return p

    def current_squad(team):
        """The squad of the LAST closed round - the one it goes into the next with."""
        if not past:
            return [], []
        squad = ((hist.get("rounds") or {}).get(str(past[-1])) or {}).get(str(team)) or []
        return ([x for x in squad if not x.get("b")], [x for x in squad if x.get("b")])

    print("=" * 70)
    print("DRAFT ROUND %d - PREVIEW LAYER (from %d closed rounds)"
          % (rnd, len(past)))
    print("=" * 70)
    for m in fixtures:
        print("")
        print("  %s  -  %s" % (name.get(m[0], m[0]), name.get(m[1], m[1])))
        for team in (m[0], m[1]):
            p, s = profile(team), standing.get(team) or {}
            starters, bench = current_squad(team)
            print("    %-24s place %d, %d pts, %d:%d"
                  % (name.get(team, team), s.get("rank", 0), s.get("total", 0),
                     s.get("for", 0), s.get("against", 0)))
            print("        weekly scores: %s" % " ".join(str(x) for x in p["weeks"]))
            print("        machine stepped in %dx (saved %d pts); unfilled places: %d (of %d rounds)"
                  % (p["subs"], p["sub_points"], p["unfilled"], len(with_minutes)))
            print("        left out on the bench in total: %d pts" % p["stuck_on_bench"])
            print("        squad moves: %d steps, balance %+d" % (p["moves"], p["guard"]))
            if p["starter_count"]:
                print("        ballast: %d%% of the starters finished on two points or fewer"
                      % round(100.0 * p["ballast"] / p["starter_count"]))
            if p["best"]:
                print("        best man: %s (%s) %d pts - %d%% of the total"
                      % (p["best"][0], p["best"][1], p["best"][2],
                         round(p["dependence"])))
            print("        bench now: %s" % ", ".join(
                "%s (%s)" % (pname(x["e"]), pclub(x["e"])) for x in bench) or "empty")
    print("")
    print("  NOTE: this is the squad of the last closed round, NOT of the next one.")
    print("  The weekly transfers are still to come, and the starting eleven can")
    print("  be changed until the round's first kick-off. Of a man on the bench now")
    print("  we know only that his manager has to decide about him.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
