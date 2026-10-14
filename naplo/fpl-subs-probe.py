#!/usr/bin/env python3
"""ONE-OFF probe: what does FPL Draft do with SUBSTITUTIONS at the end of a round?

In FPL the bench order is the substitution order: at the end of the round it
puts in, for a starter who did not play, the first bench player who fits the
formation. Three questions need an answer before the site claims anything
about it:

  1) Does FPL REWRITE the pick's "position" field after the substitution
     (12-15 -> 1-11)? If so, our collector fixes itself as soon as it fetches
     the round again. If not - if it gives them in a separate "subs" list -
     our stored bench flag ("b") stays wrong and needs separate handling.
  2) WHEN does it happen: right after the last match, or at the round's
     close the next morning (from 2026/27 at 09:00 UK)?
  3) Which field says the round is FINALLY closed? That decides how long the
     collector has to keep fetching a round that is already over. Today it
     refreshes only the CURRENT round, so as soon as current_event moves on,
     the closed round freezes - with the state from before the substitution.

Reads only. The workflow commits the log.

PRIVACY: the repository is public, so the log may NEVER contain an entry_id
or a real name. Only the league-internal id (which is in draft.json anyway)
and the player ids go into it.

Environment: DRAFT_LEAGUE_ID, SUBS_GW (the gameweek, default 1).
"""
import datetime, json, os, sys, urllib.request

B = "https://draft.premierleague.com/api/"
CLASSIC = "https://fantasy.premierleague.com/api/"
LEAGUE_ID = os.environ.get("DRAFT_LEAGUE_ID", "48093")
GW = int(os.environ.get("SUBS_GW", "1"))
HDRS = {"Accept": "application/json", "User-Agent": "Mozilla/5.0 funtasy-cseremeres/1.0"}
LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fpl-subs.txt")
# The logged lines keep the format of the records already in the log
# (kezdo=, pad=, 0perces_kezdo=, meccs=..kesz, nincs, valtozatlan): a new block
# is compared with the last one to decide whether anything changed, so a
# different wording would count as a change.


def get(url, timeout=30):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=HDRS), timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return {"__hiba": "%s: %s" % (type(e).__name__, e)}


now = datetime.datetime.now(datetime.timezone.utc)
lines = []


def out(s):
    lines.append(s)


game = get(B + "game")
det = get(B + "league/%s/details" % LEAGUE_ID)
live = get(B + "event/%d/live" % GW)
status = get(CLASSIC + "event-status/")

# ---- round state: EVERY field of game is printed, because the point is to
# find which one signals the final close. It cannot be guessed.
game_line = " ".join("%s=%s" % (k, json.dumps(v, ensure_ascii=False))
                     for k, v in sorted(game.items()) if not isinstance(v, (dict, list)))

# ---- the round's official H2H results (the source of the table)
matches = [m for m in (det.get("matches") or []) if m.get("event") == GW]
finished = sum(1 for m in matches if m.get("finished"))
match_line = "meccs=%d/%d kesz" % (finished, len(matches))

# ---- daily/round close from classic FPL (the bonus flag uses this)
esl = [s for s in (status.get("status") or []) if s.get("event") == GW]
status_line = " ".join("%s/%s" % (s.get("points"), "bonus" if s.get("bonus_added") else "-")
                       for s in esl) or "nincs"

minutes = {}
el = (live or {}).get("elements") or {}
if isinstance(el, dict):
    for k, v in el.items():
        minutes[int(k)] = ((v or {}).get("stats") or {}).get("minutes") or 0
elif isinstance(el, list):
    for v in el:
        minutes[int((v or {}).get("id") or 0)] = ((v or {}).get("stats") or {}).get("minutes") or 0

out("%s  cur=%s  %s  es=%s  %s" % (now.strftime("%m-%d %H:%M:%S"),
    game.get("current_event"), match_line, status_line, game_line))

# ---- squads. entry_id ONLY in memory; the log gets the league-internal id.
entry_to_league = {e.get("entry_id"): e.get("id") for e in (det.get("league_entries") or [])}
keys_printed = False
for eid, lid in sorted(entry_to_league.items(), key=lambda x: (x[1] or 0)):
    if not eid or not lid:
        continue
    ev = get(B + "entry/%d/event/%d" % (eid, GW))
    picks = ev.get("picks") or []
    if not picks:
        out("  L%s  nincs keret (%s)" % (lid, ev.get("__hiba") or "ures"))
        continue
    # The full structure of the response is printed ONCE: this is where a
    # separate "subs" field, unknown today, could turn up.
    if not keys_printed:
        out("  # entry/event kulcsok: %s" % sorted(ev.keys()))
        out("  # pick kulcsok:        %s" % sorted(picks[0].keys()))
        # personal fields must NOT be printed: the repository is public
        FORBIDDEN = {"picks", "entry", "entry_id", "player_first_name",
                     "player_last_name", "name", "player_name"}
        for k, v in sorted(ev.items()):
            if k in FORBIDDEN:
                continue
            out("  # entry.%s = %s" % (k, json.dumps(v, ensure_ascii=False)[:300]))
        keys_printed = True
    ordered = sorted(picks, key=lambda p: p.get("position") or 0)
    starters = [p.get("element") for p in ordered if (p.get("position") or 0) <= 11]
    bench = [p.get("element") for p in ordered if (p.get("position") or 0) > 11]
    # a starter with 0 minutes is the CANDIDATE for substitution - if FPL
    # substitutes, he has to disappear from the starters
    zero_minutes = [e for e in starters if minutes.get(e, 0) == 0]
    out("  L%s  kezdo=%s  pad=%s  0perces_kezdo=%s"
        % (lid, starters, bench, zero_minutes))

new = "\n".join(lines) + "\n"
old = ""
if os.path.exists(LOG):
    with open(LOG, encoding="utf-8") as f:
        old = f.read()

# Written ONLY ON A CHANGE - otherwise the log would hide when something
# happened. The first (timestamped) line is left out of the comparison.
def body(t):
    return "\n".join(l for l in t.strip().split("\n") if not l[:1].isdigit())


last = old.strip().split("\n\n")[-1] if old.strip() else ""
if body(new) == body(last):
    # one sign of life per hour, to show it ran but nothing changed
    if now.minute >= 50:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write("%s  (valtozatlan)\n\n" % now.strftime("%m-%d %H:%M:%S"))
    sys.exit(0)

with open(LOG, "a", encoding="utf-8") as f:
    f.write(new + "\n")
print(new)
