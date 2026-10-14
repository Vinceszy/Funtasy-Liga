#!/usr/bin/env python3
"""What did the readers say about the pieces?

The rating of an article goes to the Worker, one row per article and device.
This asks for the lot and prints a digest: how many came in, how they are
spread from one to four, which piece drew what, and the reasons as written.

The REASONS go to the run log only, never into the repository. They are the
readers' own words about our writing, given to us and not to an audience; the
log file keeps the counts, which is what a later run needs to compare
against.

Environment: PROXY_URL (the Worker), PROBE_ORIGIN (the Origin header the
Worker accepts).
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

PROXY = os.environ.get("PROXY_URL") or "https://funtasy-liga.swick00.workers.dev"
ORIGIN = os.environ.get("PROBE_ORIGIN") or "https://vinceszy.github.io"
LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ratings.txt")


def fetch(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": "FunTasy-harvest (github.com/Vinceszy/Funtasy-Liga)",
        "Origin": ORIGIN, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:300]
    except Exception as e:                                   # noqa: BLE001
        return 0, ("%s: %s" % (type(e).__name__, e)).encode()


def main():
    lines = ["", "=" * 70,
             "FETCH: %s UTC | article ratings" % time.strftime("%Y-%m-%d %H:%M")]
    c, b = fetch(PROXY + "/ertekelesek")
    if c != 200:
        # 503 = the Worker has NO storage binding: not "zero ratings" but
        # "every rating is lost". The two have to be seen apart.
        lines.append("  /ertekelesek: HTTP %s%s" % (
            c, "  <- NO STORAGE BINDING, ratings are lost" if c == 503 else ""))
        print("\n".join(lines))
        with open(LOG, "a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        return 1
    try:
        ratings = json.loads(b.decode("utf-8", "replace"))
    except Exception:                                        # noqa: BLE001
        lines.append("  the response is not JSON (%d bytes)" % len(b))
        print("\n".join(lines))
        return 1

    lines.append("  ratings in total: %d" % len(ratings))
    if not ratings:
        lines.append("  nobody has rated yet")
        print("\n".join(lines))
        with open(LOG, "a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        return 0

    distribution = {}
    per_article = {}
    with_reason = 0
    for x in ratings:
        p = x.get("pont")
        distribution[p] = distribution.get(p, 0) + 1
        k = x.get("cikk") or "?"
        per_article.setdefault(k, []).append(p)
        if (x.get("indok") or "").strip():
            with_reason += 1
    lines.append("  distribution: " + " | ".join(
        "%s points: %d" % (p, distribution[p])
        for p in sorted(distribution, key=lambda z: (z is None, z))))
    scores = [x["pont"] for x in ratings if isinstance(x.get("pont"), (int, float))]
    if scores:
        lines.append("  average: %.2f" % (sum(scores) / len(scores)))
    lines.append("  with a reason: %d / %d" % (with_reason, len(ratings)))
    lines.append("")
    lines.append("  PER ARTICLE")
    for k in sorted(per_article):
        ps = per_article[k]
        lines.append("    %-44s %s (%d)" % (k[:44], ", ".join(str(p) for p in ps), len(ps)))
    print("\n".join(lines))

    # The REASONS go to the run log only - never into the repository.
    print("")
    print("#" * 70)
    print("# REASONS - run log only, never committed to the repository")
    print("#" * 70)
    for x in ratings:
        reason = (x.get("indok") or "").strip()
        if not reason:
            continue
        print("\n### %s | %s points | %s" % (x.get("cikk"), x.get("pont"), x.get("ido")))
        print(reason)

    with open(LOG, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
