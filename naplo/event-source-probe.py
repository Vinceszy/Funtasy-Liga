#!/usr/bin/env python3
"""Probe of an external source of match events: is there a GOAL MINUTE, and how detailed.

WHY: our own data (MLSZ/FPL) gives a SUM per event, no time - the minute of a
goal and the MANNER of a goal can only come from an external source. The
development environment's network blocks every external source, so the
probe runs on the GitHub runner.

What it measures, for two leagues (English top flight and Hungarian top
flight):
  1. whether the source is reachable at all for that league
  2. whether it gives a MINUTE for the events
  3. how DETAILED: only "Goal", or "Penalty" / "Own Goal" / header etc.
  4. in what name form it gives the player (it has to be matched to our
     own squads)

No key needed (the api-football part runs only when APIFOOTBALL_KEY is set).
The result goes into naplo/event-source.txt.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer"
LEAGUES = [("english top flight", "eng.1"), ("hungarian top flight", "hun.1")]
LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "event-source.txt")
HEADERS = {"Accept": "application/json", "User-Agent": "FunTasy-probe"}


def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            return resp.status, resp.read().decode("utf-8", "replace"), int((time.time() - t0) * 1000)
    except urllib.error.HTTPError as e:
        return e.code, "", int((time.time() - t0) * 1000)
    except Exception as e:                                   # noqa: BLE001
        return 0, "%s: %s" % (type(e).__name__, e), int((time.time() - t0) * 1000)


def fetch_json(url):
    code, body, ms = fetch(url)
    if code != 200:
        return None, code, ms
    try:
        return json.loads(body), code, ms
    except ValueError:
        return None, code, ms


def probe_league(name, slug, lines):
    lines.append("")
    lines.append("--- %s (%s) ---" % (name, slug))
    # the schedule of a PAST day: search backwards until a finished match turns up
    event_id = day = None
    codes = set()
    for days_back in range(1, 15):
        d = time.strftime("%Y%m%d", time.gmtime(time.time() - days_back * 86400))
        j, code, ms = fetch_json("%s/%s/scoreboard?dates=%s" % (BASE, slug, d))
        codes.add(code)
        if j is None:
            lines.append("  scoreboard %s: HTTP %s (%d ms)" % (d, code, ms))
            if code in (0, 404):
                return
            continue
        for e in j.get("events") or []:
            state = (((e.get("status") or {}).get("type") or {}).get("state"))
            if state == "post":
                event_id, day = e.get("id"), d
                lines.append("  found a finished match: %s (%s), id=%s"
                             % (e.get("name"), d, event_id))
                break
        if event_id:
            break
    if not event_id:
        # A 403 is a REFUSAL, not an absence: the source does not let us in
        # (typically from a data-centre IP). That has to be said apart from
        # the "no such league" case, otherwise the probe records a wrong
        # conclusion.
        if 403 in codes:
            lines.append("  THE SOURCE REFUSES (HTTP 403) - this is access, not"
                         " missing data; nothing has been established about this league")
        else:
            lines.append("  no finished match found going back 14 days"
                         " (response codes received: %s)"
                         % ", ".join(str(k) for k in sorted(codes)))
        return

    j, code, ms = fetch_json("%s/%s/summary?event=%s" % (BASE, slug, event_id))
    if j is None:
        lines.append("  summary: HTTP %s (%d ms) - no event data" % (code, ms))
        return
    lines.append("  summary: HTTP 200 (%d ms), top-level keys: %s"
                 % (ms, ", ".join(sorted(j.keys()))))
    key_events = j.get("keyEvents") or []
    lines.append("  keyEvents: %d items" % len(key_events))
    if not key_events:
        lines.append("  ! no event list - this source gives no goal minute this way")
        return
    lines.append("  fields of one item: %s" % ", ".join(sorted(key_events[0].keys())))
    for e in key_events[:8]:
        clock = (e.get("clock") or {}).get("displayValue")
        kind = (e.get("type") or {}).get("text")
        who = ", ".join((x.get("athlete") or {}).get("displayName", "?")
                        for x in (e.get("participants") or [])) or "-"
        lines.append("    %-7s | %-22s | %s | %s"
                     % (clock, kind, who, (e.get("text") or "")[:70]))
    kinds = sorted({(e.get("type") or {}).get("text") or "?" for e in key_events})
    lines.append("  types occurring: %s" % ", ".join(kinds))


# --- second keyless source (thesportsdb, with its public test key) ---
TSDB = "https://www.thesportsdb.com/api/v1/json/123"


def probe_tsdb(lines):
    for country, name in (("England", "english top flight"),
                          ("Hungary", "hungarian top flight")):
        lines.append("")
        lines.append("--- %s (thesportsdb, %s) ---" % (name, country))
        j, code, ms = fetch_json("%s/search_all_leagues.php?c=%s&s=Soccer" % (TSDB, country))
        if j is None:
            lines.append("  league search: HTTP %s (%d ms)" % (code, ms))
            continue
        leagues = [x for x in (j.get("countries") or []) if x.get("idLeague")]
        if not leagues:
            lines.append("  no league for this country")
            continue
        # The league is chosen by its EXACT name. A partial match will not do:
        # the word "Premier" also matches the English fifth-tier Isthmian
        # League Premier Division, and the probe then measures a different
        # league from the one in its header.
        EXPECTED = {"England": "English Premier League", "Hungary": "Hungarian NB I"}
        first = next((x for x in leagues if (x.get("strLeague") or "") == EXPECTED[country]), None)
        if first is None:
            lines.append("  the expected league (%s) is missing; hits: %s"
                         % (EXPECTED[country],
                            ", ".join((x.get("strLeague") or "?") for x in leagues)))
            continue
        lid, lname = first["idLeague"], first.get("strLeague")
        lines.append("  league: %s (id=%s) | all hits: %d" % (lname, lid, len(leagues)))
        j2, code2, _ = fetch_json("%s/eventspastleague.php?id=%s" % (TSDB, lid))
        past = (j2 or {}).get("events") or []
        if not past:
            lines.append("  eventspastleague: HTTP %s, no finished match" % code2)
            continue
        e = past[0]
        lines.append("  last match: %s (%s), id=%s"
                     % (e.get("strEvent"), e.get("dateEvent"), e.get("idEvent")))
        j3, code3, _ = fetch_json("%s/lookuptimeline.php?id=%s" % (TSDB, e.get("idEvent")))
        tl = (j3 or {}).get("timeline")
        if not tl:
            lines.append("  lookuptimeline: HTTP %s, empty timeline"
                         " - this source gives no goal minute for this league" % code3)
            continue
        lines.append("  timeline: %d items | fields: %s"
                     % (len(tl), ", ".join(sorted(tl[0].keys()))))
        for x in tl[:10]:
            lines.append("    %3s' | %-14s | %-16s | %s"
                         % (x.get("intTime"), x.get("strTimeline"),
                            x.get("strTimelineDetail"), x.get("strPlayer")))
        lines.append("  types occurring: %s"
                     % ", ".join(sorted({str(x.get("strTimeline")) for x in tl})))
        lines.append("  details occurring: %s"
                     % ", ".join(sorted({str(x.get("strTimelineDetail")) for x in tl})))


# --- keyed source (api-football): only if the secret is set ---
AF_BASE = "https://v3.football.api-sports.io"
AF_LEAGUES = [("english top flight", 39), ("hungarian top flight", 271)]
# The free plan does not serve the current season, only 2022-2024.
FALLBACK_SEASON = 2024


def probe_af(lines):
    key = os.environ.get("APIFOOTBALL_KEY") or ""
    if not key:
        lines.append("")
        lines.append("--- keyed source: SKIPPED (no APIFOOTBALL_KEY secret) ---")
        return
    headers = {"x-apisports-key": key, "Accept": "application/json"}
    season = time.gmtime().tm_year - (1 if time.gmtime().tm_mon < 7 else 0)
    for name, lid in AF_LEAGUES:
        lines.append("")
        lines.append("--- %s (api-football league=%d, season=%d) ---" % (name, lid, season))
        req = urllib.request.Request(
            "%s/fixtures?league=%d&season=%d" % (AF_BASE, lid, season), headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                j = json.loads(resp.read().decode("utf-8", "replace"))
        except Exception as e:                               # noqa: BLE001
            lines.append("  fixtures: %s: %s" % (type(e).__name__, e))
            continue
        errors = j.get("errors")
        if errors:
            lines.append("  fixtures error: %s" % json.dumps(errors, ensure_ascii=False))
            # The plan may exclude the CURRENT season, but the structure can be
            # inspected on an older one - that shows what the paid version
            # would be worth. Both the error and the fallback are recorded.
            if not any("plan" in h for h in errors):
                continue
            season = FALLBACK_SEASON
            lines.append("  -> retrying with an allowed season: %d" % season)
            req = urllib.request.Request(
                "%s/fixtures?league=%d&season=%d" % (AF_BASE, lid, season),
                headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=25) as resp:
                    j = json.loads(resp.read().decode("utf-8", "replace"))
            except Exception as e:                           # noqa: BLE001
                lines.append("  fixtures: %s: %s" % (type(e).__name__, e))
                continue
            if j.get("errors"):
                lines.append("  fixtures error (%d): %s"
                             % (season, json.dumps(j["errors"], ensure_ascii=False)))
                continue
        resp_list = j.get("response") or []
        if not resp_list:
            lines.append("  no played match in the response - the league is not available"
                         " on this plan")
            continue
        finished = [x for x in resp_list
                    if (((x.get("fixture") or {}).get("status") or {}).get("short")) == "FT"]
        lines.append("  %d matches in the season, played: %d" % (len(resp_list), len(finished)))
        if not finished:
            lines.append("  no played match in the response")
            continue
        fx = finished[0]["fixture"]
        teams = finished[0]["teams"]
        lines.append("  last match: %s - %s (id=%s)"
                     % (teams["home"]["name"], teams["away"]["name"], fx["id"]))
        req2 = urllib.request.Request("%s/fixtures/events?fixture=%s" % (AF_BASE, fx["id"]),
                                      headers=headers)
        try:
            with urllib.request.urlopen(req2, timeout=25) as resp:
                j2 = json.loads(resp.read().decode("utf-8", "replace"))
        except Exception as e:                               # noqa: BLE001
            lines.append("  events: %s: %s" % (type(e).__name__, e))
            continue
        ev = j2.get("response") or []
        lines.append("  events: %d items" % len(ev))
        for e in ev[:10]:
            lines.append("    %3s' | %-12s | %-14s | %s"
                         % ((e.get("time") or {}).get("elapsed"), e.get("type"),
                            e.get("detail"), ((e.get("player") or {}).get("name"))))
        lines.append("  details occurring: %s"
                     % ", ".join(sorted({str(e.get("detail")) for e in ev})))


def main():
    lines = ["", "=" * 70,
             "PROBE: %s UTC" % time.strftime("%Y-%m-%d %H:%M")]
    lines.append("")
    lines.append("### keyless source (ESPN)")
    for name, slug in LEAGUES:
        probe_league(name, slug, lines)
    lines.append("")
    lines.append("### second keyless source (thesportsdb)")
    probe_tsdb(lines)
    lines.append("")
    lines.append("### keyed source (api-football)")
    probe_af(lines)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
