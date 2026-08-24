#!/usr/bin/env python3
"""EGYSZERI meres: hogyan viselkednek a PERCEK elo meccs alatt?

Ez a "ki van meg a palyan" funkcio elokeszitese. Harom kerdes:
  1) A lecserelt jatekos percszama tenyleg BEFAGY-e, mikozben a meccsora
     tovabb ketyeg? (Ebbol lesz a "lecserelve" jelzes.)
  2) Mekkora a CSUSZAS a ket vegpont kozott? A live (jatekos-percek) es a
     fixtures (meccsora) ket kulon keres; ha a szerver oldalan nem egyszerre
     frissulnek, egy palyan levo jatekos egy pillanatra lecsereltnek tunhet.
     Ez donti el, mekkora tureshatar kell.
  3) A becserelt jatekos percei tenyleg a beallastol szamolodnak-e.

Amit tudunk mar (Vince): a meccsora 45-nel es 90-nel megall.

Minden mintat kiir, nem csak a valtozast: itt eppen az idobeli lefutas az
erdekes. Csak olvas; az eredmenyt a workflow commitolja.
"""
import datetime, json, os, sys, urllib.request

HDRS = {"Accept": "application/json", "User-Agent": "Mozilla/5.0 funtasy-percmeres/1.0"}
NAPLO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fpl-percek.txt")


def hoz(url, timeout=30):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=HDRS), timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return {"__hiba": "%s: %s" % (type(e).__name__, e)}


most = datetime.datetime.now(datetime.timezone.utc)
game = hoz("https://draft.premierleague.com/api/game")
gw = game.get("current_event")
if not gw:
    sys.exit(0)

# A ket vegpontot EGYMAS UTAN, a lehető legkozelebb kerjuk le: a koztuk
# eltelt ido a meres hibahatara, ezert ki is irjuk.
t0 = datetime.datetime.now(datetime.timezone.utc)
fx = hoz("https://draft.premierleague.com/api/event/%d/fixtures" % gw)
t1 = datetime.datetime.now(datetime.timezone.utc)
live = hoz("https://draft.premierleague.com/api/event/%d/live" % gw)
t2 = datetime.datetime.now(datetime.timezone.utc)
if not isinstance(fx, list) or "__hiba" in live:
    sys.exit(0)

# csak az eppen zajlo meccs(ek) erdekesek
elok = [m for m in fx if m.get("started") and not m.get("finished")]
if not elok:
    sys.exit(0)

# jatekos -> klub a repoban levo listabol (nem kell hozza uj lekeres)
adat = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   "..", "draft_players.json"), encoding="utf-8"))
KLUB = {int(k): v["t"] for k, v in adat["players"].items()}
CSAPAT = {int(k): v for k, v in adat["teams"].items()}
el = live.get("elements") or {}


def st(eid):
    return ((el.get(str(eid)) or el.get(eid) or {}).get("stats") or {})


ujfajl = not os.path.exists(NAPLO)
with open(NAPLO, "a", encoding="utf-8") as f:
    if ujfajl:
        f.write("# Elo meccs perc-merese. Minden minta egy sor (UTC).\n"
                "# mora = a meccs oraja | dt = a ket vegpont lekerese kozt eltelt ms\n"
                "# jatekos: <id>:<perc>[k=kezdo, b=csere, R=piros]\n")
    for m in elok:
        h, a = CSAPAT.get(m.get("team_h"), "?"), CSAPAT.get(m.get("team_a"), "?")
        jatekosok = [e for e, klub in KLUB.items() if klub in (h, a)]
        # csak akit egyaltalan erint: kezdo vagy mar jatszott
        sorok = []
        for e in sorted(jatekosok):
            s = st(e)
            perc, kezdo = s.get("minutes") or 0, s.get("starts") or 0
            if not perc and not kezdo:
                continue
            jel = "k" if kezdo else "b"
            if s.get("red_cards"):
                jel += "R"
            sorok.append("%d:%d%s" % (e, perc, jel))
        f.write("%s  %s-%s  mora=%s  allas=%s-%s  fp=%s f=%s  dt=%dms | %s\n" % (
            most.strftime("%H:%M:%S"), h, a, m.get("minutes"),
            m.get("team_h_score"), m.get("team_a_score"),
            1 if m.get("finished_provisional") else 0, 1 if m.get("finished") else 0,
            int((t2 - t0).total_seconds() * 1000), " ".join(sorok)))
print("minta rogzitve (%d elo meccs)" % len(elok))
