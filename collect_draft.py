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

    # celok: az aktualis fordulo (frissul, amig tart) + minden hianyzo
    celok = {int(aktualis)}
    for gw in range(1, int(aktualis) + 1):
        megvan = hist["rounds"].get(str(gw)) or {}
        if len(megvan) < len(liga_idk):
            celok.add(gw)

    for gw in sorted(celok):
        st, live = fetch("event/%d/live" % gw)
        pont = {}
        if st == 200 and live:
            el = live.get("elements")
            if isinstance(el, dict):
                for k, v in el.items():
                    pont[str(k)] = ((v or {}).get("stats") or {}).get("total_points") or 0
            elif isinstance(el, list):
                for v in el:
                    pont[str((v or {}).get("id"))] = ((v or {}).get("stats") or {}).get("total_points") or 0
        uj = {}
        for eid, lid in entry2liga.items():
            if lid is None or eid is None:
                continue
            st, ev = fetch("entry/%d/event/%d" % (eid, gw))
            if st != 200 or not isinstance(ev, dict):
                print("  ! %d. fordulo / %s: HTTP %s" % (gw, lid, st), file=sys.stderr)
                continue
            picks = ev.get("picks") or []
            if picks and "element" not in picks[0]:
                print("  ! %d. fordulo: ismeretlen picks-szerkezet, kulcsok: %s"
                      % (gw, sorted(picks[0].keys())), file=sys.stderr)
                continue
            uj[str(lid)] = [{"e": p.get("element"),
                             "b": (p.get("position") or 0) > 11,
                             "pts": pont.get(str(p.get("element")), 0)}
                            for p in picks]
        if uj:
            hist["rounds"][str(gw)] = {**(hist["rounds"].get(str(gw)) or {}), **uj}
            print("  fordulonkenti keret: GW%d, %d/%d csapat"
                  % (gw, len(uj), len(liga_idk)))

    kiir_ha_valtozott("draft_history.json",
                      {"updated": None, "rounds": hist["rounds"]})
    print("Kesz.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
