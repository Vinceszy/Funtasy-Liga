#!/usr/bin/env python3
"""EGYSZERI felderites: MELYIK mezo mondja meg, hogy egy nap le van zarva?

Vince szerint a tegnapi (pentek/szombat) meccsek mar le vannak zarva, az
oldal megis azt irja rajuk, hogy nem. Ket jelolt van, es most egyszerre
nezzuk oket, hogy lassuk, melyik valtozott mar at:
  - a MECCS jelzoi: started / finished_provisional / finished
  - a NAP jelzoi (klasszikus FPL event-status): bonus_added / points
Csak olvas.
"""
import datetime, json, urllib.request

HDRS = {"Accept": "application/json", "User-Agent": "Mozilla/5.0 funtasy-diag/1.0"}


def hoz(url, timeout=60):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=HDRS), timeout=timeout) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return getattr(e, "code", None) or ("%s: %s" % (type(e).__name__, e)), None


print("=== a meres ideje: %s UTC" % datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M"))

st, game = hoz("https://draft.premierleague.com/api/game")
gw = (game or {}).get("current_event")
print("=== draft game: %s" % json.dumps(game, ensure_ascii=False))

st, nap = hoz("https://fantasy.premierleague.com/api/event-status/")
print("\n=== NAPONKENT (klasszikus FPL event-status) -> HTTP %s" % st)
for n in ((nap or {}).get("status") or []):
    print("    %s  bonus_added=%-5s points=%r" % (n.get("date"), n.get("bonus_added"), n.get("points")))
print("    leagues=%r" % (nap or {}).get("leagues"))

st, fx = hoz("https://draft.premierleague.com/api/event/%d/fixtures" % gw)
print("\n=== MECCSENKENT (draft fixtures) -> HTTP %s" % st)
for m in (fx or []):
    print("    id=%-3s %s  started=%-5s finished_provisional=%-5s finished=%-5s"
          % (m.get("id"), (m.get("kickoff_time") or "")[:16],
             m.get("started"), m.get("finished_provisional"), m.get("finished")))

# a klasszikus FPL fixtures is - hatha ott mar mas az allapot
st, cfx = hoz("https://fantasy.premierleague.com/api/fixtures/?event=%d" % gw)
print("\n=== MECCSENKENT (klasszikus FPL fixtures) -> HTTP %s" % st)
for m in (cfx or []):
    print("    id=%-4s %s  started=%-5s finished_provisional=%-5s finished=%-5s"
          % (m.get("id"), (m.get("kickoff_time") or "")[:16],
             m.get("started"), m.get("finished_provisional"), m.get("finished")))

print("\n--- vege ---")
