#!/usr/bin/env python3
"""What kinds of colourful fact does a Nemzeti Sport match report contain?

Style cannot be designed without knowing the palette. A goal scored with a
bicycle kick and a disputed penalty were two examples; there are probably
many more categories - the flow of the match, a goalkeeping error, a debut,
a milestone, the referee, the crowd. This probe pulls a few real reports of
a given round so the categories can be listed.

The extracted text goes to STANDARD OUTPUT ONLY, so it stays in the run log
and never enters the repository. The log file gets the urls and the sizes.

Environment (all optional, from Actions through the workflow's `environment`
input, one NAME=value per line):

  PROBE_MONTH    yyyy/mm of the article urls (default 2026/09). Required in
                 practice: an article is kept only if its url carries this
                 month, so a round in October returns nothing without
                 PROBE_MONTH=2026/10.
  PROBE_SINCE    yyyy-mm-dd; keeps only articles whose sitemap `lastmod` is
                 on or after it - the first day of the round.
  PROBE_LIMIT    how many articles to print (default 6) - the number of
                 matches in the round.
  PROBE_SECTION  the url section (default labdarugo-nb-i).
"""
import os
import re
import sys
import time
import urllib.error
import urllib.request

AGENT = "FunTasy-survey (github.com/Vinceszy/Funtasy-Liga)"
HOST = "https://www.nemzetisport.hu"
LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "report-source.txt")
MONTH = os.environ.get("PROBE_MONTH") or "2026/09"
SECTION = os.environ.get("PROBE_SECTION") or "labdarugo-nb-i"
# The reports of one ROUND are needed, not the start of the month. The
# sitemap's `lastmod` date is the filter, and as many are fetched as there are
# matches - otherwise six articles come from the top of the alphabetical
# list, old rounds among them.
SINCE = os.environ.get("PROBE_SINCE") or ""
LIMIT = int(os.environ.get("PROBE_LIMIT") or "6")


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": AGENT, "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception as e:                                   # noqa: BLE001
        return 0, "%s: %s" % (type(e).__name__, e)


def text_of(html):
    body = re.sub(r"(?is)<(script|style|nav|header|footer)[^>]*>.*?</\1>", " ", html)
    body = re.sub(r"(?s)<[^>]+>", " ", body)
    body = body.replace("&nbsp;", " ").replace("&amp;", "&").replace("&quot;", '"')
    return re.sub(r"\s+", " ", body).strip()


def main():
    out = ["", "=" * 70,
           "PROBE: %s UTC | nemzetisport report content" % time.strftime("%Y-%m-%d %H:%M")]
    code, body = fetch(HOST + "/sitemapindex.xml")
    maps = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", body) if code == 200 else []
    out.append("  sitemapindex: HTTP %s, %d maps" % (code, len(maps)))
    want = MONTH.replace("/", "")
    # the child maps are named by period; try the ones whose name carries the year
    candidates = [m for m in maps if want[:4] in m or want[2:] in m]
    out.append("  maps matching %s: %d" % (want, len(candidates)))
    for m in candidates[-6:]:
        out.append("    %s" % m)
    urls = []
    for m in candidates[-6:] + [x for x in maps if x.endswith("news_sitemap.xml")]:
        c, b = fetch(m)
        if c != 200:
            continue
        # Both the address AND the date are needed from the <url> block: that
        # is how the list narrows to one round. Where there is no lastmod the
        # address stays without a date, and drops out only when filtering by
        # date explicitly.
        for block in re.findall(r"<url>(.*?)</url>", b, re.S):
            loc = re.search(r"<loc>\s*([^<\s]+)\s*</loc>", block)
            mod = re.search(r"<lastmod>\s*([0-9-]{10})", block)
            if not loc or "/%s/%s/" % (SECTION, MONTH) not in loc.group(1):
                continue
            urls.append((loc.group(1), mod.group(1) if mod else ""))
    if SINCE:
        before = len(urls)
        urls = [(u, d) for u, d in urls if d >= SINCE]
        out.append("  since %s: %d urls (of %d)" % (SINCE, len(urls), before))
    urls = sorted({u for u, _ in urls})
    # Match REPORTS, not transfer news or photo galleries: the earlier run
    # pulled a gallery and a transfer piece, which say nothing about how a
    # goal was scored. Report slugs carry a result verb or a drama word.
    REPORT = ("verte", "nyert", "gyozott", "gyoz", "dontetlen", "kikapott",
              "hajra", "gol", "fordit", "vezetes", "pont")
    SKIP = ("kepgaleria", "galeria", "hivatalos", "szerzodest", "igazol",
            "helyzetjelentest", "tavozik", "kolcsonadta")
    reports = [u for u in urls
               if any(w in u for w in REPORT) and not any(w in u for w in SKIP)]
    out.append("  of these, report-like: %d" % len(reports))
    urls = reports or urls
    out.append("  %s articles in %s: %d" % (SECTION, MONTH, len(urls)))
    for u in urls[:16]:
        out.append("    %s" % u[len(HOST):][:100])

    print("\n".join(out))
    print("\n" + "#" * 70)
    print("# ARTICLE EXTRACTS - run log only, not stored in the repository")
    print("#" * 70)
    for u in urls[:LIMIT]:
        c, b = fetch(u)
        t = text_of(b)
        print("\n### %s  (HTTP %s, %d chars of text)" % (u[len(HOST):], c, len(t)))
        print(t[:3000])

    with open(LOG, "a", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
