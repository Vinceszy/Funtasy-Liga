#!/usr/bin/env python3
"""EGYSZERI felderites, 3. kor: mi van a meccs stats tombjeben?

Az elozo kor: a bonusz OTT VAN az explain-ben (stat: "bonus"), es a sor a
sajat meccsehez kotheto (explain = [[stat-lista, meccs_id]]). A meccs sajat
"stats" tombjeben viszont nincs "identifier" kulcs - mas az alakja, mint a
klasszikus FPL-ben. Most nyersen kiirjuk, hatha ott van a bonusz, es abbol
latszik, hogy mar veglegesitettek.

Kulon kerdes: a pentek esti meccs (id=1) ket nappal kesobb is
finished=False. Ez azt jelentene, hogy a "finished" nem meccsenkent, hanem
a fordulo vegen billen at - ezt a holnapi meres donti el.
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
print("=== game: %s" % json.dumps(game, ensure_ascii=False))
gw = (game or {}).get("current_event")

st, fx = hoz("event/%d/fixtures" % gw)
m = (fx or [{}])[0]
print("\n=== egy lement meccs (id=%s) TELJES stats tombje" % m.get("id"))
print(json.dumps(m.get("stats"), ensure_ascii=False, indent=1)[:2500])

print("\n=== minden meccs: hany stats tetel, es milyen kulcsok")
for m in (fx or []):
    st_ = m.get("stats") or []
    kulcsok = sorted({k for t in st_ if isinstance(t, dict) for k in t})
    ertekek = [t.get("s") or t.get("identifier") or t.get("name") for t in st_ if isinstance(t, dict)]
    print("    id=%-3s fin_prov=%-5s finished=%-5s  %s tetel, kulcsok=%s, s-ertekek=%s"
          % (m.get("id"), m.get("finished_provisional"), m.get("finished"),
             len(st_), kulcsok, ertekek))

# a bootstrap-static parja a Draftban: van-e benne fordulo-szintu jelzes
for ut in ("bootstrap-static", "event/%d/live" % gw):
    st, j = hoz(ut)
    if ut == "bootstrap-static" and isinstance(j, dict):
        print("\n=== bootstrap-static kulcsok: %s" % sorted(j)[:20])
        ev = next((e for e in (j.get("events") or {}).get("data", []) if e.get("id") == gw), None) \
            if isinstance(j.get("events"), dict) else None
        print("    a fordulo objektuma: %s" % json.dumps(ev, ensure_ascii=False)[:500])

print("\n--- vege ---")
