#!/usr/bin/env python3
"""FunTasy Liga - automatic data collection from the MLSZ Fantasy API.

Collects two things - hourly at :17 UTC from Thursday to Monday (the match
days), every 3 hours at :17 UTC on Tuesday and Wednesday
(.github/workflows/archive.yml):

1. H2H RESULTS (results.json) - the official round scores from the rankings
   endpoint. This is the table's only source.
2. SQUADS (squads.json, squad_history.json) - from the squad endpoint, in a
   format compatible with the browser bookmarklet; the one addition is the
   "round" field of squads.json (which round the squads belong to). The
   bookmarklet is only a fallback now, see tartalek/KERET-MENTES.md.

THE SQUAD ENDPOINT works from anywhere, without logging in, as long as the
request carries the filter[round_id] parameter. Without that parameter it
answers 403 - from GitHub Actions, through proxies and from Playwright
alike - which makes it look as if it were blocked for servers. It is not.

FURTHER FACTS, CONFIRMED BY MEASUREMENT:

- round_id = 75 + 2 x round number.
- By default the rankings return only the last closed and the current
  round; an older round can be requested with the filter[round_id]
  parameter (the answer holds that round AND the one before it).
- The squad endpoint answers 403 for a round that has not started yet
  (squads are secret until the market closes). This is expected behaviour,
  not an error.
- ROUND CLOSING: a round is closed when every player WHO HAS A MATCH has
  played it (current_round.is_played), and the match itself has finished
  (games[0].status == "completed"). A player with no match in the round
  (nogame) does not count.
  A player with no match is NOT marked as played with 0 points, contrary
  to what one might assume. Measured: the round 5 Honved players (no match)
  had is_played=false; the round 3 ETO players did have it true - but only
  because, when an old round is requested, the API falls back to the club's
  LATEST match (the same fallback behind the "odd kick-off time" error).
  So the flag does not flip when the round closes but when the club next
  plays - which can be a whole week later.
- SAFETY NET FOR CLOSING: the MLSZ's own round object. There is no
  standalone rounds endpoint (404); the round list comes through the
  competition list: competitions?include=rounds,current_round - the MLSZ
  frontend calls this too. Its fields: id, round_number, start_at, end_at,
  is_transfers_closed, closed_transfers_at. THERE IS NO CLOSED FLAG IN IT:
  at the MLSZ a round is a calendar boundary (one round's end_at is the
  next one's start_at), so this is only a fallback - if the player-level
  picture does not come together, the round still does not stay
  provisional forever.
- When the LIVE round is requested, current_round comes back only with an
  explicit competition_player.current_round include (for a closed round it
  appears without it) - this is why it is in INCLUDE.
- WHO DOES NOT PLAY IN THE ROUND: the competition_player.current_round.games
  include tells it reliably, in TWO forms (measured):
    * an empty list - this comes for the LIVE round when the club has no
      match;
    * a match of ANOTHER round - for an old round the API falls back to the
      club's latest match instead of the missing one. The match object
      itself gives it away: its round_number field looks like "3F" / "5F",
      and if it does not point to the requested round, the club has no
      match in it.
  first_played_at is useless here too: it points either to the club's NEXT
  match or to a midnight placeholder (for round 3 ETO, midnight, i.e. a day
  already past with an unscheduled time). The match list is requested only
  for the LIVE round: there it costs +2 KB, but for closed rounds the club
  logos come in base64 next to the finished match, and the answer grows
  from 17 KB to 118 KB.
- POINTS BREAKDOWN: the /game-player-stats endpoint (WITHOUT the
  competitions prefix) gives a player's itemised per-round breakdown with
  Hungarian labels:
  ?include=competition_stat_config&filter[competition_player_id]=<cp.id>
  &filter[round_id]=<round_id>. The page calls it from the browser; the
  collector only puts the cp id it needs ("id") and the "has played?" flag
  ("played" = current_round.is_played) into the squad records.
- The numbers of a round that has not closed are PROVISIONAL: they go into
  the "provisional" list of results.json, and the page leaves them out of
  the table.
- The MLSZ corrects after the fact: three observed cases (Csendi, rounds
  1-3, +1/+1/-2.5). So we ALWAYS sync to the fetched value, compare the sum
  computed from the squad with the official one, and also LOG the change
  (zarasok_nb1.json) - afterwards it can no longer be reconstructed what
  moved.
- The players' weekly_points value is ALREADY FINAL: the captain's doubling
  and the bench halving are in it. We never multiply again and never halve.
- The 0-0 guard stays: if every value of a round is 0, the round has not
  even started, and it must not go in as a played draw.
"""
import datetime
import itertools, json, os, re, sys, time, urllib.error, urllib.parse, urllib.request

# The tests load this module by its file PATH, so sys.path holds the tests
# directory, not the repository root. We add our own directory, otherwise the
# shared module would only be found in a live run.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collector_common import stamp, write_compact, read_stored

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


def competition_rounds():
    """The MLSZ's own round object - the SAFETY NET for closing.

    There is NO standalone rounds endpoint (every such path is 404); the
    round list comes through the COMPETITION LIST, with the same call the
    MLSZ's own frontend uses. The fields of a round: id, round_number,
    start_at, end_at, is_transfers_closed, closed_transfers_at.

    THERE IS NO CLOSED FLAG AMONG THEM: at the MLSZ a round is a calendar
    boundary, it lasts until its end_at, after which current_round moves on.
    So this is only a fallback behind the player-level signal, not the
    primary source.

    Returns: (current round number or None, {round number: end_at}).
    On error (None, {}) - the caller then relies on the player-level signal
    alone."""
    status, payload = api_get(ROOT + "competitions?include=rounds,current_round")
    if status != 200 or not isinstance(payload, dict):
        return None, {}
    comp = next((c for c in (payload.get("data") or [])
                 if c.get("id") == COMPETITION), None) or {}
    def number(x):
        # "9", 9 and "3F" all name a round; anything else is not one, and
        # must not stop the run
        m = re.match(r"\s*(\d+)", str(x if x is not None else ""))
        return int(m.group(1)) if m else None
    current = number((comp.get("current_round") or {}).get("round_number"))
    ends = {}
    for r in comp.get("rounds") or []:
        n = number(r.get("round_number"))
        if n is not None and r.get("end_at"):
            ends[n] = r["end_at"]
    return current, ends


def mlsz_round_over(r, mlsz_current, mlsz_ends):
    """True if, according to the MLSZ, round r is no longer running.

    The primary signal is current_round: if the MLSZ has moved on, the round
    is over. This is stronger than the calendar - if current_round says this
    is STILL the current round, the passing of end_at does not close it
    either (the two can disagree for a while, and closing a running round is
    the worse mistake: a half-finished result would silently enter the
    table).

    end_at decides only when current_round did not arrive at all."""
    if mlsz_current is not None:
        return mlsz_current > r
    end = mlsz_ends.get(r)
    if not end:
        return False
    try:
        return datetime.datetime.now(datetime.timezone.utc) > \
            datetime.datetime.fromisoformat(end)
    except ValueError:
        return False


def api_get(url, retries=3):
    """(status, json) - retries on a network error; not on a 4xx."""
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
                print("  ! network error: %s" % e, file=sys.stderr)
                return None, None
            time.sleep(3)
    return None, None


def rankings(uname, round_id=None):
    url = (BASE + "rankings?include=user_team.user.id,summary_statistics,"
           "ranking,rounds,competition_rank&page=1&per_page=5"
           "&filter%5Bsearch%5D=" + urllib.parse.quote(uname))
    if round_id:
        # string concatenation, NOT %-formatting: it would take %5B for a
        # format directive
        url += "&filter%5Bround_id%5D=" + str(round_id)
    status, payload = api_get(url)
    if status != 200 or not payload:
        return None
    rows = payload.get("data") or []
    names = [((d.get("user_team") or {}).get("user") or {}).get("username") for d in rows]
    exact = next((d for d, n in zip(rows, names)
                  if n and n.lower() == uname.lower()), None)
    if exact or not rows:
        return exact
    if any(names):
        # The answer names its users, and none of them is ours: the search
        # matched somebody else. Their points must not be recorded as ours.
        print("  ! %s: the search hits are other users (%s) - no data"
              % (uname, ", ".join(n for n in names if n)[:120]), file=sys.stderr)
        return None
    # No exact username match. The hit list is NOT thrown away (the answer
    # does not always carry the username field), but it is logged: without
    # this a mistaken search would silently record ANOTHER manager's points -
    # exactly the "silent, plausible, wrong" error the other guards are
    # against.
    print("  ! %s: no exact username match, using the first hit "
          "(%d hits)" % (uname, len(rows)), file=sys.stderr)
    return rows[0]


GAMES = "competition_player.current_round.games"


def round_points(row):
    """{round: points} from a rankings row; malformed entries are skipped.

    A single bad entry must not raise: that would stop the whole run - on
    every run, until the API changed - and nothing at all would be written."""
    out = {}
    for s in ((row or {}).get("user_team") or {}).get("round_statistics") or []:
        try:
            r, pts = int(s["round_number"]), s["points"]
        except (KeyError, TypeError, ValueError):
            print("  ! malformed round_statistics row: %r" % (s,), file=sys.stderr)
            continue
        if isinstance(pts, (int, float)):
            out[r] = pts
    return out


def squad(user_id, round_no, with_games=False):
    """with_games=True: the match list is requested too (who does NOT play in
    the round, and which clubs the match is between).

    THE TWO CLUBS ARE REQUESTED EXPLICITLY. Without them the LIVE round's
    match object is only id/start/status/score/round_number - WITHOUT the
    clubs -, and match_summary wrote "?" into meccsek.json; the profile row
    then showed a dash in place of the opponent although the result was
    there. (The API returns a closed round with its teams even without
    this.)

    MEASURED (live round 6, naplo/mlsz-live-match.txt):
      - games.home_team + games.away_team  -> HTTP 200, the club arrives
      - games.homeTeam / games.teams       -> the field does not appear
      - the answer grows 22.3 KB -> 24.8 KB, i.e. +2.5 KB: the team object
        here is LEAN (id, name, short_name, color_hex), WITHOUT A LOGO - not
        the 118 KB bloat measured on the closed-round answer.
      - there is no separate match endpoint: games/<id>, matches/<id>,
        fixtures/<id> are 404 both at the root and under competitions/3
        (ten forms).
      - from the clubs of the owned players only 4/6 matches would have had
        both sides, and home/away not at all - so it is not derived from
        that."""
    inc = INCLUDE + (("," + GAMES + "," + GAMES + ".home_team,"
                      + GAMES + ".away_team") if with_games else "")
    url = (BASE + "user-team-players-history?include=" + urllib.parse.quote(inc)
           + "&filter%5Buser_id%5D=" + str(user_id)
           + "&filter%5Bround_id%5D=" + str(rid(round_no)))
    return api_get(url)


def player_name(first, last, fallback=None):
    """The player's name in HUNGARIAN ORDER: family name first.

    The MLSZ gives the two parts separately. In the Hungarian league the
    family name comes first, and this is not only a matter of style: the
    recognisable part of a long name is the FAMILY NAME - that is what is
    on the shirt. For "Gleofilo Sabrino Rudewald Hasselbaink Vlijter" the
    western order starts with the unrecognisable half, and in narrow
    columns exactly the essential part (Vlijter) would be cut off."""
    name = " ".join(x for x in (last, first) if x)
    return name or (fallback or "")


def is_hun(cp):
    """The same rule as in the bookmarklet."""
    text = json.dumps(cp.get("countries") or cp.get("country") or "", ensure_ascii=False)
    return bool(re.search(r'magyar|hungar|"HUN"', text, re.I))


def match_round(g):
    """The match object tells WHICH round it belongs to: its round_number
    field looks like "3F" / "5F". A number, or None if it is not there."""
    m = re.match(r"\s*(\d+)", str((g or {}).get("round_number") or ""))
    return int(m.group(1)) if m else None


def player_record(d, round_no=None):
    """One player's record - field for field the bookmarklet's format."""
    cp = d.get("competition_player") or {}
    po = d.get("position") or {}
    ss = d.get("summary_statistics") or {}
    team = cp.get("team") or {}
    cr = cp.get("current_round") or {}
    name = player_name(cp.get("first_name"), cp.get("last_name"),
                       "#%s" % (cp.get("id") or d.get("id")))
    return {
        "name": name,
        "team": team.get("short_name") or team.get("name") or "",
        "pos": po.get("monogram") or po.get("name") or "",
        "u21": bool(cp.get("is_u21")),
        "hun": is_hun(cp),
        "price": (cr.get("market_price") or None),
        "cap": bool(d.get("is_captain")),
        "sub": d.get("type") == "substitutes",
        "week": ss.get("weekly_points") or 0,
        "total": ss.get("competition_points") or 0,
        # beyond the bookmarklet format: for the points breakdown and the
        # "has played?" flag (for the live round current_round comes only
        # with an explicit include, which is why it is in INCLUDE).
        # "start" is the kick-off of the player's match in the round;
        # "nogame" is added when the club has NO match in the round
        # (postponed or called off). The match list (games) tells this
        # reliably: an empty list = no match. first_played_at then gives the
        # club's NEXT match (another round's time), so it cannot be used for
        # this - it was the cause of the "odd kick-off time".
        "id": cp.get("id"),
        "played": bool(cr.get("is_played")),
        **game_fields(cr, round_no),
    }


def games_of_round(games, round_no):
    """The matches of the list that COUNT for this round.

    TWO things have to be told apart, and round_number ALONE decides
    neither - both carry an EARLIER round's number:

    1. A RESCHEDULED (postponed) MATCH. Measured: in ETO's
       current_round.games list TWO matches stood for round 7 - "3F"
       (ETO-FTC, 3 Sept., the postponed round 3 match) and "7F"
       (ETO-HONVED, 6 Sept.). So the MLSZ puts the match into the round of
       the DAY IT IS MADE UP, but keeps the ORIGINAL round's number on it.
       The points are earned where it is played.

    2. FALLBACK. If the club has NO match in the requested round, the API
       falls back to another match of the club (also with another round
       number).

    THE DIFFERENCE: next to a rescheduled match the round's OWN match is
    there too; in a fallback exactly that one is missing. So: if the list
    holds a match of the requested round, the OTHERS belong here too
    (rescheduled); if not, the whole list is a fallback.

    KNOWN LIMIT: if a club has ONLY a rescheduled match in the round (its
    own was called off too), we see a fallback and say "no match". This is
    the existing behaviour, so not a regression - the exact solution would
    be the round's TIME WINDOW (is the match inside the round's window),
    which needs the round boundaries passed to every call site. If it ever
    happens, that is what has to be built."""
    own = [g for g in (games or []) if isinstance(g, dict)]
    if not own:
        return []
    matching = [g for g in own
                if match_round(g) in (None, round_no) or round_no is None]
    return own if matching else []


def game_fields(cr, round_no=None):
    games = cr.get("games")
    if games is None:                       # the match list was not requested
        return {"start": cr.get("first_played_at")}
    own = games_of_round(games, round_no)
    if not own:                             # no match in this round
        return {"start": None, "nogame": True}
    # THERE CAN BE SEVERAL MATCHES (a rescheduled one): the player's points
    # can then change until the LAST one has finished. So `start` is the
    # nearest match NOT YET FINISHED - it tells what is still awaited -, and
    # `vege` is true only when ALL of them have finished.
    remaining = sorted((g for g in own if g.get("status") != "completed"),
                       key=lambda g: g.get("start_at") or "")
    all_games = sorted(own, key=lambda g: g.get("start_at") or "")
    g = remaining[0] if remaining else all_games[-1]
    fields = {"start": g.get("start_at") or cr.get("first_played_at")}
    # The match status is a signal of its own next to is_played. The latter
    # does NOT imply that the match is over: the MLSZ flips it to true
    # already during the match (which would make the page say "played"
    # mid-match).
    if not remaining:
        fields["vege"] = True
    return fields


def inherit_match_flags(old_round, new_round, inherit=True):
    """The flags that come from the match list must be carried over from the
    old record.

    The match list (games) is requested only for the LIVE round - the
    re-fetches after closing come without it, so whatever comes only from
    it would drop out. There are two such fields:
      nogame - the club has no match in the round (postponed/called off).
               first_played_at then gives the NEXT match, so start is reset
               to the old (empty) value too.
      vege   - the match has already finished. Without it the page would
               fall back to the "match in progress" state in the 100-180
               minute window.

    `inherit=False` WHEN THE MATCH LIST WAS FETCHED NOW: the fresh answer is
    then the truth, and the old flag must not override it. Otherwise a
    wrongly stuck `nogame` would stay FOREVER: after a fix the collector
    would rightly say that ETO DOES have a match, but the `nogame`
    inherited from the previous run would restore the error. The fix would
    block itself."""
    if not inherit:
        return
    for name, sq in new_round.items():
        old = {p.get("name"): p for p in (old_round.get(name) or [])}
        for p in sq:
            old_p = old.get(p.get("name")) or {}
            if "nogame" not in p and old_p.get("nogame"):
                p["nogame"] = True
                p["start"] = None
            if "vege" not in p and old_p.get("vege"):
                p["vege"] = True


def squad_total(sq):
    """Round score from the squad: sum of weekly_points + the Hungarian rule."""
    total = sum(p.get("week") or 0 for p in sq)
    starters = [p for p in sq if not p.get("sub")]
    hun = sum(1 for p in starters if p.get("hun"))
    u21 = sum(1 for p in starters if p.get("hun") and p.get("u21"))
    return total + (10 if (hun >= 5 and u21 >= 1) else 0)


def raw_points(r):
    """The RAW player points of a closed round from bontasok/<r>.json:
    {cp id: points}. None if the file does not exist yet.

    The rows of a breakdown are the player's OWN events, so their sum is the
    raw weekly points - WITHOUT the captain's doubling and the bench
    halving. That is exactly what is needed here: the multipliers are
    applied according to LAST WEEK's roles."""
    path = os.path.join("bontasok", "%d.json" % r)
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
    except Exception:
        return None
    return {cp: sum(x.get("p") or 0 for x in (rows or []))
            for cp, rows in (d.get("bontasok") or {}).items()}


def guardiola_squad(old_sq, raw):
    """The records of LAST WEEK's squad, with the CURRENT round's points.

    "What if I had not touched it": the same 15 players, IN THE SAME ROLES -
    who was a starter stays a starter, who sat on the bench stays there, the
    captain is the same. NOT the best line-up: that would be another measure
    (the KEZD% measures that).

    The multipliers are applied exactly as the API does: captain x2, bench
    halved, AND ROUNDED TO TWO DECIMALS - the real `week` comes back like
    this too (0.75 -> 0.38). Otherwise the difference would slip in the
    decimals.

    A PLAYER MISSING FROM THE BREAKDOWN GETS 0 POINTS - but this is only a
    last resort. Players who have left the league but were once owned must
    not land here: that skews the measure (Skribek scored 3.25 raw points
    in rounds 1 and 3, yet would count with 0 - in favour of whoever had
    just sold him). This is why collect_breakdowns requests them too
    (`extra`). If someone is missing now, a request failed, not a player is
    missing - the caller logs it too."""
    new = []
    for pl in old_sq:
        base = raw.get(str(pl.get("id")), 0)
        w = base * 2 if pl.get("cap") else (base / 2.0 if pl.get("sub") else base)
        copy = dict(pl)
        copy["week"] = round(w, 2)
        new.append(copy)
    return new


def guardiola(hist_rounds, r):
    """The "Guardiola measure" for one round: {manager: {teny, alt, guard}}.

    guard = the points of the CURRENT squad - LAST WEEK's squad IN THE SAME
    round. A negative value: the change cost points.

    BOTH sides are computed with THE SAME function (squad_total), so the
    Hungarian rule and the rounding play the same way - the difference is
    purely the work of the squad change. On purpose it is NOT subtracted
    from the official round score: that would include a later MLSZ
    correction, which is not the manager's decision.

    None if there is nothing to compare with (first round) or data is
    missing."""
    previous = (hist_rounds.get(str(r - 1)) or {})
    current = (hist_rounds.get(str(r)) or {})
    if not previous or not current:
        return None
    raw = raw_points(r)
    if raw is None:
        return None
    out, missing = {}, set()
    for name, sq in current.items():
        old_sq = previous.get(name)
        if not old_sq or not sq:
            continue
        # BOTH sides compute from the BREAKDOWN, not from the stored `week`.
        # Otherwise an unchanged squad would not give exactly 0 either: the
        # stored `week` of a bench player is the API's already halved and
        # rounded value (0.75 -> 0.38), while ours computes from the raw
        # points - the two differ by 0.01, and that would show in the
        # difference ("+0.01" although the squad was not touched).
        # So `teny` can differ from the official round score by a cent; the
        # MEASURE is exact, and that is what is shown.
        actual = squad_total(guardiola_squad(sq, raw))
        alt = squad_total(guardiola_squad(old_sq, raw))
        out[name] = {"teny": round(actual, 2), "alt": round(alt, 2),
                     "guard": round(actual - alt, 2)}
        # NOT SILENT: a player missing from the breakdown counts with 0, and
        # that makes the measure inaccurate. The breakdown covers every
        # player ever owned, so if this fires anyway it is an error - a
        # failed request or a missed backfill.
        for pl in list(sq) + list(old_sq):
            if str(pl.get("id")) not in raw:
                missing.add(pl.get("name") or str(pl.get("id")))
    if missing:
        print("  ! guardiola: round %d - missing from the breakdown, counts"
              " with 0 points: %s" % (r, ", ".join(sorted(missing))), file=sys.stderr)
    return out or None


def role(p):
    """The player's role in a squad: 'C' (captain), 'pad' (bench) or 'kezdo'
    (starter)."""
    return "C" if p.get("cap") else ("pad" if p.get("sub") else "kezdo")


def squad_changes_without_points(previous, current):
    """The changes of the RUNNING round, without point values.

    The same items (out / in / role), only without `ert`, `nyers` and
    `guard`; `pontok: False` tells the page there is nothing to add up
    here. The Hungarian-rule difference is left out too: that is points as
    well."""
    out_all = {}
    for name, sq in current.items():
        old_sq = previous.get(name)
        if not old_sq or not sq:
            continue
        old_by_id = {p.get("id"): p for p in old_sq}
        new_by_id = {p.get("id"): p for p in sq}
        item = lambda p: {"id": p.get("id"), "n": p.get("name"),
                          "tm": p.get("team"), "pos": p.get("pos"),
                          "sz": role(p)}
        out = sorted((item(p) for i, p in old_by_id.items() if i not in new_by_id),
                     key=lambda x: x["n"] or "")
        into = sorted((item(p) for i, p in new_by_id.items() if i not in old_by_id),
                      key=lambda x: x["n"] or "")
        role_changes = sorted(({"id": i, "n": p.get("name"), "tm": p.get("team"),
                                "pos": p.get("pos"), "szE": role(old_by_id[i]),
                                "szU": role(p)}
                               for i, p in new_by_id.items()
                               if i in old_by_id and role(old_by_id[i]) != role(p)),
                              key=lambda x: x["n"] or "")
        out_all[name] = {"pontok": False, "guard": None,
                         "ki": out, "be": into, "szerep": role_changes}
    return out_all or None


def squad_changes(hist_rounds, r):
    """What the manager changed for the round, and what the change was worth.

    The data of the "Valtoztatasok" (changes) tab. It computes from the same
    inputs as the Guardiola measure (guardiola), and ON PURPOSE DERIVES IT:
    next to every item stands how much it gained or lost, and the sum of the
    items is EXACTLY the `guard`. If it is not, it is a computation error -
    the `stimmel` field says so, and the test (K5) fails on it. Without this
    the tab would only be a list that nobody could check against the number
    in the table.

    Three kinds of item:
      ki      - (out) in last week's squad, not now: counts with LAST WEEK's
                role (this much it would have brought, had it been left
                alone)
      be      - (in) in the squad now, not last week: with the CURRENT role
      szerep  - (role) in throughout, but the role changed (starter <->
                bench <-> C): the item is the difference of the two values

    The fourth item is the Hungarian rule: if the change gained or lost the
    10 points, it does not show on any player but on the squad - it stands
    in a row of its own. (It is in the Guardiola measure too, see
    squad_total.)"""
    previous = (hist_rounds.get(str(r - 1)) or {})
    current = (hist_rounds.get(str(r)) or {})
    if not previous or not current:
        return None
    raw = raw_points(r)
    if raw is None:
        # NO BREAKDOWN YET (the round has not closed) - but the CHANGE is
        # already known: the squad is fixed after the deadline. What we do
        # not know then is the POINT VALUE; what we do know is who was sold,
        # who was bought and whose role changed. This is published without
        # points. The Guardiola measure is NOT produced earlier because of
        # this - it still exists only for a closed round (guardiola.json
        # unchanged).
        return squad_changes_without_points(previous, current)
    out_all = {}
    for name, sq in current.items():
        old_sq = previous.get(name)
        if not old_sq or not sq:
            continue
        # Both sides are built with THE SAME function as in the measure -
        # otherwise the rounding would drift apart and the derivation would
        # not add up.
        new_k = guardiola_squad(sq, raw)
        alt_k = guardiola_squad(old_sq, raw)
        old_by_id = {p.get("id"): p for p in alt_k}
        new_by_id = {p.get("id"): p for p in new_k}
        item = lambda p, e: {"id": p.get("id"), "n": p.get("name"),
                             "tm": p.get("team"), "pos": p.get("pos"),
                             "sz": role(p), "nyers": raw.get(str(p.get("id")), 0),
                             "ert": e}
        out = [item(p, p["week"]) for i, p in old_by_id.items() if i not in new_by_id]
        into = [item(p, p["week"]) for i, p in new_by_id.items() if i not in old_by_id]
        role_changes = []
        for i, p in new_by_id.items():
            q = old_by_id.get(i)
            if q is None or role(p) == role(q):
                continue
            role_changes.append({"id": i, "n": p.get("name"), "tm": p.get("team"),
                                 "pos": p.get("pos"), "nyers": raw.get(str(i), 0),
                                 "szE": role(q), "szU": role(p),
                                 "ertE": q["week"], "ertU": p["week"]})
        # THE ROUNDING IS NOT DECORATION: the Hungarian-rule difference comes
        # from a floating-point subtraction, and -7.1e-15 would stand in the
        # file instead of 0 - rewritten on every run, and showing on the page
        # as "0,00" garbage.
        bonus = round((squad_total(new_k) - sum(p["week"] for p in new_k)) -
                      (squad_total(alt_k) - sum(p["week"] for p in alt_k)), 2)
        guard = round(squad_total(new_k) - squad_total(alt_k), 2)
        total = round(sum(x["ert"] for x in into) - sum(x["ert"] for x in out)
                      + sum(x["ertU"] - x["ertE"] for x in role_changes) + bonus, 2)
        # The order is by IMPACT, and deterministic (ties by name): the API's
        # squad order can change from run to run, and the file would then be
        # rewritten for no reason.
        out.sort(key=lambda x: (-x["ert"], x["n"] or ""))
        into.sort(key=lambda x: (-x["ert"], x["n"] or ""))
        role_changes.sort(key=lambda x: (-(x["ertU"] - x["ertE"]), x["n"] or ""))
        out_all[name] = {"guard": guard, "ki": out, "be": into, "szerep": role_changes,
                         "bonusz": bonus, "stimmel": abs(total - guard) < 0.005}
        if not out_all[name]["stimmel"]:
            print("  ! squad changes: round %d, %s - the items sum to %s,"
                  " the measure is %s" % (r, name, total, guard), file=sys.stderr)
    return out_all or None


def rounds_to_recheck(old_rounds, count=4):
    """Rolling check: every run re-fetches a different few OLD rounds. This
    way not all of them have to be queried on every run, yet within a day
    each one comes up - if the MLSZ corrects an old round after the fact,
    it is carried over within a day at the latest. (The two most recent
    rounds are checked by every run anyway.)"""
    if not old_rounds:
        return []
    n = len(old_rounds)
    start = (int(time.time() // 10800) * count) % n      # steps every 3 hours
    return sorted({old_rounds[(start + i) % n] for i in range(min(count, n))})


def set_result(schedule, r, name, value):
    """Writes one manager's round score into the schedule.
    Returns 1 if it actually changed."""
    for m in schedule.get(str(r)) or []:
        if m[0] == name and m[2] != value:
            m[2] = value
            return 1
        if m[1] == name and m[3] != value:
            m[3] = value
            return 1
    return 0


def match_summary(g):
    """The stored form of a match for meccsek.json. A SCORE GOES IN ONLY FOR
    A FINISHED MATCH: during a match the MLSZ may give a partial score, and
    the collector, which runs hourly on match days, would immortalise it as
    final - the
    same error as the 0-0 in results.json."""
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


def collect_matches(payload, round_no, store):
    """Puts the matches travelling in the squad answer under store[game_id].
    Several players bring the same match - keying by id merges them. A match
    falling back from a LATER round does not go in, a RESCHEDULED one
    (earlier round's, played now) does - see games_of_round.
    It yields something only if games was requested at all."""
    for d in (payload or {}).get("data") or []:
        cr = (d.get("competition_player") or {}).get("current_round") or {}
        for g in games_of_round(cr.get("games"), round_no):
            if g.get("id") is None:
                continue
            store[g["id"]] = match_summary(g)


def efficiency(sq):
    """Line-up efficiency of a squad: (scored, possible) or None.

    RULE: the bench is mandatorily 1 goalkeeper + 1 defender + 1 midfielder
    + 1 forward - so there is NO choice of formation. The optimum is STILL
    not a per-position minimum: the Hungarian rule (+10 if the starters
    include at least 5 Hungarians and among them a u21 player) depends on
    WHO sits on the bench, so the 2x4x5x4 = ~160 bench combinations are all
    tried (cheap), and for each the best starter is made captain.

    The stored week is already a FINAL value (captain x2, bench x0.5 in it)
    - the raw points are recovered from the cap/sub flags. The scored value
    is squad_total (= the official round score, Hungarian rule included)."""
    if not sq or len(sq) != 15:
        return None
    positions = {}
    for p in sq:
        raw = float(p.get("week") or 0)
        if p.get("cap"):
            raw /= 2.0
        elif p.get("sub"):
            raw *= 2.0
        positions.setdefault(p.get("pos") or "?", []).append(
            (raw, bool(p.get("hun")), bool(p.get("hun") and p.get("u21"))))
    if len(positions) != 4 or any(len(v) < 2 for v in positions.values()):
        return None                     # not the expected 4-position squad template
    position_list = list(positions.values())
    best = None
    for bench_idx in itertools.product(*[range(len(a)) for a in position_list]):
        total = bench_half = 0.0
        cap = None
        hun = u21 = 0
        for a, bi in zip(position_list, bench_idx):
            for i, (raw, h, u) in enumerate(a):
                if i == bi:
                    bench_half += 0.5 * raw
                else:
                    total += raw
                    if cap is None or raw > cap:
                        cap = raw
                    if h:
                        hun += 1
                    if u:
                        u21 += 1
        s = total + bench_half + cap + (10 if (hun >= 5 and u21 >= 1) else 0)
        if best is None or s > best:
            best = s
    return round(squad_total(sq), 2), round(best, 2)


def player_roster():
    """The FULL MLSZ player roster - for the home page player list and search.

    One single request: `per_page=500` works on this endpoint (by default it
    would be 15 per page, 26 pages) - measured, see
    naplo/mlsz-player-list.txt. It CANNOT be filtered by round, so it gives
    only the current state; the profile collects the per-round points
    differently, only the season total is needed here.

    The `id` is THE SAME as the `id` of the squad records
    (competition_player.id) - measured too: for 102 of 102 saved players the
    same name stands on the same id, zero mismatches. Opening the profile
    relies on this.

    A player who has LEFT the league is no longer in the roster (5 such in
    the measurement), but is in the squad history - so the roster serves
    the search, not the profile: the profile also opens from the squad
    history.
    """
    status, payload = api_get(BASE + "players?include=team,position,summary_statistics"
                                     "&per_page=500")
    data = (payload or {}).get("data") if isinstance(payload, dict) else None
    if status != 200 or not isinstance(data, list) or not data:
        print("  ! player roster: HTTP %s - jatekosok.json unchanged" % status,
              file=sys.stderr)
        return None
    out = {}
    for p in data:
        cp = p.get("id")
        if not cp:
            continue
        po = p.get("position") or {}
        team = p.get("team") or {}
        ss = p.get("summary_statistics") or {}
        cr = p.get("current_round") or {}
        out[str(cp)] = {
            "n": player_name(p.get("first_name"), p.get("last_name"), "#%s" % cp),
            "t": team.get("short_name") or team.get("name") or "",
            "p": po.get("monogram") or po.get("name") or "",
            "u21": bool(p.get("is_u21")),
            "pts": ss.get("competition_points") or 0,
            # The CURRENT market price - not the round's (see README: the
            # saved price is always the price at the moment of the request).
            # The list needs exactly this: what it costs today.
            "ar": cr.get("market_price"),
        }
    return out


def closing_changes(old_round, new_round, store, today):
    """A points change AFTER THE MATCH ENDED, before the round is finalised.

    By the rules the points are set after every match, but the weekly total
    is FINAL only at the end of the round's last match day - in between the
    MLSZ can still adjust. Overwriting the stored value without keeping the
    change would lose it; afterwards it cannot be reconstructed.

    The store's shape follows the PL zarasok.json, so the page can use the
    same display:  {manager: {"pont": [{n,cp,pos,tm,elott,utan}]}}

    Only a player whose STORED record says the match has already ended
    (vege=True) is looked at: the points ticking during a match is not a
    change. The value is the player's OWN points (captain doubling and bench
    halving undone, rounded to the quarter), so the same change does not
    look different depending on whose squad it was in."""
    def base(p):
        return round((p.get("week") or 0) / (2 if p.get("cap") else 1)
                     * (2 if p.get("sub") else 1) * 4) / 4

    count = 0
    for name_, old_sq in (old_round or {}).items():
        new_sq = (new_round or {}).get(name_)
        if not new_sq:
            continue
        new_by_key = {}
        for p in new_sq:
            new_by_key[p.get("id") or p.get("name")] = p
        for p in old_sq:
            if not p.get("vege"):
                continue                      # a change during the match is no news
            u = new_by_key.get(p.get("id") or p.get("name"))
            if not u or u.get("week") is None or p.get("week") is None:
                continue
            before, after = base(p), base(u)
            if abs(before - after) < 0.005:
                continue
            rows = store.setdefault(name_, {}).setdefault("pont", [])
            if any(x.get("cp") == p.get("id") and x.get("n") == p.get("name")
                   and abs(x.get("utan", 0) - after) < 0.005 for x in rows):
                continue                      # do not record the same run twice
            rows.append({"n": p.get("name"), "cp": p.get("id"),
                         "pos": u.get("pos") or p.get("pos") or "",
                         "tm": u.get("team") or p.get("team") or "",
                         "elott": before, "utan": after, "d": today})
            count += 1
    return count


def closed_rounds(schedule, provisional):
    """Which rounds are CLOSED - from the stored state, not from this run.

    It matters not to work from the run's `closed` dict: that only knows the
    rounds whose squads were fetched IN THIS run (the targets set), so never
    the older ones - on the first introduction a breakdown would have been
    made only for the last round. Closed is what has a result for every
    match AND is not among the provisional ones - exactly what the page
    treats as closed too."""
    prov = {int(x) for x in (provisional or [])}
    out = []
    for r, ms in (schedule or {}).items():
        if int(r) in prov or not ms:
            continue
        if all(m[2] is not None and m[3] is not None for m in ms):
            out.append(int(r))
    return sorted(out)


def filter_breakdown(rows):
    """What has to be STORED of a breakdown.

    The MLSZ returns all 22 stat rows for every player who played, the zero
    ones too - for 385 players that is 141 KB per round, 4.5 MB by the end
    of the season. The page shows only the rows WORTH POINTS, plus the
    "Játszott perc" (minutes played) row (separately, without points, and
    the message logic decides on it). The other rows stand at zero points -
    they carry no information.

    This filtering is REVERSIBLE: the game-player-stats endpoint answers for
    old rounds too (the whole breakdown relies on that), so the omitted raw
    values can be fetched again at any time. That is why filtering is
    allowed - and why it was NOT allowed for the price log: nobody gives the
    price back retroactively. Size: 141 KB -> 40 KB per round (4.5 MB ->
    1.3 MB)."""
    return [x for x in rows if x.get("p") or x.get("n") == "Játszott perc"]


def fetch_breakdown(ids, r):
    """One round's breakdown for the given players: ({cp: rows}, error count)."""
    rows, errors = {}, 0
    for i, cp in enumerate(ids, 1):
        url = (ROOT + "game-player-stats?include=competition_stat_config"
               "&filter%5Bcompetition_player_id%5D=" + str(cp) +
               "&filter%5Bround_id%5D=" + str(rid(r)))
        status, payload = api_get(url)
        if status != 200 or payload is None:
            errors += 1
            continue
        rows[str(cp)] = filter_breakdown([
            {"n": (x.get("competition_stat_config") or {}).get("name") or "?",
             "v": x.get("value"), "p": x.get("points")}
            for x in (payload.get("data") or [])])
        if len(ids) > 50 and i % 100 == 0:
            print("    %d/%d" % (i, len(ids)))
    return rows, errors


def collect_breakdowns(closed, changed, roster, extra=()):
    """The ITEMISED points breakdown of the closed rounds into the repository
    (bontasok/<r>.json).

    WHY: the breakdown ("what made up the 9.75 points") would otherwise be
    fetched ONLY by the browser, on click, with a live MLSZ call. If the
    MLSZ or the proxy is unreachable at that moment, the dropdown shows an
    error - yet the breakdown of a closed round never changes again, so it
    can be fetched once and kept. This way a closed round's breakdown comes
    from the repository: it opens at once, independent of the network, and
    the profile of a never-owned player does not fire one live request per
    round either.

    WHY THE WHOLE FIELD (385 players), not only the owned ones: the profile
    of any player can be opened from the home page player list. The
    collector requests the MLSZ DIRECTLY from the GitHub server (no CORS, no
    proxy), so this burdens none of our quotas - only a one-off ~3 minutes
    of run time per round.

    WHEN: ONCE per round, at closing - or again if that round's result
    changed meanwhile (MLSZ correction). As long as the file exists and the
    round has not moved, nothing is fetched.

    AN INCOMPLETE RUN IS NOT WRITTEN: if the request fails for more than 10%
    of the players, the file is not created, and the next run retries. A
    half-finished file is worse than a missing one - it would never be
    retried.

    `extra` IS THE PLAYERS ALREADY GONE FROM THE ROSTER BUT ONCE OWNED. The
    roster (`players` endpoint) gives only the CURRENT field: whoever left
    the league drops out of it - but stays in the squad history. Leaving
    them out of the breakdown has a CONSEQUENCE: the Guardiola measure
    would count such a player of last week's squad with 0 points although
    he played (Skribek scored 3.25 raw points in rounds 1 and 3), and the
    measure would slip in favour of whoever had just sold such a player.

    SO AN EXISTING FILE IS COMPLETED TOO - but only with the MISSING players
    (a few requests per round), not by re-fetching all 385: the other rows
    of a closed round do not change, fetching them again would be 3 minutes
    of run time for nothing."""
    if not roster:
        return 0
    os.makedirs("bontasok", exist_ok=True)
    ids = sorted(set(roster) | {str(x) for x in extra}, key=lambda x: int(x))
    written = 0
    for r in closed:
        path = os.path.join("bontasok", "%d.json" % r)
        existing = None
        if os.path.exists(path) and r not in changed:
            try:
                with open(path, encoding="utf-8") as f:
                    existing = json.load(f).get("bontasok") or {}
            except Exception:
                existing = None          # unreadable file -> full re-fetch
        if existing is not None:
            missing = [cp for cp in ids if cp not in existing]
            if not missing:
                continue
            print("  breakdowns: round %d, filling in %d missing players"
                  % (r, len(missing)))
            rows, errors = fetch_breakdown(missing, r)
            if not rows:
                print("  ! breakdowns: filling in round %d failed (%d requests),"
                      " the next run retries" % (r, errors), file=sys.stderr)
                continue
            existing.update(rows)
            write_compact(path, {"round": r, "bontasok": existing})
            written += 1
            print("  bontasok/%d.json completed (+%d players%s)"
                  % (r, len(rows), ", %d failed" % errors if errors else ""))
            continue
        print("  breakdowns: round %d, fetching %d players%s"
              % (r, len(ids), " (again: the result changed)" if r in changed else ""))
        rows, errors = fetch_breakdown(ids, r)
        if errors > len(ids) // 10:
            print("  ! breakdowns: round %d skipped - %d/%d requests failed,"
                  " the next run retries" % (r, errors, len(ids)), file=sys.stderr)
            continue
        # The `updated` field is left out ON PURPOSE - for the same reason as
        # in the keretek/ files: a closed round's breakdown does not change,
        # and a timestamp would rewrite the file on every run.
        write_compact(path, {"round": r, "bontasok": rows})
        written += 1
        print("  bontasok/%d.json written (%d players%s)"
              % (r, len(rows), ", %d failed" % errors if errors else ""))
    return written


def update_price_log(roster, today):
    """Logging the price changes (arak.json).

    Nothing uses it today - it is collected because it CANNOT be backfilled:
    the API gives only the CURRENT price and stores the past nowhere. What
    is not recorded today is lost for good.

    Only a CHANGE is recorded, not every run: the collector runs hourly on
    match days (every 3 hours on Tuesday and Wednesday), so the file would
    grow by up to 24 unchanged entries a day. A
    player's row is therefore [[date, price], ...], and a new element is
    added only if the price differs from the last recorded one.

    A missing or zero price is NOT taken as a change: an API error thus
    does not write a false "dropped to 0" entry (the same logic as the 0-0
    guard for results.json).
    """
    log = read_stored("arak.json", {}).get("arak") or {}
    changed = 0
    for cp, rec in roster.items():
        price = rec.get("ar")
        if not isinstance(price, (int, float)) or price <= 0:
            continue
        row = log.setdefault(cp, [])
        if row and row[-1][1] == price:
            continue
        row.append([today, price])
        changed += 1
    return log, changed


def main():
    with open("results.json", encoding="utf-8") as f:
        data = json.load(f)
    schedule = data["schedule"]
    # Which round stood in the table as FINAL ALREADY BEFORE THE RUN?
    # (Every match has a result, and it was not in the provisional list.)
    # Recorded BEFORE any writes: the uncertain branch relies on it.
    was_final = {int(r) for r, ms in schedule.items()
                 if ms and all(m[2] is not None and m[3] is not None for m in ms)
                 and int(r) not in {int(x) for x in (data.get("provisional") or [])}}
    hist = read_stored("squad_history.json", {"updated": None, "rounds": {}})
    hist.setdefault("rounds", {})
    closings_nb1 = read_stored("zarasok_nb1.json", {})
    closings_nb1.setdefault("rounds", {})
    closings_nb1_changed = False
    # An early format stored TEAM-LEVEL rows (in a list, {"mgr":...}),
    # without players. Those cannot be broken down to players retroactively
    # (the player-level snapshots all hold the already corrected value), and
    # the panel cannot display them either - they are dropped, so the old
    # shape does not stop the run.
    for _r in [k for k, v in closings_nb1["rounds"].items() if not isinstance(v, dict)]:
        del closings_nb1["rounds"][_r]
        closings_nb1_changed = True
    hist_before = json.dumps(hist.get("rounds"), ensure_ascii=False, sort_keys=True)
    matches_file = read_stored("meccsek.json", {"updated": None, "rounds": {}})
    matches_file.setdefault("rounds", {})
    matches_before = json.dumps(matches_file["rounds"], ensure_ascii=False, sort_keys=True)

    # ---- 1. Ids and the fresh official points ----
    ids, points = {}, {n: {} for n in MEMBERS}
    for name, uname in MEMBERS.items():
        row = rankings(uname)
        if not row:
            print("  ! no rankings data: %s" % name, file=sys.stderr)
            continue
        uid = ((row.get("user_team") or {}).get("user") or {}).get("id")
        if uid is None:
            # without an id every later request would go out as user_id=None
            print("  ! no user id: %s" % name, file=sys.stderr)
            continue
        ids[name] = uid
        points[name].update(round_points(row))
    if not ids:
        print("No data available - the files are unchanged.")
        return 0
    current = max((r for p in points.values() for r in p), default=0)
    print("  current round: %d | ids: %d/%d" % (current, len(ids), len(MEMBERS)))

    # ---- 2. Backfilling missed old rounds (filter[round_id]) ----
    # By default the rankings give only the recent rounds; if an older
    # round's result is missing (e.g. after an outage of several days), it
    # has to be requested separately. Normally this list is empty.
    missing = sorted({int(r) for r, ms in schedule.items()
                      if int(r) < current and any(m[2] is None for m in ms)})
    # By default the rankings give only the two most recent rounds, so a
    # later MLSZ correction of an old round would not be noticed on its own.
    # So a few old rounds are re-fetched each time (see rounds_to_recheck).
    recheck = rounds_to_recheck([r for r in range(1, max(current - 1, 1))])
    for r in sorted(set(missing) | set(recheck)):
        print("  %s: official points of round %d"
              % ("backfill" if r in missing else "recheck", r))
        for name, uname in MEMBERS.items():
            row = rankings(uname, round_id=rid(r))
            if not row:
                continue
            # the endpoint is the truth: overwrite, do not only fill in
            points[name].update(round_points(row))

    # ---- 3. Syncing the results (the endpoint is the truth) ----
    added, corrected = 0, 0
    changed = set()          # the squads of these rounds are stale too
    for rnd, matches in schedule.items():
        r = int(rnd)
        for m in matches:
            hp, vp = points.get(m[0], {}).get(r), points.get(m[1], {}).get(r)
            if hp is None or vp is None:
                continue
            if not hp and not vp:          # 0-0 = the round has not even started
                continue
            if m[2] == hp and m[3] == vp:
                continue
            previous = None if m[2] is None else (m[2], m[3])
            m[2], m[3] = hp, vp
            if previous is None:
                added += 1
                print("  + round %d: %s %s - %s %s" % (r, m[0], hp, vp, m[1]))
            else:
                corrected += 1
                changed.add(r)
                print("  ~ round %d: %s %s - %s %s  (was: %s - %s) - MLSZ correction"
                      % (r, m[0], hp, vp, m[1], previous[0], previous[1]))

    # ---- 4. Collecting the squads ----
    # Target rounds: the current one (if it has started), the last closed
    # one (so later MLSZ corrections come through), and whatever is missing
    # from the history.
    targets = set()
    if current >= 1:
        targets.add(current)
    if current >= 2:
        targets.add(current - 1)
    for r in range(1, current + 1):
        stored = hist["rounds"].get(str(r)) or {}
        if len(stored) < len(MEMBERS):
            targets.add(r)
    # if an old round's official points changed now, the squads of that
    # round are stale too - they have to be fetched again
    targets |= changed
    # BACKFILLING THE OLD FORMAT. The earliest squad records have no "id",
    # "played" and "start" yet - so the page has to make a pre-request for
    # the points breakdown, and the "no match" flag is missing altogether
    # (for the round 3 ETO players the page therefore said the match had not
    # started yet, with an already past placeholder date). Such a round is
    # fetched once more - together with the match list, so nogame can go in
    # too. After that the condition no longer holds, so it does not repeat.
    to_migrate = {int(r) for r, round_squads in hist["rounds"].items()
                  if round_squads and any("played" not in p
                                          for sq in round_squads.values() for p in sq)}
    if to_migrate:
        print("  backfilling old-format squads: round %s"
              % ", ".join(str(x) for x in sorted(to_migrate)))
    targets |= to_migrate
    # BACKFILLING MATCHES for meccsek.json: a round needs it if no match of
    # it is stored yet, or it has a match without a result (not finished).
    # The live round goes with the match list anyway; for old ones this is a
    # one-off large request (next to a finished match the API loads the club
    # logos too), after which the condition no longer holds.
    # A match with a "?" club is incomplete too. Otherwise: if ALL matches
    # of a round finished while the club names were still "?", the round
    # would leave the set of rounds to re-fetch, and once the MLSZ moves on
    # it would NEVER be fetched again - the "?" would be stuck for good.
    matches_backfill = {r for r in range(1, current + 1)
                        if not matches_file["rounds"].get(str(r))
                        or any(not m.get("vege") or m.get("h") == "?" or m.get("v") == "?"
                               for m in matches_file["rounds"][str(r)])}
    if matches_backfill - {current}:
        print("  backfilling matches: round %s"
              % ", ".join(str(x) for x in sorted(matches_backfill - {current})))
    targets |= matches_backfill

    # closed: r -> True/False, but ONLY if the data is complete. What could
    # not be evaluated (failed request, 403) goes into the `uncertain` set,
    # and there the round's earlier state stays in force. Otherwise a single
    # network error would either have counted the live round's partial
    # result as final (by emptying the provisional list), or made an already
    # closed round provisional - both give a wrong table.
    closed, uncertain = {}, set()
    mlsz_current, mlsz_ends = competition_rounds()
    print("  current round according to the MLSZ: %s"
          % (mlsz_current if mlsz_current else "not available"))
    for r in sorted(targets):
        # cheap pre-check with a single squad: 403 = the round is still secret
        first_id = next(iter(ids.values()))
        status, _ = squad(first_id, r)
        if status == 403:
            print("  . round %d squads not available yet (before the market closes)" % r)
            uncertain.add(r)
            continue
        new_round, complete = {}, True
        all_finished = True          # according to the match list every match has finished
        round_matches = {m["id"]: m for m in matches_file["rounds"].get(str(r)) or []
                         if m.get("id") is not None}
        # Whether the match list is requested for this round is decided in
        # ONE place - squad and inherit_match_flags use the same answer.
        needs_games = (r == current or r in to_migrate
                       or r in matches_backfill or r in changed)
        for name, uid in ids.items():
            # The match list is requested for the live round, when the old
            # format is being backfilled, when something is missing from
            # meccsek.json, OR when the round's official points changed now.
            # The last one is the RESCHEDULED MATCH case: the postponed match
            # is simply not in the list (not "without a result"), so the
            # matches_backfill condition would not notice it - but when it is
            # played the points surely change, because minutes earn points
            # too.
            status, payload = squad(uid, r, with_games=needs_games)
            if status != 200 or not isinstance(payload, dict) or not payload.get("data"):
                print("  ! round %d / %s: HTTP %s" % (r, name, status), file=sys.stderr)
                complete = False
                continue
            new_round[name] = [player_record(d, r) for d in payload["data"]]
            collect_matches(payload, r, round_matches)
            for d in payload["data"]:
                cr = (d.get("competition_player") or {}).get("current_round") or {}
                # is_played turns true already DURING the match - so it does
                # NOT imply that the round is over. Otherwise: as soon as the
                # round's last match kicked off, everyone "played", the
                # collector classed the round as closed, and the
                # half-finished result went into the table as final. The
                # match list's status is the handle; if it was not requested
                # (old round), is_played remains.
                # ...and only if the match really belongs to THIS round: the
                # state of a match falling back from another round says
                # nothing about this round.
                # EVERY match belonging here is checked, not only the first:
                # a rescheduled match can stand at the head of the list, and
                # then the club's REAL match of the round would never be
                # looked at - the round could be closed with a match not yet
                # played.
                if any(g.get("status") != "completed"
                       for g in games_of_round(cr.get("games"), r)):
                    all_finished = False
        if not new_round:
            uncertain.add(r)
            continue
        if round_matches:
            matches_file["rounds"][str(r)] = sorted(
                round_matches.values(), key=lambda m: (m.get("start") or "", m["h"]))
        old_round = hist["rounds"].get(str(r)) or {}
        # log the post-match points adjustment BEFORE the new overwrites the old
        round_closings = closings_nb1["rounds"].setdefault(str(r), {})
        closing_count = closing_changes(old_round, new_round, round_closings,
                                        time.strftime("%Y-%m-%d", time.gmtime()))
        if not round_closings:
            del closings_nb1["rounds"][str(r)]
        if closing_count:
            closings_nb1_changed = True
            print("  ! round %d: %d points adjustments after the match ended"
                  % (r, closing_count))
        inherit_match_flags(old_round, new_round, inherit=not needs_games)
        hist["rounds"][str(r)] = {**old_round, **new_round}
        # The "everyone played" check is decided from the ALREADY MERGED
        # records, not from the raw answer: the "no match" flag exists only
        # there. (The match list is requested only for the live round; after
        # that inherit_match_flags carries it over from the earlier
        # snapshot.)
        all_played = all(p.get("played") or p.get("nogame")
                         for sq in new_round.values() for p in sq)
        full_data = complete and len(new_round) == len(MEMBERS)
        safety_note = ""
        if full_data:
            done = all_played and all_finished
            # Safety net: if for some reason the player-level picture does
            # not come together, but the MLSZ has already moved past the
            # round, it is closed. This way a round cannot stay provisional
            # indefinitely.
            if not done and mlsz_round_over(r, mlsz_current, mlsz_ends):
                done, safety_note = True, " (closed according to the MLSZ)"
            closed[r] = done
        else:
            uncertain.add(r)
        print("  squads: round %d, %d/%d managers, %s%s"
              % (r, len(new_round), len(MEMBERS),
                 ("closed" if closed[r] else "still running") if full_data
                 else "INCOMPLETE data - the closed state stays unchanged", safety_note))

        # cross-check: makes sense only for a complete and already closed round
        if not (full_data and closed[r]):
            continue
        for name, sq in new_round.items():
            official = points.get(name, {}).get(r)
            if official in (None, 0):
                continue
            computed = squad_total(sq)
            if abs(computed - official) < 0.005:
                continue
            # The squad was refreshed in this run, so more likely the official
            # value is stale: request it again for this round, and if it
            # changed, carry it over. No flagging, but fixing.
            row = rankings(MEMBERS[name], round_id=rid(r))
            fresh = round_points(row).get(r)
            # A 0 of a closed round is a transient answer, never a correction:
            # writing it would record a zero for that manager.
            if fresh not in (None, 0) and abs(fresh - official) >= 0.005:
                points[name][r] = fresh
                corrected += set_result(schedule, r, name, fresh)
                # the round's breakdown and everything computed from it is
                # stale now, exactly as after a correction found in step 3
                changed.add(r)
                print("  ~ round %d / %s: official points updated %.2f -> %.2f"
                      % (r, name, official, fresh))
                official = fresh
            if abs(computed - official) >= 0.005:
                print("  ! MISMATCH round %d / %s: from squad %.2f, official %.2f"
                      " - the two sources disagree even after a re-fetch"
                      % (r, name, computed, official), file=sys.stderr)

    # ---- 5. Provisional rounds ----
    # Only a round that already has points, but where according to the
    # squads not every player has played yet, counts as provisional.
    #
    # The round limit is NOT decoration: with the rolling check, long closed
    # rounds can get among the `targets` (if the MLSZ corrected), and there a
    # single failed squad request would give `closed[r]=False`. Such a round
    # would wrongly look provisional, and the page would move it out of the
    # SCHEDULE into the live layer - a round played weeks earlier would
    # vanish from the table. Only the round being played now or one that has
    # just closed can be provisional.
    old_prov = {int(x) for x in (data.get("provisional") or [])}

    def has_points(r):
        return any(points.get(n, {}).get(r) for n in MEMBERS)

    prov = {r for r, done in closed.items()
            if not done and r >= current - 1 and has_points(r)}
    # Where we could not evaluate, we do not guess - but the mistakes are not
    # equal. If a recent round is wrongly written in as final, the
    # half-finished result enters the table (silent, plausible, wrong). If
    # wrongly as provisional, the round is left out for a while (visible,
    # and the next run fixes it). So a recent round stays provisional by
    # default, and an old one keeps its earlier state.
    for r in uncertain:
        if r in old_prov:
            prov.add(r)
        elif r != current and r in was_final:
            # An already CLOSED round stood as final - an incomplete run
            # (network error, partial answer) must not reopen it. Otherwise a
            # single DNS error would take a closed round out of the table
            # (e.g. "no rankings data: Katyul" -> the table shows the standing
            # of one round fewer).
            # For the LIVE round (r == current) this guard does NOT apply:
            # there the "final-looking" stored number can be a partial
            # result, and the worse error is to let it into the table.
            print("  . round %d: incomplete run, but it was already final - it stays so" % r)
        elif r >= current - 1 and has_points(r):
            prov.add(r)
    provisional = sorted(prov)

    # ---- 6. Write, only if changed ----
    # `provisional` is a LIST, `old_prov` a SET - the two are never equal, so
    # comparing them directly would always be true and results.json would be
    # rewritten on every run with a fresh timestamp only. The other files all
    # compare content - this one does the same.
    if added or corrected or set(provisional) != old_prov:
        data["provisional"] = provisional
        data["updated"] = stamp()
        # The same reason as for write_compact: with a cut-off results.json
        # the next run would not even start.
        with open("results.json.uj", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=0)
            f.flush()
            os.fsync(f.fileno())
        os.replace("results.json.uj", "results.json")
        print("  results.json updated")

    # ---- Line-up efficiency: recomputed for every stored round.
    # Deterministic and cheap (a few hundred records), so no state is kept
    # for it: as long as the squads do not change, neither does the file. The
    # live round's value still changes - the page decides that the table
    # takes only the closed one.
    eff = {}
    for r_, round_squads in hist["rounds"].items():
        row = {}
        for name_, sq_ in (round_squads or {}).items():
            e_ = efficiency(sq_)
            if e_:
                row[name_] = {"sz": e_[0], "le": e_[1]}
        if row:
            eff[r_] = row
    try:
        with open("hatekonysag.json", encoding="utf-8") as f:
            eff_old = json.load(f).get("rounds")
    except Exception:
        eff_old = None
    if json.dumps(eff, ensure_ascii=False, sort_keys=True) !=             json.dumps(eff_old, ensure_ascii=False, sort_keys=True):
        write_compact("hatekonysag.json", {"updated": stamp(), "rounds": eff})
        print("  hatekonysag.json updated")

    # The roster is needed for the name rewrite too, so it is fetched BEFORE
    # the writes.
    roster = player_roster()
    # Bringing the stored names to the roster's form. Not only a one-off
    # migration (western -> Hungarian order): if the MLSZ ever corrects a
    # name, the old rounds follow too. The id is the handle, so there is no
    # name matching.
    if roster:
        renamed = 0
        for round_squads_ in hist["rounds"].values():
            for sq_ in (round_squads_ or {}).values():
                for p_ in sq_:
                    rec_ = roster.get(str(p_.get("id") or ""))
                    if rec_ and rec_["n"] and p_.get("name") != rec_["n"]:
                        p_["name"] = rec_["n"]
                        renamed += 1
        if renamed:
            print("  %d stored player names brought to the roster's form" % renamed)

    # The itemised breakdown of the closed rounds (bontasok/<r>.json). AFTER
    # the roster, because the player list comes from it; because of the
    # `changed` set a later MLSZ correction refreshes the breakdown too.
    if roster:
        # The players EVER OWNED are needed too, not only the current
        # roster: whoever left the league is no longer on the `players`
        # endpoint, but is in the squad history - and the Guardiola measure
        # reads their points from the breakdown as well.
        owned = {str(p.get("id")) for round_squads_ in hist["rounds"].values()
                 for sq_ in (round_squads_ or {}).values() for p in sq_
                 if p.get("id")}
        collect_breakdowns(closed_rounds(schedule, provisional), changed, roster,
                           owned - set(roster))

    # ---- Guardiola measure: recomputed per round, like the efficiency.
    # Made only for a round that ALREADY HAS a breakdown (so it is closed)
    # and has a previous round's squad - for the first one it conceptually
    # does not exist.
    #
    # IT STANDS AFTER THE BREAKDOWN COLLECTION, NOT BEFORE IT. Before it, a
    # breakdown freshly filled in during a run would not count yet: the
    # measure would LAG BY ONE and only the next run would put it right (the
    # backfill goes out, guardiola.json stays unchanged). So the order is
    # not a matter of taste.
    gua = {}
    for r_ in sorted((int(x) for x in hist["rounds"]), reverse=False):
        g_ = guardiola(hist["rounds"], r_)
        if g_:
            gua[str(r_)] = g_
    try:
        with open("guardiola.json", encoding="utf-8") as f:
            gua_old = json.load(f).get("rounds")
    except Exception:
        gua_old = None
    if json.dumps(gua, ensure_ascii=False, sort_keys=True) != \
       json.dumps(gua_old, ensure_ascii=False, sort_keys=True):
        write_compact("guardiola.json", {"updated": stamp(), "rounds": gua})
        print("  guardiola.json updated (%d rounds)" % len(gua))

    # ---- Squad changes (the "Valtoztatasok" tab). From the same loop and
    # with the same rounding as the Guardiola measure - the tab derives
    # exactly that, so the two files have to move together.
    changes = {}
    for r_ in sorted(int(x) for x in hist["rounds"]):
        k_ = squad_changes(hist["rounds"], r_)
        if k_:
            changes[str(r_)] = k_
    try:
        with open("keretvaltozasok.json", encoding="utf-8") as f:
            changes_old = json.load(f).get("rounds")
    except Exception:
        changes_old = None
    if json.dumps(changes, ensure_ascii=False, sort_keys=True) != \
       json.dumps(changes_old, ensure_ascii=False, sort_keys=True):
        write_compact("keretvaltozasok.json", {"updated": stamp(), "rounds": changes})
        print("  keretvaltozasok.json updated (%d rounds)" % len(changes))

    if json.dumps(matches_file["rounds"], ensure_ascii=False, sort_keys=True) != matches_before:
        matches_file["updated"] = stamp()
        write_compact("meccsek.json", matches_file)
        print("  meccsek.json updated")

    if json.dumps(hist.get("rounds"), ensure_ascii=False, sort_keys=True) != hist_before:
        hist["updated"] = stamp()
        write_compact("squad_history.json", {"updated": hist["updated"],
                                            "rounds": hist["rounds"]})
        last = max((int(r) for r in hist["rounds"]), default=0)
        # squads.json holds ONLY the last round, while the condition above
        # is true for a change in ANY round - a later correction of an old
        # round would rewrite the file with a new timestamp and unchanged
        # content. So the squads are compared separately, as for the other
        # outputs.
        new_squads = {"round": last, "squads": hist["rounds"].get(str(last)) or {}}
        try:
            with open("squads.json", encoding="utf-8") as f:
                old_squads = json.load(f)
            old_squads = {k: v for k, v in old_squads.items() if k != "updated"}
        except Exception:
            old_squads = None
        if json.dumps(old_squads, ensure_ascii=False, sort_keys=True) != \
           json.dumps(new_squads, ensure_ascii=False, sort_keys=True):
            # the field order stays (updated, round, squads) - otherwise the
            # next write would "change" the whole file because of the order
            write_compact("squads.json", {"updated": hist["updated"],
                                         "round": new_squads["round"],
                                         "squads": new_squads["squads"]})
        # Per-round squad files. The full history grows by ~19 KB per round,
        # ~630 KB by the end of the season - the page does not need all of it
        # to open one match. The `updated` field is left out of them ON
        # PURPOSE: with a timestamp written on every run, all 33 files would
        # change every time, and the repository would grow needlessly. This
        # way a round's file changes only when its squads actually changed.
        os.makedirs("keretek", exist_ok=True)
        for r, round_squads in hist["rounds"].items():
            write_compact(os.path.join("keretek", "%s.json" % r),
                         {"round": int(r), "squads": round_squads})
        print("  squad_history.json + squads.json + keretek/ updated"
              " (last round: %d)" % last)

    # ---- Player roster (the home page list + search). One request per run.
    # The `updated` field is left out of the comparison, otherwise the file
    # would change every time even if not a single point moved.
    if roster is not None:
        try:
            with open("jatekosok.json", encoding="utf-8") as f:
                roster_old = json.load(f).get("players")
        except Exception:
            roster_old = None
        if json.dumps(roster, ensure_ascii=False, sort_keys=True) != \
           json.dumps(roster_old, ensure_ascii=False, sort_keys=True):
            write_compact("jatekosok.json", {"updated": stamp(), "players": roster})
            print("  jatekosok.json updated (%d players)" % len(roster))

    if closings_nb1_changed:
        closings_nb1["updated"] = stamp()
        write_compact("zarasok_nb1.json", closings_nb1)
        print("  zarasok_nb1.json updated")

    # ---- Price log: only the changes, because the past cannot be backfilled ----
    if roster is not None:
        prices, price_changes = update_price_log(roster, time.strftime("%Y-%m-%d", time.gmtime()))
        if price_changes:
            write_compact("arak.json", {"updated": stamp(), "arak": prices})
            print("  arak.json updated (%d price changes)" % price_changes)

    if provisional:
        print("  provisional (still running): round %s" % ", ".join(map(str, provisional)))
    print("Done: %d new, %d corrected results." % (added, corrected))
    return 0


if __name__ == "__main__":
    sys.exit(main())
