#!/usr/bin/env python3
"""CONTINUOUS logging of the FPL round state.

Why: from 2026/27 the FPL closes the round ("lockdown") at 09:00 UK on the
day after the last match, and claims there is NO daily close. That is not
taken on trust but checked on the data stream: if there is a daily close
after all, it has to show as one day's fields flipping on their own evening,
not at the end of the round.

What is logged (naplo/fpl-state.txt), one line and ONLY ON A CHANGE:
  - per day: points ("" / l / p / r) and bonus_added
  - per match: - / M (started) / P (finished_provisional) / F (finished)
  - at round level: current_event_finished, processing_status, leagues

The meaning of "points" was read from the source of the Draft frontend:
  {"": empty, l: Live, p: Provisional, r: Confirmed}

This is a temporary observation. Once the answer is in, it can be deleted:
this file and its log; the workflow that runs it is shared and stays.
"""
import datetime, json, os, sys, urllib.request

LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fpl-state.txt")
HDRS = {"Accept": "application/json", "User-Agent": "Mozilla/5.0 funtasy-figyelo/1.0"}


def get(url, timeout=30):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=HDRS), timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return {"__error": "%s: %s" % (type(e).__name__, e)}


game = get("https://draft.premierleague.com/api/game")
gw = game.get("current_event")
status = get("https://fantasy.premierleague.com/api/event-status/")
if not gw or "__error" in status:
    sys.exit(0)          # a network error is not a change of state
fx = get("https://draft.premierleague.com/api/event/%s/fixtures" % gw)

days = " ".join("%s=%s%s" % (n.get("date", "")[5:], n.get("points") or "_",
                             "/Added" if n.get("bonus_added") else "")
                for n in (status.get("status") or []) if isinstance(n, dict))
matches = " ".join("%s%s" % (m.get("id"),
                             "F" if m.get("finished") else
                             ("P" if m.get("finished_provisional") else
                              ("M" if m.get("started") else "-")))
                   for m in (fx if isinstance(fx, list) else []))
# The line format (kesz=, ligak=, " | NAP ", " | MECCS ") is the format of the
# records already in the log, and the previous state is read back from it by
# the " | NAP " marker - it stays as it is, so a new line compares with the
# old ones.
state = "GW%s kesz=%s ps=%s ligak=%r | NAP %s | MECCS %s" % (
    gw, game.get("current_event_finished"), game.get("processing_status"),
    status.get("leagues"), days, matches)

previous = None
if os.path.exists(LOG):
    for line in open(LOG, encoding="utf-8"):
        if " | NAP " in line:
            previous = line.split("  ", 1)[-1].rstrip("\n")
if previous == state:
    sys.exit(0)

header = not os.path.exists(LOG)
with open(LOG, "a", encoding="utf-8") as f:
    if header:
        f.write("# The FPL round state. One line = one CHANGE (UTC).\n"
                "# points: _ = not played yet, l = Live, p = Provisional, r = Confirmed\n"
                "# match:  - = not started, M = running, P = whistle blown, F = finished\n")
    f.write("%s  %s\n" % (datetime.datetime.now(datetime.timezone.utc)
                          .strftime("%Y-%m-%d %H:%M"), state))
print("new state: %s" % state)
