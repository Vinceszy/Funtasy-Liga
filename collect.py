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
- FORDULO-LEZARAS: egy fordulo akkor zarult le, ha minden olyan jatekos,
  AKINEK VAN MECCSE, lejatszotta (current_round.is_played), es a meccse le
  is ment (games[0].status == "completed"). Akinek nincs meccse a
  forduloban (nogame), az nem szamit bele.
  Korabban a nogame-esek is szamitottak, arra a - 2026-08-23-an megmert -
  teves feltevesre, hogy az MLSZ oket is lejatszottnak jeloli 0 ponttal.
  A meres ezt megcafolta: az 5. fordulos Honved-jatekosoknal (nincs meccs)
  is_played=false, a 3. fordulos ETO-jatekosoknal viszont mar igaz - de
  csak azert, mert a regi fordulo lekeresenel az API a klub LEGUTOBBI
  meccsere esik vissza (ugyanaz a visszaeses, ami a "furcsa kezdesi
  idopont" hibat okozta). A jelzo tehat nem a fordulo lezarasakor billen at,
  hanem amikor a klub legkozelebb jatszik - ami egy egesz hetet is csuszhat.
- BIZTONSAGI HALO A LEZARASHOZ: az MLSZ sajat fordulo-objektuma. Onallo
  rounds-vegpont nincs (404), a fordulolista a versenylistan keresztul jon:
  competitions?include=rounds,current_round - ezt hivja a frontendje is.
  Mezoi: id, round_number, start_at, end_at, is_transfers_closed,
  closed_transfers_at. LEZARTSAG-JELZO NINCS BENNE: az MLSZ-nel a fordulo
  naptari hatar (az egyik end_at-je a kovetkezo start_at-je), ezert ez csak
  tartalek - ha a jatekos-szintu kep megsem all ossze, a fordulo akkor sem
  marad orokre ideiglenes.
- A current_round az ELO fordulo lekeresenel csak explicit
  competition_player.current_round include-dal jon vissza (lezart fordulonal
  enelkul is megjelenik) - ezert szerepel az INCLUDE-ban (2026-08-21).
- KI NEM JATSZIK A FORDULOBAN: a competition_player.current_round.games
  include adja meg biztosan, KET alakban (2026-08-23-i meres):
    * ures lista - az ELO fordulonal ez jon, ha a klubnak nincs meccse;
    * MASIK fordulo meccse - regi fordulonal az API a klub legutobbi
      meccsere esik vissza a hianyzo helyett. Maga a meccs-objektum arulja
      el: a round_number mezoje "3F" / "5F" alaku, es ha nem a kert
      fordulora mutat, akkor a klubnak nincs meccse benne.
  A first_played_at ilyenkor sem hasznalhato: vagy a klub KOVETKEZO meccsere
  mutat, vagy egy ejfeles helyorzore (a 3. fordulos ETO-nal 2026-08-15T00:00,
  vagyis egy mar elmult nap kituzetlen idoponttal). A meccslistat csak az ELO fordulora
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
- Az MLSZ utolag korrigal: harom megfigyelt esetunk van (Csendi, 1-3.
  fordulo, +1/+1/-2,5; 2026-08-20). Ezert a lekert ertekhez MINDIG
  szinkronizalunk, a keretbol szamolt osszeget osszevetjuk a hivatalossal,
  es a valtozast NAPLOZZUK is (zarasok_nb1.json) - utolag mar nem
  rekonstrualhato, hogy mi mozdult.
- A jatekosok weekly_points erteke MAR KESZ: benne van a kapitanyi duplazas
  es a pad felezese. Soha nem szorzunk ujra es nem felezunk.
- A 0-0 vedelem marad: ha egy fordulo minden erteke 0, a fordulo el sem
  kezdodott, nem kerulhet be lejatszott dontetlenkent.
"""
import datetime
import itertools, json, os, re, sys, time, urllib.error, urllib.parse, urllib.request

COMPETITION = 3
MEMBERS = {
    "Katyul": "peterkmrs", "Bence": "Dill Dough", "Sámsi": "samsonp",
    "Vince": "HolVanSalah", "Bazsa": "Hoxha98", "Csongi": "szcsngr",
    "Csendi": "cspeti93", "Ádám": "siuu_1885",
}
ROOT = "https://fantasy-api.mlsz.hu/"
BASE = ROOT + "competitions/%d/" % COMPETITION
HDRS = {"Accept": "application/json", "User-Agent": "funtasy-archiver/1.0",
        "Referer": "https://fantasy.mlsz.hu/"}
INCLUDE = ("position,position.alternatives,competition_player,"
           "competition_player.team,competition_player.countries,"
           "competition_player.current_round,summary_statistics")

rid = lambda n: 75 + 2 * n


def versenyfordulok():
    """Az MLSZ sajat fordulo-objektuma - a lezaras BIZTONSAGI HALOJA.

    Onallo rounds-vegpont NINCS (minden ilyen ut 404); a fordulolista a
    VERSENYLISTAN keresztul jon, ugyanazzal a hivassal, amit az MLSZ sajat
    frontendje hasznal. Egy fordulo mezoi: id, round_number, start_at,
    end_at, is_transfers_closed, closed_transfers_at.

    LEZARTSAG-JELZO NINCS KOZTUK: az MLSZ-nel a fordulo naptari hatar, az
    end_at eltelteig tart, utana lep tovabb a current_round. Ezert ez csak
    tartalek a jatekos-szintu jel mogott, nem az elsodleges forras.

    Visszaad: (aktualis forduloszam vagy None, {forduloszam: end_at}).
    Hibanal (None, {}) - a hivo ilyenkor csak a jatekos-szintu jelre epit."""
    st, j = api_get(ROOT + "competitions?include=rounds,current_round")
    if st != 200 or not isinstance(j, dict):
        return None, {}
    comp = next((c for c in (j.get("data") or [])
                 if c.get("id") == COMPETITION), None) or {}
    akt = ((comp.get("current_round") or {}).get("round_number"))
    vegek = {}
    for r in comp.get("rounds") or []:
        if r.get("round_number") and r.get("end_at"):
            vegek[int(r["round_number"])] = r["end_at"]
    return akt, vegek


def mlsz_lezarta(r, mlsz_akt, mlsz_vegek):
    """Igaz, ha az MLSZ szerint az r. fordulo mar nem tart.

    Az elsodleges jel a current_round: ha az MLSZ tovabblepett, a fordulo
    lement. Ez erosebb, mint a naptar - ha a current_round szerint MEG EZ az
    aktualis fordulo, akkor az end_at eltelte sem zarja le (a ket adat
    atmenetileg elterhet, es a futo fordulot lezarni a rosszabb teves lepes:
    a felig kesz eredmeny csendben bekerulne a tabellaba).

    Az end_at csak akkor dont, ha a current_round egyaltalan nem jott meg."""
    if mlsz_akt is not None:
        return mlsz_akt > r
    veg = mlsz_vegek.get(r)
    if not veg:
        return False
    try:
        return datetime.datetime.now(datetime.timezone.utc) > \
            datetime.datetime.fromisoformat(veg)
    except ValueError:
        return False


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
        # sztring-osszefuzes, NEM %-formazas: a %5B-t format-jelnek vennne
        url += "&filter%5Bround_id%5D=" + str(round_id)
    st, j = api_get(url)
    if st != 200 or not j:
        return None
    rows = j.get("data") or []
    pontos = next((d for d in rows
                   if ((d.get("user_team") or {}).get("user") or {}).get("username") == uname),
                  None)
    if pontos or not rows:
        return pontos
    # Nincs pontos felhasznalonev-egyezes. A talalat listat NEM dobjuk el (a
    # valasz nem mindig hozza a username mezot), de kiirjuk: enelkul egy
    # elteveszett kereses MASIK szakvezeto pontjait irna be csendben - pont az
    # a "csendes, hiheto, rossz" hiba, ami ellen a tobbi vedelem is szol.
    print("  ! %s: nincs pontos felhasznalonev-egyezes, az elso talalatot "
          "hasznaljuk (%d talalat)" % (uname, len(rows)), file=sys.stderr)
    return rows[0]


GAMES = "competition_player.current_round.games"


def squad(user_id, round_no, jatek=False):
    """jatek=True: a meccslistat is kerjuk (ki NEM jatszik a forduloban,
    es kik a meccs klubjai).

    A KET KLUBOT EXPLICIT KERJUK. Enelkul az ELO fordulo meccs-objektuma
    csak id/start/status/eredmeny/round_number - klub NELKUL -, es a
    meccs_kivonat "?"-et irt a meccsek.json-ba. Emiatt a 6. fordulo profil-
    soraban kotojel allt az ellenfel helyen, holott az eredmeny megvolt.
    (A lezart fordulot az API enelkul is csapatostul adja, ezert volt jo az
    1-5. fordulo - a meccsek.json csak a lezarasuk utan keszult.)

    MERVE (2026-08-30, elo 6. fordulo, naplo/mlsz-elo-meccs.txt):
      - games.home_team + games.away_team  -> HTTP 200, a klub megjon
      - games.homeTeam / games.teams       -> a mezo nem jelenik meg
      - a valasz 22,3 KB -> 24,8 KB, tehat +2,5 KB: a csapat-objektum itt
        SOVANY (id, name, short_name, color_hex), LOGO NELKUL - nem ez a
        118 KB-os hizas, amit a lezart fordulos valasznal mertunk.
      - kulon meccs-vegpont nincs: games/<id>, matches/<id>, fixtures/<id>
        a gyokeren es a competitions/3 alatt is 404 (tiz alak).
      - a birtokolt jatekosok klubjaibol csak 4/6 meccs ket oldala jott
        volna ossze, a hazai/vendeg pedig sehogy - ezert nem abbol
        vezetjuk le."""
    inc = INCLUDE + (("," + GAMES + "," + GAMES + ".home_team,"
                      + GAMES + ".away_team") if jatek else "")
    url = (BASE + "user-team-players-history?include=" + urllib.parse.quote(inc)
           + "&filter%5Buser_id%5D=" + str(user_id)
           + "&filter%5Bround_id%5D=" + str(rid(round_no)))
    return api_get(url)


def jatekosnev(elo, utó, tartalek=None):
    """A jatekos neve MAGYAR SORRENDBEN: vezeteknev elol.

    Az MLSZ kulon adja a ket reszt, mi pedig sokaig nyugati sorrendben
    fuztuk ossze ("Aron Alaxai"). A magyar bajnoksagban ez forditva helyes,
    es nem csak stilus kerdese: a hosszu nevek felismerheto resze a
    VEZETEKNEV - az all a mezen is. "Gleofilo Sabrino Rudewald Hasselbaink
    Vlijter" eseten a nyugati sorrend a felismerhetetlen felevel kezdodott,
    es a szuk oszlopokban pont a lenyeg (Vlijter) vagodott le."""
    nev = " ".join(x for x in (utó, elo) if x)
    return nev or (tartalek or "")


def is_hun(cp):
    """Ugyanaz a szabaly, mint a konyvjelzoben."""
    szoveg = json.dumps(cp.get("countries") or cp.get("country") or "", ensure_ascii=False)
    return bool(re.search(r'magyar|hungar|"HUN"', szoveg, re.I))


def meccs_forduloja(g):
    """A meccs-objektum megmondja, MELYIK fordulohoz tartozik: a round_number
    mezoje "3F" / "5F" alaku. Szam vagy None, ha nincs benne."""
    m = re.match(r"\s*(\d+)", str((g or {}).get("round_number") or ""))
    return int(m.group(1)) if m else None


def rekord(d, fordulo=None):
    """Egy jatekos rekordja - mezorol mezore a konyvjelzo formatuma."""
    cp = d.get("competition_player") or {}
    po = d.get("position") or {}
    ss = d.get("summary_statistics") or {}
    team = cp.get("team") or {}
    cr = cp.get("current_round") or {}
    nev = jatekosnev(cp.get("first_name"), cp.get("last_name"),
                     "#%s" % (cp.get("id") or d.get("id")))
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
        **jatek_mezok(cr, fordulo),
    }


def jatek_mezok(cr, fordulo=None):
    games = cr.get("games")
    if games is None:                       # nem kertuk a meccslistat
        return {"start": cr.get("first_played_at")}
    if not games:                           # nincs meccse ebben a forduloban
        return {"start": None, "nogame": True}
    g = games[0] or {}
    # Ures lista nem az egyetlen jelzes: regi fordulonal az API a klub
    # LEGUTOBBI meccsere esik vissza a hianyzo helyett. Maga a meccs-objektum
    # arulja el (round_number), hogy nem ehhez a fordulohoz tartozik - ez is
    # azt jelenti, hogy a klubnak nincs meccse ebben a forduloban.
    mf = meccs_forduloja(g)
    if fordulo is not None and mf is not None and mf != fordulo:
        return {"start": None, "nogame": True}
    mezok = {"start": g.get("start_at") or cr.get("first_played_at")}
    # A meccs status-a onallo jelzes az is_played mellett. Az utobbibol NEM
    # kovetkezik, hogy a meccsnek vege: az MLSZ mar a meccs kozben igazra
    # billenti (ezert irtuk egy ideig meccs kozben, hogy "lejatszotta").
    if g.get("status") == "completed":
        mezok["vege"] = True
    return mezok


def orokit_meccsjelzok(regi_fordulo, uj_fordulo):
    """A meccslistabol szarmazo jelzeseket at kell hozni a regi rekordbol.

    A meccslistat (games) csak az ELO fordulora kerjuk le - a lezaras utani
    ujralekeresek mar nelkule jonnek, tehat ami csak abbol szarmazik, az
    kiesne. Ket ilyen mezo van:
      nogame - a klubnak nincs meccse a forduloban (halasztas/elmaradas).
               A first_played_at ilyenkor a KOVETKEZO meccset adja, ezert a
               start-ot is a regi (ures) ertekre allitjuk vissza.
      vege   - a meccs mar lement. Enelkul az oldal a 100-180 perces
               ablakban visszaesne a "meccs zajlik" allapotba."""
    for nev, sq in uj_fordulo.items():
        regi = {p.get("name"): p for p in (regi_fordulo.get(nev) or [])}
        for p in sq:
            regi_p = regi.get(p.get("name")) or {}
            if "nogame" not in p and regi_p.get("nogame"):
                p["nogame"] = True
                p["start"] = None
            if "vege" not in p and regi_p.get("vege"):
                p["vege"] = True


def keret_osszeg(sq):
    """Fordulopontszam a keretbol: weekly_points osszeg + magyarszabaly."""
    ossz = sum(p.get("week") or 0 for p in sq)
    kezdok = [p for p in sq if not p.get("sub")]
    hun = sum(1 for p in kezdok if p.get("hun"))
    u21 = sum(1 for p in kezdok if p.get("hun") and p.get("u21"))
    return ossz + (10 if (hun >= 5 and u21 >= 1) else 0)


def nyers_pontok(r):
    """Egy lezart fordulo NYERS jatekos-pontjai a bontasok/<r>.json-bol:
    {cp-azonosito: pont}. None, ha a fajl meg nincs meg.

    A bontas sorai a jatekos SAJAT esemenyei, tehat az osszeguk a nyers heti
    pont - kapitanyi duplazas es padfelezes NELKUL. Epp ez kell ide: a
    szorzokat a MULT HETI szerepek szerint tesszuk ra."""
    ut = os.path.join("bontasok", "%d.json" % r)
    if not os.path.exists(ut):
        return None
    try:
        with open(ut, encoding="utf-8") as f:
            d = json.load(f)
    except Exception:
        return None
    return {cp: sum(x.get("p") or 0 for x in (sorok or []))
            for cp, sorok in (d.get("bontasok") or {}).items()}


def guardiola_keret(regi_sq, nyers):
    """A MULT HETI keret rekordjai, a MOSTANI fordulo pontjaival.

    "Mi lett volna, ha hozza sem nyulok": ugyanaz a 15 jatekos, UGYANAZOKBAN
    A SZEREPEKBEN - aki kezdo volt, kezdo marad, aki a padon ult, ott marad,
    a kapitany ugyanaz. NEM a legjobb felallitas: az mar egy masik mutato
    lenne (azt a KEZD% meri).

    A szorzokat ugyanugy tesszuk ra, mint az API: kapitany x2, pad felezve,
    ES KET TIZEDESRE KEREKITVE - a valodi `week` is igy jon vissza (0,75 ->
    0,38). Enelkul a kulonbseg tizedeken csuszna el.

    Aki mar nincs a fordulo bontasaban (kikerult az MLSZ 385-os torzsebol),
    az 0 pontot kap: nincs az idei mezonyben, tehat nem is szerezhetett."""
    uj = []
    for pl in regi_sq:
        alap = nyers.get(str(pl.get("id")), 0)
        w = alap * 2 if pl.get("cap") else (alap / 2.0 if pl.get("sub") else alap)
        masolat = dict(pl)
        masolat["week"] = round(w, 2)
        uj.append(masolat)
    return uj


def guardiola(hist_rounds, r):
    """A "Guardiola mutato" egy fordulora: {szakvezeto: {teny, alt, guard}}.

    guard = a MOSTANI keret pontja - a MULT HETI kerete UGYANEBBEN a
    forduloban. Negativ ertek: a valtoztatas pontba kerult.

    MINDKET oldal UGYANAZZAL a fuggvennyel (keret_osszeg) szamol, tehat a
    magyarszabaly es a kerekites is egyformán jatszik - a kulonbseg tisztan
    a keretvaltozas muve. Szandekosan NEM a hivatalos fordulopontbol vonunk:
    abban egy utolagos MLSZ-korrekcio is benne lenne, es az nem a
    szakvezeto dontese.

    None, ha nincs mihez hasonlitani (elso fordulo) vagy hianyzik az adat."""
    elozo = (hist_rounds.get(str(r - 1)) or {})
    mostani = (hist_rounds.get(str(r)) or {})
    if not elozo or not mostani:
        return None
    nyers = nyers_pontok(r)
    if nyers is None:
        return None
    ki = {}
    for nev, sq in mostani.items():
        regi_sq = elozo.get(nev)
        if not regi_sq or not sq:
            continue
        # MINDKET oldal a BONTASBOL szamol, nem a tarolt `week`-bol. Enelkul
        # a valtozatlan keret sem adna pontosan 0-t: a tarolt `week` a pados
        # jatekosnal az API mar felezve-kerekitett erteke (0,75 -> 0,38), a
        # miénk pedig a nyers pontbol szamol - a ketto 0,01-gyel elter, es
        # ez a kulonbsegben latszana ("+0,01", holott nem nyult a kerethez).
        # A `teny` igy egy centtel elterhet a hivatalos fordulopontto1; a
        # MUTATO viszont pontos, es azt mutatjuk.
        teny = keret_osszeg(guardiola_keret(sq, nyers))
        alt = keret_osszeg(guardiola_keret(regi_sq, nyers))
        ki[nev] = {"teny": round(teny, 2), "alt": round(alt, 2),
                   "guard": round(teny - alt, 2)}
    return ki or None


def ellenorzendo(regi, db=4):
    """Rolling ellenorzes: minden futas mas nehany REGI fordulot ker le
    ujra. Igy nem kell minden korben az osszeset lekerdezni, de egy nap
    alatt mindegyik sorra kerul - ha az MLSZ utolag korrigal egy regi
    fordulot, azt legkesobb egy napon belul atvezetjuk. (A ket legfrissebb
    fordulot amugy is minden futas ellenorzi.)"""
    if not regi:
        return []
    n = len(regi)
    kezd = (int(time.time() // 10800) * db) % n      # 3 orankent lep
    return sorted({regi[(kezd + i) % n] for i in range(min(db, n))})


def beir_eredmeny(schedule, r, nev, ertek):
    """Egy szakvezeto fordulopontszamat beirja a menetrendbe.
    1-et ad vissza, ha tenylegesen valtozott."""
    for m in schedule.get(str(r)) or []:
        if m[0] == nev and m[2] != ertek:
            m[2] = ertek
            return 1
        if m[1] == nev and m[3] != ertek:
            m[3] = ertek
            return 1
    return 0


def meccs_kivonat(g):
    """Egy meccs tarolando alakja a meccsek.json-hoz. EREDMENY CSAK LEZART
    MECCSROL kerul bele: meccs kozben az MLSZ reszallast adhat, es a 3
    orankent futo gyujto azt veglegeskent orokitene meg - ugyanaz a hiba
    lenne, mint a 0-0 a results.json-ban."""
    m = {"id": g.get("id"),
         "h": ((g.get("home_team") or {}).get("short_name")
               or (g.get("home_team") or {}).get("name") or "?"),
         "v": ((g.get("away_team") or {}).get("short_name")
               or (g.get("away_team") or {}).get("name") or "?"),
         "start": g.get("start_at")}
    if g.get("status") == "completed":
        m["hp"], m["vp"] = g.get("home_score"), g.get("away_score")
        m["vege"] = True
    return m


def meccsek_gyujtes(j, fordulo, tarolo):
    """A keret-valaszban utazo meccseket teszi a tarolo[game_id] ala.
    Ugyanazt a meccset tobb jatekos is hozza - az id szerinti kulcsolas
    von ossze. A masik fordulobol visszaeso meccs (lasd meccs_forduloja)
    nem kerul be. Csak akkor ad valamit, ha a games-t egyaltalan kertuk."""
    for d in (j or {}).get("data") or []:
        cr = (d.get("competition_player") or {}).get("current_round") or {}
        for g in cr.get("games") or []:
            if not isinstance(g, dict) or g.get("id") is None:
                continue
            mf = meccs_forduloja(g)
            if mf is not None and mf != fordulo:
                continue
            tarolo[g["id"]] = meccs_kivonat(g)


def hatekonysag(sq):
    """Kezdoallitasi hatekonysag egy keretre: (szerzett, leheto) vagy None.

    SZABALY: a pad kotelezoen 1 kapus + 1 vedo +
    1 kozeppalyas + 1 csatar - formaciovalasztas tehat NINCS. Az optimum
    MEGSEM posztonkenti minimum: a magyarszabaly (+10, ha a kezdok kozt
    legalabb 5 magyar es koztuk U21-es van) fugg attol, KI ul a padon,
    ezert a 2x4x5x4 = ~160 pad-kombinaciot vegigprobaljuk (olcso), es
    mindegyikhez a legjobb kezdot tesszuk kapitanynak.

    A tarolt week mar KESZ ertek (kapitanyi x2, pad x0.5 benne van) - a
    nyers pontot a cap/sub jelzobol fejtjuk vissza. A szerzett a
    keret_osszeg (= a hivatalos fordulopont, magyarszaballyal egyutt)."""
    if not sq or len(sq) != 15:
        return None
    posztok = {}
    for p in sq:
        raw = float(p.get("week") or 0)
        if p.get("cap"):
            raw /= 2.0
        elif p.get("sub"):
            raw *= 2.0
        posztok.setdefault(p.get("pos") or "?", []).append(
            (raw, bool(p.get("hun")), bool(p.get("hun") and p.get("u21"))))
    if len(posztok) != 4 or any(len(v) < 2 for v in posztok.values()):
        return None                     # nem a vart 4-posztos keretsablon
    poszt_lista = list(posztok.values())
    legjobb = None
    for pad_idx in itertools.product(*[range(len(a)) for a in poszt_lista]):
        ossz = pad_fel = 0.0
        cap = None
        hun = u21 = 0
        for a, bi in zip(poszt_lista, pad_idx):
            for i, (raw, h, u) in enumerate(a):
                if i == bi:
                    pad_fel += 0.5 * raw
                else:
                    ossz += raw
                    if cap is None or raw > cap:
                        cap = raw
                    if h:
                        hun += 1
                    if u:
                        u21 += 1
        s = ossz + pad_fel + cap + (10 if (hun >= 5 and u21 >= 1) else 0)
        if legjobb is None or s > legjobb:
            legjobb = s
    return round(keret_osszeg(sq), 2), round(legjobb, 2)


def jatekostorzs():
    """A TELJES MLSZ-jatekostorzs - a fooldali jatekoslistahoz es kereseshez.

    Egyetlen kerés: a `per_page=500` mukodik ezen a vegponton (alapbol 15/lap
    lenne, 26 lap) - kimerve, lasd naplo/mlsz-jatekoslista.txt. Fordulora NEM
    szurheto, tehat csak a mostani allapotot adja; a fordulonkenti pontot a
    profil maskepp szedi ossze, ide csak a szezon-osszpont kell.

    Az `id` UGYANAZ, mint a keret-rekordok `id`-je (competition_player.id) -
    ezt is kimertuk: 102 mentett jatekosbol 102-nel ugyanaz a nev all
    ugyanazon az azonositon, elteres nulla. A profil megnyitasa ezen all.

    Aki KIKERULT a bajnoksagbol, az a torzsben mar nincs benne (a meresben 5
    ilyen volt), a keret-elozmenyben viszont igen - ezert a torzs a keresest
    szolgalja ki, nem a profilt: a profil a keret-elozmenybol is megnyilik.
    """
    st, j = api_get(BASE + "players?include=team,position,summary_statistics"
                          "&per_page=500")
    adat = (j or {}).get("data") if isinstance(j, dict) else None
    if st != 200 or not isinstance(adat, list) or not adat:
        print("  ! jatekostorzs: HTTP %s - a jatekosok.json valtozatlan" % st,
              file=sys.stderr)
        return None
    ki = {}
    for p in adat:
        cp = p.get("id")
        if not cp:
            continue
        po = p.get("position") or {}
        team = p.get("team") or {}
        ss = p.get("summary_statistics") or {}
        cr = p.get("current_round") or {}
        ki[str(cp)] = {
            "n": jatekosnev(p.get("first_name"), p.get("last_name"), "#%s" % cp),
            "t": team.get("short_name") or team.get("name") or "",
            "p": po.get("monogram") or po.get("name") or "",
            "u21": bool(p.get("is_u21")),
            "pts": ss.get("competition_points") or 0,
            # A MOSTANI piaci ar - nem az adott fordulóé (lasd README:
            # a mentett ar mindig a lekeres pillanatanak ara). A listaban
            # eppen ez kell: mennyibe kerul ma.
            "ar": cr.get("market_price"),
        }
    return ki


def zaras_valtozas(regi_fordulo, uj_fordulo, tarolo, mai):
    """Pontvaltozas a MECCS VEGE utan, a fordulo veglegesitese elott.

    A szabalyzat szerint a pont minden meccs utan meghatarozasra kerul, de a
    heti osszeg csak a fordulo utolso jateknapjanak vegen VEGLEGES - a ketto
    kozott az MLSZ meg igazithat. A gyujto a valtozast eddig atvezette, de
    NEM orizte meg; utolag rekonstrualhatatlan.

    A tarolo alakja a PL zarasok.json-jat koveti, hogy az oldal ugyanazt a
    megjelenitest hasznalhassa:  {szakvezeto: {"pont": [{n,cp,pos,tm,elott,utan}]}}

    Csak azt a jatekost nezzuk, akinek a TAROLT rekordja szerint a meccse mar
    veget ert (vege=True): a meccs kozbeni pontketyeges nem valtozas. Az
    ertek a jatekos SAJAT pontja (kapitanyi duplazas es padfelezes
    visszaszamolva, negyedre kerekitve), tehat ugyanaz a valtozas nem nez ki
    maskepp aszerint, kinel volt."""
    def alap(p):
        return round((p.get("week") or 0) / (2 if p.get("cap") else 1)
                     * (2 if p.get("sub") else 1) * 4) / 4

    db = 0
    for nev_, regi_sq in (regi_fordulo or {}).items():
        uj_sq = (uj_fordulo or {}).get(nev_)
        if not uj_sq:
            continue
        ujak = {}
        for p in uj_sq:
            ujak[p.get("id") or p.get("name")] = p
        for p in regi_sq:
            if not p.get("vege"):
                continue                      # meccs kozben a valtozas nem hir
            u = ujak.get(p.get("id") or p.get("name"))
            if not u or u.get("week") is None or p.get("week") is None:
                continue
            e, ut = alap(p), alap(u)
            if abs(e - ut) < 0.005:
                continue
            sorok = tarolo.setdefault(nev_, {}).setdefault("pont", [])
            if any(x.get("cp") == p.get("id") and x.get("n") == p.get("name")
                   and abs(x.get("utan", 0) - ut) < 0.005 for x in sorok):
                continue                      # ugyanazt a futast ne irjuk ketszer
            sorok.append({"n": p.get("name"), "cp": p.get("id"),
                          "pos": u.get("pos") or p.get("pos") or "",
                          "tm": u.get("team") or p.get("team") or "",
                          "elott": e, "utan": ut, "d": mai})
            db += 1
    return db


def zart_fordulok(schedule, provisional):
    """Mely fordulok LEZARTAK - a tarolt allapotbol, nem a mostani futasbol.

    Fontos, hogy ne a futas `lezart` szotarabol dolgozzunk: az csak azokat a
    fordulokat ismeri, amiknek a keretet EBBEN a futasban lekertuk (a
    celok halmaz), tehat a regebbieket sosem. Igy az elso bevezeteskor csak
    az utolso fordulohoz keszult volna bontas. Lezart az, aminek minden
    meccse eredmenyes ES nincs az ideiglenesek kozott - pontosan az, amit az
    oldal is lezartkent kezel."""
    prov = {int(x) for x in (provisional or [])}
    ki = []
    for r, ms in (schedule or {}).items():
        if int(r) in prov or not ms:
            continue
        if all(m[2] is not None and m[3] is not None for m in ms):
            ki.append(int(r))
    return sorted(ki)


def bontas_szures(sorok):
    """Amit a bontasbol TAROLNI kell.

    Az MLSZ minden jatszott jatekosra mind a 22 statisztika-sort visszaadja,
    a nullas ertekueket is - a 385 jatekos igy fordulonkent 141 KB, a szezon
    vegere 4,5 MB. Az oldal viszont csak a PONTOT ERO sorokat mutatja, plusz
    a "Jatszott perc" sort (azt kulon, pont nelkul, es az uzenet-logika is
    abbol dol el). A tobbi sor nulla ponttal all - informaciot nem visz.

    Ez a szures VISSZAFORDITHATO: a game-player-stats vegpont a regi
    fordulokra is valaszol (ezen mult eddig az egesz bontas), tehat a
    kihagyott nyers ertekek barmikor ujra lekerhetok. Ezert lehet szurni -
    az arnaplonal pont ezert NEM lehetett: az arat visszamenoleg senki nem
    adja vissza. Meret: 141 KB -> 40 KB fordulonkent (4,5 MB -> 1,3 MB)."""
    return [x for x in sorok if x.get("p") or x.get("n") == "Játszott perc"]


def bontasok_gyujtes(zartak, valtozott, torzs):
    """A lezart fordulok TETELES pont-bontasa a repoba (bontasok/<r>.json).

    MIERT: a bontast ("mibol jott ossze a 9,75 pont") eddig KIZAROLAG a
    bongeszo kerte le, kattintasra, elo MLSZ-hivassal. Ha az MLSZ vagy a
    kozvetito eppen nem elerheto, a lenyilo hibat irt - pedig a lezart
    fordulo bontasa mar sosem valtozik, tehat egyszer le lehet kerni es el
    lehet tenni. Innentol a lezart fordulo bontasa a repobol jon: azonnal
    nyilik, halozat-fuggetlenul, es a soha nem birtokolt jatekos profilja
    sem lo ki fordulonkent egy-egy elo kerest.

    MIERT A TELJES MEZONY (385 jatekos), nem csak a birtokoltak: a fooldali
    jatekoslistabol barmelyik jatekos profilja megnyithato. A gyujto a
    GitHub szerverérol KOZVETLENUL keri az MLSZ-t (nincs CORS, nincs
    kozvetito), tehat ez egyik kvotankat sem terheli - csak fordulonkent
    egyszeri ~3 perc futasido.

    MIKOR: fordulonkent EGYSZER, a lezaraskor - vagy ujra, ha az adott
    fordulo eredmenye kozben valtozott (MLSZ-korrekcio). Amig a fajl megvan
    es a fordulo nem mozdult, nem kerunk le semmit.

    HIANYOS FUTAST NEM IRUNK KI: ha a jatekosok 10%-anal tobbnel elhasal a
    keres, a fajl nem keszul el, es a kovetkezo futas ujraprobalja. Egy
    felig kesz fajl rosszabb a hianyzonal - azt sosem probalnank ujra."""
    if not torzs:
        return 0
    os.makedirs("bontasok", exist_ok=True)
    idk = sorted(torzs, key=lambda x: int(x))
    kiirt = 0
    for r in zartak:
        ut = os.path.join("bontasok", "%d.json" % r)
        if os.path.exists(ut) and r not in valtozott:
            continue
        print("  bontasok: %d. fordulo, %d jatekos lekerese%s"
              % (r, len(idk), " (ujra: az eredmeny valtozott)" if r in valtozott else ""))
        sorok, hiba = {}, 0
        for i, cp in enumerate(idk, 1):
            url = (ROOT + "game-player-stats?include=competition_stat_config"
                   "&filter%5Bcompetition_player_id%5D=" + str(cp) +
                   "&filter%5Bround_id%5D=" + str(rid(r)))
            st, j = api_get(url)
            if st != 200 or j is None:
                hiba += 1
                continue
            sorok[str(cp)] = bontas_szures([
                {"n": (x.get("competition_stat_config") or {}).get("name") or "?",
                 "v": x.get("value"), "p": x.get("points")}
                for x in (j.get("data") or [])])
            if i % 100 == 0:
                print("    %d/%d" % (i, len(idk)))
        if hiba > len(idk) // 10:
            print("  ! bontasok: %d. fordulo kihagyva - %d/%d keres elhasalt,"
                  " a kovetkezo futas ujraprobalja" % (r, hiba, len(idk)), file=sys.stderr)
            continue
        # Az `updated` mezo SZANDEKOSAN nincs benne - ugyanaz az ok, mint a
        # keretek/ fajloknal: a lezart fordulo bontasa nem valtozik, es egy
        # idobelyeg minden futasnal ujrairna a fajlt.
        kompakt_iras(ut, {"round": r, "bontasok": sorok})
        kiirt += 1
        print("  bontasok/%d.json kiirva (%d jatekos%s)"
              % (r, len(sorok), ", %d sikertelen" % hiba if hiba else ""))
    return kiirt


def arnaplo_frissit(torzs, mai):
    """Az arak valtozasanak naplozasa (arak.json).

    Ma semmi nem hasznalja - azert gyujtjuk, mert visszamenoleg NEM lehet
    pototlni: az API csak a MOSTANI arat adja, a multat sehol nem tarolja.
    Amit ma nem irunk fel, az orokre elveszett.

    Csak a VALTOZAST irjuk fel, nem minden futast: a gyujto 3 oraankent fut,
    igy a fajl napi nyolc valtozatlan bejegyzessel hizna. Egy jatekos sora
    tehat [[datum, ar], ...], es uj elem csak akkor kerul bele, ha az ar mas,
    mint a legutobb feljegyzett.

    A hianyzo vagy nulla arat NEM tekintjuk valtozasnak: az API-hiba igy nem
    ir be hamis "0-ra esett" bejegyzest (ugyanaz a logika, mint a 0-0
    vedelem a results.json-nal).
    """
    try:
        with open("arak.json", encoding="utf-8") as f:
            naplo = json.load(f).get("arak") or {}
    except Exception:
        naplo = {}
    valtozott = 0
    for cp, rec in torzs.items():
        ar = rec.get("ar")
        if not isinstance(ar, (int, float)) or ar <= 0:
            continue
        sor = naplo.setdefault(cp, [])
        if sor and sor[-1][1] == ar:
            continue
        sor.append([mai, ar])
        valtozott += 1
    return naplo, valtozott


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
    # Melyik fordulo allt MAR A FUTAS ELOTT veglegeskent a tabellaban?
    # (Minden meccsen van eredmeny, es nem volt az ideiglenes listaban.)
    # MEG A BEIRASOK ELOTT rogzitjuk: a bizonytalan ag erre tamaszkodik.
    volt_vegleges = {int(r) for r, ms in schedule.items()
                     if ms and all(m[2] is not None and m[3] is not None for m in ms)
                     and int(r) not in {int(x) for x in (data.get("provisional") or [])}}
    try:
        with open("squad_history.json", encoding="utf-8") as f:
            hist = json.load(f)
    except Exception:
        hist = {"updated": None, "rounds": {}}
    hist.setdefault("rounds", {})
    try:
        with open("zarasok_nb1.json", encoding="utf-8") as f:
            zarasok_nb1 = json.load(f)
    except Exception:
        zarasok_nb1 = {}
    zarasok_nb1.setdefault("rounds", {})
    zarasok_nb1_valtozott = False
    # A legelso valtozat CSAPATSZINTU sorokat tarolt (listaban, {"mgr":...}),
    # jatekos nelkul. Azokat nem lehet visszamenoleg jatekosra bontani (a
    # jatekos-szintu pillanatkepek mind a mar javitott erteket tartalmazzak),
    # es a panel sem tudja megjeleniteni oket - eldobjuk, hogy a regi alak ne
    # akassza meg a futast.
    for _r in [k for k, v in zarasok_nb1["rounds"].items() if not isinstance(v, dict)]:
        del zarasok_nb1["rounds"][_r]
        zarasok_nb1_valtozott = True
    hist_elotte = json.dumps(hist.get("rounds"), ensure_ascii=False, sort_keys=True)
    try:
        with open("meccsek.json", encoding="utf-8") as f:
            meccsek = json.load(f)
    except Exception:
        meccsek = {"updated": None, "rounds": {}}
    meccsek.setdefault("rounds", {})
    meccsek_elotte = json.dumps(meccsek["rounds"], ensure_ascii=False, sort_keys=True)

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
    # A ranglista alapbol csak a ket legfrissebb fordulot adja, tehat egy
    # regi fordulo utolagos MLSZ-korrekciojarol magatol nem ertesulnenk.
    # Ezert koronkent nehany regi fordulot ujra lekerunk (lasd ellenorzendo).
    ujra = ellenorzendo([r for r in range(1, max(aktualis - 1, 1))])
    for r in sorted(set(hianyzo) | set(ujra)):
        print("  %s: %d. fordulo hivatalos pontjai"
              % ("potlas" if r in hianyzo else "ellenorzes", r))
        for nev, uname in MEMBERS.items():
            row = rankings(uname, round_id=rid(r))
            if not row:
                continue
            for s in (row.get("user_team") or {}).get("round_statistics") or []:
                # a vegpont az igazsag: felulirjuk, nem csak potoljuk
                pontok[nev][int(s["round_number"])] = s["points"]

    # ---- 3. Eredmenyek szinkronja (a vegpont az igazsag) ----
    beirt, javitott = 0, 0
    valtozott = set()          # ezekhez a fordulokhoz a keret is elavult
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
                valtozott.add(r)
                print("  ~ %d. fordulo: %s %s - %s %s  (volt: %s - %s) - MLSZ-korrekcio"
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
    # ha egy regi fordulo hivatalos pontja most valtozott, akkor a hozza
    # tartozo keret is elavult - azt is ujra le kell kerni
    celok |= valtozott
    # REGI FORMATUM POTLASA. A 2026-08-21 elotti keret-rekordokban meg nincs
    # "id", "played" es "start" - emiatt az oldal a pont-bontashoz elohivast
    # kenytelen inditani, es a "nincs meccse" jelzes teljesen hianyzik (a 3.
    # fordulos ETO-jatekosoknal ezert irta az oldal, hogy a meccs meg nem
    # kezdodott el, egy mar elmult helyorzo datummal). Az ilyen fordulot
    # egyszer ujra lekerjuk - a meccslistaval egyutt, hogy a nogame is
    # bekerulhessen. Utana a feltetel mar nem teljesul, tehat nem ismetlodik.
    migralando = {int(r) for r, keret in hist["rounds"].items()
                  if keret and any("played" not in p
                                   for sq in keret.values() for p in sq)}
    if migralando:
        print("  regi formatumu keretek potlasa: %s. fordulo"
              % ", ".join(str(x) for x in sorted(migralando)))
    celok |= migralando
    # MECCSEK POTLASA a meccsek.json-hoz: az a fordulo szorul ra, amelyikbol
    # meg nincs meccs eltarolva, vagy van eredmeny nelkuli (nem lezart)
    # meccse. Az elo fordulo amugy is meccslistaval megy; a regiekre ez
    # egyszeri nagy lekeres (a lezart meccs melle az API a klublogokat is
    # betolti), utana a feltetel mar nem all fenn.
    # A "?" klubu meccs is hianyos. Enelkul: ha egy fordulo OSSZES meccse
    # lement, mikozben a klubnevek meg "?"-ek voltak, a fordulo kikerult
    # volna az ujrakerendok kozul, es amint az MLSZ tovabblep, SOHA TOBBE
    # nem kertuk volna le - a "?" veglegesen bent ragadt volna.
    meccs_potlas = {r for r in range(1, aktualis + 1)
                    if not meccsek["rounds"].get(str(r))
                    or any(not m.get("vege") or m.get("h") == "?" or m.get("v") == "?"
                           for m in meccsek["rounds"][str(r)])}
    if meccs_potlas - {aktualis}:
        print("  meccsek potlasa: %s. fordulo"
              % ", ".join(str(x) for x in sorted(meccs_potlas - {aktualis})))
    celok |= meccs_potlas

    # lezart: r -> True/False, de CSAK ha teljes az adat. Amit nem tudtunk
    # kiertekelni (elhasalt lekeres, 403), az a `bizonytalan` halmazba kerul,
    # es ott a fordulo korabbi allapota marad ervenyben. Enelkul egyetlen
    # halozati hiba vagy veglegesnek szamitotta volna az elo fordulo
    # reszeredmenyet (a provisional lista kiurulesevel), vagy ideiglenesse
    # minositett volna egy mar lezart fordulot - mindketto rossz tabellat ad.
    lezart, bizonytalan = {}, set()
    mlsz_akt, mlsz_vegek = versenyfordulok()
    print("  az MLSZ szerinti aktualis fordulo: %s" % (mlsz_akt if mlsz_akt else "nem elerheto"))
    for r in sorted(celok):
        # olcso elovizsgalat egyetlen kerettel: 403 = a fordulo meg titkos
        elso_id = next(iter(ids.values()))
        st, _ = squad(elso_id, r)
        if st == 403:
            print("  . %d. fordulo keretei meg nem elerhetok (piaczaras elott)" % r)
            bizonytalan.add(r)
            continue
        uj_fordulo, teljes = {}, True
        mind_lement = True          # a meccslista szerint minden meccs lement
        fordulo_meccsei = {m["id"]: m for m in meccsek["rounds"].get(str(r)) or []
                           if m.get("id") is not None}
        for nev, uid in ids.items():
            # A meccslistat akkor kerjuk, ha az elo fordulorol van szo, ha a
            # regi formatumot potoljuk, ha a meccsek.json-bol hianyzik valami,
            # VAGY ha a fordulo hivatalos pontja most valtozott. Az utobbi a
            # POTOLT MECCS esete: az elhalasztott meccs egyszeruen nincs benne
            # a listaban (nem "eredmeny nelkuli"), tehat a meccs_potlas
            # feltetele nem venne eszre - a lejatszasakor viszont a pontok
            # biztosan valtoznak, mert a percekert is jar pont.
            st, j = squad(uid, r, jatek=(r == aktualis or r in migralando
                                         or r in meccs_potlas or r in valtozott))
            if st != 200 or not isinstance(j, dict) or not j.get("data"):
                print("  ! %d. fordulo / %s: HTTP %s" % (r, nev, st), file=sys.stderr)
                teljes = False
                continue
            uj_fordulo[nev] = [rekord(d, r) for d in j["data"]]
            meccsek_gyujtes(j, r, fordulo_meccsei)
            for d in j["data"]:
                cr = (d.get("competition_player") or {}).get("current_round") or {}
                # Az is_played mar a meccs KOZBEN igazra vall - abbol tehat NEM
                # kovetkezik, hogy a fordulo lement. Enelkul: amint a fordulo
                # utolso meccse elkezdodott, mindenki "jatszott" lett, a gyujto
                # lezartnak minositette a fordulot, es a felig kesz eredmeny
                # veglegeskent kerult a tabellaba. A meccslista status-a a
                # fogodzo; ha nem kertuk le (regi fordulo), marad az is_played.
                # ...es csak akkor, ha a meccs tenyleg EHHEZ a fordulohoz
                # tartozik: a masik fordulobol visszaeso meccs allapota nem
                # mondhat semmit errol a forduloról.
                g = cr.get("games")
                if g and meccs_forduloja(g[0]) in (None, r) \
                        and (g[0] or {}).get("status") != "completed":
                    mind_lement = False
        if not uj_fordulo:
            bizonytalan.add(r)
            continue
        if fordulo_meccsei:
            meccsek["rounds"][str(r)] = sorted(
                fordulo_meccsei.values(), key=lambda m: (m.get("start") or "", m["h"]))
        regi_fordulo = hist["rounds"].get(str(r)) or {}
        # meccs utani pontigazitas naplozasa, MIELOTT az uj felulirja a regit
        zvalt = zarasok_nb1["rounds"].setdefault(str(r), {})
        zdb = zaras_valtozas(regi_fordulo, uj_fordulo, zvalt,
                             time.strftime("%Y-%m-%d", time.gmtime()))
        if not zvalt:
            del zarasok_nb1["rounds"][str(r)]
        if zdb:
            zarasok_nb1_valtozott = True
            print("  ! %d. fordulo: %d pontigazitas a meccs vege utan" % (r, zdb))
        orokit_meccsjelzok(regi_fordulo, uj_fordulo)
        hist["rounds"][str(r)] = {**regi_fordulo, **uj_fordulo}
        # A "mindenki jatszott" vizsgalat a MAR OSSZEFESULT rekordokbol dol
        # el, nem a nyers valaszbol: a "nincs meccse" jelzes csak ott van meg.
        # (A meccslistat csak az elo fordulora kerjuk le, utana a
        # orokit_meccsjelzok hozza at a korabbi pillanatkepbol.)
        mind_jatszott = all(p.get("played") or p.get("nogame")
                            for sq in uj_fordulo.values() for p in sq)
        hianytalan = teljes and len(uj_fordulo) == len(MEMBERS)
        halo = ""
        if hianytalan:
            kesz = mind_jatszott and mind_lement
            # Biztonsagi halo: ha valamiert megsem all ossze a jatekos-szintu
            # kep, de az MLSZ mar tovabblepett a fordulon, akkor lezart. Igy
            # egy fordulo nem tud vegtelen ideig ideiglenes maradni.
            if not kesz and mlsz_lezarta(r, mlsz_akt, mlsz_vegek):
                kesz, halo = True, " (az MLSZ szerint lezarult)"
            lezart[r] = kesz
        else:
            bizonytalan.add(r)
        print("  keretek: %d. fordulo, %d/%d szakvezeto, %s%s"
              % (r, len(uj_fordulo), len(MEMBERS),
                 ("lezart" if lezart[r] else "meg tart") if hianytalan
                 else "HIANYOS adat - a lezartsag valtozatlan marad", halo))

        # keresztellenorzes: csak teljes es mar lezart fordulora van ertelme
        if not (hianytalan and lezart[r]):
            continue
        for nev, sq in uj_fordulo.items():
            hiv = pontok.get(nev, {}).get(r)
            if hiv in (None, 0):
                continue
            szamolt = keret_osszeg(sq)
            if abs(szamolt - hiv) < 0.005:
                continue
            # A keret ebben a futasban frissult, tehat inkabb a hivatalos
            # ertek elavult: kerjuk le ujra erre a fordulora, es ha valtozott,
            # vezessuk at. Nem jelzunk, hanem javitunk.
            row = rankings(MEMBERS[nev], round_id=rid(r))
            friss = None
            for st2 in ((row or {}).get("user_team") or {}).get("round_statistics") or []:
                if int(st2["round_number"]) == r:
                    friss = st2["points"]
            if friss is not None and abs(friss - hiv) >= 0.005:
                pontok[nev][r] = friss
                javitott += beir_eredmeny(schedule, r, nev, friss)
                print("  ~ %d. fordulo / %s: hivatalos pont frissitve %.2f -> %.2f"
                      % (r, nev, hiv, friss))
                hiv = friss
            if abs(szamolt - hiv) >= 0.005:
                print("  ! ELTERES %d. fordulo / %s: keretbol %.2f, hivatalos %.2f"
                      " - a ket forras ujralekeres utan sem egyezik"
                      % (r, nev, szamolt, hiv), file=sys.stderr)

    # ---- 5. Ideiglenes fordulok ----
    # Csak az szamit ideiglenesnek, aminek mar van pontja, de a keretek
    # szerint meg nem jatszott le minden jatekos.
    #
    # A fordulo-korlat NEM diszites: a rolling ellenorzes ota reg lezart
    # fordulok is bekerulhetnek a `celok` koze (ha az MLSZ korrigalt), es ott
    # egyetlen elhasalt keret-lekeres is `lezart[r]=False`-t adna. Az ilyen
    # fordulo hibasan ideiglenesnek latszana, az oldal pedig kivenne a
    # SCHEDULE-bol az elo retegbe - vagyis egy hetekkel korabbi, lejatszott
    # fordulo eltunne a tabellabol. Ideiglenes csak a most zajlo vagy eppen
    # most zarult fordulo lehet.
    regi_prov = {int(x) for x in (data.get("provisional") or [])}

    def van_pont(r):
        return any(pontok.get(n, {}).get(r) for n in MEMBERS)

    prov = {r for r, kesz in lezart.items()
            if not kesz and r >= aktualis - 1 and van_pont(r)}
    # Amit nem tudtunk kiertekelni, ott nem talalgatunk - de nem is egyformak
    # a tevedesek. Ha egy friss fordulot tevesen veglegesnek irunk be, a
    # felig kesz eredmeny bekerul a tabellaba (csendes, hihetо, rossz). Ha
    # tevesen ideiglenesnek, a fordulo atmenetileg kimarad (lathato, es a
    # kovetkezo futas javitja). Ezert a friss fordulo alapertelmezetten
    # ideiglenes marad, a regi pedig megtartja a korabbi allapotat.
    for r in bizonytalan:
        if r in regi_prov:
            prov.add(r)
        elif r != aktualis and r in volt_vegleges:
            # A mar LEZART fordulo veglegeskent allt kint - egy hianyos futas
            # (halozati hiba, reszleges valasz) nem nyithatja ujra. Enelkul
            # egyetlen DNS-hiba kivette az 5. fordulot a tabellabol
            # (megtortent: 2026-08-25 21:47, "nincs ranglista-adat: Katyul"
            # -> a tabella a 4 fordulos allast mutatta).
            # Az ELO fordulora (r == aktualis) a vedelem NEM all: ott a
            # "veglegesnek latszo" tarolt szam reszeredmeny is lehet, es a
            # rosszabb hiba az, ha az bekerul a tabellaba.
            print("  . %d. fordulo: hianyos futas, de mar vegleges volt - az is marad" % r)
        elif r >= aktualis - 1 and van_pont(r):
            prov.add(r)
    provisional = sorted(prov)

    # ---- 6. Iras, csak ha valtozott ----
    # A `provisional` LISTA, a `regi_prov` HALMAZ - a ketto sosem egyenlo,
    # tehat ez a feltetel korabban MINDIG igaz volt, es a results.json minden
    # futasban ujrairodott friss idobelyeggel. (Mert: a 36 utolso
    # results.json-commitbol 30-ban CSAK az `updated` mezo valtozott.) A
    # tobbi fajl mind tartalmat hasonlit - ez most mar ugyanugy.
    if beirt or javitott or set(provisional) != regi_prov:
        data["provisional"] = provisional
        data["updated"] = stamp()
        with open("results.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=0)
        print("  results.json frissitve")

    # ---- Kezdoallitasi hatekonysag: minden tarolt fordulora ujraszamolva.
    # Determinisztikus es olcso (nehany szaz rekord), ezert nem tartunk hozza
    # allapotot: amig a keret nem valtozik, a fajl sem. Az elo fordulo erteke
    # meg valtozik - a lap donti el, hogy a tabellaba csak a lezartat veszi.
    hat = {}
    for r_, keretek in hist["rounds"].items():
        sor = {}
        for nev_, sq_ in (keretek or {}).items():
            h_ = hatekonysag(sq_)
            if h_:
                sor[nev_] = {"sz": h_[0], "le": h_[1]}
        if sor:
            hat[r_] = sor
    try:
        with open("hatekonysag.json", encoding="utf-8") as f:
            hat_regi = json.load(f).get("rounds")
    except Exception:
        hat_regi = None
    if json.dumps(hat, ensure_ascii=False, sort_keys=True) !=             json.dumps(hat_regi, ensure_ascii=False, sort_keys=True):
        kompakt_iras("hatekonysag.json", {"updated": stamp(), "rounds": hat})
        print("  hatekonysag.json frissitve")

    # ---- Guardiola mutato: fordulonkent ujraszamolva, mint a hatekonysag.
    # Csak arra a fordulora keszul, aminek MAR VAN bontasa (tehat lezart) es
    # van elozo fordulos kerete - az elsore fogalmilag nincs.
    gua = {}
    for r_ in sorted((int(x) for x in hist["rounds"]), reverse=False):
        g_ = guardiola(hist["rounds"], r_)
        if g_:
            gua[str(r_)] = g_
    try:
        with open("guardiola.json", encoding="utf-8") as f:
            gua_regi = json.load(f).get("rounds")
    except Exception:
        gua_regi = None
    if json.dumps(gua, ensure_ascii=False, sort_keys=True) != \
       json.dumps(gua_regi, ensure_ascii=False, sort_keys=True):
        kompakt_iras("guardiola.json", {"updated": stamp(), "rounds": gua})
        print("  guardiola.json frissitve (%d fordulo)" % len(gua))

    # A torzs a nev-atirashoz is kell, ezert MEG a kiiras elott lekerjuk.
    torzs = jatekostorzs()
    # A tarolt nevek atvezetese a torzs szerinti alakra. Nem csak egyszeri
    # migracio (nyugati -> magyar sorrend): ha az MLSZ barmikor javit egy
    # nevet, a regi fordulok is kovetik. Az azonosito a fogodzo, tehat nem
    # nev-egyeztetessel dolgozunk.
    if torzs:
        atirt = 0
        for keretek_ in hist["rounds"].values():
            for sq_ in (keretek_ or {}).values():
                for p_ in sq_:
                    rec_ = torzs.get(str(p_.get("id") or ""))
                    if rec_ and rec_["n"] and p_.get("name") != rec_["n"]:
                        p_["name"] = rec_["n"]
                        atirt += 1
        if atirt:
            print("  %d tarolt jatekosnev atvezetve a torzs szerinti alakra" % atirt)

    # A lezart fordulok teteles bontasa (bontasok/<r>.json). A torzs UTAN,
    # mert abbol jon a jatekoslista; a `valtozott` halmaz miatt egy utolagos
    # MLSZ-korrekcio a bontast is frissiti.
    if torzs:
        bontasok_gyujtes(zart_fordulok(schedule, provisional), valtozott, torzs)

    if json.dumps(meccsek["rounds"], ensure_ascii=False, sort_keys=True) != meccsek_elotte:
        meccsek["updated"] = stamp()
        kompakt_iras("meccsek.json", meccsek)
        print("  meccsek.json frissitve")

    if json.dumps(hist.get("rounds"), ensure_ascii=False, sort_keys=True) != hist_elotte:
        hist["updated"] = stamp()
        kompakt_iras("squad_history.json", {"updated": hist["updated"],
                                            "rounds": hist["rounds"]})
        utolso = max((int(r) for r in hist["rounds"]), default=0)
        # A squads.json CSAK az utolso fordulot tartalmazza, a fenti feltetel
        # viszont BARMELYIK fordulo valtozasara igaz - egy regi fordulo
        # utolagos korrekcioja igy ujra kiirta volna a fajlt uj idobelyeggel,
        # valtozatlan tartalommal. (Az utolso 14 valtozasabol 2 ilyen volt.)
        # A kereteket ezert kulon hasonlitjuk, ahogy a tobbi kimenetnel is.
        uj_squads = {"round": utolso, "squads": hist["rounds"].get(str(utolso)) or {}}
        try:
            with open("squads.json", encoding="utf-8") as f:
                regi_squads = json.load(f)
            regi_squads = {k: v for k, v in regi_squads.items() if k != "updated"}
        except Exception:
            regi_squads = None
        if json.dumps(regi_squads, ensure_ascii=False, sort_keys=True) != \
           json.dumps(uj_squads, ensure_ascii=False, sort_keys=True):
            # a mezosorrend marad (updated, round, squads) - kulonben a
            # kovetkezo iras az egesz fajlt "megvaltoztatna" a sorrend miatt
            kompakt_iras("squads.json", {"updated": hist["updated"],
                                         "round": uj_squads["round"],
                                         "squads": uj_squads["squads"]})
        # Fordulonkenti keret-fajlok. A teljes elozmeny fordulonkent ~19 KB-tal
        # no, a szezon vegere ~630 KB - egy meccs megnyitasahoz az oldalnak
        # nem kell az egesz. A `updated` mezo SZANDEKOSAN nincs bennuk: ha
        # minden futasnal belekerulne az idobelyeg, mind a 33 fajl valtozna
        # minden korben, es a repo feleslegesen hizna. Igy egy fordulo fajlja
        # csak akkor valtozik, ha a keretek tenylegesen valtoztak.
        os.makedirs("keretek", exist_ok=True)
        for r, keret in hist["rounds"].items():
            kompakt_iras(os.path.join("keretek", "%s.json" % r),
                         {"round": int(r), "squads": keret})
        print("  squad_history.json + squads.json + keretek/ frissitve"
              " (utolso fordulo: %d)" % utolso)

    # ---- Jatekostorzs (a fooldali lista + kereses). Egy keres futasonkent.
    # Az `updated` mezot az osszehasonlitasbol kihagyjuk, kulonben minden
    # korben valtozna a fajl akkor is, ha egyetlen pont sem mozdult.
    if torzs is not None:
        try:
            with open("jatekosok.json", encoding="utf-8") as f:
                torzs_regi = json.load(f).get("players")
        except Exception:
            torzs_regi = None
        if json.dumps(torzs, ensure_ascii=False, sort_keys=True) != \
           json.dumps(torzs_regi, ensure_ascii=False, sort_keys=True):
            kompakt_iras("jatekosok.json", {"updated": stamp(), "players": torzs})
            print("  jatekosok.json frissitve (%d jatekos)" % len(torzs))

    if zarasok_nb1_valtozott:
        zarasok_nb1["updated"] = stamp()
        kompakt_iras("zarasok_nb1.json", zarasok_nb1)
        print("  zarasok_nb1.json frissitve")

    # ---- Arnaplo: csak a valtozasok, mert a multat nem lehet potolni ----
    if torzs is not None:
        arak, valtozott = arnaplo_frissit(torzs, time.strftime("%Y-%m-%d", time.gmtime()))
        if valtozott:
            kompakt_iras("arak.json", {"updated": stamp(), "arak": arak})
            print("  arak.json frissitve (%d arvaltozas)" % valtozott)

    if provisional:
        print("  ideiglenes (meg tart): %s. fordulo" % ", ".join(map(str, provisional)))
    print("Kesz: %d uj, %d javitott eredmeny." % (beirt, javitott))
    return 0


if __name__ == "__main__":
    sys.exit(main())
