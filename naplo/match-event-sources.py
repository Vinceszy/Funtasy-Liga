#!/usr/bin/env python3
"""Survey of sources that could give per-minute match events for both leagues.

Only three candidates were checked before, which is not enough to conclude
that a paid plan is the only option. This script walks a wider field and
records, for each candidate: what its robots.txt allows, whether it answers
at all, and whether the answer looks like it carries event minutes.

It stores no article text and no response bodies - only status codes, sizes
and structural hints.

Robots handling: the standard library parser fetches robots.txt with its own
default user agent. Sites that reject that agent make the parser report
"everything disallowed", which is its own rejection rather than the site's
rule. This script therefore fetches robots.txt itself and evaluates the
rules for the wildcard group, longest matching rule wins.
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

# (label, what it might cover, url to probe, optional extra headers)
CANDIDATES = [
    ("sofascore", "both", "https://api.sofascore.com/api/v1/sport/football/scheduled-events/"
     + time.strftime("%Y-%m-%d", time.gmtime(time.time() - 86400)), None),
    ("premierleague (pulselive)", "english", "https://footballapi.pulselive.com/football/competitions",
     {"Origin": "https://www.premierleague.com"}),
    ("football-data.org", "english", "https://api.football-data.org/v4/competitions/PL", None),
    ("mlsz adatbank", "hungarian", "https://adatbank.mlsz.hu/", None),
    ("eredmenyek.com", "both", "https://www.eredmenyek.com/", None),
    ("livescore.com", "both", "https://www.livescore.com/en/football/england/premier-league/", None),
    ("fotmob", "both", "https://www.fotmob.com/api/matches?date="
     + time.strftime("%Y%m%d", time.gmtime(time.time() - 86400)), None),
    ("worldfootball.net", "both", "https://www.worldfootball.net/", None),
]
# keys or words that suggest per-minute events are present
HINTS = ("minute", "elapsed", "incident", "\"time\"", "goalscorer", "perc")


def fetch(url, headers=None):
    req = urllib.request.Request(url, headers=dict({"User-Agent": AGENT,
                                                    "Accept": "*/*"}, **(headers or {})))
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.status, r.read().decode("utf-8", "replace"), int((time.time() - t0) * 1000)
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", "replace")[:200]
        except Exception:                                    # noqa: BLE001
            pass
        return e.code, body, int((time.time() - t0) * 1000)
    except Exception as e:                                   # noqa: BLE001
        return 0, "%s: %s" % (type(e).__name__, e), int((time.time() - t0) * 1000)


def robots_verdict(url):
    """(allowed, reason). Wildcard group only; longest matching rule wins."""
    base = "/".join(url.split("/", 3)[:3])
    path = "/" + url.split("/", 3)[3] if url.count("/") > 2 else "/"
    code, body, _ = fetch(base + "/robots.txt")
    if code != 200:
        return None, "robots.txt HTTP %s" % code
    active, rules, agents = False, [], []
    for line in body.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            agents = []
            continue
        if ":" not in line:
            continue
        key, value = (x.strip() for x in line.split(":", 1))
        low = key.lower()
        if low == "user-agent":
            agents.append(value)
            active = "*" in agents
        elif low in ("allow", "disallow") and active and value:
            rules.append((low == "allow", value))
    best = None
    for allow, pattern in rules:
        if path.startswith(pattern) and (best is None or len(pattern) > len(best[1])
                                         or (len(pattern) == len(best[1]) and allow)):
            best = (allow, pattern)
    return (True, "no rule matches") if best is None else (best[0], best[1])


def main():
    out = ["", "=" * 70,
           "SURVEY: %s UTC | per-minute match event sources" % time.strftime("%Y-%m-%d %H:%M")]
    for label, covers, url, headers in CANDIDATES:
        out.append("")
        out.append("--- %s (%s) ---" % (label, covers))
        out.append("  url: %s" % url[:100])
        allowed, why = robots_verdict(url)
        out.append("  robots: %s (%s)" % ({True: "ALLOWS", False: "disallows",
                                           None: "unknown"}[allowed], why))
        if allowed is False:
            out.append("  -> not fetched; the rule is respected")
            continue
        code, body, ms = fetch(url, headers)
        out.append("  request: HTTP %s, %d kb, %d ms" % (code, len(body) // 1024, ms))
        if code != 200:
            if body:
                out.append("  answer: %s" % body.replace("\n", " ")[:120])
            continue
        stripped = body.lstrip()[:1]
        kind = "json" if stripped in "[{" else "html/other"
        found = sorted({h for h in HINTS if h in body.lower()})
        out.append("  body: %s | minute-like keys: %s"
                   % (kind, ", ".join(found) if found else "none"))
        if kind == "json":
            try:
                parsed = json.loads(body)
                if isinstance(parsed, dict):
                    out.append("  top-level keys: %s" % ", ".join(sorted(parsed)[:10]))
            except ValueError:
                pass
    with open(LOG, "a", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
