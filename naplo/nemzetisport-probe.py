#!/usr/bin/env python3
"""What nemzetisport.hu allows, and whether it has a channel meant for machine use.

WHY: an earlier probe concluded from a single library call that the site
forbids fetching. But a false "can_fetch" can also come from robots.txt not
being readable, or from only ONE path being disallowed - so the actual rules
have to be looked at, not the verdict.

What it measures:
  1. the raw content of robots.txt (it is a public rule file meant for
     machines - it may go into the log)
  2. per path, separately: what it allows and what it disallows
  3. whether there is a news feed (RSS/Atom) - that is put out
     specifically for machine reading

It stores no article text either.
"""
import os
import sys
import time
import urllib.error
import urllib.request
import urllib.robotparser

AGENT = "FunTasy-probe (github.com/Vinceszy/Funtasy-Liga)"
HOST = "https://www.nemzetisport.hu"
PATHS = ["/", "/foci-nb-i", "/rss", "/rss.xml", "/feed", "/feed/", "/hirek"]
FEEDS = ["/publicapi/hu/rss/", "/publicapi/hu/rss/index",
         "/publicapi/hu/rss/all", "/publicapi/hu/rss/labdarugas",
         "/publicapi/hu/rss/foci-nb-i", "/rss", "/rss.xml", "/feed"]
LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "report-source.txt")


def fetch(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {"User-Agent": AGENT})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            return resp.status, resp.read().decode("utf-8", "replace"), int((time.time() - t0) * 1000)
    except urllib.error.HTTPError as e:
        return e.code, "", int((time.time() - t0) * 1000)
    except Exception as e:                                   # noqa: BLE001
        return 0, "%s: %s" % (type(e).__name__, e), int((time.time() - t0) * 1000)


def main():
    lines = ["", "=" * 70,
             "PROBE: %s UTC | nemzetisport.hu: what it allows" % time.strftime("%Y-%m-%d %H:%M")]

    code, body, ms = fetch(HOST + "/robots.txt")
    lines.append("")
    lines.append("--- robots.txt (HTTP %s, %d ms) ---" % (code, ms))
    if code == 200:
        # Written WITH THE EMPTY LINES: they separate the groups, and that is
        # exactly what the earlier wrong verdict turned on.
        for line in body.splitlines():
            lines.append("  | " + line.rstrip()[:110])
    else:
        lines.append("  not readable - in that case the earlier 'disallows' verdict"
                     " was NOT the site's decision but a read error")

    def own_decision(txt, path):
        """Decides by the rules of the `*` group, respecting group boundaries.

        The library merged the groups when the file had no empty line between
        them, and so a `Disallow: /` meant for ANOTHER agent seemed to apply
        to us. The longest matching rule wins, Allow on equal length."""
        active, rules, agents = False, [], []
        for line in txt.splitlines():
            t = line.split("#", 1)[0].strip()
            if not t:
                agents = []
                continue
            if ":" not in t:
                continue
            key, value = (x.strip() for x in t.split(":", 1))
            k = key.lower()
            if k == "user-agent":
                agents.append(value)
                active = "*" in agents
            elif k in ("allow", "disallow") and active and value:
                rules.append((k == "allow", value))
        best = None
        for allow, pattern in rules:
            if path.startswith(pattern) and (best is None or len(pattern) > len(best[1])
                                             or (len(pattern) == len(best[1]) and allow)):
                best = (allow, pattern)
        return (True, "no rule for it") if best is None else (best[0], best[1])

    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(HOST + "/robots.txt")
    try:
        rp.read()
        read_ok = True
    except Exception:                                        # noqa: BLE001
        read_ok = False
    lines.append("")
    lines.append("--- decision per path (agent: ours) ---")
    if not read_ok:
        lines.append("  robots.txt could not be read with the library")
    else:
        for path in PATHS:
            library = rp.can_fetch(AGENT, HOST + path)
            allow, rule = own_decision(body, path)
            lines.append("  %-18s ours: %-9s (%s) | library: %s"
                         % (path, "ALLOWS" if allow else "disallows", rule,
                            "allows" if library else "disallows"))

    # WHY THE LIBRARY DIFFERED: RobotFileParser uses the default urllib agent
    # for its own request. If the site answers that with 401/403, the parser
    # switches to "disallow everything" - so the verdict came from its own
    # refusal, not from the file's rules. That is measured separately.
    lines.append("")
    lines.append("--- why the library differed ---")
    code2, _, ms2 = fetch(HOST + "/robots.txt", {"User-Agent": "Python-urllib/3.11"})
    lines.append("  robots.txt with the default urllib agent: HTTP %s (%d ms)"
                 % (code2, ms2))
    lines.append("  (on 401/403 RobotFileParser treats everything as disallowed)")

    lines.append("")
    lines.append("--- sitemap: the machine index of the articles ---")
    code3, sm, ms3 = fetch(HOST + "/sitemapindex.xml")
    lines.append("  sitemapindex.xml: HTTP %s, %d kbytes (%d ms)"
                 % (code3, len(sm) // 1024, ms3))
    import re as _re
    children = _re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", sm)
    lines.append("  maps referenced: %d" % len(children))
    for g in children[:5]:
        lines.append("    %s" % g)
    if children:
        # the last one is usually the newest
        target = children[-1]
        code4, child, ms4 = fetch(target)
        urls = _re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", child)
        lines.append("  last map (%s): HTTP %s, %d urls (%d ms)"
                     % (target.rsplit("/", 1)[-1], code4, len(urls), ms4))
        # A sample is shown UNFILTERED too: an earlier run gave zero hits for
        # its own filter, and that did not show whether the filter was wrong
        # or there really was no football in the index.
        lines.append("  sample of the urls (unfiltered):")
        for c in urls[:10]:
            lines.append("    %s" % c[:110])
        from collections import Counter
        prefixes = Counter()
        for c in urls:
            r = c.split("//", 1)[-1].split("/")[1:]
            prefixes[r[0] if r else "(root)"] += 1
        lines.append("  path prefixes: %s"
                     % ", ".join("%s (%d)" % (k, v) for k, v in prefixes.most_common(8)))

    lines.append("")
    lines.append("--- looking for a news feed ---")
    found = []
    for path in FEEDS:
        allow, rule = own_decision(body, path)
        if not allow:
            lines.append("  %-26s disallowed by robots (%s), not requested" % (path, rule))
            continue
        code, body, ms = fetch(HOST + path, {"User-Agent": AGENT,
                                             "Accept": "application/rss+xml, application/xml"})
        mark = ""
        if code == 200:
            start = body.lstrip()[:200].lower()
            if "<rss" in start or "<feed" in start or "<?xml" in start:
                mark = " | XML feed, %d items" % body.count("<item")
                found.append(path)
            else:
                mark = " | not XML (probably an HTML page)"
        lines.append("  %-26s HTTP %s (%d ms)%s" % (path, code, ms, mark))
    lines.append("")
    lines.append("  usable feed: %s" % (", ".join(found) if found else "none"))

    with open(LOG, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
