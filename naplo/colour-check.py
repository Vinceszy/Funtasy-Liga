#!/usr/bin/env python3
"""Checks a round's colour table - offline, against our own data.

It asserts four things:

1. Every `event` and `record` row finds its counterpart in the structured
   block (`matches`) of the same file: a goal (tags goal, goal_manner,
   luck), an assist (only where the block carries assists), a goal or VAR
   decision (disputed), a big chance (big_miss, only where the block carries
   them). If it does not, either the minute is wrong, or the player, or the
   claim did not happen. Other tags are not checked: the block does not hold
   them.
2. NB1 only: an `event` goal row's player has a goal in our stored
   breakdown (bontasok/<round>.json). Skipped while the round has no stored
   breakdown.
3. PL only, and only for rows that carry a `club`: the (player, club) pair is
   in somebody's squad that round exactly when the anchor is not `record`.
   A player nobody owns can only be `record`: we hold no data on him.
4. Every `statement` row names its speaker; every PL match has its kick-off
   time.

The two sources do not always agree on stoppage-time minutes (the text
commentary writes "45+2" where the shotmap writes 45), so the base minute
counts; an initial before the name ("N.Jackson") is cut off.

The two leagues' structured blocks differ: the NB1's comes from the formal
part of the Hungarian report (scorers, no VAR list, no shotmap), the PL's
from FotMob. What a block does not hold is not checked either - an admitted
limit is better than false safety. The kick-off time is expected only from
the PL table, because only there is it collected.

Usage: python3 naplo/colour-check.py <league> <round>
"""
import json
import os
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")


def plain(s):
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    first = s.split(".")[0]
    return s.split(".")[-1].strip() if 0 < len(first) <= 2 else s


def base_minute(p):
    return str(p).replace(" ", "").split("+")[0]


# OUR OWN data on the goals: bontasok/<round>.json lists item by item who
# scored points from what. An `event` goal row has to stand up to that too,
# not only to the table's own list of goals.
def _breakdown_scorers(rnd):
    """The NB1's own scorers from the stored breakdown. None if there is nothing to measure against."""
    path = os.path.join(HERE, "..", "bontasok", "%s.json" % rnd)
    if not os.path.exists(path):
        return None                      # nothing to measure against (not closed yet)
    with open(path, encoding="utf-8") as fh:
        b = json.load(fh).get("bontasok") or {}
    path2 = os.path.join(HERE, "..", "jatekosok.json")
    with open(path2, encoding="utf-8") as fh:
        roster = json.load(fh).get("players") or {}
    out = set()
    for cp, rows in b.items():
        if any((x.get("n") or "").startswith("Gól") and x.get("p") for x in rows):
            n = (roster.get(cp) or {}).get("n")
            if n:
                out.add(plain(n))
    return out


def match_key(name, matches):
    """'Man City 5-3 Sunderland' -> 'Man City - Sunderland'."""
    if name in matches:
        return name
    for k in matches:
        h, _, v = k.partition(" - ")
        if name.startswith(h) and name.endswith(v):
            return k
    return None


def squads(rnd):
    """(name, club) pairs that were in any squad in that round."""
    hist = json.load(open(os.path.join(ROOT, "draft_history.json"), encoding="utf-8"))
    players = json.load(open(os.path.join(ROOT, "draft_players.json"), encoding="utf-8"))["players"]
    out = set()
    for squad in (hist.get("rounds", {}).get(str(rnd), {}) or {}).values():
        for x in squad:
            j = players.get(str(x["e"])) or {}
            out.add((j.get("n"), j.get("t")))
    return out


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    league, rnd = sys.argv[1], sys.argv[2]
    path = os.path.join(HERE, "%s-colour-%s.json" % (league, rnd))
    d = json.load(open(path, encoding="utf-8"))
    matches = d.get("matches") or {}
    rows = d.get("claims") or []
    owned = squads(rnd) if league == "pl" else set()
    # OUR OWN scorers; None if there is no stored breakdown (round not
    # closed) - then there is nothing to measure against, and the row passes.
    # NB1 ONLY: bontasok/ and jatekosok.json are the NB1's data. Measuring the
    # PL against them would mean looking for an English scorer in the
    # Hungarian league's breakdown - every row would fail there.
    scorers = _breakdown_scorers(rnd) if league == "nb1" else None

    def has_scored(name):
        return scorers is None or plain(name or "") in scorers

    problems = []
    for s in rows:
        anchor, tag = s.get("anchor"), s.get("tag")
        if anchor == "statement":
            if not s.get("speaker"):
                problems.append("statement without a speaker: %s" % s.get("sentence"))
            continue

        if owned and s.get("club"):
            present = (s.get("player"), s.get("club")) in owned
            if present and anchor == "record":
                problems.append("%s (%s): in a squad, yet record" % (s["player"], s["club"]))
            if not present and anchor != "record":
                problems.append("%s (%s): in no squad, yet %s" % (s["player"], s["club"], anchor))

        if anchor not in ("event", "record"):
            continue
        k = match_key(s.get("match"), matches)
        if not k:
            problems.append("unknown match: %s" % s.get("match"))
            continue
        # The squad's name and the report's name can differ: the Draft keeps
        # the player under a short name ("Yeremy"), FotMob under his full one
        # ("Yeremi Pino"). The row's `source_name` then says whom to look for.
        m, p = matches[k], base_minute(s.get("minute"))
        name = plain(s.get("source_name") or s.get("player"))

        def in_goals(field="player"):
            return any(base_minute(g.get("minute")) == p and name in plain(g.get(field))
                       for g in m.get("goals") or [])

        if tag in ("goal", "goal_manner", "luck"):
            found = in_goals()
            # AND OUR OWN DATA TOO: the check above only measures the table
            # against itself, so a scorer entered under the wrong name passes
            # it. Round 9's Paks scorer was "Horvath K." - Kevin Horvath (PAKS) -
            # and he went into the table as Krisztofer Gyorgy Horvath (UJPEST),
            # whom two managers own. The table agreed with itself; the
            # breakdown knew that man had no goal.
            if found and anchor == "event" and not has_scored(s.get("player")):
                problems.append("%s: the table gives him a goal, the breakdown has none"
                                % s.get("player"))
        elif tag == "assist":
            # Assists are only tracked by a block that has such a field: the
            # formal part of the Hungarian report names the scorer, nothing else.
            has_field = any("assist" in g for g in m.get("goals") or [])
            found = in_goals("assist") if has_field else True
        elif tag == "disputed":
            found = in_goals() or any(
                base_minute(v.get("minute")) == p and name in plain(v.get("player"))
                for v in m.get("var") or [])
        elif tag == "big_miss":
            # The list of big chances exists only where a shotmap is collected.
            found = ("big_chances_missed" not in m) or any(
                base_minute(h.get("minute")) == p and name in plain(h.get("player"))
                for h in m["big_chances_missed"])
        else:
            # card, sub, milestone, history, match_picture: the block does not
            # hold them, so there is nothing to measure against.
            found = True
        if not found:
            problems.append("no cover: %s %s' %s (%s)" % (s.get("player"), s.get("minute"), tag, k))

    missing = [k for k, m in matches.items() if not m.get("kickoff")] if league == "pl" else []
    if missing:
        problems.append("match without kick-off time: %s" % ", ".join(sorted(missing)))

    print("%s round %s: %d rows, %d matches" % (league, rnd, len(rows), len(matches)))
    if problems:
        for b in problems:
            print("  - %s" % b)
        return 1
    print("  ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
