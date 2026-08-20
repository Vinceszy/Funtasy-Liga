#!/usr/bin/env python3
"""Egyszeri diagnosztika (IDEIGLENES fajl, torolheto): mit enged az MLSZ API
szerverrol, ha HELYESEN kerdezzuk?

Miert kell: a korabbi szerveroldali probak mind 403-at kaptak, es ebbol az a
kovetkeztetes szuletett, hogy a keret-vegpont szerverrol tiltott. Csakhogy azok
a probak MEG A filter[round_id] kotelezoessegenek felfedezese ELOTT tortentek -
es a bongeszoben is pont a hianyzo round_id okozta a 403-at. Lehet tehat, hogy
nem az IP volt a baj, hanem a keres.

Ez a szkript CSAK OLVAS es nyomtat, semmilyen fajlt nem ir es nem modosit.
Ket kerdesre keres valaszt:
  A) Lekerheto-e a keret szerverrol a helyes parameterekkel?
  B) Ad-e az API hasznalhato "fordulo lezarult" jelzest?
"""
import json, sys, urllib.parse, urllib.request

BASE = "https://fantasy-api.mlsz.hu/competitions/3/"

EGYSZERU = {"Accept": "application/json", "User-Agent": "funtasy-archiver/1.0",
            "Referer": "https://fantasy.mlsz.hu/"}
BONGESZOS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "hu-HU,hu;q=0.9,en;q=0.8",
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"),
    "Referer": "https://fantasy.mlsz.hu/",
    "Origin": "https://fantasy.mlsz.hu",
}

INCLUDE = ("position,position.alternatives,competition_player,"
           "competition_player.team,competition_player.countries,summary_statistics")


def get(url, headers):
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.headers.get("content-type", ""), r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", "replace")
        except Exception:
            pass
        return e.code, e.headers.get("content-type", "") if e.headers else "", body
    except Exception as e:
        return None, "", "%s: %s" % (type(e).__name__, e)


def mutat(cim, status, ctype, body, n=700):
    print("\n--- %s ---" % cim)
    print("    HTTP %s | %s" % (status, ctype))
    print("    " + body[:n].replace("\n", " "))


def main():
    print("MLSZ API diagnosztika a GitHub Actions futojarol")

    # ============ 1. Ranglista (referencia - ez eddig is ment) ============
    url = (BASE + "rankings?include=user_team.user.id,summary_statistics,ranking,"
           "rounds,competition_rank&page=1&per_page=5&filter%5Bsearch%5D="
           + urllib.parse.quote("HolVanSalah"))
    st, ct, body = get(url, EGYSZERU)
    mutat("1. ranglista (referencia)", st, ct, body, 200)

    user_id = None
    if st == 200:
        try:
            j = json.loads(body)
            row = j["data"][0]
            user_id = row["user_team"]["user"]["id"]
            print("    user_id: %s" % user_id)
            # B) kerdes: mit tudunk a fordulokrol ebbol a valaszbol?
            rs = (row.get("user_team") or {}).get("round_statistics") or []
            print("\n--- 1b. round_statistics[0] TELJES tartalma (fordulo-jelzest keresunk) ---")
            print("    " + json.dumps(rs[0] if rs else {}, ensure_ascii=False)[:600])
            print("\n--- 1c. a sor tobbi kulcsa ---")
            print("    row: %s" % ", ".join(sorted(row.keys())))
            print("    user_team: %s" % ", ".join(sorted((row.get("user_team") or {}).keys())))
        except Exception as e:
            print("    ! feldolgozasi hiba: %s" % e)

    # ============ 2. KERET szerverrol, HELYES parameterekkel ============
    if user_id:
        squad = (BASE + "user-team-players-history?include=" + urllib.parse.quote(INCLUDE)
                 + "&filter%5Buser_id%5D=" + str(user_id) + "&filter%5Bround_id%5D=83")
        st, ct, body = get(squad, EGYSZERU)
        mutat("2a. keret (4. fordulo), egyszeru fejlecek", st, ct, body)
        st, ct, body = get(squad, BONGESZOS)
        mutat("2b. keret (4. fordulo), bongeszo-szeru fejlecek", st, ct, body)
        # 2c. kontroll: round_id NELKUL - ha ez 403 es a 2a/2b nem, akkor
        # bizonyitott, hogy a parameter szamit, nem az IP
        rossz = (BASE + "user-team-players-history?include=" + urllib.parse.quote(INCLUDE)
                 + "&filter%5Buser_id%5D=" + str(user_id))
        st, ct, body = get(rossz, EGYSZERU)
        mutat("2c. kontroll: keret round_id NELKUL (varhatoan 403)", st, ct, body, 200)

    # ============ 3. Fordulo-vegpontok (B kerdeshez) ============
    for utvonal in ("rounds", "rounds?page=1&per_page=50", ""):
        st, ct, body = get(BASE + utvonal, EGYSZERU)
        mutat("3. GET %s" % (BASE + utvonal), st, ct, body, 600)

    print("\nDiagnosztika vege. Ez a szkript semmit nem irt es nem modositott.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
