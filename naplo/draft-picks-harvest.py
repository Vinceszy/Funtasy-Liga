#!/usr/bin/env python3
"""The draft itself, stored once: who chose whom, when, and in which round.

The draft happened once and never changes, so this is not collector work -
it runs by hand and writes draft_picks.json.

TWO IDS. The choices name a team by its FPL entry id; everything we store
uses the league-entry id. The mapping is in the league details, and the
real entry id never reaches the file - that is the same id the collector
refuses to write, because the repository is public.

NAMES DO NOT GO IN EITHER. The response carries real player and manager
names; only ids, round, pick, whether the clock made the choice, and how
long it took come out.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

B = "https://draft.premierleague.com/api/"
HDRS = {"Accept": "application/json", "Accept-Language": "en-GB,en;q=0.9",
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")}
GYOKER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KI = os.path.join(GYOKER, "draft_picks.json")
TILTOTT = ("player_first_name", "player_last_name", "entry_name", "short_name")


def js(path):
    try:
        req = urllib.request.Request(B + path, headers=HDRS)
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception as e:                                   # noqa: BLE001
        print("  ! %s: %s" % (path, e))
        return 0, None


def main():
    liga = os.environ.get("LEAGUE_ID") or str(
        json.load(open(os.path.join(GYOKER, "draft.json"), encoding="utf-8"))
        .get("league", {}).get("id") or "")
    if not liga:
        print("nincs liga-azonosito"); return 1
    print("liga: %s" % liga)

    st, det = js("league/%s/details" % liga)
    if st != 200 or not det:
        print("league details: HTTP %s - megallunk" % st); return 1
    # entry (valodi csapat-azonosito) -> league_entry (amit mi tarolunk)
    terkep = {}
    for e in det.get("league_entries") or []:
        if e.get("entry") is not None and e.get("id") is not None:
            terkep[str(e["entry"])] = str(e["id"])
    print("csapat-leképezés: %d" % len(terkep))

    st, ch = js("draft/%s/choices" % liga)
    if st != 200 or not ch:
        print("choices: HTTP %s - megallunk" % st); return 1
    valasztasok = ch.get("choices") or []
    print("valasztas: %d" % len(valasztasok))

    ki, parositatlan = [], 0
    for c in valasztasok:
        t = terkep.get(str(c.get("entry")))
        if not t:
            parositatlan += 1
            continue
        ki.append({"r": c.get("round"), "p": c.get("pick"), "i": c.get("index"),
                   "e": c.get("element"), "t": t,
                   "auto": bool(c.get("was_auto")),
                   "sec": c.get("seconds_to_pick")})
    ki.sort(key=lambda x: (x["i"] if x["i"] is not None else 0))
    # A parositatlan valasztast KIIRJUK: csendben eldobva egy csapat draftja
    # tunne el, es azt a szovegen mar nem lehetne eszrevenni.
    print("parositatlan valasztas: %d" % parositatlan)
    if parositatlan:
        print("  ! a csapat-leképezés hiányos - a fájl NEM készül el")
        return 1

    korok = max([x["r"] for x in ki] or [0])
    csapatok = len({x["t"] for x in ki})
    print("korok: %d | csapatok: %d" % (korok, csapatok))
    for t in sorted({x["t"] for x in ki}):
        sajat = [x for x in ki if x["t"] == t]
        auto = sum(1 for x in sajat if x["auto"])
        print("   %s: %d valasztas, ebbol gepi: %d, elso kore: %d. osszesitett hely"
              % (t, len(sajat), auto, min(x["i"] for x in sajat)))

    tartalom = {"updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "league": int(liga), "rounds": korok, "picks": ki}
    szoveg = json.dumps(tartalom, ensure_ascii=False, separators=(",", ":"))
    for tilt in TILTOTT:
        if tilt in szoveg:
            print("HIBA: '%s' a kimenetben - a mentes megszakitva." % tilt)
            return 1
    open(KI, "w", encoding="utf-8").write(szoveg)
    print("kiirva: draft_picks.json (%d bajt)" % len(szoveg))
    return 0


if __name__ == "__main__":
    sys.exit(main())
