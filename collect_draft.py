#!/usr/bin/env python3
"""FunTasy Liga - FPL Draft liga adatainak lekerese (felderito valtozat).

Ez a valtozat meg NEM epit oldalt es nem szamol tabellat: az a dolga, hogy
kiderítse, egyaltalan elerheto-e a vegpont a GitHub Actions adatkozponti
IP-jerol, es hogy pontosan milyen szerkezetu adat jon vissza.

A vegpont egyszerre adja a resztvevoket, a teljes H2H menetrendet es az
eredmenyeket, tehat menetrendet nem kell kezzel bevinni (ellentetben az
MLSZ-resszel, ahol a SCHEDULE_NB1 be van egetve).

A liga azonositoja a DRAFT_LEAGUE_ID kornyezeti valtozobol felulirhato -
az FPL Draft ligak szezononkent uj azonositot kapnak.

A szkript SOHA nem all le hibaval: ha a lekeres nem megy, kiirja az okot es
0-val ter vissza, hogy a munkafolyamat ne legyen piros egy olyan dolog miatt,
amirol meg nem tudjuk, mukodhet-e egyaltalan.
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
    for i in range(retries):
        try:
            req = urllib.request.Request(URL, headers=HDRS)
            with urllib.request.urlopen(req, timeout=30) as r:
                raw = r.read().decode("utf-8")
                return json.loads(raw), None
        except urllib.error.HTTPError as e:
            body = ""
            try:
                body = e.read().decode("utf-8", "replace")[:300]
            except Exception:
                pass
            msg = "HTTP %s %s | valasz eleje: %s" % (e.code, e.reason, body or "(ures)")
            # 401/403/404 nem javul ujraprobalastol
            if e.code in (401, 403, 404):
                return None, msg
        except Exception as e:
            msg = "%s: %s" % (type(e).__name__, e)
        if i == retries - 1:
            return None, msg
        time.sleep(3)
    return None, "ismeretlen hiba"


def leiras(data):
    """Kiirja a valasz szerkezetet, hogy lassuk, mivel dolgozhatunk."""
    print("\n--- A valasz szerkezete ---")
    if not isinstance(data, dict):
        print("  a gyoker nem objektum, hanem %s" % type(data).__name__)
        return
    for key, val in data.items():
        if isinstance(val, list):
            print("  %-22s lista, %d elem" % (key, len(val)))
            if val and isinstance(val[0], dict):
                print("  %-22s   elso elem mezoi: %s"
                      % ("", ", ".join(sorted(val[0].keys()))))
        elif isinstance(val, dict):
            print("  %-22s objektum, mezok: %s" % (key, ", ".join(sorted(val.keys()))))
        else:
            print("  %-22s %r" % (key, val))


def main():
    print("FPL Draft liga lekerese")
    print("  liga azonosito: %s" % LEAGUE_ID)
    print("  vegpont:        %s" % URL)

    data, err = fetch()

    if err:
        print("\n  ! NEM SIKERULT: %s" % err, file=sys.stderr)
        print("\n  Mit jelent ez:")
        print("   - 403 vagy 401 -> a vegpont bejelentkezest var, vagy tiltja az")
        print("     adatkozponti IP-t. Ilyenkor konyvjelzos megoldas kell, mint")
        print("     az MLSZ-kereteknel (lasd KERET-MENTES.md).")
        print("   - 404 -> nincs ilyen liga. Az FPL Draft ligak szezononkent uj")
        print("     azonositot kapnak; allitsd at a DRAFT_LEAGUE_ID valtozot.")
        print("\n  A %s valtozatlan maradt." % OUT)
        return 0

    leiras(data)

    payload = {
        "updated": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "league_id": LEAGUE_ID,
        "data": data,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=0)

    meret = os.path.getsize(OUT)
    print("\n  + %s kiirva (%d byte)" % (OUT, meret))
    print("Kesz.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
