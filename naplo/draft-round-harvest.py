#!/usr/bin/env python3
"""The fantasy layer of one Draft round, from our own stored data.

The NB1 has had this since the paper started (round-colour-harvest.py); the
Draft did not, so its summaries were written by reading four files by hand.
Everything here comes from the repository - no external source - and it is
the first of the three layers a summary is built from (see round-pipeline.md).

What a Draft round turns on is not what an NB1 round turns on. There is no
captain and no shared player: a footballer belongs to exactly one squad, and
the bench scores nothing by itself. So the levers are the line-up and the
week's waiver and free-agent moves, which is what `guard` measures.

AND THE AUTOMATIC SUBSTITUTION, which is why a bench score is not simply
lost: at the close of the round the FPL replaces every starter who did not
play with the first bench player who did, keeping the formation valid (a
goalkeeper only for a goalkeeper). A big number on the bench therefore
counts whenever a starter stayed in the stands - and until the round is
final, the line-up printed here is the one before those swaps.

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
        done = [int(r) for r in hist.get("rounds", {})]
        rnd = str(max(done)) if done else "1"
    rnd = str(int(rnd))

    name = {e["id"]: e["name"] for e in draft.get("entries", [])}
    players = load("draft_players.json").get("players", {})
    points = (load("draft_pontok.json").get("rounds", {}) or {}).get(rnd, {})
    squads = (hist.get("rounds", {}) or {}).get(rnd, {})
    changes = (load("draft_keretvaltozasok.json").get("rounds", {}) or {}).get(rnd, {})
    # The automatic substitutions CARRIED OUT at the close. The stored squad is
    # the state AFTER the substitution, so it does not show who did not take
    # the field - the substitution cannot be reconstructed from it. Nor do
    # the `szerep` rows of `draft_keretvaltozasok.json` say it: they mark the
    # change against the PREVIOUS round, in which a manager's decision and
    # the substitution at the close look the same.
    close = (load("zarasok.json").get("rounds", {}) or {}).get(rnd, {})
    fixtures = (draft.get("schedule", {}) or {}).get(rnd, [])
    final = int(rnd) in [int(x) for x in (hist.get("veglegesek") or [])]

    def pname(e):
        j = players.get(str(e)) or {}
        return j.get("n") or j.get("name") or ("#%s" % e)

    def pclub(e):
        j = players.get(str(e)) or {}
        return j.get("t") or j.get("team") or "?"

    print("=" * 70)
    print("DRAFT ROUND %s - from our own data%s" % (
        rnd, "" if final else "   [NOT FINAL YET: the bonus may still move]"))
    print("=" * 70)

    for m in fixtures:
        h, v, hp, vp = m[0], m[1], m[2], m[3]
        print("")
        print("  %s %s : %s %s" % (name.get(h, h), hp, vp, name.get(v, v)))
        for team in (h, v):
            squad = squads.get(str(team)) or []
            starters = [p for p in squad if not p.get("b")]
            bench = [p for p in squad if p.get("b")]
            total = sum(p.get("pts") or 0 for p in starters)
            on_bench = sum(p.get("pts") or 0 for p in bench)
            zeros = [p for p in starters if not (p.get("pts") or 0)]
            # The starter the automatic substitution replaces is the one who
            # DID NOT TAKE THE FIELD - not the one on nought points. Nought
            # points can be scored in ninety minutes too, and that earns no
            # substitution.
            minutes = lambda e: (points.get(str(e)) or [None, None])[1]
            not_played = [p for p in starters if (minutes(p["e"]) or 0) == 0]
            bench_played = [p for p in bench if (minutes(p["e"]) or 0) > 0]
            best = max(starters, key=lambda p: p.get("pts") or 0) if starters else None
            best_bench = max(bench, key=lambda p: p.get("pts") or 0) if bench else None
            ch = changes.get(str(team)) or {}
            print("    %-24s starters %s pts | bench %s pts | starters on nought: %d"
                  % (name.get(team, team), total, on_bench, len(zeros)))
            if best:
                print("        best starter: %s (%s) %s" % (
                    pname(best["e"]), pclub(best["e"]), best.get("pts")))
            if best_bench and (best_bench.get("pts") or 0) > 0:
                print("        best on the bench: %s (%s) %s" % (
                    pname(best_bench["e"]), pclub(best_bench["e"]), best_bench.get("pts")))
            zx = close.get(str(team)) or {}
            if zx.get("ki") or zx.get("be"):
                print("        AUTOMATIC SUBSTITUTION AT THE CLOSE (carried out):")
                for x in zx.get("ki") or []:
                    print("          OUT %-22s %-5s did not take the field, %s pts" % (
                        pname(x["e"]), pclub(x["e"]), x.get("pts")))
                for x in zx.get("be") or []:
                    print("          IN  %-22s %-5s %s min, %s pts" % (
                        pname(x["e"]), pclub(x["e"]), minutes(x["e"]), x.get("pts")))
            if not_played:
                # Whoever stayed in after the substitution with nought minutes:
                # there was nobody to replace him with while keeping the
                # formation valid.
                print("        UNFILLED PLACE - still in after the substitution, did not play: %s"
                      % ", ".join("%s (%s)" % (pname(p["e"]), pclub(p["e"]))
                                  for p in not_played))
                print("        who played on the bench: %s"
                      % (", ".join("%s (%s pts)" % (pname(p["e"]), p.get("pts"))
                                   for p in bench_played) or "nobody"))
            elif not (zx.get("be") or []) and best_bench and (best_bench.get("pts") or 0) > 0:
                print("        (no substitution at the close, so the bench points stay there)")
            if ch:
                print("        weekly balance (guard): %s" % ch.get("guard"))
                for x in ch.get("ki") or []:
                    print("          OUT %-22s %-5s pts: %s" % (
                        pname(x["e"]), x.get("sz"), x.get("pont")))
                for x in ch.get("be") or []:
                    print("          IN  %-22s %-5s pts: %s" % (
                        pname(x["e"]), x.get("sz"), x.get("pont")))
                for x in ch.get("szerep") or []:
                    # Against the previous round - NOT necessarily a manager's decision.
                    print("          ROLE %-21s %s -> %s (against the previous round)  pts: %s" % (
                        pname(x["e"]), x.get("szE"), x.get("szU"), x.get("pont")))
            if zeros:
                print("        starters on nought: %s" % ", ".join(
                    "%s (%s)" % (pname(p["e"]), pclub(p["e"])) for p in zeros))
        # In the Draft the two squads have NO overlap - the question is who
        # left how much on the bench, and what the weekly moves brought.
    print("")
    print("  The players' MINUTES and goals: draft_pontok.json (%d players)" % len(points))
    return 0


if __name__ == "__main__":
    sys.exit(main())
