#!/usr/bin/env python3
"""FunTasy Liga - FPL Draft liga adatainak gyujtese.

A vegpont bejelentkezes nelkul is elerheto, ezert ez a resz - az MLSZ-keretekkel
ellentetben - teljesen automatizalhato, es egyszerre adja a resztvevoket, a
teljes menetrendet es az eredmenyeket. Menetrendet nem kell kezzel bevinni.

FONTOS - adatvedelem:
A vegpont valaszaban a resztvevok VALODI NEVE is szerepel
(player_first_name / player_last_name). Ez a repo publikus, ezert a szkript
soha nem menti a nyers valaszt: az entries listat mezonkent epiti fel, es
csak a csapatnevet (entry_name) meg a monogramot (short_name) veszi at.
Ha valaki kesobb bovitene, ezt a szabalyt tartsa meg.

FONTOS - ket kulonbozo azonosito:
Minden resztvevonek van egy "entry_id"-ja (az FPL csapat azonositoja) es egy
"id"-ja (a ligan beluli azonosito). A matches es a standings az "id"-ra
hivatkozik, NEM az entry_id-ra. Ezt osszekeverni nema hiba: rossz nevek
kerulnenek a meccsek melle.

FONTOS - le nem jatszott fordulo:
A meg le nem jatszott meccsek 0-0-val jonnek vissza. Ezeket None-kent
mentjuk, nem 0-0-kent, kulonben lejatszott dontetlennek latszananak - ez
ugyanaz a csapda, mint a results.json-nal. A vegpont ad "finished" jelzot,
tehat itt nem kell talalgatni.

A liga azonositoja a DRAFT_LEAGUE_ID kornyezeti valtozobol felulirhato.
"""
import json, os, sys, time, urllib.error, urllib.request

LEAGUE_ID = os.environ.get("DRAFT_LEAGUE_ID", "48093")
URL = "https://draft.premierleague.com/api/league/%s/details" % LEAGUE_ID
OUT = "draft.json"

HDRS = {
    "Accept": "application/json",
    "Accept-Language": "en-GB,en;q=0.9",
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"),
}


def fetch(retries=3):
    """Visszaad: (adat, None) siker eseten, (None, hibauzenet) egyebkent."""
    msg = "ismeretlen hiba"
    for i in range(retries):
        try:
            req = urllib.request.Request(URL, headers=HDRS)
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode("utf-8")), None
        except urllib.error.HTTPError as e:
            body = ""
            try:
                body = e.read().decode("utf-8", "replace")[:300]
            except Exception:
                pass
            msg = "HTTP %s %s | valasz eleje: %s" % (e.code, e.reason, body or "(ures)")
            if e.code in (401, 403, 404):   # ezek nem javulnak ujraprobalastol
                return None, msg
        except Exception as e:
            msg = "%s: %s" % (type(e).__name__, e)
        if i == retries - 1:
            return None, msg
        time.sleep(3)
    return None, msg


def atalakit(data):
    """A nyers valaszbol a mentendo szerkezetet epiti - valodi nevek nelkul.

    A visszaadott 'schedule' szandekosan ugyanolyan alaku, mint a results.json-e:
    {"1": [[hazai_id, vendeg_id, hazai_pont, vendeg_pont], ...]}
    A pontok None-ok, amig a meccs nincs lejatszva.
    """
    liga = data.get("league") or {}

    # Csak a megengedett mezok - a nyers elemet SOHA nem masoljuk at egyben.
    entries = []
    for e in data.get("league_entries") or []:
        entries.append({
            "id": e.get("id"),
            "name": e.get("entry_name") or "",
            "short": e.get("short_name") or "",
        })
    entries.sort(key=lambda x: (x["name"] or "").lower())

    schedule, lejatszott = {}, 0
    for m in data.get("matches") or []:
        rnd = str(m.get("event"))
        kesz = bool(m.get("finished"))
        hp = m.get("league_entry_1_points") if kesz else None
        vp = m.get("league_entry_2_points") if kesz else None
        if kesz:
            lejatszott += 1
        schedule.setdefault(rnd, []).append(
            [m.get("league_entry_1"), m.get("league_entry_2"), hp, vp])

    allas = []
    for s in data.get("standings") or []:
        allas.append({
            "id": s.get("league_entry"),
            "rank": s.get("rank"),
            "played": s.get("matches_played"),
            "won": s.get("matches_won"),
            "drawn": s.get("matches_drawn"),
            "lost": s.get("matches_lost"),
            "for": s.get("points_for"),
            "against": s.get("points_against"),
            "total": s.get("total"),
        })

    return {
        "updated": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "league": {
            "id": liga.get("id"),
            "name": liga.get("name") or "",
            "start_event": liga.get("start_event"),
            "stop_event": liga.get("stop_event"),
        },
        "entries": entries,
        "schedule": schedule,
        "standings": allas,
    }, lejatszott


def nevszures(payload):
    """Biztonsagi halo: ha barhogy valodi nev keveredne a kimenetbe, alljunk le."""
    szoveg = json.dumps(payload, ensure_ascii=False)
    for tiltott in ("player_first_name", "player_last_name", "entry_id"):
        if tiltott in szoveg:
            raise SystemExit("HIBA: '%s' a kimenetben - a mentes megszakitva." % tiltott)


def main():
    print("FPL Draft liga lekerese")
    print("  liga azonosito: %s" % LEAGUE_ID)
    print("  vegpont:        %s" % URL)

    data, err = fetch()
    if err:
        print("\n  ! NEM SIKERULT: %s" % err, file=sys.stderr)
        print("\n  Mit jelent ez:")
        print("   - 403 vagy 401 -> a vegpont bejelentkezest var, vagy tiltja az")
        print("     adatkozponti IP-t. Ilyenkor konyvjelzos megoldas kell.")
        print("   - 404 -> nincs ilyen liga; allitsd at a DRAFT_LEAGUE_ID valtozot.")
        print("\n  A %s valtozatlan maradt." % OUT)
        return 0

    payload, lejatszott = atalakit(data)
    nevszures(payload)

    fordulok = len(payload["schedule"])
    meccsek = sum(len(v) for v in payload["schedule"].values())
    print("\n  liga:       %s (%s)" % (payload["league"]["name"], payload["league"]["id"]))
    print("  resztvevok: %d" % len(payload["entries"]))
    print("  fordulok:   %d (%d meccs)" % (fordulok, meccsek))
    print("  lejatszott: %d meccs" % lejatszott)
    if not lejatszott:
        print("  . meg egyetlen fordulo sincs lezarva - minden pont None marad")

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=0)
    print("\n  + %s kiirva (%d byte)" % (OUT, os.path.getsize(OUT)))
    print("Kesz.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
