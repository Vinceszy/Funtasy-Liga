#!/usr/bin/env python3
"""FunTasy Liga - H2H eredmenyek automatikus archivalasa.

A ranglista-vegpont adatkozponti IP-rol is elerheto, ezert ez a resz teljesen automata.
A KERETEK gyujtese NEM itt tortenik: azt a vegpontot az MLSZ 403-mal tiltja szerverrol,
arra a bongeszos konyvjelzo valo (lasd KERET-MENTES.md).
"""
import json, os, sys, time, urllib.parse, urllib.request

COMPETITION = 3
MEMBERS = {
    "Katyul": "peterkmrs", "Bence": "Dill Dough", "Sámsi": "samsonp",
    "Vince": "HolVanSalah", "Bazsa": "Hoxha98", "Csongi": "szcsngr",
    "Csendi": "cspeti93", "Ádám": "siuu_1885",
}
API = ("https://fantasy-api.mlsz.hu/competitions/%d/rankings?include=user_team.user.id,"
       "summary_statistics,ranking,rounds,competition_rank&page=1&per_page=5&filter%%5Bsearch%%5D=")
HDRS = {"Accept": "application/json", "User-Agent": "funtasy-archiver/1.0",
        "Referer": "https://fantasy.mlsz.hu/"}


def fetch(username, retries=3):
    url = (API % COMPETITION) + urllib.parse.quote(username)
    for i in range(retries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=HDRS), timeout=30) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            if i == retries - 1:
                print("  ! %s: %s" % (username, e), file=sys.stderr)
                return None
            time.sleep(3)


def main():
    with open("results.json", encoding="utf-8") as f:
        data = json.load(f)
    schedule = data["schedule"]

    points = {}
    for name, uname in MEMBERS.items():
        j = fetch(uname)
        rows = (j or {}).get("data") or []
        row = next((d for d in rows
                    if ((d.get("user_team") or {}).get("user") or {}).get("username") == uname),
                   rows[0] if rows else None)
        if not row:
            print("  ! nincs talalat: %s" % uname, file=sys.stderr)
            continue
        stats = (row.get("user_team") or {}).get("round_statistics") or []
        points[name] = {int(s["round_number"]): s["points"] for s in stats}
        print("  %s: fordulok=%s" % (name, sorted(points[name])))

    # --- Melyik fordulo tekintheto veglegesnek? ---
    # A ranglista-vegpont nem ad "lezarult" jelzot, ezert kovetkeztetni kell.
    # A fordulok nem fedik at egymast, tehat ha egy KESOBBI fordulonak mar van
    # pontja, az elozo biztosan lezarult. A legutolso ilyen fordulo maga meg
    # tarthat -> az IDEIGLENES.
    #
    # Ez azert szamit, mert korabban egy menet kozben elkapott reszeredmeny
    # veglegesként kerult be, es soha nem javult (a "ha mar ki van tolve,
    # hagyd ki" agy miatt). Most ket dolog valtozott:
    #   1. az ideiglenes fordulo eredmenye MINDEN futasnal felulirodik, tehat
    #      a reszeredmeny magatol helyesre javul;
    #   2. a fajl megmondja, mely fordulo ideiglenes, es az oldal azt nem
    #      szamolja bele a tabellaba.
    minden_r = sorted(int(x) for x in schedule)
    utolso_r = minden_r[-1] if minden_r else 0
    elindult = [r for r in minden_r
                if any(points.get(n, {}).get(r) for n in MEMBERS)]
    max_elindult = max(elindult) if elindult else 0

    def veglegesnek_tekintheto(r):
        if r < max_elindult:
            return True                    # egy kesobbi fordulo mar elindult
        if r == utolso_r == max_elindult:
            # A szezon utolso fordulojanal nincs "kovetkezo", ami lezarna.
            # Ilyenkor akkor tekintjuk lezartnak, ha MINDEN szakvezetonek van
            # pontja - ez a szezon vegen mar biztonsagos.
            return all(points.get(n, {}).get(r) for n in MEMBERS)
        return False

    beirt, javitott, ideiglenes = 0, 0, []
    for rnd, matches in schedule.items():
        r = int(rnd)
        vegleges = veglegesnek_tekintheto(r)
        if r in elindult and not vegleges:
            ideiglenes.append(r)
        for m in matches:
            hp, vp = points.get(m[0], {}).get(r), points.get(m[1], {}).get(r)
            if hp is None or vp is None:
                continue
            if not hp and not vp:          # 0-0 = a fordulo el sem kezdodott
                continue
            if m[2] == hp and m[3] == vp:
                continue                   # nincs valtozas
            # A vegpont az igazsag: ha mas erteket ad, a tarolt volt hibas
            # (pl. menet kozben elkapott reszeredmeny, vagy utolagos MLSZ-
            # korrekcio). Ezert MINDIG szinkronizalunk hozza - ez az, ami
            # korabban hianyzott, es amiatt ragadt be a reszeredmeny. Minden
            # ilyen javitas naplozva van, es a commit diffjeben is latszik.
            elozo = None if m[2] is None else (m[2], m[3])
            m[2], m[3] = hp, vp
            if elozo is None:
                beirt += 1
                print("  + %d. fordulo%s: %s %s - %s %s"
                      % (r, "" if vegleges else " (ideiglenes)", m[0], hp, vp, m[1]))
            else:
                javitott += 1
                print("  ~ %d. fordulo%s: %s %s - %s %s  (volt: %s - %s)"
                      % (r, "" if vegleges else " (ideiglenes)", m[0], hp, vp, m[1],
                         elozo[0], elozo[1]))

    ideiglenes = sorted(set(ideiglenes))
    regi_ideiglenes = data.get("provisional") or []
    valtozott = bool(beirt or javitott) or ideiglenes != regi_ideiglenes

    if valtozott:
        # Az oldal ebbol tudja, melyik fordulot ne szamolja a tabellaba.
        data["provisional"] = ideiglenes
        data["updated"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        with open("results.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=0)

    if ideiglenes:
        print("  . ideiglenes (meg tarthat): %s. fordulo"
              % ", ".join(str(r) for r in ideiglenes))
    print("Kesz: %d uj, %d javitott eredmeny." % (beirt, javitott))
    return 0


if __name__ == "__main__":
    sys.exit(main())
