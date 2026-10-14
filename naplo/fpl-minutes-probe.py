#!/usr/bin/env python3
"""ONE-OFF probe: how do the MINUTES behave during a live match?

This prepares the "who is still on the pitch" feature. Three questions:
  1) Does a substituted player's minute count really FREEZE while the match
     clock keeps ticking? (That becomes the "substituted" flag.)
  2) How large is the LAG between the two endpoints? live (player minutes)
     and fixtures (match clock) are two separate requests; if the server does
     not refresh them together, a player on the pitch can look substituted
     for a moment. This decides how large a tolerance is needed.
  3) Are a substitute's minutes really counted from when he came on?

Already known: the match clock stops at 45 and at 90.

Every sample is written, not only the changes: here the course over time is
exactly what matters. Reads only; the workflow commits the result.

The sample line keeps the format of the records already in the log (mora =
match clock, allas = score, fp/f = finished_provisional/finished, dt = ms
between the two requests, players as <id>:<minutes>[k=starter, b=substitute,
R=red card]), so the file reads as one series.
"""
import datetime, json, os, sys, urllib.request

HDRS = {"Accept": "application/json", "User-Agent": "Mozilla/5.0 funtasy-percmeres/1.0"}
LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fpl-minutes.txt")


def get(url, timeout=30):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=HDRS), timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return {"__error": "%s: %s" % (type(e).__name__, e)}


now = datetime.datetime.now(datetime.timezone.utc)
game = get("https://draft.premierleague.com/api/game")
gw = game.get("current_event")
if not gw:
    sys.exit(0)

# The two endpoints are requested ONE AFTER THE OTHER, as close as possible:
# the time between them is the probe's margin of error, so it is written too.
t0 = datetime.datetime.now(datetime.timezone.utc)
t0 = datetime.datetime.now(datetime.timezone.utc)
fx = get("https://draft.premierleague.com/api/event/%d/fixtures" % gw)
t1 = datetime.datetime.now(datetime.timezone.utc)
live = get("https://draft.premierleague.com/api/event/%d/live" % gw)
t2 = datetime.datetime.now(datetime.timezone.utc)
if not isinstance(fx, list) or "__error" in live:
    sys.exit(0)

# only the match(es) in progress matter
live_matches = [m for m in fx if m.get("started") and not m.get("finished")]
if not live_matches:
    sys.exit(0)

# player -> club from the list in the repository (no new request needed)
data = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   "..", "draft_players.json"), encoding="utf-8"))
CLUB = {int(k): v["t"] for k, v in data["players"].items()}
TEAM = {int(k): v for k, v in data["teams"].items()}
el = live.get("elements") or {}


def st(eid):
    return ((el.get(str(eid)) or el.get(eid) or {}).get("stats") or {})


new_file = not os.path.exists(LOG)
with open(LOG, "a", encoding="utf-8") as f:
    if new_file:
        f.write("# Live match minute probe. Every sample is one line (UTC).\n"
                "# mora = the match clock | dt = ms between the two endpoint requests\n"
                "# player: <id>:<minutes>[k=starter, b=substitute, R=red card]\n")
        # Which statistics does FPL know at all? If "starts" is listed here,
        # it is likely to appear in the explain somewhere too - if not, in a
        # double round it cannot be told per match.
        bs = get("https://draft.premierleague.com/api/bootstrap-static")
        f.write("# element_stats: %s\n"
                % json.dumps(bs.get("element_stats"), ensure_ascii=False)[:800])
        # The match's own stats array: is there anything starter/substitute-like in it?
        for m in live_matches:
            f.write("# match stats identifiers: %s\n"
                    % [x.get("s") or x.get("identifier") for x in (m.get("stats") or [])])
            break
        # The explain of one starter and one substitute is written RAW, once.
        # This is needed to plan for the double round: the explain comes split
        # by match, and the question is whether "starts" is in it. If only
        # the point-scoring items are there, then in a double round we cannot
        # tell per match whether he started - only that he started one of
        # the two.
        for m in live_matches:
            h2, a2 = TEAM.get(m.get("team_h"), "?"), TEAM.get(m.get("team_a"), "?")
            sample = [e for e, k in CLUB.items() if k in (h2, a2)]
            starter = next((e for e in sample if (st(e).get("starts") or 0)), None)
            sub = next((e for e in sample
                        if not (st(e).get("starts") or 0) and (st(e).get("minutes") or 0)), None)
            for label, e in (("STARTER", starter), ("SUBSTITUTE", sub)):
                if e is None:
                    continue
                v = el.get(str(e)) or el.get(e) or {}
                f.write("# %s explain (id=%s): %s\n"
                        % (label, e, json.dumps(v.get("explain"), ensure_ascii=False)[:900]))
                f.write("# %s stats.starts=%s minutes=%s\n"
                        % (label, (v.get("stats") or {}).get("starts"),
                           (v.get("stats") or {}).get("minutes")))
    for m in live_matches:
        h, a = TEAM.get(m.get("team_h"), "?"), TEAM.get(m.get("team_a"), "?")
        players = [e for e, club in CLUB.items() if club in (h, a)]
        # only those it concerns at all: a starter, or one who has played
        rows = []
        for e in sorted(players):
            s = st(e)
            minutes, started = s.get("minutes") or 0, s.get("starts") or 0
            if not minutes and not started:
                continue
            mark = "k" if started else "b"
            if s.get("red_cards"):
                mark += "R"
            rows.append("%d:%d%s" % (e, minutes, mark))
        f.write("%s  %s-%s  mora=%s  allas=%s-%s  fp=%s f=%s  dt=%dms | %s\n" % (
            now.strftime("%H:%M:%S"), h, a, m.get("minutes"),
            m.get("team_h_score"), m.get("team_a_score"),
            1 if m.get("finished_provisional") else 0, 1 if m.get("finished") else 0,
            int((t2 - t0).total_seconds() * 1000), " ".join(rows)))
print("sample recorded (%d live matches)" % len(live_matches))
