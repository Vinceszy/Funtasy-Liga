#!/usr/bin/env python3
"""The draft itself, stored once: who chose whom, when, and in which round.

The draft happened once and never changes, so this is not collector work -
it runs by hand and writes draft_picks.json.

TWO IDS. The choices name a team by its FPL entry id; everything we store
uses the league-entry id. The mapping is in the league details, and the
real entry id never reaches the file - that is the same id the collector
refuses to write, because the repository is public.

NAMES DO NOT GO IN EITHER. The response carries real player and manager
names; only ids, round, pick, whether the clock made the choice, and how
long it took come out.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

B = "https://draft.premierleague.com/api/"
HDRS = {"Accept": "application/json", "Accept-Language": "en-GB,en;q=0.9",
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")}
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "draft_picks.json")
FORBIDDEN = ("player_first_name", "player_last_name", "entry_name", "short_name")


def js(path):
    try:
        req = urllib.request.Request(B + path, headers=HDRS)
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception as e:                                   # noqa: BLE001
        print("  ! %s: %s" % (path, e))
        return 0, None


def main():
    league = os.environ.get("LEAGUE_ID") or str(
        json.load(open(os.path.join(ROOT, "draft.json"), encoding="utf-8"))
        .get("league", {}).get("id") or "")
    if not league:
        print("no league id"); return 1
    print("league: %s" % league)

    st, det = js("league/%s/details" % league)
    if st != 200 or not det:
        print("league details: HTTP %s - stopping" % st); return 1
    # entry_id (the real team id) -> id (the league_entry we store).
    # The field is called entry_id, not entry - looking for 'entry' ends with
    # an empty mapping. Several names are accepted, and the one that matched
    # is PRINTED: a silent rename then cannot go unnoticed.
    mapping, field = {}, None
    for candidate in ("entry_id", "entry"):
        t = {}
        for e in det.get("league_entries") or []:
            if e.get(candidate) is not None and e.get("id") is not None:
                t[str(e[candidate])] = str(e["id"])
        if t:
            mapping, field = t, candidate
            break
    print("team mapping: %d (field: %s)" % (len(mapping), field))
    if not mapping:
        print("  ! neither field is in the league data; present: %s"
              % ", ".join(sorted((det.get("league_entries") or [{}])[0].keys())))
        return 1

    st, ch = js("draft/%s/choices" % league)
    if st != 200 or not ch:
        print("choices: HTTP %s - stopping" % st); return 1
    choices = ch.get("choices") or []
    print("choices: %d" % len(choices))

    picks, unmatched = [], 0
    for c in choices:
        t = mapping.get(str(c.get("entry")))
        if not t:
            unmatched += 1
            continue
        picks.append({"r": c.get("round"), "p": c.get("pick"), "i": c.get("index"),
                      "e": c.get("element"), "t": t,
                      "auto": bool(c.get("was_auto")),
                      "sec": c.get("seconds_to_pick")})
    picks.sort(key=lambda x: (x["i"] if x["i"] is not None else 0))
    # An unmatched choice is PRINTED: dropped silently, a team's whole draft
    # would vanish, and that could no longer be noticed in the text.
    print("unmatched choices: %d" % unmatched)
    if unmatched:
        print("  ! the team mapping is incomplete - the file is NOT written")
        return 1

    rounds = max([x["r"] for x in picks] or [0])
    teams = len({x["t"] for x in picks})
    print("rounds: %d | teams: %d" % (rounds, teams))
    for t in sorted({x["t"] for x in picks}):
        own = [x for x in picks if x["t"] == t]
        auto = sum(1 for x in own if x["auto"])
        print("   %s: %d choices, by the machine: %d, first pick: overall %d."
              % (t, len(own), auto, min(x["i"] for x in own)))

    content = {"updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               "league": int(league), "rounds": rounds, "picks": picks}
    text = json.dumps(content, ensure_ascii=False, separators=(",", ":"))
    for word in FORBIDDEN:
        if word in text:
            print("ERROR: '%s' in the output - save aborted." % word)
            return 1
    open(OUT, "w", encoding="utf-8").write(text)
    print("written: draft_picks.json (%d bytes)" % len(text))
    return 0


if __name__ == "__main__":
    sys.exit(main())
