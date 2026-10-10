#!/usr/bin/env python3
"""Mi tortenik a 9. forduloval? - az MLSZ sajat valasza, nem a mi olvasatunk.

A gyujto 2026-09-20 ota nem irt uj NB1 eredmenyt. Minden futasban ugyanaz a
ket sor all a naploban: "az MLSZ szerinti aktualis fordulo: 9" es
". 9. fordulo keretei meg nem elerhetok (piaczaras elott)". Ez utobbi egy
403-bol kovetkeztetes - a meres azt nezi meg, igaz-e a kovetkeztetes.

Negy kerdest tesz fel, mindegyiket kulon kiirva:
  1. mit mond az MLSZ a 8-11. fordulo objektumarol (start_at, end_at,
     is_transfers_closed, closed_transfers_at) - ebbol latszik, tenyleg
     nyitva van-e meg az atigazolasi piac;
  2. mit ad a keret-vegpont MINDEN szakvezetore a 9. forduloban (a gyujto
     csak EGYET kerdez meg, es abbol altalanosit);
  3. mit ir a ranglista a 9. fordulohoz (van-e egyaltalan sora, es mennyi);
  4. van-e meccs a 9. forduloban, es ha igen, mikor.

A valasz a naplo/nb1-fordulo-allas.txt-be kerul, nem a futas logjaba: a log
napok alatt olvashatatlanna valik, es egy korabbi meres pont ezert veszett el.
"""
import json
import os
import sys
import importlib.util

GYOKER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KI = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nb1-fordulo-allas.txt")

spec = importlib.util.spec_from_file_location("collect", os.path.join(GYOKER, "collect.py"))
c = importlib.util.module_from_spec(spec)
sys.modules["collect"] = c
spec.loader.exec_module(c)

sorok = []


def ir(s=""):
    print(s)
    sorok.append(s)


ir("=" * 70)
ir("MERES: a 9. NB1 fordulo allapota az MLSZ szerint")
ir("ido: " + c.stamp())
ir("=" * 70)

# ---- 1) a fordulo-objektumok nyersen ----
ir("")
ir("1) VERSENY + FORDULOK (competitions?include=rounds,current_round)")
st, j = c.api_get(c.ROOT + "competitions?include=rounds,current_round")
ir("   HTTP %s" % st)
if st == 200 and isinstance(j, dict):
    comp = next((x for x in (j.get("data") or []) if x.get("id") == c.COMPETITION), None) or {}
    cr = comp.get("current_round") or {}
    ir("   current_round: szam=%s id=%s" % (cr.get("round_number"), cr.get("id")))
    ir("   current_round nyersen: %s" % json.dumps(cr, ensure_ascii=False))
    ir("   a fordulo-objektumok mezoi: %s"
       % sorted({k for r in (comp.get("rounds") or []) for k in r}))
    for r in sorted(comp.get("rounds") or [], key=lambda x: x.get("round_number") or 0):
        if 7 <= (r.get("round_number") or 0) <= 11:
            ir("   %2s. fordulo: %s" % (r.get("round_number"),
                                        json.dumps(r, ensure_ascii=False)))
else:
    ir("   nem ertelmezheto valasz")

# ---- 2) a keret-vegpont MINDEN szakvezetore ----
ir("")
ir("2) KERET-VEGPONT a 8. es a 9. fordulora, MINDEN szakvezetore")
ir("   (a gyujto csak az ELSO szakvezetot kerdezi meg, es a 403-bol")
ir("    'piaczaras elott'-ra kovetkeztet - itt latszik, egysegesek-e)")
ids = {}
for nev, uname in c.MEMBERS.items():
    sor = c.rankings(uname)
    if not sor:
        ir("   ! nincs ranglista-adat: %s" % nev)
        continue
    ids[nev] = ((sor.get("user_team") or {}).get("user") or {}).get("id")
for r in (8, 9):
    for nev, uid in ids.items():
        st2, j2 = c.squad(uid, r)
        db = len((j2 or {}).get("data") or []) if isinstance(j2, dict) else 0
        ir("   %s. fordulo | %-10s -> HTTP %s, %d jatekos" % (r, nev, st2, db))

# ---- 3) mit ir a ranglista a 9. fordulohoz ----
ir("")
ir("3) RANGLISTA round_statistics (van-e egyaltalan 9. fordulos sor)")
for nev, uname in c.MEMBERS.items():
    sor = c.rankings(uname)
    if not sor:
        continue
    st3 = (sor.get("user_team") or {}).get("round_statistics") or []
    volt = {int(s["round_number"]): s.get("points") for s in st3}
    ir("   %-10s fordulok: %s" % (nev, json.dumps(volt, ensure_ascii=False)))

# ---- 4) van-e meccs a 9. forduloban ----
ir("")
ir("4) A 9. FORDULO MECCSEI (a keret-vegpont games-agan keresztul)")
if ids:
    uid = next(iter(ids.values()))
    st4, j4 = c.squad(uid, 9, jatek=True)
    ir("   HTTP %s" % st4)
    if st4 == 200 and isinstance(j4, dict):
        meccsek = {}
        for p in j4.get("data") or []:
            for g in (p.get("games") or []):
                meccsek[g.get("id")] = g
        ir("   kulonbozo meccs: %d" % len(meccsek))
        for g in list(meccsek.values())[:12]:
            ir("     %s" % json.dumps({k: g.get(k) for k in
               ("id", "round_number", "start_at", "status", "is_played",
                "home_score", "away_score")}, ensure_ascii=False))
    else:
        ir("   a keret nem kerheto le, tehat a meccslista sem jon vele")

ir("")
ir("=" * 70)
with open(KI, "a", encoding="utf-8") as f:
    f.write("\n".join(sorok) + "\n")
print("\nkiirva: %s (%d sor)" % (KI, len(sorok)))
