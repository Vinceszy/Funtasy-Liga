#!/usr/bin/env python3
"""EGYSZERI felderites, 2. kor: hol latszik, hogy a bonusz mar hivatalos?

Az 1. kor: az explain szerkezete [[stat-lista, meccs_id]] - a sort tehat a
sajat meccsehez lehet kotni. Minden lejatszott meccs most
finished_provisional=True, finished=False.

Most azt nezzuk:
 a) van-e egyaltalan bonusz-sor az explain-ben (olyan jatekost keresunk,
    akinek bonus > 0);
 b) a MECCS sajat "stats" tombje mit tartalmaz - az FPL-ben ide a "bonus"
    tetel csak akkor kerul be, amikor a bonuszt veglegesitettek, addig csak
    "bps" van. Ha igy van, ez a keresett harmadik allapot jelzese.
Csak olvas.
"""
import json, urllib.request

BASE = "https://draft.premierleague.com/api/"
HDRS = {"Accept": "application/json", "User-Agent": "Mozilla/5.0 funtasy-diag/1.0"}


def hoz(ut, timeout=60):
    try:
        with urllib.request.urlopen(urllib.request.Request(BASE + ut, headers=HDRS), timeout=timeout) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return getattr(e, "code", None) or ("%s: %s" % (type(e).__name__, e)), None


st, game = hoz("game")
gw = (game or {}).get("current_event")
print("=== game: current_event=%s current_event_finished=%s processing_status=%s"
      % (gw, (game or {}).get("current_event_finished"), (game or {}).get("processing_status")))

st, fx = hoz("event/%d/fixtures" % gw)
print("\n=== a MECCSEK sajat stats tombje (mi van benne, es benne van-e a bonus?)")
for m in (fx or []):
    stats = m.get("stats") or []
    azonositok = [s.get("identifier") for s in stats]
    print("    id=%-3s started=%-5s fin_prov=%-5s finished=%-5s  stats: %s"
          % (m.get("id"), m.get("started"), m.get("finished_provisional"),
             m.get("finished"), azonositok or "(ures)"))
    if "bonus" in azonositok:
        b = next(s for s in stats if s.get("identifier") == "bonus")
        print("        bonus tetel: %s" % json.dumps(b, ensure_ascii=False)[:300])

st, live = hoz("event/%d/live" % gw)
el = (live or {}).get("elements") or {}
tetelek = el.items() if isinstance(el, dict) else list(enumerate(el))
bonuszosak = [(k, v) for k, v in tetelek if ((v or {}).get("stats") or {}).get("bonus")]
print("\n=== %s jatekosbol %s-nek van bonusza (bonus > 0)" % (len(tetelek), len(bonuszosak)))
for k, v in bonuszosak[:4]:
    s = v.get("stats") or {}
    print("\n    elem %s: bonus=%s bps=%s total=%s" % (k, s.get("bonus"), s.get("bps"), s.get("total_points")))
    print("      explain: %s" % json.dumps(v.get("explain"), ensure_ascii=False)[:600])

print("\n--- vege ---")
