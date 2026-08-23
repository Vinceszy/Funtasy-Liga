#!/usr/bin/env python3
"""EGYSZERI felderites: hol latszik az FPL NAPI pontzarasa?

Vince kepe a Draft feluleterol: "Day | Match Points | Bonus Points" tablazat,
naponkent egy sorral, es mindharom lejatszott napnal PROVISIONAL. Tehat a
veglegesites NAPONKENT tortenik, nem meccsenkent - az en jelzom (a meccs
finished mezoje) nem ezt meri.

Az FPL-ben van erre kulon vegpont: event-status. Megnezzuk a klasszikus es a
Draft oldalon is, plusz mindent, ami napi bontast adhat. Csak olvas.
"""
import json, urllib.request

HDRS = {"Accept": "application/json", "User-Agent": "Mozilla/5.0 funtasy-diag/1.0"}


def hoz(url, timeout=60):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=HDRS), timeout=timeout) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return getattr(e, "code", None) or ("%s: %s" % (type(e).__name__, e)), None


JELOLTEK = [
    "https://draft.premierleague.com/api/event-status",
    "https://draft.premierleague.com/api/event-status/",
    "https://fantasy.premierleague.com/api/event-status/",
    "https://draft.premierleague.com/api/game",
]
for u in JELOLTEK:
    st, j = hoz(u)
    print("\n=== %s -> HTTP %s" % (u, st))
    if j is not None:
        print("    %s" % json.dumps(j, ensure_ascii=False, indent=1)[:1200])

# a Draft bootstrap-static: van-e benne napi/fordulo-szintu jelzes
st, j = hoz("https://draft.premierleague.com/api/bootstrap-static")
print("\n=== draft bootstrap-static -> HTTP %s" % st)
if isinstance(j, dict):
    print("    kulcsok: %s" % sorted(j))
    ev = j.get("events")
    if isinstance(ev, dict):
        print("    events kulcsok: %s" % sorted(ev))
        adat = ev.get("data") or []
        for e in adat[:2]:
            print("      fordulo: %s" % json.dumps(e, ensure_ascii=False)[:600])

print("\n--- vege ---")
