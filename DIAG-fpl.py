#!/usr/bin/env python3
"""EGYSZERI felderites: valtozott-e valami az elozo meresek ota?

Korabbi meresek (mind ugyanazt adta):
  21:04 / 21:59 / 22:04 UTC -> minden lejatszott meccs finished=False,
  minden lejatszott nap bonus_added=False, points='p'.
Vince szerint viszont mostmar minden meccs le van zarva. Nezzuk, mi valtozott.
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


print("=== a meres ideje: %s UTC" % datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S"))
st, game = hoz("https://draft.premierleague.com/api/game")
print("=== draft game: %s" % json.dumps(game, ensure_ascii=False))
gw = (game or {}).get("current_event")

st, nap = hoz("https://fantasy.premierleague.com/api/event-status/")
print("\n=== NAPONKENT -> HTTP %s" % st)
for n in ((nap or {}).get("status") or []):
    print("    %s  bonus_added=%-5s points=%r" % (n.get("date"), n.get("bonus_added"), n.get("points")))
print("    leagues=%r" % (nap or {}).get("leagues"))

st, fx = hoz("https://draft.premierleague.com/api/event/%d/fixtures" % gw)
print("\n=== MECCSENKENT -> HTTP %s" % st)
for m in (fx or []):
    print("    id=%-3s %s  started=%-5s fin_prov=%-5s finished=%-5s"
          % (m.get("id"), (m.get("kickoff_time") or "")[:16],
             m.get("started"), m.get("finished_provisional"), m.get("finished")))

# a bonusz erteke egy konkret jatekosnal - valtozott-e a korabbi mereshez kepest
st, live = hoz("https://draft.premierleague.com/api/event/%d/live" % gw)
el = (live or {}).get("elements") or {}
print("\n=== ellenorzo jatekosok (a 21:04-es meresbol)")
for k in ("10", "12", "15", "68"):
    v = el.get(k) or el.get(int(k)) or {}
    s2 = v.get("stats") or {}
    print("    elem %-4s bonus=%s bps=%s total=%s" % (k, s2.get("bonus"), s2.get("bps"), s2.get("total_points")))

print("\n--- vege ---")
