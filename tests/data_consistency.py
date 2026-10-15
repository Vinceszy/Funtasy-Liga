#!/usr/bin/env python3
"""Internal contradictions of the STORED LEAGUE DATA - without network, from the repository.

WHY IT IS NEEDED: the collectors overwrite these files every three hours from
the response of an external API. The collectors' own tests (collector_*.py)
check that the collector processes what it gets correctly; not that the
RESULT makes sense. Half a squad, a vanished captain or the same Draft player
in two squads only means on the page that some odd number shows up - and the
text written from this data silently lies.

The rules are the two games' own rules, not our choices:
  NB1 (salary cap): eight managers, fifteen-player squads, eleven starters,
    exactly one captain - the captain is the only armband in the game.
  Draft: fifteen-player squads, eleven starters, and ONE player in ONE squad -
    the whole point of a draft is that the players are divided up.
If any of these is broken, the data is wrong, not the rule that changed.
"""
import json
import os
import re
import sys
from collections import Counter

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
failures = []
assertions = []


def check(cond, label):
    print(("OK   " if cond else "FAIL ") + label)
    assertions.append(label)
    if not cond:
        failures.append(label)


def J(name):
    with open(os.path.join(ROOT, name), encoding="utf-8") as f:
        return json.load(f)


# ---- NB1: squads ----
problems = []
for r, squads in sorted(J("squad_history.json")["rounds"].items(), key=lambda kv: int(kv[0])):
    if len(squads) != 8:
        problems.append("round %s: %d squads of the eight" % (r, len(squads)))
    for mgr, squad in squads.items():
        starters = [p for p in squad if not p.get("sub")]
        cap = [p for p in starters if p.get("cap")]
        if len(squad) != 15:
            problems.append("%s. %s: %d-player squad" % (r, mgr, len(squad)))
        if len(starters) != 11:
            problems.append("%s. %s: %d starters" % (r, mgr, len(starters)))
        if len(cap) != 1:
            problems.append("%s. %s: %d captains among the starters" % (r, mgr, len(cap)))
check(not problems, "A1: the NB1 squads are complete (15 players, 11 starters, 1 captain)"
      + ("" if not problems else " - " + "; ".join(problems[:3])))

# ---- Draft: squads and the ban on shared players ----
problems = []
for r, squads in sorted(J("draft_history.json")["rounds"].items(), key=lambda kv: int(kv[0])):
    everyone = []
    for team, squad in squads.items():
        starters = [p for p in squad if not p.get("b")]
        if len(squad) != 15:
            problems.append("%s. %s: %d-player squad" % (r, team, len(squad)))
        if len(starters) != 11:
            problems.append("%s. %s: %d starters" % (r, team, len(starters)))
        everyone += [p["e"] for p in squad]
    twice = [e for e, n in Counter(everyone).items() if n > 1]
    if twice:
        problems.append("round %s: %d players in more than one squad" % (r, len(twice)))
check(not problems, "A2: the Draft squads are complete, and a player is in one squad only"
      + ("" if not problems else " - " + "; ".join(problems[:3])))

# ---- NB1 schedule: four matches per round, eight different teams ----
problems = []
for r, matches in J("results.json")["schedule"].items():
    names = [x for m in matches for x in m[:2]]
    if len(matches) != 4:
        problems.append("round %s: %d matches" % (r, len(matches)))
    if len(set(names)) != len(names):
        problems.append("round %s: someone appears twice" % r)
check(not problems, "A3: the NB1 schedule is four matches per round, eight teams"
      + ("" if not problems else " - " + "; ".join(problems[:3])))

# ---- The published articles point to a real head-to-head ----
# A misspelt name or a wrong round does not vanish: the article simply does
# not appear at that match, and only someone looking for it notices.
art = J("articles.json")
res = J("results.json")["schedule"]
dr = J("draft.json")
pl_ids = {e["name"]: str(e["id"]) for e in dr["entries"]}
problems = []
for league, rounds in (art.get("leagues") or {}).items():
    schedule = res if league == "nb1" else dr["schedule"]
    for r, kinds in rounds.items():
        if r not in schedule:
            problems.append("%s %s.: no such round" % (league, r))
            continue
        pairs = {frozenset((str(a), str(b))) for a, b, *_ in schedule[r]}
        for kind, articles in kinds.items():
            for key in articles:
                if kind == "elemzes":
                    # The column belongs to the round, not to a head-to-head:
                    # its key is its own title. It may not contain a vertical
                    # bar, because the page would read two team names from it.
                    if "|" in key:
                        problems.append("%s %s. column: | in the title (%s)" % (league, r, key))
                    continue
                sides = key.split("|")
                if len(sides) != 2:
                    problems.append("%s %s. %s: bad pairing (%s)" % (league, r, kind, key))
                    continue
                if league == "pl":
                    sides = [pl_ids.get(x, "") for x in sides]
                if frozenset(sides) not in pairs:
                    problems.append("%s %s. %s: %s did not play each other"
                                    % (league, r, kind, key))
check(not problems, "A4: every article points to a real head-to-head played in that round"
      + ("" if not problems else " - " + "; ".join(problems[:3])))

# ---- A5: the two squad sources say the same ----
# THE SAME DATA IN TWO PLACES. The match sheet loads the per-round
# keretek/<r>.json (the full history is ~630 KB by the end of the season, and
# one match needs a single round), while the season's players tab and the
# player profile work from squad_history.json. Both come from the same run,
# but they are written out on SEPARATE branches - if one branch is skipped,
# the two views claim different things about the same round, and neither
# shows a broken screen.
_hist = (J("squad_history.json") or {}).get("rounds") or {}
_sdir = os.path.join(ROOT, "keretek")
_files = sorted(f for f in os.listdir(_sdir) if f.endswith(".json")) \
    if os.path.isdir(_sdir) else []
problems = []
for _f in _files:
    _r = _f[:-5]
    _sq = (J(os.path.join("keretek", _f)) or {}).get("squads") or {}
    _h = _hist.get(_r) or {}
    if set(_sq) != set(_h):
        problems.append("%s.: different managers (%d vs %d)" % (_r, len(_sq), len(_h)))
        continue
    for _n in sorted(_sq):
        if json.dumps(_sq[_n], sort_keys=True) != json.dumps(_h[_n], sort_keys=True):
            problems.append("%s. %s's squad differs" % (_r, _n))
check(_files and not problems,
      "A5: the per-round squad file says the same as the full history (%d rounds)"
      % len(_files) + ("" if not problems else " - DIFFERS: " + "; ".join(problems[:3])))

print("\n" + ("All %d assertions passed." % len(assertions) if not failures
              else "%d of %d assertions failed." % (len(failures), len(assertions))))
sys.exit(1 if failures else 0)
