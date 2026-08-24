#!/usr/bin/env python3
"""EGYSZERI meres: mit csinal az FPL Draft a fordulo vegen a CSEREKKEL?

A pad sorrendje az FPL-ben csere-sorrend: a fordulo vegen az elso olyan
padost allitja be a nem jatszo kezdo helyere, aki formaciolag befer. Harom
kerdesre kell valasz, mielott az oldal barmit allit errol:

  1) A csere utan ATIRJA-e az FPL a pick "position" mezojet (12-15 -> 1-11)?
     Ha igen, a gyujtonk magatol rendbe jon, amint ujra lekeri a fordulot.
     Ha nem - kulon "subs" listaban adja -, akkor a tarolt pad-jelzonk
     ("b") hibas marad, es kulon kezeles kell hozza.
  2) MIKOR tortenik: rogton az utolso meccs utan, vagy a fordulo masnap
     reggeli zarasakor (2026/27-tol 09:00 UK)?
  3) Melyik mezo mondja meg, hogy a fordulo VEGLEG lezarult? Ez donti el,
     meddig kell a gyujtonek ujra lekernie egy mar lement fordulot. Ma csak
     az AKTUALIS fordulot frissiti, tehat amint a current_event tovabblep,
     a lezart fordulo befagy - benne a csere elotti allapottal.

Csak olvas. A naplot a workflow commitolja.

ADATVEDELEM: a repo publikus, ezert a naplo SOHA nem tartalmazhat entry_id-t
vagy valodi nevet. Csak a liga-belso azonosito (ami a draft.json-ban amugy is
benne van) es a jatekos-azonositok kerulnek bele.
"""
import datetime, json, os, sys, urllib.request

B = "https://draft.premierleague.com/api/"
KLASSZIKUS = "https://fantasy.premierleague.com/api/"
LEAGUE_ID = os.environ.get("DRAFT_LEAGUE_ID", "48093")
GW = int(os.environ.get("CSERE_GW", "1"))
HDRS = {"Accept": "application/json", "User-Agent": "Mozilla/5.0 funtasy-cseremeres/1.0"}
NAPLO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fpl-cserek.txt")


def hoz(url, timeout=30):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=HDRS), timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return {"__hiba": "%s: %s" % (type(e).__name__, e)}


most = datetime.datetime.now(datetime.timezone.utc)
sorok = []


def ki(s):
    sorok.append(s)


game = hoz(B + "game")
det = hoz(B + "league/%s/details" % LEAGUE_ID)
live = hoz(B + "event/%d/live" % GW)
allapot = hoz(KLASSZIKUS + "event-status/")

# ---- fordulo-allapot: MINDEN mezot kiirunk a game-bol, mert epp azt
# keressuk, melyik jelzi a vegleges zarast. Tippelni mar ketszer draga volt.
gsor = " ".join("%s=%s" % (k, json.dumps(v, ensure_ascii=False))
                for k, v in sorted(game.items()) if not isinstance(v, (dict, list)))

# ---- a fordulo hivatalos H2H eredmenyei (a tabella forrasa)
meccsek = [m for m in (det.get("matches") or []) if m.get("event") == GW]
kesz = sum(1 for m in meccsek if m.get("finished"))
msor = "meccs=%d/%d kesz" % (kesz, len(meccsek))

# ---- napi/fordulo zaras a klasszikus FPL-bol (ezt hasznalja a bonusz-jelzes)
esl = [s for s in (allapot.get("status") or []) if s.get("event") == GW]
esor = " ".join("%s/%s" % (s.get("points"), "bonus" if s.get("bonus_added") else "-")
                for s in esl) or "nincs"

perc = {}
el = (live or {}).get("elements") or {}
if isinstance(el, dict):
    for k, v in el.items():
        perc[int(k)] = ((v or {}).get("stats") or {}).get("minutes") or 0
elif isinstance(el, list):
    for v in el:
        perc[int((v or {}).get("id") or 0)] = ((v or {}).get("stats") or {}).get("minutes") or 0

ki("%s  cur=%s  %s  es=%s  %s" % (most.strftime("%m-%d %H:%M:%S"),
   game.get("current_event"), msor, esor, gsor))

# ---- keretek. entry_id CSAK memoriaban; a naplóba a liga-belso id megy.
entry2liga = {e.get("entry_id"): e.get("id") for e in (det.get("league_entries") or [])}
kulcsok_kiirva = False
for eid, lid in sorted(entry2liga.items(), key=lambda x: (x[1] or 0)):
    if not eid or not lid:
        continue
    ev = hoz(B + "entry/%d/event/%d" % (eid, GW))
    picks = ev.get("picks") or []
    if not picks:
        ki("  L%s  nincs keret (%s)" % (lid, ev.get("__hiba") or "ures"))
        continue
    # EGYSZER kiirjuk a valasz teljes szerkezetet: itt derulhet ki, hogy van
    # kulon "subs" mezo, amirol ma nem tudunk.
    if not kulcsok_kiirva:
        ki("  # entry/event kulcsok: %s" % sorted(ev.keys()))
        ki("  # pick kulcsok:        %s" % sorted(picks[0].keys()))
        # a szemelyes mezoket ki NE irjuk: a repo publikus
        TILTOTT = {"picks", "entry", "entry_id", "player_first_name",
                   "player_last_name", "name", "player_name"}
        for k, v in sorted(ev.items()):
            if k in TILTOTT:
                continue
            ki("  # entry.%s = %s" % (k, json.dumps(v, ensure_ascii=False)[:300]))
        kulcsok_kiirva = True
    ren = sorted(picks, key=lambda p: p.get("position") or 0)
    kezdo = [p.get("element") for p in ren if (p.get("position") or 0) <= 11]
    pad = [p.get("element") for p in ren if (p.get("position") or 0) > 11]
    # akinek 0 perce van a kezdok kozul, az a csere JELOLTJE - ha az FPL
    # cserel, ennek kell eltunnie a kezdok kozul
    nullas = [e for e in kezdo if perc.get(e, 0) == 0]
    ki("  L%s  kezdo=%s  pad=%s  0perces_kezdo=%s"
       % (lid, kezdo, pad, nullas))

uj = "\n".join(sorok) + "\n"
regi = ""
if os.path.exists(NAPLO):
    with open(NAPLO, encoding="utf-8") as f:
        regi = f.read()

# Csak VALTOZASKOR irunk - kulonben a naplo elfedne, mikor tortent valami.
# Az osszehasonlitasbol az elso (idobelyeges) sor kimarad.
def torzs(t):
    return "\n".join(l for l in t.strip().split("\n") if not l[:1].isdigit())


utolso = regi.strip().split("\n\n")[-1] if regi.strip() else ""
if torzs(uj) == torzs(utolso):
    # oranként egy eletjel, hogy latszodjon: futott, csak nem valtozott
    if most.minute >= 50:
        with open(NAPLO, "a", encoding="utf-8") as f:
            f.write("%s  (valtozatlan)\n\n" % most.strftime("%m-%d %H:%M:%S"))
    sys.exit(0)

with open(NAPLO, "a", encoding="utf-8") as f:
    f.write(uj + "\n")
print(uj)
