#!/usr/bin/env python3
"""FunTasy Liga - FPL Draft liga adatainak gyujtese.

Negy fajlt gondoz (mind kompakt JSON, a repo tobbi adatfajljanak stilusaban):

  draft.json         - resztvevok, menetrend, eredmenyek, allasok
  draft_players.json - jatekos-torzsadat: {id: {n: nev, t: klub, p: poszt}}
  draft_squads.json  - a JELENLEGI keretek: {liga_id: [element_id, ...]}
  draft_history.json - fordulonkenti keretek pontokkal (a GW1 indulasatol):
                       {rounds: {gw: {liga_id: [{e, b, pts}, ...]}}}
                       e=jatekos-azonosito, b=pad (bench), pts=heti pont

VEGPONTOK (2026-08-20-an merve, a GitHub futojarol):
  - league/{id}/details        200 - resztvevok, menetrend, eredmenyek
  - bootstrap-static           200 - 599 jatekos, klubok, posztok
  - league/{id}/element-status 200 - ki birtokolja most az adott jatekost
  - entry/{eid}/event/{gw}     404 A FORDULO INDULASAIG, utana picks
  - event/{gw}/live            200 - jatekosonkenti heti pontok
  - game                       200 - current_event (aktualis fordulo)

FONTOS - adatvedelem:
A details valasza a resztvevok VALODI NEVET is tartalmazza. A repo publikus,
ezert soha nem mentunk nyers valaszt: minden kimeno rekord mezonkent epul,
es a mentes elott a nevszures() ellenorzi, hogy tiltott mezo (valodi nev,
entry_id) nem szivargott-e ki. A labdarugok neve nyilvanos adat, az mehet.

FONTOS - ket kulonbozo azonosito:
Minden resztvevonek van "entry_id"-ja (FPL csapat-azonosito) es "id"-ja
(liga-beli azonosito). A matches/standings az "id"-t hasznalja, a
keret-vegpontok az entry_id-t. A repoban CSAK az "id" szerepel; az
entry_id-t futas kozben, memoriaban hasznaljuk. Az element-status "owner"
mezojenek azonosito-tere bizonytalan volt, ezert futaskor ismerjuk fel,
melyik terben van, es liga-id-ra kepezzuk.

A liga azonositoja a DRAFT_LEAGUE_ID kornyezeti valtozobol felulirhato.
"""
import json, os, sys, time, urllib.error, urllib.request

LEAGUE_ID = os.environ.get("DRAFT_LEAGUE_ID", "48093")
B = "https://draft.premierleague.com/api/"
HDRS = {
    "Accept": "application/json",
    "Accept-Language": "en-GB,en;q=0.9",
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"),
}


def fetch(path, retries=3):
    """(status, adat) - halozati hibanal ujraprobal, 4xx-nel nem."""
    url = B + path
    for i in range(retries):
        time.sleep(0.2)
        try:
            req = urllib.request.Request(url, headers=HDRS)
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.status, json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            return e.code, None
        except Exception as e:
            if i == retries - 1:
                print("  ! halozati hiba (%s): %s" % (path, e), file=sys.stderr)
                return None, None
            time.sleep(3)
    return None, None


def atalakit(data):
    """A details valaszabol a draft.json szerkezete - valodi nevek nelkul."""
    liga = data.get("league") or {}
    entries = []
    for e in data.get("league_entries") or []:
        entries.append({"id": e.get("id"),
                        "name": e.get("entry_name") or "",
                        "short": e.get("short_name") or ""})
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
        allas.append({"id": s.get("league_entry"), "rank": s.get("rank"),
                      "played": s.get("matches_played"), "won": s.get("matches_won"),
                      "drawn": s.get("matches_drawn"), "lost": s.get("matches_lost"),
                      "for": s.get("points_for"), "against": s.get("points_against"),
                      "total": s.get("total")})
    return {
        "updated": None,
        "league": {"id": liga.get("id"), "name": liga.get("name") or "",
                   "start_event": liga.get("start_event"),
                   "stop_event": liga.get("stop_event")},
        "entries": entries, "schedule": schedule, "standings": allas,
    }, lejatszott


def nevszures(payload):
    """Biztonsagi halo: tiltott mezo a kimenetben -> leallas, nincs mentes."""
    szoveg = json.dumps(payload, ensure_ascii=False)
    for tiltott in ("player_first_name", "player_last_name", "entry_id"):
        if tiltott in szoveg:
            raise SystemExit("HIBA: '%s' a kimenetben - a mentes megszakitva." % tiltott)


def stamp():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def kiir_ha_valtozott(path, tartalom, regi_nelkul_kulcs="updated"):
    """Kompakt iras, csak ha a tartalom (updated nelkul) valtozott."""
    try:
        with open(path, encoding="utf-8") as f:
            regi = json.load(f)
    except Exception:
        regi = None

    def mag(x):
        if not isinstance(x, dict):
            return x
        return {k: v for k, v in x.items() if k != regi_nelkul_kulcs}

    if regi is not None and json.dumps(mag(regi), sort_keys=True, ensure_ascii=False) \
                          == json.dumps(mag(tartalom), sort_keys=True, ensure_ascii=False):
        return False
    tartalom["updated"] = stamp()
    nevszures(tartalom)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(tartalom, f, ensure_ascii=False, separators=(",", ":"))
    print("  + %s kiirva (%d byte)" % (path, os.path.getsize(path)))
    return True


def zarasi_kulonbseg(regi, uj):
    """A zaras elotti (tarolt) es utani (friss) keretek kulonbsege.
    Csapatonkent: "pont" = jatekosonkenti pontvaltozas (a bonusz-korrekcio),
    "ki"/"be" = az automatikus cserek (a pad-jelzo valtozasabol - a zaraskor
    az FPL atirja a position mezot, merve 2026-08-25). None, ha nincs mibol
    szamolni (nincs tarolt pillanatkep); ures dict, ha semmi sem valtozott -
    az is eredmeny: azt jelenti, a zaras nem hozott valtozast."""
    if not regi:
        return None
    ki = {}
    for lid, friss in uj.items():
        volt = regi.get(lid)
        if not volt:
            continue
        vp = {x["e"]: x for x in volt}
        pont = [{"e": x["e"], "elott": vp[x["e"]]["pts"], "utan": x["pts"]}
                for x in friss if x["e"] in vp and vp[x["e"]]["pts"] != x["pts"]]
        # a cserenel a PONT is kell: a bekerult jatekos pontja mondja meg,
        # mit hozott a csere (a kikerulte pedig, miert tortent)
        csere_ki = [{"e": x["e"], "pts": x["pts"]} for x in friss
                    if x["b"] and x["e"] in vp and not vp[x["e"]]["b"]]
        csere_be = [{"e": x["e"], "pts": x["pts"]} for x in friss
                    if not x["b"] and x["e"] in vp and vp[x["e"]]["b"]]
        if pont or csere_ki or csere_be:
            ki[lid] = {}
            if pont:
                ki[lid]["pont"] = pont
            if csere_ki or csere_be:
                ki[lid]["ki"], ki[lid]["be"] = csere_ki, csere_be
    return ki


def jatekos_pont(v):
    """Egy jatekos fordulo-pontja a live valaszbol: (pont, bontasbol_jott).

    A PONT A TETELES BONTASBOL (explain) ALL OSSZE, nem a stats
    osszesitojebol - UGYANAZ A SZABALY, mint az oldalon (pl/index.html,
    fetchLivePts). A ket helyen ugyanannak a szamnak kell kijonnie: amit a
    latogato lat, azt kell archivalni is.

    MIERT (2026-08-30, GW2): az FPL a stats.total_points-ot es az explain
    esemenylistat KULON tartja, es az osszesito beragadt - egy jatekosnal a
    sor 1 pontot mutatott, a bontasa viszont 90 percet es golt, osszesen
    8-at. Ugyanez az ellentmondas a HIVATALOS FPL-appban is latszott, tehat
    a forras hibaja. A bontas a hiteles: az konkret esemenyekbol all ossze.

    MIERT FONTOS ITT IS: a lezart fordulot a gyujto SOHA TOBBE nem keri le
    (veglegesek), es az oldal onnantol a MENTETT szamot mutatja. Ami a
    lezaraskor bekerult, az orokre bent marad - az FPL a regi fordulot nem
    adja vissza.

    VISSZAESES: ha az explain ures (a jatekos nem lepett palyara) vagy az
    FPL atalakitja a szerkezetet, egyetlen sort sem talalunk, es a
    stats.total_points marad. Egy API-valtozas igy a REGI viselkedest adja
    vissza, nem nullakat."""
    stats = (v or {}).get("stats") or {}
    ossz, van = 0, False
    for fx in (v or {}).get("explain") or []:
        # a Draft alakja: [[stat-lista, meccs_id], ...] - dupla fordulonal
        # ket elem, ezert osszeadjuk
        for t in (fx[0] if isinstance(fx, (list, tuple)) and fx else None) or []:
            if isinstance(t, dict):
                van = True
                ossz += t.get("points") or 0
    return (ossz, True) if van else (stats.get("total_points") or 0, False)


# A Draft ervenyes felallasai: pontosan 1 kapus, legalabb 3 vedo, legalabb 1
# csatar. Az automatikus csere csak akkor mehet vegbe, ha a csere UTAN is
# ervenyes a felallas - ezert valthatja a kapust csak kapus (ket kapus nem
# ervenyes), es ezert nem all be egy pados, ha a felallas emiatt szetesne.
#
# A KOZEPPALYAS MINIMUM 2, nem 3 - EZ A SOR A KERDESES. Az FPL sajat
# megfogalmazasa (1 kapus, legalabb 3 vedo, legalabb 1 csatar) 5 vedovel es
# 3 csatarral eppen 2 kozeppalyast hagy, vagyis az 5-2-3 ervenyes. A tarolt
# 20 valos felallasban a legkevesebb 3 volt, de az 5-2-3 amugy is ritka,
# tehat ez NEM bizonyitek. Ha kiderul, hogy a Draftban 3 a minimum, EZ AZ
# EGY SZAM valtozik (es a gyujto_draftguardiola.py D7 esete fordul meg).
FORMACIO = {"GKP": (1, 1), "DEF": (3, 5), "MID": (2, 5), "FWD": (1, 3)}


def ervenyes_formacio(posztok):
    if len(posztok) != 11 or None in posztok:
        return False
    for p, (lo, hi) in FORMACIO.items():
        n = sum(1 for x in posztok if x == p)
        if not (lo <= n <= hi):
            return False
    return True


def auto_csere(kezdok, pad, poszt, perc):
    """Az FPL fordulo-vegi automatikus cserei: a palyara sem lepett kezdo
    helyere beall az elso olyan pados, aki jatszott ES a felallitas utana is
    ervenyes. A pad SORRENDJE szamit - azt az FPL-tol kapjuk (picks 12-15),
    es soha nem rendezzuk at.

    MIERT KELL A GUARDIOLA MUTATOHOZ: a valodi eredmenyben a cserek benne
    vannak (a tarolt keret mar a zaras utani allapot). Ha az alternativat
    csere nelkul szamolnank, a mult heti keretet ALULMERNENK, es a mutato
    szisztematikusan a valtoztatas javara torzulna."""
    kezdok, pad = list(kezdok), list(pad)
    for i, e in enumerate(kezdok):
        if perc.get(str(e), 0) > 0:
            continue
        for j, b in enumerate(pad):
            if perc.get(str(b), 0) <= 0:
                continue
            proba = list(kezdok)
            proba[i] = b
            if ervenyes_formacio([poszt.get(str(x)) for x in proba]):
                kezdok[i], pad[j] = b, e
                break
    return kezdok


def keret_vegso(keret, pontok, poszt):
    """Akik a fordulo vegen TENYLEG szamitanak (automatikus cserekkel).

    Kulon fuggveny, mert nem csak az osszeg kell: a "Valtoztatasok" ful
    JATEKOSONKENT vezeti le a mutatot, ahhoz pedig tudni kell, ki szamitott
    bele es ki nem. Egy keretben egy jatekos erteke = a pontja, ha benne van
    ebben a listaban, kulonben 0 - es ezek osszege pontosan a keret_pont."""
    kezdok = [x.get("e") for x in keret if not x.get("b")]
    pad = [x.get("e") for x in keret if x.get("b")]
    perc = {k: v[1] for k, v in pontok.items()}
    return auto_csere(kezdok, pad, poszt, perc)


def keret_pont(keret, pontok, poszt):
    """Egy Draft-keret fordulo-pontja: a kezdok pontja, automatikus
    cserekkel. A `keret` a tarolt alak: [{e, b, pts}, ...] - a `b` a padot
    jelzi, a lista sorrendje az FPL sajat sorrendje."""
    return round(sum((pontok.get(str(e)) or [0, 0])[0]
                     for e in keret_vegso(keret, pontok, poszt)), 2)


def draft_guardiola(hist_rounds, gw, pontok_gw, poszt):
    """A "Guardiola mutato" egy fordulora: {liga_id: {teny, alt, guard}}.

    guard = a MOSTANI keret pontja - a MULT HETI kerete UGYANEBBEN a
    forduloban. Ugyanaz a definicio, mint az NB1-en (collect.py guardiola).

    MINDKET oldal UGYANAZON a fuggvenyen (keret_pont) megy at, tehat a
    valtozatlan keret pontosan 0-t ad - a cserelogika sem csuszhat el a ket
    oldal kozott."""
    elozo = hist_rounds.get(str(gw - 1)) or {}
    mostani = hist_rounds.get(str(gw)) or {}
    if not elozo or not mostani or not pontok_gw:
        return None
    ki = {}
    for lid, keret in mostani.items():
        regi = elozo.get(lid)
        if not regi or not keret:
            continue
        teny = keret_pont(keret, pontok_gw, poszt)
        alt = keret_pont(regi, pontok_gw, poszt)
        ki[str(lid)] = {"teny": teny, "alt": alt, "guard": round(teny - alt, 2)}
    return ki or None


def draft_szerep(e, keret):
    """Amit az EMBER dontott a jatekosrol: kezdo vagy pad.

    SZANDEKOSAN nem keveredik bele, hogy az automatikus csere utan
    tenylegesen szamitott-e: az mar a GEP muve (lasd draft_keretvaltozas)."""
    return "pad" if any(x.get("e") == e and x.get("b") for x in keret) else "kezdo"


def draft_keretvaltozas_pont_nelkul(elozo, mostani):
    """A FOLYO fordulo valtoztatasai a PL-en, pontertek nelkul.

    Csak azt tartalmazza, amit az EMBER dontott (elengedve / megszerezve /
    kezdo <-> pad). A zarasi automatikus csere ilyenkor meg nem tortent meg,
    tehat nincs is mit kulon sorba tenni."""
    ki_ossz = {}
    for lid, keret in mostani.items():
        regi = elozo.get(lid)
        if not regi or not keret:
            continue
        uj_id = [x.get("e") for x in keret]
        regi_id = [x.get("e") for x in regi]
        ki = sorted(({"e": e, "sz": draft_szerep(e, regi)}
                     for e in regi_id if e not in uj_id), key=lambda x: x["e"])
        be = sorted(({"e": e, "sz": draft_szerep(e, keret)}
                     for e in uj_id if e not in regi_id), key=lambda x: x["e"])
        szer = sorted(({"e": e, "szE": draft_szerep(e, regi),
                        "szU": draft_szerep(e, keret)}
                       for e in uj_id
                       if e in regi_id
                       and draft_szerep(e, regi) != draft_szerep(e, keret)),
                      key=lambda x: x["e"])
        ki_ossz[str(lid)] = {"pontok": False, "guard": None,
                             "ki": ki, "be": be, "szerep": szer}
    return ki_ossz or None


def draft_keretvaltozas(hist_rounds, gw, pontok_gw, poszt):
    """Mit valtoztatott a csapat a fordulora, es mit ert - a "Valtoztatasok"
    ful adata. Ugyanaz a szerep, mint az NB1-en (collect.py keretvaltozas):
    LEVEZETI a Guardiola mutatot, es a tetelek osszege PONTOSAN a `guard`.

    KETTEVALASZTVA: AMIT AZ EMBER CSINALT, ES AMIT A GEP JAVITOTT RAJTA.
    A Draftban a fordulo vegen az FPL automatikus cseret hajt vegre - az nem
    a szakvezeto erdeme vagy hibaja. Ha egyben mutatnank, ugy tunne, hogy
    valaki jol variált, holott a gep tette helyre a keretet (vagy forditva).
    Ezert:
      ember: minden jatekos a MEGNEVEZETT szerepevel szamit - a kezdo a
             pontjaval, a pados nullaval, akkor is, ha vegul beallt;
      gep:   a keret tenyleges pontja (auto_csere-vel) MINUSZ a fenti osszeg.
             Ez pontosan az automatikus csere hozadeka arra a keretre.
    A ketto osszege a keret pontja, tehat a levezetes maradek nelkul kijon.

    Magyarszabaly itt nincs, tehat kulon sor sem kell hozza."""
    elozo = hist_rounds.get(str(gw - 1)) or {}
    mostani = hist_rounds.get(str(gw)) or {}
    if not elozo or not mostani:
        return None
    if not pontok_gw:
        # NINCS MEG A FORDULO PONT-ADATA - a valtoztatas viszont mar ismert:
        # a keret a hatarido utan rogzitett. Ilyenkor pont nelkul adjuk ki
        # (lasd collect.py keretvaltozas_pont_nelkul). A mutato ettol nem
        # keszul el korabban.
        return draft_keretvaltozas_pont_nelkul(elozo, mostani)
    pont = lambda e: (pontok_gw.get(str(e)) or [0, 0])[0]

    def ember(keret):
        """{element: ertek} a MEGNEVEZETT szerepek szerint (pad = 0)."""
        return {x.get("e"): (0 if x.get("b") else pont(x.get("e"))) for x in keret}

    ki_ossz = {}
    for lid, keret in mostani.items():
        regi = elozo.get(lid)
        if not regi or not keret:
            continue
        eU, eE = ember(keret), ember(regi)
        teny = keret_pont(keret, pontok_gw, poszt)
        alt = keret_pont(regi, pontok_gw, poszt)
        gepU = round(teny - sum(eU.values()), 2)
        gepE = round(alt - sum(eE.values()), 2)
        ki = [{"e": e, "sz": draft_szerep(e, regi), "pont": pont(e), "ert": eE[e]}
              for e in eE if e not in eU]
        be = [{"e": e, "sz": draft_szerep(e, keret), "pont": pont(e), "ert": eU[e]}
              for e in eU if e not in eE]
        szer = []
        for e in eU:
            if e not in eE:
                continue
            szE, szU = draft_szerep(e, regi), draft_szerep(e, keret)
            if szE == szU:
                continue
            szer.append({"e": e, "pont": pont(e), "szE": szE, "szU": szU,
                         "ertE": eE[e], "ertU": eU[e]})
        guard = round(teny - alt, 2)
        osszeg = round(sum(x["ert"] for x in be) - sum(x["ert"] for x in ki)
                       + sum(x["ertU"] - x["ertE"] for x in szer)
                       + (gepU - gepE), 2)
        ki.sort(key=lambda x: (-x["ert"], x["e"]))
        be.sort(key=lambda x: (-x["ert"], x["e"]))
        szer.sort(key=lambda x: (-(x["ertU"] - x["ertE"]), x["e"]))
        ki_ossz[str(lid)] = {"guard": guard, "ki": ki, "be": be, "szerep": szer,
                             "gepE": gepE, "gepU": gepU,
                             "stimmel": abs(osszeg - guard) < 0.005}
        if not ki_ossz[str(lid)]["stimmel"]:
            print("  ! draft_keretvaltozas: %d. fordulo, %s - a tetelek osszege"
                  " %s, a mutato %s" % (gw, lid, osszeg, guard), file=sys.stderr)
    return ki_ossz or None


def main():
    print("FPL Draft gyujtes (liga: %s)" % LEAGUE_ID)

    # ---- 1. Liga-adatok (resztvevok, menetrend, eredmenyek) ----
    st, data = fetch("league/%s/details" % LEAGUE_ID)
    if st != 200 or not data:
        print("  ! details: HTTP %s - a fajlok valtozatlanok." % st, file=sys.stderr)
        print("   (403/401: a vegpont zarva; 404: rossz liga-azonosito,")
        print("    allitsd a DRAFT_LEAGUE_ID valtozot.)")
        return 0
    payload, lejatszott = atalakit(data)
    liga_idk = {e["id"] for e in payload["entries"]}
    # entry_id -> liga-id lekepezes, CSAK memoriaban
    entry2liga = {e.get("entry_id"): e.get("id")
                  for e in data.get("league_entries") or []}
    print("  liga: %s | resztvevok: %d | lejatszott meccs: %d"
          % (payload["league"]["name"], len(liga_idk), lejatszott))
    kiir_ha_valtozott("draft.json", payload)

    # ---- 2. Jatekos-torzsadat ----
    st, bs = fetch("bootstrap-static")
    players = {}
    if st == 200 and bs:
        klub = {t.get("id"): (t.get("short_name") or t.get("name") or "")
                for t in bs.get("teams") or []}
        poszt = {t.get("id"): (t.get("singular_name_short") or "")
                 for t in bs.get("element_types") or []}
        for el in bs.get("elements") or []:
            players[str(el.get("id"))] = {
                "n": el.get("web_name") or "",
                "t": klub.get(el.get("team"), ""),
                "p": poszt.get(el.get("element_type"), ""),
                # a szezonpont a fooldali jatekoslistahoz kell (csokkeno
                # pontsorrend + kereses). A bootstrap-static amugy is
                # lejon minden korben, tehat ez NEM plusz keres.
                "pts": el.get("total_points") or 0,
            }
        # a "teams" (csapat-id -> rovidnev) az elo fixtures-valasz
        # csapat-azonositoinak feloldasahoz kell a bongeszoben
        # (jatszott mar? jelzes: a meccse elkezdodott-e)
        kiir_ha_valtozott("draft_players.json",
                          {"updated": None, "players": players,
                           "teams": {str(k): v for k, v in klub.items()}})
        print("  jatekos-torzs: %d jatekos, %d csapat" % (len(players), len(klub)))
    else:
        print("  ! bootstrap-static: HTTP %s - a torzsadat valtozatlan" % st,
              file=sys.stderr)

    # ---- 3. Jelenlegi keretek (tulajdonlas) ----
    st, es = fetch("league/%s/element-status" % LEAGUE_ID)
    if st == 200 and es:
        squads = {}
        ismeretlen = set()
        for x in es.get("element_status") or []:
            owner = x.get("owner")
            if owner is None:
                continue
            # az owner azonosito-tere futaskor derul ki
            if owner in liga_idk:
                lid = owner
            elif owner in entry2liga:
                lid = entry2liga[owner]
            else:
                ismeretlen.add(owner)
                continue
            squads.setdefault(str(lid), []).append(x.get("element"))
        for lid in squads:
            squads[lid].sort()
        if ismeretlen:
            print("  ! element-status: %d ismeretlen tulajdonos-azonosito: %s"
                  % (len(ismeretlen), sorted(ismeretlen)[:5]), file=sys.stderr)
        kiir_ha_valtozott("draft_squads.json",
                          {"updated": None, "squads": squads})
        print("  jelenlegi keretek: %d csapat, %d birtokolt jatekos"
              % (len(squads), sum(len(v) for v in squads.values())))
    else:
        print("  ! element-status: HTTP %s" % st, file=sys.stderr)

    # ---- 4. Fordulonkenti keretek + pontok (a GW1 indulasatol) ----
    st, game = fetch("game")
    aktualis = (game or {}).get("current_event") if st == 200 else None
    if not aktualis:
        print("  . a szezon meg nem kezdodott el (current_event=%s) - "
              "fordulonkenti keret meg nincs" % aktualis)
        print("Kesz.")
        return 0

    try:
        with open("draft_history.json", encoding="utf-8") as f:
            hist = json.load(f)
    except Exception:
        hist = {"updated": None, "rounds": {}}
    hist.setdefault("rounds", {})
    try:
        with open("zarasok.json", encoding="utf-8") as f:
            zarasok = json.load(f)
    except Exception:
        zarasok = {"updated": None, "rounds": {}}
    zarasok.setdefault("rounds", {})
    zarasok_elotte = json.dumps(zarasok["rounds"], ensure_ascii=False, sort_keys=True)

    # Celok: az aktualis fordulo (frissul, amig tart), minden hianyzo, ES
    # minden olyan fordulo, amirol meg NEM tudjuk biztosan, hogy veglegesen
    # lezarult.
    #
    # MIERT: az FPL a fordulo vegen AUTOMATIKUS CSEREKET hajt vegre - a nem
    # jatszo kezdo helyere beallitja az elso beferot a padrol -, es ilyenkor
    # ATIRJA a pick "position" mezojet. Merve (2026-08-25, naplo/fpl-cserek.txt):
    # ez a "lockdown"-kor tortenik, egyszerre a tobbivel, 08:03 es 08:23 UTC
    # kozott; a jelzese a game vegpont "current_event_finished" mezoje.
    # A gyujto 3 orankent fut, tehat ha a current_event azelott lepne tovabb,
    # hogy a zaras utan meg egyszer lekertuk volna a fordulot, a keret
    # VEGLEGESEN a csere elotti allapotban fagyna be (rossz "b" jelzo, rossz
    # "Kezdok" osszeg). 2026-08-25-en ez csak azon mult, hogy a futas hat
    # perccel a zaras utan esett.
    #
    # A mar lezartnak ismert fordulokat a hist["veglegesek"] tartja szamon, hogy egy
    # veglegesitett fordulot ne kerjunk le ujra minden korben.
    # AZ AKTUALIS FORDULO MINDIG CEL, akkor is, ha mar lezarult. Ez a regi
    # viselkedes, es nem diszites: amig a current_event nem lep tovabb (egy
    # hetig), addig az utolagos FPL-korrekciok igy jonnek at. Egy korabbi
    # valtozat ezt kivette (a lezart fordulot veglegesnek jelolve), amivel a
    # zaras utani egesz hetet vakon hagyta volna.
    # A `veglegesek` lista csak azt donti el, hogy a REGI fordulokat kell-e ujra
    # kerni - lasd lentebb, miert.
    veglegesek = {int(x) for x in (hist.get("veglegesek") or [])}
    celok = {int(aktualis)}
    for gw in range(1, int(aktualis) + 1):
        megvan = hist["rounds"].get(str(gw)) or {}
        if len(megvan) < len(liga_idk) or gw not in veglegesek:
            celok.add(gw)

    most_teljes = {}          # gw -> ebben a futasban minden csapat kerete megjott-e
    pontok_tar = {}           # gw -> {element: [pont, perc]} a TELJES mezonyre
    for gw in sorted(celok):
        st, live = fetch("event/%d/live" % gw)
        pont, perc, eltero = {}, {}, 0
        if st == 200 and live:
            el = live.get("elements")
            elemek = (list(el.items()) if isinstance(el, dict)
                      else [(str((v or {}).get("id")), v) for v in el] if isinstance(el, list)
                      else [])
            for k, v in elemek:
                p, van = jatekos_pont(v)
                if van and p != (((v or {}).get("stats") or {}).get("total_points") or 0):
                    eltero += 1
                pont[str(k)] = p
                # A PERC az automatikus cserekhez kell (0 perc = nem lepett
                # palyara), a Guardiola mutato alternativajaban.
                perc[str(k)] = ((v or {}).get("stats") or {}).get("minutes") or 0
        # UGYANAZ A SZABALY, MINT AZ OLDALON: az elteres nem nema. Ha
        # rendszeres, a naplobol latszik - es akkor nezzuk meg ujra, melyik
        # forras romlott el.
        if eltero:
            print("  ! %d. fordulo: %d jatekosnal az FPL osszesitoje ELTER a"
                  " teteles bontas osszegetol - a bontast tartjuk meg"
                  % (gw, eltero), file=sys.stderr)
        # D1: ha az elo pontok nem jottek meg, a fordulot KIHAGYJUK. Kulonben
        # minden jatekos 0 ponttal irodna be, a fordulo "teljesnek" szamitana,
        # es soha nem kernenk le ujra - a nullak veglegesen bennragadnanak.
        if not pont:
            print("  ! %d. fordulo: az elo pontok nem jottek meg (HTTP %s),"
                  " a fordulot kihagyjuk" % (gw, st), file=sys.stderr)
            continue
        uj = {}
        for eid, lid in entry2liga.items():
            if lid is None or eid is None:
                continue
            st, ev = fetch("entry/%d/event/%d" % (eid, gw))
            if st != 200 or not isinstance(ev, dict):
                print("  ! %d. fordulo / %s: HTTP %s" % (gw, lid, st), file=sys.stderr)
                continue
            picks = ev.get("picks") or []
            # D2: ures keretet nem tarolunk el - "teljes" rekordkent szamitana,
            # es orokre ures maradna ehhez a fordulohoz
            if not picks:
                print("  ! %d. fordulo / %s: ures keret, kihagyva" % (gw, lid),
                      file=sys.stderr)
                continue
            if "element" not in picks[0]:
                print("  ! %d. fordulo: ismeretlen picks-szerkezet, kulcsok: %s"
                      % (gw, sorted(picks[0].keys())), file=sys.stderr)
                continue
            uj[str(lid)] = [{"e": p.get("element"),
                             "b": (p.get("position") or 0) > 11,
                             "pts": pont.get(str(p.get("element")), 0)}
                            for p in picks]
        # ZARASI KULONBSEG: pontosan egyszer, a veglegesito futasban
        # szamoljuk ki - amikor a fordulo MOST kerulne a veglegesek koze.
        # Ilyenkor a hist meg a zaras ELOTTI pillanatkepet orzi (a legutobbi,
        # legfeljebb 3 oraval korabbi futasbol), az "uj" pedig a zaras UTANI
        # allapot: a ketto kulonbsege a lockdown muve (bonusz-korrekcio,
        # automatikus cserek). Regi pillanatkep nelkul (backfill) nincs mibol
        # szamolni - olyankor kimarad.
        veglegesitendo = (gw not in veglegesek and len(uj) == len(liga_idk)
                          and (gw < int(aktualis)
                               or (gw == int(aktualis)
                                   and bool(game.get("current_event_finished")))))
        if veglegesitendo and str(gw) not in zarasok["rounds"]:
            valtozas = zarasi_kulonbseg(hist["rounds"].get(str(gw)) or {}, uj)
            if valtozas is not None:
                zarasok["rounds"][str(gw)] = valtozas
                print("  zarasi kulonbseg: GW%d, %d csapat erintett"
                      % (gw, len(valtozas)))

        # EBBEN A FUTASBAN jott-e be minden csapat kerete? A tarolt adatbol
        # ez nem latszik: a sor alatti osszefesules miatt egy regebbi, teljes
        # pillanatkep akkor is teljesnek mutatna a fordulot, ha most epp
        # elhasalt egy lekeres - es akkor a csere elotti allapotot
        # rogzitenenk veglegesnek.
        # A TELJES mezony pontja+perce a fordulora. Kell a Guardiola
        # mutatohoz: a mult heti keretben lehet olyan jatekos, aki mar
        # SENKINEL sincs - GW1->GW2-ben 11 ilyen volt -, es akkor a pontja
        # sehol nem lenne meg. Csak azt tesszuk el, aki jatszott vagy pontot
        # szerzett; a hianyzo [0, 0]-nak szamit.
        pontok_tar[str(gw)] = {k: [pont[k], perc.get(k, 0)]
                               for k in pont if pont[k] or perc.get(k)}
        most_teljes[gw] = (len(uj) == len(liga_idk))
        if uj:
            hist["rounds"][str(gw)] = {**(hist["rounds"].get(str(gw)) or {}), **uj}
            print("  fordulonkenti keret: GW%d, %d/%d csapat"
                  % (gw, len(uj), len(liga_idk)))

    # Egy fordulo VEGLEGES, ha az FPL mar tullepett rajta, vagy ha o az
    # aktualis, de a game vegpont szerint befejezodott (lockdown megtortent).
    # Csak akkor jelolheto veglegesnek, ha ebben a futasban minden csapat keretet
    # sikerult behozni - kulonben egy elhasalt lekeres utan a csere elotti
    # allapotot rogzitenenk veglegesnek.
    veg = bool(game.get("current_event_finished")) if isinstance(game, dict) else False
    for gw in sorted(celok):
        if not most_teljes.get(gw):
            continue
        if gw < int(aktualis) or (gw == int(aktualis) and veg):
            veglegesek.add(gw)
    if json.dumps(zarasok["rounds"], ensure_ascii=False, sort_keys=True) != zarasok_elotte:
        zarasok["updated"] = stamp()
        kiir_ha_valtozott("zarasok.json", zarasok)

    kiir_ha_valtozott("draft_history.json",
                      {"updated": None, "rounds": hist["rounds"],
                       "veglegesek": sorted(veglegesek)})

    # ---- A TELJES mezony fordulonkenti pontja+perce (draft_pontok.json).
    # Osszefesuljuk a tarolttal: ebben a futasban csak a `celok` fordulait
    # kertuk le, a tobbi adatat nem szabad eldobni.
    try:
        with open("draft_pontok.json", encoding="utf-8") as f:
            pontok = json.load(f).get("rounds") or {}
    except Exception:
        pontok = {}
    pontok.update(pontok_tar)
    kiir_ha_valtozott("draft_pontok.json", {"updated": None, "rounds": pontok})

    # ---- Guardiola mutato. Ugyanaz a definicio, mint az NB1-en; a
    # szamitas determinisztikus, ezert minden futasban ujra megy.
    # A nev SZANDEKOSAN nem `poszt`: az ebben a fuggvenyben mar foglalt
    # (poszt-tipus -> rovidnev a bootstrap-bol). Ugyanaz a nevutkozes-csapda,
    # mint a .pos/.ppos-nal.
    jatekos_poszt = {k: (v or {}).get("p") for k, v in (players or {}).items()}
    gua = {}
    # HA NINCS POSZT-ADAT, NEM SZAMOLUNK. A bootstrap-static elhasalasakor a
    # `players` ures, es akkor az auto_csere formacio-ellenorzese MINDIG
    # hamis lenne - egyetlen csere sem menne vegbe, es a mutato csendben
    # rossz erteket adna. Ilyenkor a korabbi fajl marad ervenyben.
    if jatekos_poszt:
        for gw_ in sorted(int(x) for x in hist["rounds"]):
            g_ = draft_guardiola(hist["rounds"], gw_, pontok.get(str(gw_)), jatekos_poszt)
            if g_:
                gua[str(gw_)] = g_
    else:
        print("  ! nincs jatekos-poszt adat, a Guardiola mutato valtozatlan",
              file=sys.stderr)
    try:
        with open("draft_guardiola.json", encoding="utf-8") as f:
            gua_regi = json.load(f).get("rounds")
    except Exception:
        gua_regi = None
    if gua and json.dumps(gua, ensure_ascii=False, sort_keys=True) != \
       json.dumps(gua_regi, ensure_ascii=False, sort_keys=True):
        kiir_ha_valtozott("draft_guardiola.json", {"updated": stamp(), "rounds": gua})
        print("  draft_guardiola.json frissitve (%d fordulo)" % len(gua))

    # ---- Keretvaltozasok ("Valtoztatasok" ful). Ugyanabbol a korbol, mint a
    # mutato - a ful eppen azt vezeti le, tehat egyutt kell mozdulniuk.
    # A jatekos NEVET nem taroljuk: a lap a draft_players.json-bol amugy is
    # feloldja (a mezony teljes, a tavozo jatekos is benne marad) - az NB1-en
    # ez azert mas, mert ott a jatekostorzs csak a MOSTANI mezonyt adja.
    kvalt = {}
    if jatekos_poszt:
        for gw_ in sorted(int(x) for x in hist["rounds"]):
            k_ = draft_keretvaltozas(hist["rounds"], gw_, pontok.get(str(gw_)),
                                     jatekos_poszt)
            if k_:
                kvalt[str(gw_)] = k_
    try:
        with open("draft_keretvaltozasok.json", encoding="utf-8") as f:
            kvalt_regi = json.load(f).get("rounds")
    except Exception:
        kvalt_regi = None
    if kvalt and json.dumps(kvalt, ensure_ascii=False, sort_keys=True) != \
       json.dumps(kvalt_regi, ensure_ascii=False, sort_keys=True):
        kiir_ha_valtozott("draft_keretvaltozasok.json",
                          {"updated": stamp(), "rounds": kvalt})
        print("  draft_keretvaltozasok.json frissitve (%d fordulo)" % len(kvalt))

    print("Kesz.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
