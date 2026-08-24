#!/usr/bin/env python3
"""EGYSZERI meres: mit ad az MLSZ API, amibol az NB1 megkaphatna a
PL-oldalon mar mukodo adatokat (jatszott perc, kezdo-e, meccseredmeny)?

Negy kerdes, mindegyik a beepitest donti el - ADDIG NEM allitunk semmit:

  1) A LEZART fordulos keret-valasz meccs-objektumaban van-e EREDMENY
     (es ellenfel)? A gyujto docstringje szerint a kesz meccs melle az API
     a ket csapatot is beteszi (a valasz 17->118 KB) - de a pontszam-mezot
     meg sosem neztuk meg. Ha van, a bontas folotti allas-sor az NB1-en is
     megepitheto.
  2) A game-player-stats vegpont mukodik-e CSAK round_id szurovel (jatekos
     nelkul)? Ha igen, a jatszott perc egy keresbol megvan a fordulo OSSZES
     jatekosara -> oszlop lehet a keretlistaban. Ha nem, a perc csak a
     lenyiloban maradhat (ott ma is megvan).
  3) Van-e barhol "kezdo volt-e" adat? A stat-config teljes nevlistajat
     es egy jatekos OSSZES nyers sorat (a 0 pontosakat is) kiirjuk.
  4) A current_round objektum teljes kulcslistaja - hatha van olyan mezo,
     amit eddig nem hasznaltunk (pl. kezdo-jelzes).

A collect.py fuggvenyeit importaljuk (api_get, squad, MEMBERS, rankings),
nem masoljuk. Csak olvas; a naplot a workflow commitolja.

ADATVEDELEM: a repo publikus. A naplóba MLSZ user_id nem kerul (a
felhasznalonevek amugy is a repoban vannak, de az id-t sem irjuk ki);
a labdarugok neve nyilvanos adat. A base64 kepadatot (klublogo) levagjuk.
"""
import json, os, sys, urllib.parse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import collect  # api_get, squad, MEMBERS, rankings, rid, ROOT

NAPLO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mlsz-adat.txt")
R = int(os.environ.get("MERES_FORDULO", "1"))     # lezart fordulo
sorok = []
ki = sorok.append


def rovidit(v, hossz=160):
    """Hosszu erteket (base64 logo!) levag, a szerkezetet megtartja."""
    if isinstance(v, str) and len(v) > hossz:
        return "<%d karakteres szoveg>" % len(v)
    if isinstance(v, dict):
        return {k: rovidit(x, hossz) for k, x in v.items()}
    if isinstance(v, list):
        return [rovidit(x, hossz) for x in v[:4]] + (["<+%d elem>" % (len(v) - 4)] if len(v) > 4 else [])
    return v


def dump(cim, obj):
    ki("--- %s ---" % cim)
    ki(json.dumps(rovidit(obj), ensure_ascii=False, indent=1))


# ---- egy resztvevo user_id-ja (csak memoriaban, a naploba nem kerul) ----
uid = None
for nev, uname in collect.MEMBERS.items():
    row = collect.rankings(uname)
    if row:
        uid = ((row.get("user_team") or {}).get("user") or {}).get("id")
        if uid:
            break
if not uid:
    ki("! nincs elerheto resztvevo - a ranglista nem valaszolt")

# ---- 1+4) lezart fordulos keret a meccslistaval ----
if uid:
    st, j = collect.squad(uid, R, jatek=True)
    ki("=== 1) keret-valasz a %d. fordulora (meccslistaval) -> HTTP %s" % (R, st))
    talalt_meccs = talalt_cr = False
    for d in (j or {}).get("data") or []:
        cp = d.get("competition_player") or {}
        cr = cp.get("current_round") or {}
        games = cr.get("games") or []
        if not talalt_cr and cr:
            ki("=== 4) current_round OSSZES kulcsa: %s" % sorted(cr.keys()))
            talalt_cr = True
        if not talalt_meccs and games:
            nevj = " ".join(x for x in (cp.get("first_name"), cp.get("last_name")) if x)
            ki("    (a meccs %s jatekosanal)" % nevj)
            dump("a meccs-objektum TELJES tartalma", games[0])
            talalt_meccs = True
        if talalt_meccs and talalt_cr:
            break
    if not talalt_meccs:
        ki("! egyetlen jatekosnal sincs meccslista a valaszban")

# ---- 2) game-player-stats CSAK round_id szurovel ----
for cimke, url in [
    ("round-only", collect.ROOT + "game-player-stats?include=competition_stat_config"
     "&filter%%5Bround_id%%5D=%d" % collect.rid(R)),
    ("round+competition", collect.ROOT + "game-player-stats?include=competition_stat_config"
     "&filter%%5Bround_id%%5D=%d&filter%%5Bcompetition_id%%5D=3" % collect.rid(R)),
]:
    st, j = collect.api_get(url)
    n = len((j or {}).get("data") or []) if isinstance(j, dict) else None
    ki("=== 2) game-player-stats %s -> HTTP %s, sorok: %s" % (cimke, st, n))
    if st == 200 and n:
        dump("elso sor", j["data"][0])

# ---- 3) egy sokperces es egy 0 perces jatekos OSSZES nyers sora ----
try:
    with open(os.path.join(os.path.dirname(NAPLO), "..", "squad_history.json"), encoding="utf-8") as f:
        hist = json.load(f)
    keretek = hist["rounds"].get(str(R)) or {}
    jeloltek = []
    for sq in keretek.values():
        for p in sq:
            if p.get("id"):
                jeloltek.append(p)
    sokperces = next((p for p in jeloltek if (p.get("week") or 0) > 0), None)
    nullas = next((p for p in jeloltek if not p.get("week")), None)
except Exception as e:
    sokperces = nullas = None
    ki("! squad_history nem olvashato: %s" % e)

statnevek = set()
for p in (sokperces, nullas):
    if not p:
        continue
    url = (collect.ROOT + "game-player-stats?include=competition_stat_config"
           + "&filter%%5Bcompetition_player_id%%5D=%s&filter%%5Bround_id%%5D=%d"
           % (p["id"], collect.rid(R)))
    st, j = collect.api_get(url)
    ki("=== 3) %s (%s, %s pont) -> HTTP %s" % (p.get("name"), p.get("team"), p.get("week"), st))
    for s in (j or {}).get("data") or []:
        nevs = (s.get("competition_stat_config") or {}).get("name") or "?"
        statnevek.add(nevs)
        ki("    %-45s ertek=%-6s pont=%s" % (nevs, s.get("value"), s.get("points")))

ki("=== stat-nevek osszesen: %s" % sorted(statnevek))

with open(NAPLO, "w", encoding="utf-8") as f:
    f.write("\n".join(sorok) + "\n")
print("\n".join(sorok))
