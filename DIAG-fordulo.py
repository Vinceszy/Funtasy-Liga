#!/usr/bin/env python3
"""EGYSZERI felderites, 5. kor: a FORDULO-OBJEKTUM.

A 4. kor megtalalta a frontend sajat hivasat a JS-csomagban:
    /competitions?include=teams,teams.media,rounds,current_round
Tehat a fordulolista a VERSENYLISTAN keresztul jon, nem onallo vegpontkent
(ezert volt minden rounds-proba 404). Most kikerjuk, es kiirjuk a teljes
fordulo-objektumot - ebben kell lennie annak, ahogy az MLSZ lezarja a
fordulot. Csak olvas.
"""
import json, urllib.request

API = "https://fantasy-api.mlsz.hu/"
HDRS = {"Accept": "application/json", "User-Agent": "Mozilla/5.0 funtasy-diag/1.0",
        "Referer": "https://fantasy.mlsz.hu/"}


def hoz(ut, timeout=60):
    try:
        with urllib.request.urlopen(urllib.request.Request(API + ut, headers=HDRS), timeout=timeout) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return getattr(e, "code", None) or ("%s: %s" % (type(e).__name__, e)), None


st, j = hoz("competitions?include=teams,teams.media,rounds,current_round")
print("=== competitions?include=rounds,current_round -> HTTP %s" % st)
comp = next((c for c in ((j or {}).get("data") or []) if c.get("id") == 3), None)
if not comp:
    print("    nincs 3-as verseny a valaszban: %s" % json.dumps(j, ensure_ascii=False)[:600])
else:
    print("    verseny kulcsok: %s" % sorted(comp))
    cr = comp.get("current_round")
    print("\n--- current_round ---")
    print("    %s" % json.dumps(cr, ensure_ascii=False, indent=1)[:1500])
    rounds = comp.get("rounds") or []
    print("\n--- rounds: %s db ---" % len(rounds))
    if rounds:
        print("    egy fordulo osszes mezoje:\n%s" % json.dumps(rounds[0], ensure_ascii=False, indent=1)[:1500])
        kulcsok = sorted({k for r in rounds for k in r})
        print("\n    minden mezonev: %s" % kulcsok)
        print("\n    fordulonkent (elso 12):")
        for r in rounds[:12]:
            print("      %s" % json.dumps({k: r.get(k) for k in kulcsok if k not in
                                           ("created_at", "updated_at")}, ensure_ascii=False)[:300])

# kontroll: a ranglista helyes elotaggal (a 4. korben lemaradt a competitions/3/)
st, j = hoz("competitions/3/rankings?include=user_team.user.id,summary_statistics,ranking,"
            "rounds,competition_rank&page=1&per_page=1")
d = ((j or {}).get("data") or [{}])[0]
ut_ = d.get("user_team") or {}
print("\n=== kontroll: rankings HTTP %s, fordulok=%s" % (
    st, [(s.get("round_number"), s.get("points")) for s in (ut_.get("round_statistics") or [])]))

print("\n--- vege ---")
