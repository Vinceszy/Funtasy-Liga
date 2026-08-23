#!/usr/bin/env python3
"""EGYSZERI felderites: a bonuszpontok harom allapota az FPL Draft API-ban.

Amit tudni akarunk:
 1) a fixtures harom jelzoje (started / finished_provisional / finished)
    tenyleg harom allapotot ad-e ki, es most eppen melyik hol tart;
 2) az event/{gw}/live "explain" mezoje MILYEN szerkezetu - benne van-e a
    meccs azonositoja, hogy egy bonusz-sort a sajat meccsehez tudjunk kotni
    (dupla fordulonal ez donti el, melyik sor melyik allapotban van);
 3) megjelenik-e a bonusz az explain-ben mar a meccs alatt.
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
print("=== game -> HTTP %s" % st)
print("    %s" % json.dumps(game, ensure_ascii=False)[:400])
gw = (game or {}).get("current_event")

for cimke, g in (("aktualis", gw), ("elozo", (gw - 1) if gw and gw > 1 else None)):
    if not g:
        continue
    st, fx = hoz("event/%d/fixtures" % g)
    print("\n=== %s fordulo (%s) fixtures -> HTTP %s, %s meccs" % (cimke, g, st, len(fx or [])))
    if isinstance(fx, list) and fx:
        print("    egy meccs OSSZES mezoje: %s" % sorted(fx[0]))
        for m in fx:
            print("      id=%-6s started=%-5s finished_prov=%-5s finished=%-5s kickoff=%s"
                  % (m.get("id"), m.get("started"), m.get("finished_provisional"),
                     m.get("finished"), m.get("kickoff_time")))

st, live = hoz("event/%d/live" % gw) if gw else (None, None)
el = (live or {}).get("elements") or {}
print("\n=== aktualis fordulo live -> HTTP %s, %s jatekos" % (st, len(el)))
minta = el.items() if isinstance(el, dict) else enumerate(el)
db = 0
for k, v in minta:
    stats = (v or {}).get("stats") or {}
    if not (stats.get("bonus") or stats.get("bps")):
        continue
    print("\n    elem %s: bonus=%s bps=%s total=%s"
          % (k, stats.get("bonus"), stats.get("bps"), stats.get("total_points")))
    print("      stats kulcsok: %s" % sorted(stats))
    print("      explain NYERSEN: %s" % json.dumps(v.get("explain"), ensure_ascii=False)[:700])
    db += 1
    if db >= 3:
        break
if not db:
    print("    (egy jatekosnak sincs bonus/bps erteke - a fordulo valoszinuleg meg el sem kezdodott)")
    for k, v in list(minta)[:1]:
        print("      minta elem %s: %s" % (k, json.dumps(v, ensure_ascii=False)[:500]))

print("\n--- vege ---")
