#!/usr/bin/env python3
"""End-to-end probe of the Worker's "last known standing" store.

WHY HERE: the development environment's network does not reach workers.dev
(measured: immediate connection failure), so there the Worker's logic can
only be tested with a fake KV (tesztek/workertarolo.teszt.js). The LIVE
behaviour - whether the second visitor really gets the stored standing - can
only be measured from outside; the GitHub Actions runner reaches the
internet, so it runs from there.

What it measures:
  1. /tarolt BEFORE the request  - whether a standing is stored yet, and from when
  2. an ordinary proxy request   - this is what stores the response
  3. /tarolt AFTER the request   - whether it is there, and HOW FAST it comes
  4. the same repeated           - with unchanged data the timestamp must not
                                   change (i.e. it really writes only on a change)

It appends the result to naplo/storage-probe.txt.

Environment: PROXY_URL (the Worker), PROBE_UNAME (the manager to request).
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

PROXY = os.environ.get("PROXY_URL") or "https://funtasy-liga.swick00.workers.dev"
ORIGIN = "https://vinceszy.github.io"
COMPETITION = 3
# A real manager - the site requests exactly this URL too.
# `or` (not get()'s default) is needed because the workflow passes an EMPTY
# string when the input is left blank - get() does not fall back to the
# default then, and the probe would have measured a different URL from the
# one the site requests.
UNAME = os.environ.get("PROBE_UNAME") or "HolVanSalah"
TARGET = (f"https://fantasy-api.mlsz.hu/competitions/{COMPETITION}/rankings"
          "?include=user_team.user.id,summary_statistics,ranking,rounds,"
          "competition_rank&page=1&per_page=5"
          f"&filter%5Bsearch%5D={urllib.parse.quote(UNAME)}")
LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "storage-probe.txt")


def fetch(url):
    """(HTTP code, body, elapsed ms). Network error: (0, error message, ms)."""
    req = urllib.request.Request(url, headers={
        "Accept": "application/json", "Origin": ORIGIN,
        "User-Agent": "FunTasy-probe (github.com/Vinceszy/Funtasy-Liga)"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            return resp.status, resp.read().decode("utf-8", "replace"), int((time.time() - t0) * 1000)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace"), int((time.time() - t0) * 1000)
    except Exception as e:                                   # noqa: BLE001
        return 0, "%s: %s" % (type(e).__name__, e), int((time.time() - t0) * 1000)


def stored():
    code, body, ms = fetch(PROXY + "/tarolt?url=" + urllib.parse.quote(TARGET, safe=""))
    if code != 200:
        return None, ms, "HTTP %s" % code
    try:
        j = json.loads(body)
    except ValueError:
        return None, ms, "not JSON"
    return j.get(TARGET), ms, None


def main():
    lines = ["", "=" * 62,
             "PROBE: %s UTC | manager: %s" % (time.strftime("%Y-%m-%d %H:%M"), UNAME)]

    before, ms, error = stored()
    lines.append("1. /tarolt BEFORE the request: %s (%d ms)%s" % (
        ("present, ido=%s, %d bytes" % (before.get("ido"), len(before.get("adat") or ""))
         if before else "not stored yet"), ms, " [%s]" % error if error else ""))

    code, body, ms2 = fetch(PROXY + "/?url=" + urllib.parse.quote(TARGET, safe=""))
    lines.append("2. ordinary proxy request: HTTP %d, %d bytes, %d ms" % (code, len(body), ms2))
    if code != 200:
        lines.append("   ! the request failed, the remaining steps are meaningless")
        write(lines)
        return 1

    time.sleep(3)                       # for the waitUntil write to finish
    after, ms3, error3 = stored()
    lines.append("3. /tarolt AFTER the request: %s (%d ms)%s" % (
        ("present, ido=%s, %d bytes" % (after.get("ido"), len(after.get("adat") or ""))
         if after else "MISSING - storing does not work"), ms3, " [%s]" % error3 if error3 else ""))
    if after:
        lines.append("   matches the proxy response: %s"
                     % ("YES" if after.get("adat") == body else "NO"))
        if ms3:
            lines.append("   the stored response came %.1fx faster than the fresh request"
                         % (ms2 / ms3))

    # 4. the same once more: with UNCHANGED data nothing may be written again
    fetch(PROXY + "/?url=" + urllib.parse.quote(TARGET, safe=""))
    time.sleep(3)
    again, _, _ = stored()
    if after and again:
        same = after.get("ido") == again.get("ido")
        lines.append("4. the timestamp after unchanged data: %s"
                     % ("UNCHANGED - written only on a change, as it should be" if same
                        else "CHANGED - every request writes, this would eat the daily quota"))
    write(lines)
    return 0


def write(lines):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write("\n".join(s for s in lines if s is not None) + "\n")
    print("\n".join(s for s in lines if s is not None))


if __name__ == "__main__":
    sys.exit(main())
