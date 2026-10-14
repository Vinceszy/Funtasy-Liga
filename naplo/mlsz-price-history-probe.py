#!/usr/bin/env python3
"""ONE-OFF probe: does the player data sheet give the price PER ROUND, and in what form?

WHY: the site shows a price per round on the profile. The list body gives
only the CURRENT price, and our own price log (arak.json) has been filling
only since it was started - so it holds nothing for the first rounds of the
season. According to the README the player data sheet's `rounds` array gives
it retroactively, but nobody has measured the FIELD NAMES, and the round's
id (round_id = 75 + 2 x round) is not the same as the row's own `id` - mixing
the two up would silently put every price in the wrong round.

What it decides: whether `rounds` exists, what a row holds, which field is
the round, and whether the last round's price matches what the body gives as
the current price.

Reads only. It needs the network, so it runs from Actions.

Environment: PRICE_CP (a competition player id; default: the first player of
the list).
"""
import json
import os
import sys
import urllib.request

API = "https://fantasy-api.mlsz.hu/"
HEADERS = {"Accept": "application/json", "User-Agent": "Mozilla/5.0 funtasy-armeres/1.0"}
LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mlsz-price-history.txt")


def get(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=40) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:                                    # noqa: BLE001
        return {"__error": "%s: %s" % (type(e).__name__, e)}


def main():
    lines = []

    def out(s=""):
        print(s)
        lines.append(s)

    cp = os.environ.get("PRICE_CP")
    if not cp:
        # Any player will do: the first row of the list.
        listing = get(API + "competitions/3/players?page%5Bsize%5D=1")
        data = (listing or {}).get("data") or []
        cp = str(data[0].get("id")) if data else ""
        out("first player of the list: %s" % (cp or "DID NOT ARRIVE"))
    if not cp:
        out("nothing to measure with - stopping")
        return 1

    j = get(API + "competitions/3/players/" + cp)
    if j.get("__error"):
        out("data sheet: %s" % j["__error"])
        return 1
    out("data sheet root keys: %s" % sorted(j.keys()))
    r = j.get("rounds")
    out("rounds type: %s, length: %s" % (type(r).__name__, len(r) if isinstance(r, list) else "-"))
    if not isinstance(r, list) or not r:
        out("NO per-round row - the price history cannot be filled in from here")
        return 0

    out("keys of one row: %s" % sorted(r[0].keys()))
    out("")
    out("%-10s %-10s %-8s %-10s" % ("id", "round_id", "price", "played"))
    for x in r:
        out("%-10s %-10s %-8s %-10s" % (x.get("id"), x.get("round_id"),
                                        x.get("market_price"), x.get("is_played")))
    out("")
    # The decision the probe was made for: which field gives the round number?
    for field in ("round_id", "id"):
        values = [x.get(field) for x in r if isinstance(x.get(field), int)]
        numbers = sorted((e - 75) / 2 for e in values)
        valid = all(float(n).is_integer() and 1 <= n <= 38 for n in numbers)
        out("from %s (id-75)/2: %s -> %s" % (field, numbers[:8],
                                            "VALID round numbers" if valid else "not a round"))
    body_price = ((j.get("current_round") or {}).get("market_price"))
    out("")
    out("the body's CURRENT price: %s | the last row's price: %s"
        % (body_price, r[-1].get("market_price")))
    return 0


if __name__ == "__main__":
    import io as _io
    import contextlib
    buffer = _io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = main()
    text = buffer.getvalue()
    sys.stdout.write(text)
    with open(LOG, "w", encoding="utf-8") as f:
        f.write(text)
    sys.exit(code)
