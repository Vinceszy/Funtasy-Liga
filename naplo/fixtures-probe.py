#!/usr/bin/env python3
"""The real NB I programme of one round, from published schedule pages.

WHY: a preview needs who plays whom in the coming round, and the fantasy API
serves no future matches (naplo/mlsz-player-list.txt). The programme is
published on news and club sites, and the development environment cannot
reach them - so this runs from Actions and prints, for every page, the text
that follows each mention of the round. Two independent pages that agree
pair by pair are what naplo/nb1-fixtures-<round>.txt records.

Environment (from Actions through the workflow's `environment` input):

  PROBE_URLS   comma-separated page addresses (required)
  PROBE_ROUND  the round number (default 11)
  PROBE_CHARS  how much text to print after each mention (default 1200)

The page text goes to STANDARD OUTPUT ONLY, so it stays in the run log; the
log file gets the addresses, the status and the number of mentions.
"""
import html
import os
import re
import sys
import time
import urllib.error
import urllib.request

AGENT = "FunTasy-probe (github.com/Vinceszy/Funtasy-Liga)"
LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures-probe.txt")
URLS = [u.strip() for u in (os.environ.get("PROBE_URLS") or "").split(",") if u.strip()]
ROUND = int(os.environ.get("PROBE_ROUND") or "11")
CHARS = int(os.environ.get("PROBE_CHARS") or "1200")


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": AGENT})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception as e:
        return "error: %s" % e.__class__.__name__, ""


def text_of(page):
    page = re.sub(r"(?is)<(script|style|noscript)\b.*?</\1>", " ", page)
    page = re.sub(r"(?i)<br\s*/?>|</(p|li|tr|h\d|div)>", "\n", page)
    page = html.unescape(re.sub(r"<[^>]+>", " ", page))
    return re.sub(r"[ \t\r\f\v]+", " ", page)


def main():
    if not URLS:
        sys.exit("PROBE_URLS is empty")
    mention = re.compile(r"\b%d\s*\.\s*fordul" % ROUND, re.I)
    log = ["", "=" * 70,
           "PROBE: %s | NB I round %d programme" % (time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()), ROUND)]
    for url in URLS:
        code, page = fetch(url)
        text = text_of(page)
        hits = [m.start() for m in mention.finditer(text)]
        log.append("  %s  HTTP %s, %d mentions of round %d" % (url, code, len(hits), ROUND))
        print("\n### %s  (HTTP %s, %d mentions)" % (url, code, len(hits)))
        for h in hits[:4]:
            print("--- at %d ---" % h)
            print(re.sub(r"\n\s*\n+", "\n", text[h:h + CHARS]).strip())
        time.sleep(1)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write("\n".join(log) + "\n")
    print("\n".join(log))
    return 0


if __name__ == "__main__":
    sys.exit(main())
