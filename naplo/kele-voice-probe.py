#!/usr/bin/env python3
"""The SOURCE of the imitated voice: the author's own football writing.

WHY: the column imitates the voice of an existing columnist. The voice is not
to be guessed but read - the characteristic devices show only in the real
text.

THE FETCHED TEXT GOES UNDER `tartalek/kele/`. A measurement exists only as
long as it is written down: a run log is out of reach after a few days, and
then either the same thing has to be fetched again or - worse - one writes
from memory. `tartalek/` is the part of the repository the site does not
serve and D9 does not look at.

BYLINE CHECK. The author page also carries the publisher's own "latest news"
strip, full of other people's articles. A bare "dated article link" pattern
collects those too, and the probe comes back full of weather forecasts while
looking successful. So every downloaded page is checked for the AUTHOR's own
link; a page that fails is dropped, and the count of those is printed at
the end.

Environment: KELE_PAGES (how many archive pages, default 6), KELE_ARTICLES
(at most how many articles to download, default 40).
"""
import html
import os
import re
import sys
import time
import urllib.request

HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                         "(KHTML, like Gecko) Chrome/124 Safari/537.36",
           "Accept": "text/html,application/xhtml+xml"}
# MEASURED: the protection in front of Substack refuses EVERYTHING from a
# data-centre address with 403 - the feed and the archive API too - while the
# other publisher's author page lets it through. The list comes from there,
# and so do the article bodies.
AUTHOR = "https://24.hu/author/kelejanos/"
BYLINE = "/author/kelejanos"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(ROOT, "tartalek", "kele")
PAGE_COUNT = int(os.environ.get("KELE_PAGES", "6"))
ARTICLE_COUNT = int(os.environ.get("KELE_ARTICLES", "40"))


def get(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS),
                                    timeout=45) as r:
            return r.read().decode("utf-8", "replace")
    except Exception as e:                                    # noqa: BLE001
        return "__ERROR__ %s: %s" % (type(e).__name__, e)


def paragraphs(h):
    """The body text without markup. Not perfect - good enough to read."""
    h = re.sub(r"(?is)<(script|style|nav|footer|svg|aside)[^>]*>.*?</\1>", " ", h)
    h = re.sub(r"(?is)<br\s*/?>", "\n", h)
    h = re.sub(r"(?is)</(p|h1|h2|h3|li|div)>", "\n", h)
    h = re.sub(r"(?s)<[^>]+>", " ", h)
    h = html.unescape(h)
    lines = [re.sub(r"[ \t ]+", " ", x).strip() for x in h.split("\n")]
    return [x for x in lines if len(x) > 40]


def title(h):
    m = re.search(r"(?is)<title>(.*?)</title>", h)
    return html.unescape(m.group(1)).strip() if m else ""


def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:70]


def main():
    os.makedirs(TARGET, exist_ok=True)
    candidates = []
    for page in range(1, PAGE_COUNT + 1):
        u = AUTHOR if page == 1 else "%spage/%d/" % (AUTHOR, page)
        h = get(u)
        if h.startswith("__ERROR__"):
            print("archive %d.: %s" % (page, h))
            continue
        new = [x for x in dict.fromkeys(re.findall(
            r'href="(https://24\.hu/[a-z-]+/20\d\d/\d\d/\d\d/[^"#?]+)"', h))]
        print("archive page %d: %d links" % (page, len(new)))
        candidates += [x for x in new if x not in candidates]
    print("\nall candidates: %d" % len(candidates))

    own = foreign = failed = 0
    for c in candidates:
        if own >= ARTICLE_COUNT:
            break
        ch = get(c)
        time.sleep(0.4)
        if ch.startswith("__ERROR__"):
            failed += 1
            print("  ERROR  %s  %s" % (c, ch))
            continue
        # The byline decides, not the fact that the link came from the author page.
        if BYLINE not in ch:
            foreign += 1
            continue
        rows = paragraphs(ch)
        if len(rows) < 5:
            failed += 1
            print("  EMPTY  %s" % c)
            continue
        own += 1
        name = slug(c.rstrip("/").split("/")[-1]) or ("article-%02d" % own)
        path = os.path.join(TARGET, "%s.txt" % name)
        with open(path, "w", encoding="utf-8") as f:
            f.write("# %s\n# %s\n\n%s\n" % (title(ch), c, "\n\n".join(rows)))
        print("  SAVED  %s  (%d paragraphs)  -> tartalek/kele/%s.txt"
              % (c, len(rows), name))

    print("\n%d own articles saved, %d foreign dropped (byline did not match), "
          "%d failed" % (own, foreign, failed))
    if not own:
        print("NOT A SINGLE own article arrived - the probe did NOT succeed.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
