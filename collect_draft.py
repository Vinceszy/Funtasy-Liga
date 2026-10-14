#!/usr/bin/env python3
"""FunTasy Liga - collecting the data of the FPL Draft league.

Looks after four files (all compact JSON, in the style of the repository's
other data files):

  draft.json         - entries, schedule, results, standings
  draft_players.json - player master data: {id: {n: name, t: club, p: position}}
  draft_squads.json  - the CURRENT squads: {league_id: [element_id, ...]}
  draft_history.json - per-round squads with points (from the start of GW1):
                       {rounds: {gw: {league_id: [{e, b, pts}, ...]}}}
                       e=player id, b=bench, pts=weekly points

ENDPOINTS (measured from the GitHub runner):
  - league/{id}/details        200 - entries, schedule, results
  - bootstrap-static           200 - 599 players, clubs, positions
  - league/{id}/element-status 200 - who owns a given player now
  - entry/{eid}/event/{gw}     404 UNTIL THE ROUND STARTS, picks after that
  - event/{gw}/live            200 - weekly points per player
  - game                       200 - current_event (the current round)

IMPORTANT - privacy:
The details answer also holds the entrants' REAL NAMES. The repository is
public, so a raw answer is never saved: every output record is built field
by field, and before saving the private-field check makes sure that no
forbidden field (real name, entry_id) has leaked. The footballers' names are
public data, those may go.

IMPORTANT - two different ids:
Every entrant has an "entry_id" (FPL team id) and an "id" (id within the
league). matches/standings use the "id", the squad endpoints the entry_id.
ONLY the "id" appears in the repository; the entry_id is used during the
run, in memory. The id space of the element-status "owner" field was
uncertain, so at run time we detect which space it is in, and map it to the
league id.

The league id can be overridden by the DRAFT_LEAGUE_ID environment variable.
"""
import json, os, sys, time, urllib.error, urllib.request

# The tests load this module by its file PATH, so sys.path holds the tests
# directory, not the repository root. We add our own directory, otherwise the
# shared module would only be found in a live run.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collector_common import stamp, write_compact, read_stored

LEAGUE_ID = os.environ.get("DRAFT_LEAGUE_ID", "48093")
B = "https://draft.premierleague.com/api/"
HDRS = {
    "Accept": "application/json",
    "Accept-Language": "en-GB,en;q=0.9",
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"),
}


def fetch(path, retries=3):
    """(status, data) - retries on a network error, not on a 4xx."""
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
                print("  ! network error (%s): %s" % (path, e), file=sys.stderr)
                return None, None
            time.sleep(3)
    return None, None


def transform_details(data):
    """The structure of draft.json from the details answer - without real names."""
    league = data.get("league") or {}
    entries = []
    for e in data.get("league_entries") or []:
        entries.append({"id": e.get("id"),
                        "name": e.get("entry_name") or "",
                        "short": e.get("short_name") or ""})
    entries.sort(key=lambda x: (x["name"] or "").lower())

    schedule, played = {}, 0
    for m in data.get("matches") or []:
        rnd = str(m.get("event"))
        finished = bool(m.get("finished"))
        hp = m.get("league_entry_1_points") if finished else None
        vp = m.get("league_entry_2_points") if finished else None
        if finished:
            played += 1
        schedule.setdefault(rnd, []).append(
            [m.get("league_entry_1"), m.get("league_entry_2"), hp, vp])

    standings = []
    for s in data.get("standings") or []:
        standings.append({"id": s.get("league_entry"), "rank": s.get("rank"),
                          "played": s.get("matches_played"), "won": s.get("matches_won"),
                          "drawn": s.get("matches_drawn"), "lost": s.get("matches_lost"),
                          "for": s.get("points_for"), "against": s.get("points_against"),
                          "total": s.get("total")})
    return {
        "updated": None,
        "league": {"id": league.get("id"), "name": league.get("name") or "",
                   "start_event": league.get("start_event"),
                   "stop_event": league.get("stop_event")},
        "entries": entries, "schedule": schedule, "standings": standings,
    }, played


def check_private_fields(payload):
    """Safety net: a forbidden field in the output -> stop, nothing is saved."""
    text = json.dumps(payload, ensure_ascii=False)
    for forbidden in ("player_first_name", "player_last_name", "entry_id"):
        if forbidden in text:
            raise SystemExit("ERROR: '%s' in the output - saving aborted." % forbidden)


def write_if_changed(path, content, ignored_key="updated"):
    """Compact write, only if the content (without updated) changed."""
    try:
        with open(path, encoding="utf-8") as f:
            old = json.load(f)
    except Exception:
        old = None

    def core(x):
        if not isinstance(x, dict):
            return x
        return {k: v for k, v in x.items() if k != ignored_key}

    if old is not None and json.dumps(core(old), sort_keys=True, ensure_ascii=False) \
                        == json.dumps(core(content), sort_keys=True, ensure_ascii=False):
        return False
    content["updated"] = stamp()
    check_private_fields(content)
    write_compact(path, content)
    print("  + %s written (%d bytes)" % (path, os.path.getsize(path)))
    return True


def closing_diff(old, new):
    """The difference between the squads before (stored) and after (fresh)
    the close.
    Per team: "pont" = per-player points change (the bonus correction),
    "ki"/"be" = the automatic substitutions (from the change of the bench
    flag - at the close the FPL rewrites the position field, measured). None
    if there is nothing to compute from (no stored snapshot); an empty dict
    if nothing changed - that is a result too: it means the close brought no
    change."""
    if not old:
        return None
    out = {}
    for lid, fresh in new.items():
        before = old.get(lid)
        if not before:
            continue
        by_element = {x["e"]: x for x in before}
        points = [{"e": x["e"], "elott": by_element[x["e"]]["pts"], "utan": x["pts"]}
                  for x in fresh
                  if x["e"] in by_element and by_element[x["e"]]["pts"] != x["pts"]]
        # a substitution needs the POINTS too: the incoming player's points
        # tell what the substitution brought (and the outgoing one's, why it
        # happened)
        sub_out = [{"e": x["e"], "pts": x["pts"]} for x in fresh
                   if x["b"] and x["e"] in by_element and not by_element[x["e"]]["b"]]
        sub_in = [{"e": x["e"], "pts": x["pts"]} for x in fresh
                  if not x["b"] and x["e"] in by_element and by_element[x["e"]]["b"]]
        if points or sub_out or sub_in:
            out[lid] = {}
            if points:
                out[lid]["pont"] = points
            if sub_out or sub_in:
                out[lid]["ki"], out[lid]["be"] = sub_out, sub_in
    return out


def player_points(v):
    """One player's round points from the live answer: (points, from_breakdown).

    THE POINTS ARE SUMMED FROM THE ITEMISED BREAKDOWN (explain), not from the
    stats total - THE SAME RULE as on the page (pl/index.html,
    fetchLivePts). Both places must come to the same number: what the
    visitor sees is what has to be archived.

    WHY: the FPL keeps stats.total_points and the explain event list
    SEPARATELY, and the total can get stuck - for one player the row showed
    1 point while its breakdown had 90 minutes and a goal, 8 in all. The
    same contradiction showed in the OFFICIAL FPL app as well, so it is a
    fault of the source. The breakdown is the authoritative one: it adds up
    from concrete events.

    WHY IT MATTERS HERE TOO: a closed round is NEVER fetched again by the
    collector (veglegesek), and from then on the page shows the SAVED
    number. Whatever went in at closing stays in forever - the FPL does not
    give back an old round.

    FALLBACK: if explain is empty (the player did not come on) or the FPL
    changes the structure, not a single row is found, and
    stats.total_points remains. An API change thus gives back the OLD
    behaviour, not zeros."""
    stats = (v or {}).get("stats") or {}
    total, found = 0, False
    for fx in (v or {}).get("explain") or []:
        # the Draft shape: [[stat list, match_id], ...] - in a double round
        # there are two elements, so they are added up
        for t in (fx[0] if isinstance(fx, (list, tuple)) and fx else None) or []:
            if isinstance(t, dict):
                found = True
                total += t.get("points") or 0
    return (total, True) if found else (stats.get("total_points") or 0, False)


# The valid Draft formations: exactly 1 goalkeeper, at least 3 defenders, at
# least 1 forward. An automatic substitution can happen only if the
# formation is still valid AFTER it - so only a goalkeeper can replace the
# goalkeeper (two goalkeepers is not valid), and a bench player does not
# come on if the formation would fall apart because of it.
#
# THE MIDFIELD MINIMUM IS 2, not 3 - THIS IS THE QUESTIONABLE LINE. The FPL's
# own wording (1 goalkeeper, at least 3 defenders, at least 1 forward) leaves
# exactly 2 midfielders with 5 defenders and 3 forwards, i.e. 5-2-3 is
# valid. In the 20 real stored formations the lowest was 3, but 5-2-3 is
# rare anyway, so this is NOT proof. If it turns out that the Draft minimum
# is 3, THIS ONE NUMBER changes (and case D7 of gyujto_draftguardiola.py
# flips).
FORMATION = {"GKP": (1, 1), "DEF": (3, 5), "MID": (2, 5), "FWD": (1, 3)}


def valid_formation(positions):
    if len(positions) != 11 or None in positions:
        return False
    for p, (lo, hi) in FORMATION.items():
        n = sum(1 for x in positions if x == p)
        if not (lo <= n <= hi):
            return False
    return True


def auto_substitute(starters, bench, position, minutes):
    """The FPL's end-of-round automatic substitutions: in place of a starter
    who did not come on, the first bench player who played AND keeps the
    formation valid comes on. The ORDER of the bench matters - it comes from
    the FPL (picks 12-15), and it is never reordered.

    WHY THE GUARDIOLA MEASURE NEEDS IT: the real result has the
    substitutions in it (the stored squad is already the post-close state).
    If the alternative were computed without substitutions, last week's
    squad would be UNDERRATED, and the measure would be systematically
    skewed in favour of the change."""
    starters, bench = list(starters), list(bench)
    for i, e in enumerate(starters):
        if minutes.get(str(e), 0) > 0:
            continue
        for j, b in enumerate(bench):
            if minutes.get(str(b), 0) <= 0:
                continue
            trial = list(starters)
            trial[i] = b
            if valid_formation([position.get(str(x)) for x in trial]):
                starters[i], bench[j] = b, e
                break
    return starters


def final_lineup(squad, points, position):
    """Who REALLY counts at the end of the round (with automatic
    substitutions).

    A separate function, because not only the sum is needed: the
    "Valtoztatasok" (changes) tab derives the measure PLAYER BY PLAYER, and
    for that it has to be known who counted in it and who did not. Within a
    squad a player's value = their points if they are in this list, else 0
    - and the sum of these is exactly squad_points."""
    starters = [x.get("e") for x in squad if not x.get("b")]
    bench = [x.get("e") for x in squad if x.get("b")]
    minutes = {k: v[1] for k, v in points.items()}
    return auto_substitute(starters, bench, position, minutes)


def squad_points(squad, points, position):
    """The round points of a Draft squad: the starters' points, with
    automatic substitutions. `squad` is the stored shape: [{e, b, pts}, ...]
    - `b` marks the bench, the list order is the FPL's own order."""
    return round(sum((points.get(str(e)) or [0, 0])[0]
                     for e in final_lineup(squad, points, position)), 2)


def draft_guardiola(hist_rounds, gw, points_gw, position):
    """The "Guardiola measure" for one round: {league_id: {teny, alt, guard}}.

    guard = the points of the CURRENT squad - LAST WEEK's squad IN THE SAME
    round. The same definition as for the NB1 (collect.py guardiola).

    BOTH sides go through THE SAME function (squad_points), so an unchanged
    squad gives exactly 0 - the substitution logic cannot drift apart
    between the two sides either."""
    previous = hist_rounds.get(str(gw - 1)) or {}
    current = hist_rounds.get(str(gw)) or {}
    if not previous or not current or not points_gw:
        return None
    out = {}
    for lid, squad in current.items():
        old = previous.get(lid)
        if not old or not squad:
            continue
        actual = squad_points(squad, points_gw, position)
        alt = squad_points(old, points_gw, position)
        out[str(lid)] = {"teny": actual, "alt": alt, "guard": round(actual - alt, 2)}
    return out or None


def draft_role(e, squad):
    """What the PERSON decided about the player: starter ('kezdo') or bench
    ('pad').

    ON PURPOSE it does not mix in whether the player actually counted after
    the automatic substitution: that is the MACHINE's work (see
    draft_squad_changes)."""
    return "pad" if any(x.get("e") == e and x.get("b") for x in squad) else "kezdo"


def draft_squad_changes_without_points(previous, current):
    """The changes of the RUNNING round on the PL, without point values.

    It holds only what the PERSON decided (released / acquired / starter <->
    bench). The automatic substitution at the close has not happened yet,
    so there is nothing to put in a separate row."""
    out_all = {}
    for lid, squad in current.items():
        old = previous.get(lid)
        if not old or not squad:
            continue
        new_ids = [x.get("e") for x in squad]
        old_ids = [x.get("e") for x in old]
        out = sorted(({"e": e, "sz": draft_role(e, old)}
                      for e in old_ids if e not in new_ids), key=lambda x: x["e"])
        into = sorted(({"e": e, "sz": draft_role(e, squad)}
                       for e in new_ids if e not in old_ids), key=lambda x: x["e"])
        role_changes = sorted(({"e": e, "szE": draft_role(e, old),
                                "szU": draft_role(e, squad)}
                               for e in new_ids
                               if e in old_ids
                               and draft_role(e, old) != draft_role(e, squad)),
                              key=lambda x: x["e"])
        out_all[str(lid)] = {"pontok": False, "guard": None,
                             "ki": out, "be": into, "szerep": role_changes}
    return out_all or None


def draft_squad_changes(hist_rounds, gw, points_gw, position):
    """What the team changed for the round, and what it was worth - the data
    of the "Valtoztatasok" (changes) tab. The same role as for the NB1
    (collect.py squad_changes): it DERIVES the Guardiola measure, and the
    sum of the items is EXACTLY the `guard`.

    SPLIT IN TWO: WHAT THE PERSON DID, AND WHAT THE MACHINE FIXED ON IT.
    In the Draft the FPL performs automatic substitutions at the end of the
    round - that is not the manager's merit or fault. Shown together, it
    would look as if someone had rotated well, when the machine put the
    squad right (or the reverse).
    So:
      person:  every player counts with their NAMED role - a starter with
               their points, a bench player with zero, even if they came on
               in the end;
      machine: the squad's actual points (with auto_substitute) MINUS the
               sum above. This is exactly what the automatic substitution
               brought for that squad.
    The two add up to the squad's points, so the derivation comes out with
    no remainder.

    There is no Hungarian rule here, so no separate row is needed for it."""
    previous = hist_rounds.get(str(gw - 1)) or {}
    current = hist_rounds.get(str(gw)) or {}
    if not previous or not current:
        return None
    if not points_gw:
        # NO POINTS DATA FOR THE ROUND YET - but the change is already known:
        # the squad is fixed after the deadline. Then it is published
        # without points (see collect.py squad_changes_without_points). The
        # measure is not produced earlier because of this.
        return draft_squad_changes_without_points(previous, current)
    pts = lambda e: (points_gw.get(str(e)) or [0, 0])[0]

    def person(squad):
        """{element: value} by the NAMED roles (bench = 0)."""
        return {x.get("e"): (0 if x.get("b") else pts(x.get("e"))) for x in squad}

    out_all = {}
    for lid, squad in current.items():
        old = previous.get(lid)
        if not old or not squad:
            continue
        person_new, person_old = person(squad), person(old)
        actual = squad_points(squad, points_gw, position)
        alt = squad_points(old, points_gw, position)
        machine_new = round(actual - sum(person_new.values()), 2)
        machine_old = round(alt - sum(person_old.values()), 2)
        out = [{"e": e, "sz": draft_role(e, old), "pont": pts(e), "ert": person_old[e]}
               for e in person_old if e not in person_new]
        into = [{"e": e, "sz": draft_role(e, squad), "pont": pts(e), "ert": person_new[e]}
                for e in person_new if e not in person_old]
        role_changes = []
        for e in person_new:
            if e not in person_old:
                continue
            role_old, role_new = draft_role(e, old), draft_role(e, squad)
            if role_old == role_new:
                continue
            role_changes.append({"e": e, "pont": pts(e), "szE": role_old, "szU": role_new,
                                 "ertE": person_old[e], "ertU": person_new[e]})
        guard = round(actual - alt, 2)
        total = round(sum(x["ert"] for x in into) - sum(x["ert"] for x in out)
                      + sum(x["ertU"] - x["ertE"] for x in role_changes)
                      + (machine_new - machine_old), 2)
        out.sort(key=lambda x: (-x["ert"], x["e"]))
        into.sort(key=lambda x: (-x["ert"], x["e"]))
        role_changes.sort(key=lambda x: (-(x["ertU"] - x["ertE"]), x["e"]))
        out_all[str(lid)] = {"guard": guard, "ki": out, "be": into, "szerep": role_changes,
                             "gepE": machine_old, "gepU": machine_new,
                             "stimmel": abs(total - guard) < 0.005}
        if not out_all[str(lid)]["stimmel"]:
            print("  ! draft_squad_changes: round %d, %s - the items sum to"
                  " %s, the measure is %s" % (gw, lid, total, guard), file=sys.stderr)
    return out_all or None


def main():
    print("FPL Draft collection (league: %s)" % LEAGUE_ID)

    # ---- 1. League data (entries, schedule, results) ----
    status, data = fetch("league/%s/details" % LEAGUE_ID)
    if status != 200 or not data:
        print("  ! details: HTTP %s - the files are unchanged." % status, file=sys.stderr)
        print("   (403/401: the endpoint is closed; 404: wrong league id,")
        print("    set the DRAFT_LEAGUE_ID variable.)")
        return 0
    payload, played = transform_details(data)
    # A 200 with no entries is not a league: writing it would empty the page
    # until the next good run.
    if not payload.get("entries"):
        print("  ! details: empty entry list - the files are unchanged.", file=sys.stderr)
        return 0
    league_ids = {e["id"] for e in payload["entries"]}
    # entry_id -> league id mapping, ONLY in memory
    entry_to_league = {e.get("entry_id"): e.get("id")
                       for e in data.get("league_entries") or []}
    print("  league: %s | entries: %d | matches played: %d"
          % (payload["league"]["name"], len(league_ids), played))
    write_if_changed("draft.json", payload)

    # ---- 2. Player master data ----
    status, bs = fetch("bootstrap-static")
    players = {}
    if status == 200 and bs:
        club = {t.get("id"): (t.get("short_name") or t.get("name") or "")
                for t in bs.get("teams") or []}
        position = {t.get("id"): (t.get("singular_name_short") or "")
                    for t in bs.get("element_types") or []}
        for el in bs.get("elements") or []:
            players[str(el.get("id"))] = {
                "n": el.get("web_name") or "",
                "t": club.get(el.get("team"), ""),
                "p": position.get(el.get("element_type"), ""),
                # the season points are needed for the home page player list
                # (descending points order + search). bootstrap-static comes
                # down on every run anyway, so this is NOT an extra request.
                "pts": el.get("total_points") or 0,
            }
        # "teams" (team id -> short name) is needed in the browser to resolve
        # the team ids of the live fixtures answer
        # (the "has played?" flag: has their match started)
        if players:
            write_if_changed("draft_players.json",
                             {"updated": None, "players": players,
                              "teams": {str(k): v for k, v in club.items()}})
            print("  player master data: %d players, %d teams" % (len(players), len(club)))
        else:
            # an empty 200 must not overwrite the stored player list
            print("  ! bootstrap-static: empty player list - master data unchanged",
                  file=sys.stderr)
    else:
        print("  ! bootstrap-static: HTTP %s - master data unchanged" % status,
              file=sys.stderr)

    # ---- 3. Current squads (ownership) ----
    status, es = fetch("league/%s/element-status" % LEAGUE_ID)
    if status == 200 and es:
        squads = {}
        unknown = set()
        for x in es.get("element_status") or []:
            owner = x.get("owner")
            if owner is None:
                continue
            # the owner's id space is found out at run time
            if owner in league_ids:
                lid = owner
            elif owner in entry_to_league:
                lid = entry_to_league[owner]
            else:
                unknown.add(owner)
                continue
            squads.setdefault(str(lid), []).append(x.get("element"))
        for lid in squads:
            squads[lid].sort()
        if unknown:
            print("  ! element-status: %d unknown owner ids: %s"
                  % (len(unknown), sorted(unknown)[:5]), file=sys.stderr)
        if squads:
            write_if_changed("draft_squads.json",
                             {"updated": None, "squads": squads})
            print("  current squads: %d teams, %d owned players"
                  % (len(squads), sum(len(v) for v in squads.values())))
        else:
            # after the draft every team owns players: an empty answer is an
            # API fault, not an empty league
            print("  ! element-status: empty ownership - squads unchanged",
                  file=sys.stderr)
    else:
        print("  ! element-status: HTTP %s" % status, file=sys.stderr)

    # ---- 4. Per-round squads + points (from the start of GW1) ----
    status, game = fetch("game")
    if status != 200:
        # an outage must not read like the close season in the run log
        print("  ! game: HTTP %s - per-round data is not refreshed now" % status,
              file=sys.stderr)
        print("Done.")
        return 0
    current = (game or {}).get("current_event")
    if not current:
        print("  . the season has not started yet (current_event=%s) - "
              "no per-round squad yet" % current)
        print("Done.")
        return 0

    hist = read_stored("draft_history.json", {"updated": None, "rounds": {}})
    hist.setdefault("rounds", {})
    closings = read_stored("zarasok.json", {"updated": None, "rounds": {}})
    closings.setdefault("rounds", {})
    closings_before = json.dumps(closings["rounds"], ensure_ascii=False, sort_keys=True)

    # Targets: the current round (refreshed while it runs), every missing
    # one, AND every round not yet KNOWN for certain to have closed for good.
    #
    # WHY: at the end of a round the FPL performs AUTOMATIC SUBSTITUTIONS -
    # in place of a starter who did not play it puts in the first bench
    # player who fits -, and then it REWRITES the pick's "position" field.
    # Measured (naplo/fpl-subs.txt): this happens at "lockdown", together
    # with the rest, between 08:03 and 08:23 UTC; its signal is the game
    # endpoint's "current_event_finished" field.
    # The collector runs every 3 hours, so if current_event moved on before
    # the round had been fetched once more after the close, the squad would
    # freeze FOR GOOD in its pre-substitution state (wrong "b" flag, wrong
    # "Kezdok" (starters) total). A run landing shortly after the close is
    # not something to rely on.
    #
    # The rounds already known to be closed are kept in hist["veglegesek"],
    # so a finalised round is not fetched again on every run.
    # THE CURRENT ROUND IS ALWAYS A TARGET, even if it has already closed.
    # This is not decoration: until current_event moves on (a week), later
    # FPL corrections come through this way. Marking the closed round as
    # final and dropping it would leave the whole week after the close
    # blind.
    # The `veglegesek` list only decides whether the OLD rounds have to be
    # fetched again - see below why.
    finals = {int(x) for x in (hist.get("veglegesek") or [])}
    targets = {int(current)}
    for gw in range(1, int(current) + 1):
        stored = hist["rounds"].get(str(gw)) or {}
        if len(stored) < len(league_ids) or gw not in finals:
            targets.add(gw)

    complete_now = {}         # gw -> did every team's squad arrive in this run
    points_store = {}         # gw -> {element: [points, minutes]} for the WHOLE field
    for gw in sorted(targets):
        status, live = fetch("event/%d/live" % gw)
        pts, minutes, mismatched = {}, {}, 0
        if status == 200 and live:
            el = live.get("elements")
            elements = (list(el.items()) if isinstance(el, dict)
                        else [(str((v or {}).get("id")), v) for v in el] if isinstance(el, list)
                        else [])
            for k, v in elements:
                p, found = player_points(v)
                if found and p != (((v or {}).get("stats") or {}).get("total_points") or 0):
                    mismatched += 1
                pts[str(k)] = p
                # The MINUTES are needed for the automatic substitutions (0
                # minutes = did not come on), in the Guardiola measure's
                # alternative.
                minutes[str(k)] = ((v or {}).get("stats") or {}).get("minutes") or 0
        # THE SAME RULE AS ON THE PAGE: the mismatch is not silent. If it is
        # regular, the log shows it - and then it is time to look again at
        # which source broke.
        if mismatched:
            print("  ! round %d: for %d players the FPL total DIFFERS from the"
                  " sum of the itemised breakdown - the breakdown is kept"
                  % (gw, mismatched), file=sys.stderr)
        # D1: if the live points did not arrive, the round is SKIPPED.
        # Otherwise every player would be written with 0 points, the round
        # would count as "complete", and it would never be fetched again -
        # the zeros would be stuck for good.
        if not pts:
            print("  ! round %d: the live points did not arrive (HTTP %s),"
                  " the round is skipped" % (gw, status), file=sys.stderr)
            continue
        new = {}
        for eid, lid in entry_to_league.items():
            if lid is None or eid is None:
                continue
            status, ev = fetch("entry/%d/event/%d" % (eid, gw))
            if status != 200 or not isinstance(ev, dict):
                print("  ! round %d / %s: HTTP %s" % (gw, lid, status), file=sys.stderr)
                continue
            picks = ev.get("picks") or []
            # D2: an empty squad is not stored - it would count as a
            # "complete" record, and would stay empty for this round forever
            if not picks:
                print("  ! round %d / %s: empty squad, skipped" % (gw, lid),
                      file=sys.stderr)
                continue
            if "element" not in picks[0]:
                print("  ! round %d: unknown picks structure, keys: %s"
                      % (gw, sorted(picks[0].keys())), file=sys.stderr)
                continue
            new[str(lid)] = [{"e": p.get("element"),
                              "b": (p.get("position") or 0) > 11,
                              "pts": pts.get(str(p.get("element")), 0)}
                             for p in picks]
        # CLOSING DIFFERENCE: computed exactly once, in the finalising run -
        # when the round would NOW join the finals. At that point hist still
        # keeps the snapshot from BEFORE the close (from the latest run, at
        # most 3 hours earlier), and "new" is the state AFTER the close: the
        # difference of the two is the work of the lockdown (bonus
        # correction, automatic substitutions). Without an old snapshot
        # (backfill) there is nothing to compute from - then it is left out.
        to_finalise = (gw not in finals and len(new) == len(league_ids)
                       and (gw < int(current)
                            or (gw == int(current)
                                and bool(game.get("current_event_finished")))))
        if to_finalise and str(gw) not in closings["rounds"]:
            diff = closing_diff(hist["rounds"].get(str(gw)) or {}, new)
            if diff is not None:
                closings["rounds"][str(gw)] = diff
                print("  closing difference: GW%d, %d teams affected"
                      % (gw, len(diff)))

        # Did EVERY team's squad arrive IN THIS RUN? The stored data does not
        # show it: because of the merge below an older, complete snapshot
        # would make the round look complete even if a request failed just
        # now - and then the pre-substitution state would be recorded as
        # final.
        # The points+minutes of the WHOLE field for the round. The Guardiola
        # measure needs it: last week's squad can hold a player who is now
        # in NOBODY's squad - GW1->GW2 had 11 such -, and then their points
        # would be nowhere. Only those who played or scored points are kept;
        # a missing one counts as [0, 0].
        points_store[str(gw)] = {k: [pts[k], minutes.get(k, 0)]
                                 for k in pts if pts[k] or minutes.get(k)}
        complete_now[gw] = (len(new) == len(league_ids))
        if new:
            hist["rounds"][str(gw)] = {**(hist["rounds"].get(str(gw)) or {}), **new}
            print("  per-round squads: GW%d, %d/%d teams"
                  % (gw, len(new), len(league_ids)))

    # A round is FINAL if the FPL has moved past it, or if it is the current
    # one but according to the game endpoint it has finished (lockdown done).
    # It can be marked final only if every team's squad was brought in during
    # this run - otherwise after a failed request the pre-substitution state
    # would be recorded as final.
    finished = bool(game.get("current_event_finished")) if isinstance(game, dict) else False
    for gw in sorted(targets):
        if not complete_now.get(gw):
            continue
        if gw < int(current) or (gw == int(current) and finished):
            finals.add(gw)
    if json.dumps(closings["rounds"], ensure_ascii=False, sort_keys=True) != closings_before:
        closings["updated"] = stamp()
        write_if_changed("zarasok.json", closings)

    write_if_changed("draft_history.json",
                     {"updated": None, "rounds": hist["rounds"],
                      "veglegesek": sorted(finals)})

    # ---- The per-round points+minutes of the WHOLE field (draft_pontok.json).
    # Merged with the stored one: this run fetched only the `targets` rounds,
    # the data of the others must not be thrown away.
    points = read_stored("draft_pontok.json", {}).get("rounds") or {}
    points.update(points_store)
    write_if_changed("draft_pontok.json", {"updated": None, "rounds": points})

    # ---- Guardiola measure. The same definition as for the NB1; the
    # computation is deterministic, so it reruns on every run.
    # The name is ON PURPOSE not `position`: that is already taken in this
    # function (position type -> short name, from bootstrap). The same
    # name-collision trap as with .pos/.ppos.
    player_position = {k: (v or {}).get("p") for k, v in (players or {}).items()}
    gua = {}
    # WITHOUT POSITION DATA, NOTHING IS COMPUTED. When bootstrap-static fails,
    # `players` is empty, and then the formation check of auto_substitute
    # would ALWAYS be false - not a single substitution would happen, and the
    # measure would silently give a wrong value. The earlier file then stays
    # in force.
    if player_position:
        for gw_ in sorted(int(x) for x in hist["rounds"]):
            g_ = draft_guardiola(hist["rounds"], gw_, points.get(str(gw_)), player_position)
            if g_:
                gua[str(gw_)] = g_
    else:
        print("  ! no player position data, the Guardiola measure is unchanged",
              file=sys.stderr)
    try:
        with open("draft_guardiola.json", encoding="utf-8") as f:
            gua_old = json.load(f).get("rounds")
    except Exception:
        gua_old = None
    if gua and json.dumps(gua, ensure_ascii=False, sort_keys=True) != \
       json.dumps(gua_old, ensure_ascii=False, sort_keys=True):
        write_if_changed("draft_guardiola.json", {"updated": stamp(), "rounds": gua})
        print("  draft_guardiola.json updated (%d rounds)" % len(gua))

    # ---- Squad changes (the "Valtoztatasok" tab). From the same loop as the
    # measure - the tab derives exactly that, so they have to move together.
    # The player NAME is not stored: the page resolves it from
    # draft_players.json anyway (the field is complete, a departed player
    # stays in it) - on the NB1 this differs because there the player roster
    # gives only the CURRENT field.
    changes = {}
    if player_position:
        for gw_ in sorted(int(x) for x in hist["rounds"]):
            k_ = draft_squad_changes(hist["rounds"], gw_, points.get(str(gw_)),
                                     player_position)
            if k_:
                changes[str(gw_)] = k_
    try:
        with open("draft_keretvaltozasok.json", encoding="utf-8") as f:
            changes_old = json.load(f).get("rounds")
    except Exception:
        changes_old = None
    if changes and json.dumps(changes, ensure_ascii=False, sort_keys=True) != \
       json.dumps(changes_old, ensure_ascii=False, sort_keys=True):
        write_if_changed("draft_keretvaltozasok.json",
                         {"updated": stamp(), "rounds": changes})
        print("  draft_keretvaltozasok.json updated (%d rounds)" % len(changes))

    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
