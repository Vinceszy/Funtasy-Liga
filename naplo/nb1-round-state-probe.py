#!/usr/bin/env python3
"""What is the state of an NB1 round? - the MLSZ's own answer, not our reading.

The collector writes a round's results only once the squads of that round
can be fetched. Until then every run logs the same two lines: "current
round according to the MLSZ: N" and "squads of round N not available yet
(before the market closes)". The second line is an inference from a 403;
this probe checks whether the inference holds.

It asks four questions and prints each one separately:
  1. what the MLSZ says in the round objects around the round (start_at,
     end_at, is_transfers_closed, closed_transfers_at) - whether the
     transfer market really is still open;
  2. what the squad endpoint returns for EVERY manager (the collector asks
     only ONE and generalises from the answer);
  3. what the ranking shows for the round (whether it has a row at all);
  4. whether the round has matches, and when.

The answer goes to naplo/nb1-round-state.txt, not to the run log: a run log
becomes unreadable within days, and an earlier measurement was lost exactly
that way.

Usage: PROBE_ROUND=<round> python3 naplo/nb1-round-state-probe.py
"""
import json
import os
import sys
import importlib.util

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nb1-round-state.txt")
ROUND = int(os.environ.get("PROBE_ROUND") or "9")

spec = importlib.util.spec_from_file_location("collect", os.path.join(ROOT, "collect.py"))
c = importlib.util.module_from_spec(spec)
sys.modules["collect"] = c
spec.loader.exec_module(c)

lines = []


def out(s=""):
    print(s)
    lines.append(s)


out("=" * 70)
out("PROBE: the state of NB1 round %d according to the MLSZ" % ROUND)
out("time: " + c.stamp())
out("=" * 70)

# ---- 1) the round objects, raw ----
out("")
out("1) COMPETITION + ROUNDS (competitions?include=rounds,current_round)")
st, j = c.api_get(c.ROOT + "competitions?include=rounds,current_round")
out("   HTTP %s" % st)
if st == 200 and isinstance(j, dict):
    comp = next((x for x in (j.get("data") or []) if x.get("id") == c.COMPETITION), None) or {}
    cr = comp.get("current_round") or {}
    out("   current_round: number=%s id=%s" % (cr.get("round_number"), cr.get("id")))
    out("   current_round raw: %s" % json.dumps(cr, ensure_ascii=False))
    out("   fields of the round objects: %s"
        % sorted({k for r in (comp.get("rounds") or []) for k in r}))
    for r in sorted(comp.get("rounds") or [], key=lambda x: x.get("round_number") or 0):
        if ROUND - 2 <= (r.get("round_number") or 0) <= ROUND + 2:
            out("   round %2s: %s" % (r.get("round_number"), json.dumps(r, ensure_ascii=False)))
else:
    out("   unreadable answer")

# ---- 2) the squad endpoint for EVERY manager ----
out("")
out("2) SQUAD ENDPOINT for the previous and this round, EVERY manager")
out("   (the collector asks only the FIRST manager and infers 'before the")
out("    market closes' from a 403 - this shows whether they agree)")
ids = {}
for name, uname in c.MEMBERS.items():
    row = c.rankings(uname)
    if not row:
        out("   ! no ranking data: %s" % name)
        continue
    ids[name] = ((row.get("user_team") or {}).get("user") or {}).get("id")
for r in (ROUND - 1, ROUND):
    for name, uid in ids.items():
        st2, j2 = c.squad(uid, r)
        n = len((j2 or {}).get("data") or []) if isinstance(j2, dict) else 0
        out("   round %s | %-10s -> HTTP %s, %d players" % (r, name, st2, n))

# ---- 3) what the ranking shows for the round ----
out("")
out("3) RANKING round_statistics (is there a row for the round at all)")
for name, uname in c.MEMBERS.items():
    row = c.rankings(uname)
    if not row:
        continue
    stats = (row.get("user_team") or {}).get("round_statistics") or []
    seen = {int(s["round_number"]): s.get("points") for s in stats}
    out("   %-10s rounds: %s" % (name, json.dumps(seen, ensure_ascii=False)))

# ---- 4) the round's matches ----
out("")
out("4) THE MATCHES OF ROUND %d (through the squad endpoint's games branch)" % ROUND)
if ids:
    uid = next(iter(ids.values()))
    st4, j4 = c.squad(uid, ROUND, with_games=True)
    out("   HTTP %s" % st4)
    if st4 == 200 and isinstance(j4, dict):
        games = {}
        for p in j4.get("data") or []:
            for g in (p.get("games") or []):
                games[g.get("id")] = g
        out("   distinct matches: %d" % len(games))
        for g in list(games.values())[:12]:
            out("     %s" % json.dumps({k: g.get(k) for k in
                ("id", "round_number", "start_at", "status", "is_played",
                 "home_score", "away_score")}, ensure_ascii=False))
    else:
        out("   the squad cannot be fetched, so neither can its match list")

out("")
out("=" * 70)
with open(OUT, "a", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
print("\nwritten: %s (%d lines)" % (OUT, len(lines)))
