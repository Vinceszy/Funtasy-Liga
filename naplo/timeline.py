#!/usr/bin/env python3
"""A Draft round on a single clock: what happened when, and in which head-to-head.

WHY: the goal minutes are not collected so that every goal can be written up
with the minute it was scored. They are collected so that the round can go
on one timeline - with matches running in parallel, only then is it visible
where a head-to-head turned, and what was happening meanwhile on another
ground.

The kick-off time comes from the colour table (`matches[...]["kickoff"]`,
written there by pl-colour-harvest.py), the minute from the rows under
`claims`. Their sum is the real time of the event; the fifteen minutes of
half-time are added to the second-half minutes, and stoppage-time minutes to
their own minute.

This is an approximation: it does not look for the second, only for whether
two events happened in the same minute on two different grounds.

Usage: python3 naplo/timeline.py <round>
"""
import collections
import datetime
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
HALF_TIME = 15
INTERESTING = ("goal_manner", "goal", "luck", "assist", "disputed", "big_miss")


def load(name):
    with open(os.path.join(ROOT, name), encoding="utf-8") as f:
        return json.load(f)


def real_time(kickoff, minute):
    t = datetime.datetime.strptime(kickoff, "%Y-%m-%dT%H:%M:%SZ")
    p = str(minute).replace(" ", "")
    base = int(p.split("+")[0])
    added = int(p.split("+")[1]) if "+" in p else 0
    return t + datetime.timedelta(minutes=base + added + (HALF_TIME if base > 45 else 0))


def main():
    rnd = sys.argv[1] if len(sys.argv) > 1 else "5"
    colour = json.load(open(os.path.join(HERE, "pl-colour-%s.json" % rnd), encoding="utf-8"))
    matches = colour.get("matches") or {}
    draft = load("draft.json")
    name = {e["id"]: e["name"] for e in draft["entries"]}
    squads = load("draft_history.json")["rounds"][rnd]
    players = load("draft_players.json")["players"]

    owner = {}
    for team, squad in squads.items():
        for x in squad:
            j = players.get(str(x["e"])) or {}
            owner[(j.get("n"), j.get("t"))] = (name[int(team)], "bench" if x.get("b") else "XI")

    opponent = {}
    for m in draft["schedule"][rnd]:
        opponent[name[m[0]]], opponent[name[m[1]]] = name[m[1]], name[m[0]]

    def match_key(match_name):
        if match_name in matches:
            return match_name
        for k in matches:
            h, _, v = k.partition(" - ")
            if match_name.startswith(h) and match_name.endswith(v):
                return k
        return None

    events = []
    for s in colour.get("claims") or []:
        if s.get("tag") not in INTERESTING or not s.get("minute"):
            continue
        k = match_key(s.get("match"))
        who = owner.get((s.get("player"), s.get("club")))
        if not k or not who or not matches[k].get("kickoff"):
            continue
        events.append((real_time(matches[k]["kickoff"], s["minute"]), who[0], who[1],
                       s["player"], s["minute"], s["tag"], s["sentence"], k))
    events.sort()

    head_to_head = collections.defaultdict(list)
    for e in events:
        head_to_head[tuple(sorted((e[1], opponent[e[1]])))].append(e)

    print("=" * 70)
    print("ROUND %s TIMELINE - %d events, %d matches" % (rnd, len(events), len(matches)))
    print("=" * 70)
    for (a, b), rows in head_to_head.items():
        print("")
        print("  %s - %s" % (a, b))
        previous = None
        for t, team, role, player, minute, tag, sentence, match in rows:
            together = " <<< same time" if previous and t == previous else ""
            print("    %s  %-22s %-5s %-15s %4s'  %-12s %s%s" % (
                t.strftime("%a %H:%M"), team, role, player, minute, tag, match, together))
            previous = t
    print("")
    print("  Times are UTC. Two identical timestamps on two different grounds are simultaneous.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
