#!/usr/bin/env python3
"""Egyszeri diagnosztika, 3. kor (IDEIGLENES): honnan jon a pont-BONTAS?

A 2. kor a bundle-bol include-okat talalt (current_round.games,
round_statistics), de a teteles bontas vegpontjat nem: az utvonalak
template-literalokban lehetnek. Ez a kor:
  A) utvonal-szeru sztringek a bundle-bol (legalabb egy / jellel)
  B) kodkontextus a *statistics elofordulasok korul
  C) magyar cimkek (Kulcspassz, Gyozelem...) a kliensben vannak-e
  D) a talalt igeretes include-ok azonnali kiprobalasa az API-n

CSAK OLVAS es nyomtat.
"""
import json, re, sys, time, urllib.error, urllib.parse, urllib.request

M_BASE = "https://fantasy-api.mlsz.hu/competitions/3/"
UI = "https://fantasy.mlsz.hu/"
HDRS = {"Accept": "application/json", "User-Agent": "funtasy-archiver/1.0",
        "Referer": "https://fantasy.mlsz.hu/"}


def get(url, szoveg=False):
    time.sleep(0.2)
    try:
        req = urllib.request.Request(url, headers=HDRS)
        with urllib.request.urlopen(req, timeout=30) as r:
            adat = r.read().decode("utf-8", "replace")
            return r.status, adat if szoveg else json.loads(adat)
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception as e:
        return None, str(e)


def main():
    st, html = get(UI, szoveg=True)
    if st != 200:
        print("fooldal HTTP %s" % st); return 0
    utak = re.findall(r'(?:src|href)="([^"]+\.js[^"]*)"', html)
    js = ""
    for ut in utak:
        teljes = ut if ut.startswith("http") else UI.rstrip("/") + "/" + ut.lstrip("/")
        st, adat = get(teljes, szoveg=True)
        if st == 200 and isinstance(adat, str):
            js += adat
    print("bundle osszmeret: %d bajt" % len(js))

    print("\n========== A) utvonal-szeru sztringek ==========")
    minta = re.compile(r'["\'`]((?:[a-z0-9_\-]|\$\{[^}]*\})+(?:/(?:[a-z0-9_\-]|\$\{[^}]*\})+)+)["\'`]')
    for s in sorted(set(minta.findall(js))):
        if re.search(r'(player|round|statistic|user|team|competition|point)', s):
            print("  %s" % s)

    print("\n========== B) kontextus a statisztika-hivatkozasok korul ==========")
    for kulcs in ("round_statistics", "competition_statistics", "has_statistics"):
        for m in list(re.finditer(re.escape(kulcs), js))[:6]:
            resz = js[max(0, m.start() - 160):m.end() + 160].replace("\n", " ")
            print("[%s] ...%s..." % (kulcs, resz))
        print()

    print("========== C) magyar cimkek a kliensben? ==========")
    for cimke in ("Kulcspassz", "Gy\\u0151zelem", "Győzelem", "p\\u00e1rharc", "párharc",
                  "Percek a p", "Gólok", "G\\u00f3lok"):
        db = js.count(cimke)
        if db:
            m = re.search(re.escape(cimke), js)
            resz = js[max(0, m.start() - 120):m.end() + 200].replace("\n", " ")
            print("'%s' x%d: ...%s..." % (cimke, db, resz))
        else:
            print("'%s': nincs" % cimke)

    print("\n========== D) igeretes include-ok az API-n ==========")
    probak = [
        ("user-team-players-history", "competition_player.current_round.games,"
         "competition_player.current_round.games.home_team,"
         "competition_player.current_round.games.away_team"),
        ("user-team-players-history", "competition_player.current_round.round"),
        ("user-team-players-history", "competition_player.current_round.competition_player"),
        ("user-team-players-history", "round_statistics"),
        ("user-team-players-history", "competition_player.round_statistics.details"),
        ("user-team-players-history", "competition_player.round_statistics.statistics"),
    ]
    for vegpont, inc in probak:
        url = (M_BASE + vegpont + "?include=" + urllib.parse.quote(inc)
               + "&filter%5Buser_id%5D=5483&filter%5Bround_id%5D=83")
        st, j = get(url)
        if st == 200 and j and j.get("data"):
            print("+%s -> 200:" % inc)
            print(json.dumps(j["data"][0], ensure_ascii=False)[:1500])
        else:
            print("+%s -> HTTP %s" % (inc, st))

    print("\nDiagnosztika vege - semmit nem irt.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
