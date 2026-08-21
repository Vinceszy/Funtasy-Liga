#!/usr/bin/env python3
"""FunTasy Liga - automatikus adatgyujtes az MLSZ Fantasy API-bol.

Ket dolgot gyujt 3 orankent (.github/workflows/archive.yml):

1. H2H EREDMENYEK (results.json) - a hivatalos fordulopontszamok a
   ranglista-vegpontrol. A tabella egyetlen forrasa ez.
2. KERETEK (squads.json, squad_history.json) - a keret-vegpontrol, a
   bongeszos konyvjelzo formatumaval kompatibilisen; egy tobblet van, a
   squads.json "round" mezoje (hanyadik fordulo kerete). A konyvjelzo
   mostantol csak tartalek, lasd tartalek/KERET-MENTES.md.

A KERET-VEGPONT TORTENETE: sokaig azt hittuk, szerverrol tiltott (GitHub
Actionsbol, proxykon at, Playwrighttal is 403 volt). 2026-08-20-an kiderult:
a 403-at a hianyzo filter[round_id] parameter okozta - a korabbi szerveres
probak meg a parameter felfedezese elott keszultek. Helyes keressel a
vegpont barhonnan, bejelentkezes nelkul mukodik.

TOVABBI MERESSEL IGAZOLT TENYEK (2026-08-20):

- round_id = 75 + 2 x forduloszam.
- A ranglista alapbol csak az utolso lezart es az aktualis fordulot adja
  vissza; regebbi fordulo a filter[round_id] parameterrel kerheto le
  (a valasz az adott fordulot ES az elozot tartalmazza).
- A keret-vegpont a meg el nem kezdodott fordulora 403-at ad (piaczarasig
  titkosak a keretek). Ez varhato viselkedes, nem hiba.
- FORDULO-LEZARAS: egy fordulo akkor zarult le, ha minden szakvezeto minden
  jatekosanal current_round.is_played igaz. A halasztott meccs jatekosait
  az MLSZ lejatszottnak jeloli 0 ponttal (igazolva a 3. fordulos ETO-Fradi
  eseten), tehat a halasztas nem akasztja meg a lezarast.
- A current_round az ELO fordulo lekeresenel csak explicit
  competition_player.current_round include-dal jon vissza (lezart fordulonal
  enelkul is megjelenik) - ezert szerepel az INCLUDE-ban (2026-08-21).
- KI NEM JATSZIK A FORDULOBAN: a competition_player.current_round.games
  include adja meg biztosan - ures lista = a klubnak nincs meccse ebben a
  forduloban (halasztas, pl. a Fradi kupameccse miatt). A first_played_at
  ilyenkor a klub KOVETKEZO meccsere mutat (masik fordulo idopontjara),
  tehat abbol nem lehet kovetkeztetni. A meccslistat csak az ELO fordulora
  kerjuk: ott +2 KB, a lezartaknal viszont a kesz meccs melle bejonnek a
  klublogok is base64-ben, es a valasz 17 KB-rol 118 KB-ra no.
- PONT-BONTAS: a /game-player-stats vegpont (competitions elotag NELKUL)
  adja egy jatekos fordulonkenti teteles bontasat magyar cimkekkel:
  ?include=competition_stat_config&filter[competition_player_id]=<cp.id>
  &filter[round_id]=<round_id>. Ezt az oldal bongeszobol hivja, a gyujto
  csak a hozza kello cp-azonositot ("id") es a "jatszott mar?" jelzot
  ("played" = current_round.is_played) teszi a keret-rekordokba.
- A le nem zarult fordulo szamai IDEIGLENESEK: a results.json "provisional"
  listajaba kerulnek, es az oldal nem szamolja oket a tabellaba.
- Az MLSZ utolag korrigalhat jatekos-statisztikat, es atvezeti a hivatalos
  fordulo-osszegre is (megtortent: Csendi, 1-3. fordulo). Ezert a lekert
  ertekhez MINDIG szinkronizalunk, es a keretbol szamolt osszeget
  osszevetjuk a hivatalossal - elteresnel figyelmeztetes megy a naploba.
- A jatekosok weekly_points erteke MAR KESZ: benne van a kapitanyi duplazas
  es a pad felezese. Soha nem szorzunk ujra es nem felezunk.
- A 0-0 vedelem marad: ha egy fordulo minden erteke 0, a fordulo el sem
  kezdodott, nem kerulhet be lejatszott dontetlenkent.
"""
import json, re, sys, time, urllib.error, urllib.parse, urllib.request

COMPETITION = 3
MEMBERS = {
    "Katyul": "peterkmrs", "Bence": "Dill Dough", "Sámsi": "samsonp",
    "Vince": "HolVanSalah", "Bazsa": "Hoxha98", "Csongi": "szcsngr",
    "Csendi": "cspeti93", "Ádám": "siuu_1885",
}
BASE = "https://fantasy-api.mlsz.hu/competitions/%d/" % COMPETITION
HDRS = {"Accept": "application/json", "User-Agent": "funtasy-archiver/1.0",
        "Referer": "https://fantasy.mlsz.hu/"}
INCLUDE = ("position,position.alternatives,competition_player,"
           "competition_player.team,competition_player.countries,"
           "competition_player.current_round,summary_statistics")

rid = lambda n: 75 + 2 * n


def api_get(url, retries=3):
    """(status, json) - halozati hibanal ujraprobal; 4xx-nel nem."""
    for i in range(retries):
        time.sleep(0.15)
        try:
            req = urllib.request.Request(url, headers=HDRS)
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.status, json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            return e.code, None
        except Exception as e:
            if i == retries - 1:
                print("  ! halozati hiba: %s" % e, file=sys.stderr)
                return None, None
            time.sleep(3)
    return None, None


def rankings(uname, round_id=None):
    url = (BASE + "rankings?include=user_team.user.id,summary_statistics,"
           "ranking,rounds,competition_rank&page=1&per_page=5"
           "&filter%5Bsearch%5D=" + urllib.parse.quote(uname))
    if round_id:
        url += "&filter%5Bround_id%5D=%d" % round_id
    st, j = api_get(url)
    if st != 200 or not j:
        return None
    rows = j.get("data") or []
    return next((d for d in rows
                 if ((d.get("user_team") or {}).get("user") or {}).get("username") == uname),
                rows[0] if rows else None)


def squad(user_id, round_no, jatek=False):
    """jatek=True: a meccslistat is kerjuk (ki NEM jatszik a forduloban).
    Csak az ELO fordulora hasznaljuk: ott a meccsek meg 'scheduled'
    allapotuak, es a valasz alig no (+2 KB). A lezart forduloknal viszont
    a kesz meccs melle az API a ket csapatot is beteszi a klublogokkal
    egyutt (base64 kepadat), es a valasz 17 KB-rol 118 KB-ra hizik -
    ezert oda nem kerjuk; a jelzest a fordulo alatt mar elmentettuk."""
    inc = INCLUDE + (",competition_player.current_round.games" if jatek else "")
    url = (BASE + "user-team-players-history?include=" + urllib.parse.quote(inc)
           + "&filter%5Buser_id%5D=" + str(user_id)
           + "&filter%5Bround_id%5D=" + str(rid(round_no)))
    return api_get(url)


def is_hun(cp):
    """Ugyanaz a szabaly, mint a konyvjelzoben."""
    szoveg = json.dumps(cp.get("countries") or cp.get("country") or "", ensure_ascii=False)
    return bool(re.search(r'magyar|hungar|"HUN"', szoveg, re.I))


def rekord(d):
    """Egy jatekos rekordja - mezorol mezore a konyvjelzo formatuma."""
    cp = d.get("competition_player") or {}
    po = d.get("position") or {}
    ss = d.get("summary_statistics") or {}
    team = cp.get("team") or {}
    cr = cp.get("current_round") or {}
    nev = " ".join(x for x in (cp.get("first_name"), cp.get("last_name")) if x) \
          or ("#%s" % (cp.get("id") or d.get("id")))
    return {
        "name": nev,
        "team": team.get("short_name") or team.get("name") or "",
        "pos": po.get("monogram") or po.get("name") or "",
        "u21": bool(cp.get("is_u21")),
        "hun": is_hun(cp),
        "price": (cr.get("market_price") or None),
        "cap": bool(d.get("is_captain")),
        "sub": d.get("type") == "substitutes",
        "week": ss.get("weekly_points") or 0,
        "total": ss.get("competition_points") or 0,
        # a konyvjelzo-formatumon felul: a pont-bontashoz es a
        # "jatszott mar?" jelzeshez (elo fordulonal a current_round csak
        # explicit include-dal jon, ezert szerepel az INCLUDE-ban).
        # A "start" a jatekos adott fordulos meccsenek kezdese; a "nogame"
        # akkor kerul be, ha a klubnak NINCS meccse a forduloban (halasztas
        # vagy elmaradas). Ezt a meccslista (games) mondja meg biztosan:
        # ures lista = nincs meccs. A first_played_at ilyenkor a klub
        # KOVETKEZO meccset adja (masik fordulo idopontjat), ezert nem
        # hasznalhato ra - ez volt a "furcsa kezdesi ido" oka.
        "id": cp.get("id"),
        "played": bool(cr.get("is_played")),
        **jatek_mezok(cr),
    }


def jatek_mezok(cr):
    games = cr.get("games")
    if games is None:                       # nem kertuk a meccslistat
        return {"start": cr.get("first_played_at")}
    if not games:                           # nincs meccse ebben a forduloban
        return {"start": None, "nogame": True}
    g = games[0] or {}
    mezok = {"start": g.get("start_at") or cr.get("first_played_at")}
    # A meccs lefujasa es a pontok megjelenese kozott orak telhetnek el:
    # ilyenkor az is_played meg hamis, de a meccs status-a mar "completed".
    # E nelkul a lejatszott meccsre is azt irtuk, hogy "a meccs zajlik".
    if g.get("status") == "completed":
        mezok["vege"] = True
    return mezok


def orokit_nogame(regi_fordulo, uj_fordulo):
    """A "nincs meccse a forduloban" jelzest a fordulo ALATT gyujtjuk be
    (csak ott kerjuk a meccslistat). A lezaras utani ujralekeresek mar
    nelkule jonnek, ezert a korabban rogzitett jelzest at kell hozni -
    kulonben minden futas kitorolne. A meccs nelkuli jatekosnal a
    first_played_at a KOVETKEZO fordulo meccsere mutat, ezert a start-ot
    is a regi (ures) ertekre allitjuk vissza."""
    for nev, sq in uj_fordulo.items():
        regi = {p.get("name"): p for p in (regi_fordulo.get(nev) or [])}
        for p in sq:
            if "nogame" not in p and regi.get(p.get("name"), {}).get("nogame"):
                p["nogame"] = True
                p["start"] = None


def keret_osszeg(sq):
    """Fordulopontszam a keretbol: weekly_points osszeg + magyarszabaly."""
    ossz = sum(p.get("week") or 0 for p in sq)
    kezdok = [p for p in sq if not p.get("sub")]
    hun = sum(1 for p in kezdok if p.get("hun"))
    u21 = sum(1 for p in kezdok if p.get("hun") and p.get("u21"))
    return ossz + (10 if (hun >= 5 and u21 >= 1) else 0)


def kompakt_iras(path, obj):
    """A konyvjelzoevel azonos, kompakt JSON-formatum."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))


def stamp():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def main():
    with open("results.json", encoding="utf-8") as f:
        data = json.load(f)
    schedule = data["schedule"]
    try:
        with open("squad_history.json", encoding="utf-8") as f:
            hist = json.load(f)
    except Exception:
        hist = {"updated": None, "rounds": {}}
    hist.setdefault("rounds", {})
    hist_elotte = json.dumps(hist.get("rounds"), ensure_ascii=False, sort_keys=True)

    # ---- 1. Azonositok es a friss hivatalos pontok ----
    ids, pontok = {}, {n: {} for n in MEMBERS}
    for nev, uname in MEMBERS.items():
        row = rankings(uname)
        if not row:
            print("  ! nincs ranglista-adat: %s" % nev, file=sys.stderr)
            continue
        ids[nev] = ((row.get("user_team") or {}).get("user") or {}).get("id")
        for s in (row.get("user_team") or {}).get("round_statistics") or []:
            pontok[nev][int(s["round_number"])] = s["points"]
    if not ids:
        print("Nincs elerheto adat - a fajlok valtozatlanok.")
        return 0
    aktualis = max((r for p in pontok.values() for r in p), default=0)
    print("  aktualis fordulo: %d | azonositok: %d/%d" % (aktualis, len(ids), len(MEMBERS)))

    # ---- 2. Kimaradt regi fordulok potlasa (filter[round_id]) ----
    # A ranglista alapbol csak a friss fordulokat adja; ha egy regebbi
    # fordulo eredmenye hianyzik (pl. tobb napos leallas utan), azt kulon
    # kell lekerni. Normal esetben ez a lista ures.
    hianyzo = sorted({int(r) for r, ms in schedule.items()
                      if int(r) < aktualis and any(m[2] is None for m in ms)})
    for r in hianyzo:
        print("  potlas: %d. fordulo hivatalos pontjai" % r)
        for nev, uname in MEMBERS.items():
            row = rankings(uname, round_id=rid(r))
            if not row:
                continue
            for s in (row.get("user_team") or {}).get("round_statistics") or []:
                pontok[nev].setdefault(int(s["round_number"]), s["points"])

    # ---- 3. Eredmenyek szinkronja (a vegpont az igazsag) ----
    beirt, javitott = 0, 0
    for rnd, matches in schedule.items():
        r = int(rnd)
        for m in matches:
            hp, vp = pontok.get(m[0], {}).get(r), pontok.get(m[1], {}).get(r)
            if hp is None or vp is None:
                continue
            if not hp and not vp:          # 0-0 = a fordulo el sem kezdodott
                continue
            if m[2] == hp and m[3] == vp:
                continue
            elozo = None if m[2] is None else (m[2], m[3])
            m[2], m[3] = hp, vp
            if elozo is None:
                beirt += 1
                print("  + %d. fordulo: %s %s - %s %s" % (r, m[0], hp, vp, m[1]))
            else:
                javitott += 1
                print("  ~ %d. fordulo: %s %s - %s %s  (volt: %s - %s) - MLSZ-korrekcio?"
                      % (r, m[0], hp, vp, m[1], elozo[0], elozo[1]))

    # ---- 4. Keretek gyujtese ----
    # Celfordulok: az aktualis (ha mar elindult), az utolso lezart (hogy az
    # utolagos MLSZ-korrekciok atjojjenek), es ami hianyzik az elozmenybol.
    celok = set()
    if aktualis >= 1:
        celok.add(aktualis)
    if aktualis >= 2:
        celok.add(aktualis - 1)
    for r in range(1, aktualis + 1):
        megvan = hist["rounds"].get(str(r)) or {}
        if len(megvan) < len(MEMBERS):
            celok.add(r)

    lezart = {}          # r -> True/False (minden jatekos jatszott-e)
    for r in sorted(celok):
        # olcso elovizsgalat egyetlen kerettel: 403 = a fordulo meg titkos
        elso_id = next(iter(ids.values()))
        st, _ = squad(elso_id, r)
        if st == 403:
            print("  . %d. fordulo keretei meg nem elerhetok (piaczaras elott)" % r)
            continue
        uj_fordulo, mind_jatszott, teljes = {}, True, True
        for nev, uid in ids.items():
            st, j = squad(uid, r, jatek=(r == aktualis))
            if st != 200 or not isinstance(j, dict) or not j.get("data"):
                print("  ! %d. fordulo / %s: HTTP %s" % (r, nev, st), file=sys.stderr)
                teljes = False
                continue
            sq = [rekord(d) for d in j["data"]]
            uj_fordulo[nev] = sq
            for d in j["data"]:
                cr = (d.get("competition_player") or {}).get("current_round") or {}
                if not cr.get("is_played"):
                    mind_jatszott = False
        if not uj_fordulo:
            continue
        regi_fordulo = hist["rounds"].get(str(r)) or {}
        orokit_nogame(regi_fordulo, uj_fordulo)
        hist["rounds"][str(r)] = {**regi_fordulo, **uj_fordulo}
        lezart[r] = teljes and mind_jatszott and len(uj_fordulo) == len(MEMBERS)
        print("  keretek: %d. fordulo, %d/%d szakvezeto, %s"
              % (r, len(uj_fordulo), len(MEMBERS),
                 "lezart" if lezart[r] else "meg tart / hianyos"))

        # keresztellenorzes: a keretbol szamolt osszeg vs hivatalos
        for nev, sq in uj_fordulo.items():
            hiv = pontok.get(nev, {}).get(r)
            if hiv in (None, 0) or not lezart[r]:
                continue
            szamolt = keret_osszeg(sq)
            if abs(szamolt - hiv) >= 0.005:
                print("  ! ELTERES %d. fordulo / %s: keretbol %.2f, hivatalos %.2f"
                      " - az MLSZ korrigalhatott" % (r, nev, szamolt, hiv), file=sys.stderr)

    # ---- 5. Ideiglenes fordulok ----
    # Csak az szamit ideiglenesnek, aminek mar van pontja, de a keretek
    # szerint meg nem jatszott le minden jatekos.
    provisional = sorted(r for r, kesz in lezart.items()
                         if not kesz and any(pontok.get(n, {}).get(r) for n in MEMBERS))
    regi_prov = data.get("provisional") or []

    # ---- 6. Iras, csak ha valtozott ----
    if beirt or javitott or provisional != regi_prov:
        data["provisional"] = provisional
        data["updated"] = stamp()
        with open("results.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=0)
        print("  results.json frissitve")

    if json.dumps(hist.get("rounds"), ensure_ascii=False, sort_keys=True) != hist_elotte:
        hist["updated"] = stamp()
        kompakt_iras("squad_history.json", {"updated": hist["updated"],
                                            "rounds": hist["rounds"]})
        utolso = max((int(r) for r in hist["rounds"]), default=0)
        kompakt_iras("squads.json", {"updated": hist["updated"], "round": utolso,
                                     "squads": hist["rounds"].get(str(utolso)) or {}})
        print("  squad_history.json + squads.json frissitve (utolso fordulo: %d)" % utolso)

    if provisional:
        print("  ideiglenes (meg tart): %s. fordulo" % ", ".join(map(str, provisional)))
    print("Kesz: %d uj, %d javitott eredmeny." % (beirt, javitott))
    return 0


if __name__ == "__main__":
    sys.exit(main())
