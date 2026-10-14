#!/usr/bin/env python3
"""Whether a match-report source is reachable for both leagues, and whether it may be used.

WHY: the MANNER of a goal (header, bicycle kick) and a disputed decision are
not event data but text. The planned processing extracts a FACT from the
report, and lets it out only if player + minute match an event already known
from the structured source.

This probe does NOT collect text. It measures:
  1. what robots.txt says - whether the article page may be requested at all
  2. whether the source is reachable from the runner (HTTP code, size,
     response time)
  3. whether the response contains a minute-like pattern at all (e.g. "63.")

ONLY these numbers go into the log, never the article text - taking the text
over would be a different question from using a fact extracted from it.
"""
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser

AGENT = "FunTasy-probe (github.com/Vinceszy/Funtasy-Liga)"
LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "report-source.txt")

# (league, label, an existing section or article page)
SOURCES = [
    ("hungarian", "nemzetisport", "https://www.nemzetisport.hu/foci-nb-i"),
    ("hungarian", "m4sport", "https://m4sport.hu/labdarugas/"),
    ("hungarian", "mlsz", "https://www.mlsz.hu/hirek"),
    ("english", "bbc", "https://www.bbc.com/sport/football/premier-league"),
    ("english", "guardian", "https://www.theguardian.com/football/premierleague"),
    ("english", "premierleague", "https://www.premierleague.com/news"),
]
MINUTE = re.compile(r"\b\d{1,2}\+?\d*\s*(?:\.|')\s")


def robots_allows(url):
    r = urllib.parse.urlparse(url)
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url("%s://%s/robots.txt" % (r.scheme, r.netloc))
    try:
        rp.read()
    except Exception as e:                                   # noqa: BLE001
        return None, "robots.txt not readable (%s)" % type(e).__name__
    return rp.can_fetch(AGENT, url), None


def main():
    lines = ["", "=" * 70,
             "PROBE: %s UTC | availability of report sources" % time.strftime("%Y-%m-%d %H:%M")]
    for league, label, url in SOURCES:
        lines.append("")
        lines.append("--- %s | %s ---" % (league, label))
        lines.append("  url: %s" % url)
        allowed, error = robots_allows(url)
        if error:
            lines.append("  robots.txt: %s" % error)
        else:
            lines.append("  robots.txt: %s" % ("ALLOWS" if allowed else "DISALLOWS"))
        if allowed is False:
            lines.append("  -> not requested; the disallow is respected")
            continue
        req = urllib.request.Request(url, headers={"User-Agent": AGENT,
                                                   "Accept": "text/html"})
        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                body = resp.read().decode("utf-8", "replace")
                code = resp.status
        except urllib.error.HTTPError as e:
            lines.append("  request: HTTP %s (%d ms)" % (e.code, int((time.time() - t0) * 1000)))
            continue
        except Exception as e:                               # noqa: BLE001
            lines.append("  request: %s: %s" % (type(e).__name__, e))
            continue
        ms = int((time.time() - t0) * 1000)
        lines.append("  request: HTTP %d, %d kbytes, %d ms" % (code, len(body) // 1024, ms))
        lines.append("  minute-like patterns in the response: %d" % len(MINUTE.findall(body)))
    with open(LOG, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
