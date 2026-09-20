#!/usr/bin/env python3
"""What kinds of colourful fact does a Nemzeti Sport match report contain?

Style cannot be designed without knowing the palette. A goal scored with a
bicycle kick and a disputed penalty were two examples; there are probably
many more categories - the flow of the match, a goalkeeping error, a debut,
a milestone, the referee, the crowd. This probe pulls a few real reports of
a given round so the categories can be listed.

The extracted text goes to STANDARD OUTPUT ONLY, so it stays in the run log
and never enters the repository. The log file gets the urls and the sizes.
"""
import os
import re
import sys
import time
import urllib.error
import urllib.request

AGENT = "FunTasy-survey (github.com/Vinceszy/Funtasy-Liga)"
HOST = "https://www.nemzetisport.hu"
LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "beszamolo-forras.txt")
MONTH = os.environ.get("PROBE_MONTH") or "2026/09"
SECTION = os.environ.get("PROBE_SECTION") or "labdarugo-nb-i"


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
    kesok = [m for m in maps if want[:4] in m or want[2:] in m]
    out.append("  maps matching %s: %d" % (want, len(kesok)))
    for m in kesok[-6:]:
        out.append("    %s" % m)
    urls = []
    for m in kesok[-6:] + [x for x in maps if x.endswith("news_sitemap.xml")]:
        c, b = fetch(m)
        if c != 200:
            continue
        found = [u for u in re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", b)
                 if "/%s/%s/" % (SECTION, MONTH) in u]
        urls.extend(found)
    urls = sorted(set(urls))
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
    for u in urls[:12]:
        out.append("    %s" % u[len(HOST):][:100])

    print("\n".join(out))
    print("\n" + "#" * 70)
    print("# ARTICLE EXTRACTS - run log only, not stored in the repository")
    print("#" * 70)
    for u in urls[:6]:
        c, b = fetch(u)
        t = text_of(b)
        print("\n### %s  (HTTP %s, %d chars of text)" % (u[len(HOST):], c, len(t)))
        print(t[:3000])

    with open(LOG, "a", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
