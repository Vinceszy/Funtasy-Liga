#!/usr/bin/env python3
"""What does the Draft league remember about the draft itself?

A draft league has a fact the salary-cap side cannot have: every player was
CHOSEN, by somebody, at a known moment. "A first-round pick sitting on the
bench" and "the man nobody wanted until the fourteenth round" are the kind
of sentence a summary is worth reading for - but only if the data is really
there and really joins to the squads we already store.

Probed here:
  draft/<league>/choices        who picked whom, in which round, at which pick
  draft/<league>/transactions   the waiver moves behind them (league level)
  draft/<league>/trades         offers between managers
  draft/entry/<entry>/transactions  the same, per team

OUR OWN CHANGE LOG ALREADY HAS the ins and outs: it is derived by comparing
one round's squad with the next. What comparison can never show is the
mechanism (a waiver claim or a free agent taken afterwards), the waiver
order, and the claims that FAILED - somebody who tried and was beaten to a
player never touches a squad at all. That is what these endpoints are for.

For each: the status, the keys, and - the part that decides whether it is
usable - whether the ids JOIN to the element and entry ids we already have.
An endpoint that answers 200 with ids we cannot match is worth nothing.

Reads only; writes the log file. No article or personal text is stored: the
Draft API returns real names, so the probe reports SHAPES and counts, and
the few sample rows it prints carry ids, not names.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

B = "https://draft.premierleague.com/api/"
HDRS = {"Accept": "application/json", "Accept-Language": "en-GB,en;q=0.9",
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")}
HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "draft-picks.txt")
LEAGUE = os.environ.get("LEAGUE_ID") or "48093"


def fetch(path):
    t = time.time()
    try:
        req = urllib.request.Request(B + path, headers=HDRS)
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read(), int((time.time() - t) * 1000)
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:300], int((time.time() - t) * 1000)
    except Exception as e:                                   # noqa: BLE001
        return 0, ("%s: %s" % (type(e).__name__, e)).encode(), int((time.time() - t) * 1000)


def our_ids():
    """The ids already stored: the response has to join to these."""
    root = os.path.dirname(HERE)
    load = lambda n: json.load(open(os.path.join(root, n), encoding="utf-8"))
    d = load("draft.json")
    hist = load("draft_history.json")
    entries = {str(e["id"]) for e in d.get("entries", [])}
    elements = set()
    for sq in hist.get("rounds", {}).values():
        for squad in sq.values():
            for x in squad:
                elements.add(str(x["e"]))
    return entries, elements


def main():
    entries, elements = our_ids()
    out = ["", "=" * 70,
           "PROBE: %s UTC | draft choices / transactions (league %s)"
           % (time.strftime("%Y-%m-%d %H:%M"), LEAGUE),
           "  our own ids: %d teams, %d players" % (len(entries), len(elements))]

    # A real team id for the team-level endpoint. It is not stored in the
    # repository (public), so it is requested from the league data at run time.
    one_entry = None
    code, body, _ = fetch("league/%s/details" % LEAGUE)
    if code == 200:
        try:
            for e in (json.loads(body).get("league_entries") or []):
                if e.get("entry_id") is not None:
                    one_entry = str(e["entry_id"])
                    break
        except Exception:                                    # noqa: BLE001
            pass
    out.append("  id available for the team-level endpoint: %s" % bool(one_entry))

    paths = [("choices", "draft/%s/choices" % LEAGUE),
             ("transactions (league)", "draft/%s/transactions" % LEAGUE),
             ("trades", "draft/%s/trades" % LEAGUE),
             ("league details (already used)", "league/%s/details" % LEAGUE)]
    if one_entry:
        paths += [("transactions (team)", "draft/entry/%s/transactions" % one_entry),
                  ("transactions (under entry)", "entry/%s/transactions" % one_entry),
                  ("watchlist", "watchlist/%s" % one_entry)]
    for name, path in paths:
        code, body, ms = fetch(path)
        out.append("")
        out.append("--- %s ---" % name)
        out.append("  %s: HTTP %s, %d kb, %d ms" % (path, code, len(body) // 1024, ms))
        if code != 200:
            out.append("  response: %s" % body[:160].decode("utf-8", "replace"))
            continue
        try:
            j = json.loads(body)
        except Exception:                                    # noqa: BLE001
            out.append("  not json")
            continue
        if isinstance(j, dict):
            out.append("  top-level keys: %s" % ", ".join(sorted(j.keys())))
            items = None
            for k in ("choices", "transactions", "trades"):
                if isinstance(j.get(k), list):
                    items = j[k]
                    out.append("  '%s' list: %d items" % (k, len(items)))
                    break
        else:
            items = j if isinstance(j, list) else None
            out.append("  list: %d items" % (len(items) if items else 0))
        if not items:
            continue
        out.append("  item keys: %s" % ", ".join(sorted(items[0].keys())))
        # THE POINT: do the ids join to what we already have?
        for field, known, label in (("element", elements, "player"),
                                    ("entry", entries, "team")):
            values = [str(x.get(field)) for x in items if x.get(field) is not None]
            if not values:
                out.append("  %-8s field: not in the response" % field)
                continue
            matched = sum(1 for v in values if v in known)
            out.append("  %-8s field: %d values, matching our own %s ids: %d"
                       % (field, len(values), label, matched))
        # sample rows: ONLY ids and numbers, no names
        safe = ("element", "entry", "round", "pick", "index", "event", "kind",
                "result", "added", "removed", "entry_in", "entry_out",
                "element_in", "element_out", "offered_entry", "received_entry")
        print("\n  == %s sample rows (no names) ==" % name)
        for x in items[:5]:
            print("     | %s" % json.dumps({k: x.get(k) for k in safe if k in x},
                                           ensure_ascii=False))
        print("     (all fields: %s)" % ", ".join(sorted(items[0].keys())))

    text = "\n".join(out) + "\n"
    print(text)
    header = ("Probe of the Draft league's own draft and transactions.\n"
              "Written by naplo/draft-picks-probe.py. It stores NO names:\n"
              "only shapes, counts and whether the ids join.\n")
    old = open(LOG, encoding="utf-8").read() if os.path.exists(LOG) else header
    open(LOG, "w", encoding="utf-8").write(old.rstrip("\n") + "\n" + text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
