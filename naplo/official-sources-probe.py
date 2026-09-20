#!/usr/bin/env python3
"""Deeper probe of the two official sources that answered in the survey.

The survey showed that the English league's own feed and the Hungarian
federation's data bank both respond from the runner. Those are the sources
worth having: no third-party middleman, and for the Hungarian one the same
federation whose fantasy API the collector already uses.

This probe looks for the endpoints that would carry event minutes. It
records status codes, shapes and discovered endpoint paths - no bodies.
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

AGENT = "FunTasy-survey (github.com/Vinceszy/Funtasy-Liga)"
LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "match-event-sources.txt")
PL_API = "https://footballapi.pulselive.com/football"
PL_HEAD = {"Origin": "https://www.premierleague.com", "Account": "premierleague"}


def fetch(url, headers=None):
    req = urllib.request.Request(url, headers=dict({"User-Agent": AGENT,
                                                    "Accept": "*/*"}, **(headers or {})))
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.status, r.read().decode("utf-8", "replace"), int((time.time() - t0) * 1000)
    except urllib.error.HTTPError as e:
        try:
            return e.code, e.read().decode("utf-8", "replace")[:200], int((time.time() - t0) * 1000)
        except Exception:                                    # noqa: BLE001
            return e.code, "", int((time.time() - t0) * 1000)
    except Exception as e:                                   # noqa: BLE001
        return 0, "%s: %s" % (type(e).__name__, e), int((time.time() - t0) * 1000)


def premier_league(out):
    out.append("")
    out.append("--- english league own feed (pulselive) ---")
    code, body, ms = fetch(PL_API + "/competitions/1/compseasons?pageSize=5", PL_HEAD)
    out.append("  compseasons: HTTP %s (%d ms)" % (code, ms))
    season = None
    if code == 200:
        try:
            content = json.loads(body).get("content") or []
            if content:
                # The id arrives as a float ("841.0"); the query needs the
                # plain integer, otherwise the answer is HTTP 400.
                season = content[0].get("id")
                if isinstance(season, float) or (isinstance(season, str)
                                                 and season.endswith(".0")):
                    season = int(float(season))
                out.append("  newest season: %s (id=%s)"
                           % (content[0].get("label"), season))
        except ValueError:
            pass
    if season is None:
        out.append("  no season id, stopping here")
        return
    url = (PL_API + "/fixtures?comps=1&compSeasons=%s&page=0&pageSize=3"
           "&statuses=C&sort=desc" % season)
    code, body, ms = fetch(url, PL_HEAD)
    out.append("  finished fixtures: HTTP %s (%d ms)" % (code, ms))
    if code != 200:
        out.append("  answer: %s" % body.replace("\n", " ")[:120])
        return
    try:
        items = json.loads(body).get("content") or []
    except ValueError:
        items = []
    if not items:
        out.append("  no fixture in the answer")
        return
    fid = items[0].get("id")
    teams = " - ".join((t.get("team") or {}).get("name", "?") for t in items[0].get("teams") or [])
    out.append("  fixture: %s (id=%s)" % (teams, fid))
    code, body, ms = fetch(PL_API + "/fixtures/%s?altIds=true" % fid, PL_HEAD)
    out.append("  fixture detail: HTTP %s, %d kb (%d ms)" % (code, len(body) // 1024, ms))
    if code != 200:
        return
    try:
        det = json.loads(body)
    except ValueError:
        return
    ev = det.get("events") or []
    out.append("  events: %d | keys: %s"
               % (len(ev), ", ".join(sorted(ev[0])) if ev else "-"))
    for e in ev[:8]:
        out.append("    %-8s | %-18s | %s"
                   % ((e.get("clock") or {}).get("label"), e.get("type"),
                      ((e.get("personId") or e.get("description") or ""))))
    if ev:
        out.append("  event types: %s" % ", ".join(sorted({str(e.get("type")) for e in ev})))


def mlsz(out):
    out.append("")
    out.append("--- hungarian federation data bank ---")
    code, body, ms = fetch("https://adatbank.mlsz.hu/")
    out.append("  root: HTTP %s, %d kb (%d ms)" % (code, len(body) // 1024, ms))
    if code != 200:
        return
    # endpoints referenced by the page itself - discovery, not guessing
    paths = sorted({m for m in re.findall(r'["\'](/[a-zA-Z0-9_\-/]*(?:api|json|ajax|data)'
                                          r'[a-zA-Z0-9_\-/]*)["\']', body)})
    out.append("  api-like paths referenced by the page: %d" % len(paths))
    for p in paths[:12]:
        out.append("    %s" % p[:100])
    scripts = sorted({m for m in re.findall(r'src=["\']([^"\']+\.js[^"\']*)["\']', body)})
    out.append("  scripts: %d (the endpoints usually live in these)" % len(scripts))
    for sc in scripts[:6]:
        out.append("    %s" % sc[:100])


def fotmob(out):
    out.append("")
    out.append("--- fotmob (path retry) ---")
    day = time.strftime("%Y%m%d", time.gmtime(time.time() - 86400))
    for path in ("/api/data/matches?date=" + day, "/api/matches?date=" + day,
                 "/api/data/match?matchId=0"):
        code, body, ms = fetch("https://www.fotmob.com" + path)
        kind = "json" if body.lstrip()[:1] in "[{" else "html/other"
        out.append("  %-34s HTTP %s, %d kb, %s (%d ms)"
                   % (path[:34], code, len(body) // 1024, kind, ms))


def fotmob_events(out):
    out.append("")
    out.append("--- fotmob match events ---")
    day = time.strftime("%Y%m%d", time.gmtime(time.time() - 86400))
    code, body, ms = fetch("https://www.fotmob.com/api/data/matches?date=" + day)
    out.append("  day list: HTTP %s, %d kb (%d ms)" % (code, len(body) // 1024, ms))
    if code != 200:
        return
    try:
        data = json.loads(body)
    except ValueError:
        out.append("  answer is not json")
        return
    wanted, found = ("Premier League", "NB I"), []
    for league in data.get("leagues") or []:
        name = league.get("name") or ""
        if not any(w.lower() in name.lower() for w in wanted):
            continue
        for m in league.get("matches") or []:
            found.append((league.get("ccode"), name, m.get("id")))
    out.append("  matches in the two leagues: %d" % len(found))
    for ccode, name, mid in found[:3]:
        out.append("    %s | %s | id=%s" % (ccode, name, mid))
    if not found:
        names = [(x.get("ccode"), x.get("name")) for x in (data.get("leagues") or [])][:8]
        out.append("  sample of leagues present: %s" % names)
        return
    mid = found[0][2]
    code, body, ms = fetch("https://www.fotmob.com/api/data/matchDetails?matchId=%s" % mid)
    out.append("  match detail: HTTP %s, %d kb (%d ms)" % (code, len(body) // 1024, ms))
    if code != 200:
        return
    try:
        det = json.loads(body)
    except ValueError:
        return
    out.append("  top-level keys: %s" % ", ".join(sorted(det)[:12]))
    events = (((det.get("content") or {}).get("matchFacts") or {}).get("events") or {})
    lst = events.get("events") if isinstance(events, dict) else None
    out.append("  matchFacts.events: %s"
               % ("%d item" % len(lst) if isinstance(lst, list) else type(events).__name__))
    for e in (lst or [])[:8]:
        out.append("    %-6s | %-12s | %s"
                   % (e.get("time"), e.get("type"), (e.get("player") or {}).get("name")
                      if isinstance(e.get("player"), dict) else e.get("nameStr")))
    if lst:
        out.append("  event types: %s" % ", ".join(sorted({str(e.get("type")) for e in lst})))


def mlsz_script(out):
    out.append("")
    out.append("--- hungarian data bank: endpoints inside its own script ---")
    code, body, ms = fetch("https://ada1bank.mlsz.hu/meccs-center/js/adatbank.js")
    out.append("  adatbank.js: HTTP %s, %d kb (%d ms)" % (code, len(body) // 1024, ms))
    if code != 200:
        return
    paths = sorted({m for m in re.findall(r'["\'](/?[a-zA-Z0-9_\-/]*(?:api|json|ajax|get)'
                                          r'[a-zA-Z0-9_\-/]*)["\']', body)})
    out.append("  endpoint-like strings: %d" % len(paths))
    for p in paths[:15]:
        out.append("    %s" % p[:100])


def main():
    out = ["", "=" * 70,
           "PROBE: %s UTC | official sources, deeper" % time.strftime("%Y-%m-%d %H:%M")]
    premier_league(out)
    mlsz(out)
    fotmob_events(out)
    mlsz_script(out)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
