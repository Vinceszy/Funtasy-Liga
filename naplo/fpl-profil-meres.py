#!/usr/bin/env python3
"""EGYSZERI meres a jatekosprofil PL-oldalahoz.

Az MLSZ-oldal mar tisztazva (naplo/mlsz-jatekoslista.txt):
  - a teljes torzs egy keresbol megjon (players?per_page=500);
  - egy jatekos EGESZ szezonjanak teteles pontbontasa is megjon
    (game-player-stats?filter[competition_player_id]=X, fordulo-szuro
    NELKUL) - es ezt a bongeszo maga is hivhatja, ahogy ma is teszi.

A PL-oldalon ket dolog hianyzik a profilhoz:
  1) egy jatekos FORDULONKENTI pontja akkor is, amikor SENKINEL sem volt
     (a draft_history.json csak a kereteket orzi);
  2) az adott fordulos ELLENFEL es eredmeny (a lezart fordulok meccseit ma
     a bongeszo keri le fordulonkent, event/{gw}/fixtures).

Ez a meres azt kerdezi, van-e olyan vegpont, ami egy JATEKOS egesz
szezonjat egy keresbol adja - a klasszikus FPL element-summary pontosan
ilyen. A kerdes, hogy (a) elerheto-e, (b) UGYANAZOK-e az azonositok, mint
a Draft-jatekban. A (b)-t nem hisszuk el, hanem OSSZEVETJUK a repoban levo
draft_history.json 1. fordulos pontjaival.

Csak olvas; a naplot a workflow commitolja.
"""
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import collect_draft  # fetch, B

import urllib.error, urllib.parse, urllib.request

GYOKER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAPLO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fpl-profil.txt")
sorok = []
ki = sorok.append


def get(url, retries=2):
    """Nyers lekeres tetszoleges hoszra (a collect_draft.fetch mindig a Draft
    eloteteet teszi ele)."""
    keres = urllib.request.Request(url, headers={
        "Accept": "application/json",
        "User-Agent": "funtasy-archiver/1.0"})
    for i in range(retries):
        try:
            with urllib.request.urlopen(keres, timeout=30) as v:
                return v.status, json.loads(v.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            return e.code, None
        except Exception as e:
            if i == retries - 1:
                return "hiba: %s" % e, None
    return None, None


def meret(o):
    return len(json.dumps(o, separators=(",", ":")))


# ---- referencia: mit tudunk MAR a repobol? ----
with open(os.path.join(GYOKER, "draft_history.json"), encoding="utf-8") as f:
    tortenet = json.load(f)["rounds"]
with open(os.path.join(GYOKER, "draft_players.json"), encoding="utf-8") as f:
    torzs = json.load(f)["players"]

gw = sorted(tortenet, key=int)[0]
ismert = {}                       # element -> pont az adott forduloban
for lista in tortenet[gw].values():
    for p in lista:
        ismert[p["e"]] = p["pts"]
minta = sorted(ismert, key=lambda e: -ismert[e])[:5]

ki("# PL profil-meres. Referencia: a repo draft_history.json %s. forduloja." % gw)
ki("# Ismert (Draft) pontok az osszevetéshez:")
for e in minta:
    ki("#   element %-4s %-16s -> %s pont" % (e, (torzs.get(str(e)) or {}).get("n"), ismert[e]))
ki("")

# ---- 1) van-e element-summary a DRAFT API-ban? ----
ki("## 1) element-summary a Draft API-ban")
for e in minta[:2]:
    st, j = get(collect_draft.B + "element-summary/%d" % e)
    kulcsok = sorted(j.keys()) if isinstance(j, dict) else None
    ki("=== draft element-summary/%-4s -> HTTP %s | kulcsok: %s" % (e, st, kulcsok))
    if isinstance(j, dict) and isinstance(j.get("history"), list) and j["history"]:
        ki("    history[0]: %s" % json.dumps(j["history"][0], ensure_ascii=False)[:400])
        ki("    history hossz: %d | valasz merete: %d bajt" % (len(j["history"]), meret(j)))
ki("")

# ---- 2) a KLASSZIKUS FPL element-summary: elerheto-e, es stimmel-e az azonosito? ----
ki("## 2) klasszikus FPL element-summary - es EGYEZNEK-E AZ AZONOSITOK?")
KL = "https://fantasy.premierleague.com/api/"
for e in minta:
    st, j = get(KL + "element-summary/%d/" % e)
    if not isinstance(j, dict):
        ki("=== klasszikus element-summary/%-4s -> HTTP %s" % (e, st))
        continue
    hist = j.get("history") or []
    sor = next((h for h in hist if str(h.get("round")) == str(gw)), None)
    ki("=== klasszikus element-summary/%-4s -> HTTP %s | history=%d | %d bajt"
       % (e, st, len(hist), meret(j)))
    if sor:
        ki("    %s. fordulo: %s pont (a Draftban: %s) %s"
           % (gw, sor.get("total_points"), ismert[e],
              "EGYEZIK" if sor.get("total_points") == ismert[e] else "!!! ELTER"))
        ki("    a sor mezoi: %s" % sorted(sor.keys()))
        ki("    ellenfel/eredmeny mezok: opponent_team=%s was_home=%s team_h_score=%s team_a_score=%s"
           % (sor.get("opponent_team"), sor.get("was_home"),
              sor.get("team_h_score"), sor.get("team_a_score")))
ki("")

# ---- 3) mennyibe kerul a fordulonkenti tarolas (a masik ut)? ----
ki("## 3) a masik ut: fordulonkent EGY keres mindenkire (event/{gw}/live)")
st, j = get(collect_draft.B + "event/%s/live" % gw)
el = (j or {}).get("elements") if isinstance(j, dict) else None
if isinstance(el, dict):
    k = list(el)[0]
    ki("=== event/%s/live -> HTTP %s | %d jatekos | %d bajt" % (gw, st, len(el), meret(j)))
    ki("    egy elem kulcsai: %s" % sorted(el[k].keys()))
    ki("    stats: %s" % json.dumps((el[k].get("stats") or {}), ensure_ascii=False)[:400])
    csak_pont = {i: (v.get("stats") or {}).get("total_points") for i, v in el.items()
                 if (v.get("stats") or {}).get("total_points")}
    ki("    ha CSAK a nem-nulla pontot tarolnank: %d jatekos, %d bajt/fordulo"
       % (len(csak_pont), meret(csak_pont)))
else:
    ki("=== event/%s/live -> HTTP %s (nincs elements)" % (gw, st))
ki("")

ki("## 4) a fordulo meccsei (a tarolando meccsfajlhoz)")
st, fx = get(collect_draft.B + "event/%s/fixtures" % gw)
if isinstance(fx, list) and fx:
    ki("=== event/%s/fixtures -> HTTP %s | %d meccs | %d bajt" % (gw, st, len(fx), meret(fx)))
    ki("    egy meccs kulcsai: %s" % sorted(fx[0].keys()))
else:
    ki("=== event/%s/fixtures -> HTTP %s" % (gw, st))

# ---- 5) a ket hianyzo reszlet: van-e total_points, es van-e osszpont a torzsben? ----
ki("")
ki("## 5) a ket hianyzo reszlet")
st, j = get(collect_draft.B + "element-summary/%d" % minta[0])
h = ((j or {}).get("history") or [None])[0] if isinstance(j, dict) else None
if h:
    ki("=== draft element-summary history-sor MINDEN mezoje:")
    ki("    %s" % sorted(h.keys()))
    ki("    total_points=%s (a Draftban ismert: %s) | detail=%r | event=%s"
       % (h.get("total_points"), ismert[minta[0]], h.get("detail"), h.get("event")))
    fx = (j or {}).get("fixtures") or []
    ki("    fixtures: %d jovobeli meccs, elso: %s"
       % (len(fx), json.dumps(fx[0], ensure_ascii=False)[:200] if fx else "-"))
st, bs = collect_draft.fetch("bootstrap-static")
el = (bs or {}).get("elements") if isinstance(bs, dict) else None
if el:
    ki("=== draft bootstrap-static: egy jatekos MINDEN mezoje:")
    ki("    %s" % sorted(el[0].keys()))
    p0 = next((x for x in el if x.get("id") == minta[0]), el[0])
    ki("    %s: total_points=%s event_points=%s"
       % (p0.get("web_name"), p0.get("total_points"), p0.get("event_points")))

with open(NAPLO, "w", encoding="utf-8") as f:
    f.write("\n".join(sorok) + "\n")
print("\n".join(sorok))
