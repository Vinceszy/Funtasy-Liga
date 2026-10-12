#!/usr/bin/env python3
"""The first step of every Nemzethy Sport piece: rules, spent material, data.

A piece is not written from memory. This prints, in one go, everything a
piece has to be written from:

  1. the rule files IN FULL - the voice, the method and, for the column,
     its own recipe. Printing them is the point: whoever runs this has them
     in front of them, instead of relying on having read them once;
  2. what is already spent - the published pieces the new one may not
     repeat (the round's preview for a summary, the last round's summaries
     for a preview, the last column of the league for a column);
  3. the data:
       preview - a season mirror for every pairing of the round: margins,
                 where each finished in every round's score order, form,
                 season best, previous meetings, table position; for the
                 NB1 also what the two squads shared last round, and
                 whether the real fixtures of the round are recorded;
       summary - the round harvest (the fantasy layer), and whether the
                 round's colour table exists.

Usage: python3 naplo/cikk-elott.py <nb1|pl> <round> <summary|preview|column>
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

RULES = {
    "summary": ["summary-voice.md", "round-pipeline.md", "colour-taxonomy.md"],
    "preview": ["summary-voice.md", "round-pipeline.md"],
    "column": ["kele-janek.md", "round-pipeline.md"],
}
STORE_KIND = {"summary": "summary", "preview": "preview", "column": "elemzes"}


def load(name):
    with open(os.path.join(ROOT, name), encoding="utf-8") as f:
        return json.load(f)


def heading(text):
    print("\n" + "=" * 78 + "\n" + text + "\n" + "=" * 78)


def print_rules(kind):
    for name in RULES[kind]:
        heading("RULE FILE: naplo/" + name)
        with open(os.path.join(HERE, name), encoding="utf-8") as f:
            print(f.read())


def print_piece(title, piece):
    print("\n--- " + title)
    if piece.get("short"):
        print("  [lead] " + piece["short"])
    for paragraph in piece.get("text") or []:
        print("  " + paragraph)


def print_spent(league, rnd, kind):
    store = load("articles.json").get("leagues", {}).get(league, {})
    heading("SPENT - published pieces the new one may not repeat")
    shown = False
    if kind == "summary":
        for key, piece in (store.get(str(rnd), {}).get("preview") or {}).items():
            print_piece("preview %d. %s" % (rnd, key), piece)
            shown = True
    elif kind == "preview":
        for key, piece in (store.get(str(rnd - 1), {}).get("summary") or {}).items():
            print_piece("summary %d. %s" % (rnd - 1, key), piece)
            shown = True
    else:
        for r in sorted((int(x) for x in store), reverse=True):
            columns = store[str(r)].get("elemzes") or {}
            for key, piece in columns.items():
                print_piece("column %d. %s" % (r, key), piece)
                shown = True
            if columns:
                break
    if not shown:
        print("(nothing published to check against)")


# ---- the season, per league: [(round, home, away, home_pts, away_pts)] ----

def nb1_season():
    res = load("results.json")
    provisional = {int(x) for x in res.get("provisional") or []}
    out, upcoming = [], {}
    for r, games in (res.get("schedule") or {}).items():
        for h, v, hp, vp in games:
            if hp is None or vp is None or int(r) in provisional:
                upcoming.setdefault(int(r), []).append((h, v))
            else:
                out.append((int(r), h, v, hp, vp))
    return out, upcoming


def pl_season():
    draft = load("draft.json")
    final = set(load("draft_history.json").get("veglegesek") or [])
    name = {e["id"]: e["name"] for e in draft.get("entries") or []}
    out, upcoming = [], {}
    for r, games in (draft.get("schedule") or {}).items():
        for a, b, ap, bp in games:
            if int(r) in final and ap is not None and bp is not None:
                out.append((int(r), name.get(a, a), name.get(b, b), ap, bp))
            else:
                upcoming.setdefault(int(r), []).append((name.get(a, a), name.get(b, b)))
    return out, upcoming


def mirror(season, pairs):
    """Per manager: every result with its margin, the round rank, form."""
    games = {}
    by_round = {}
    for r, h, v, hp, vp in season:
        games.setdefault(h, []).append((r, v, hp, vp))
        games.setdefault(v, []).append((r, h, vp, hp))
        by_round.setdefault(r, []).extend([hp, vp])

    def rank(r, score):
        return 1 + sum(1 for s in by_round[r] if s > score)

    table = {}
    for m, gl in games.items():
        pts = sum(3 if a > b else 1 if a == b else 0 for _, _, a, b in gl)
        diff = sum(a - b for _, _, a, b in gl)
        scored = sum(a for _, _, a, _ in gl)
        table[m] = (pts, diff, scored)
    order = sorted(table, key=lambda m: table[m], reverse=True)

    heading("SEASON MIRROR - where the spine comes from")
    field = max(len(s) for s in by_round.values())
    print("table (points, then point difference, then points scored):")
    for i, m in enumerate(order, 1):
        p, d, s = table[m]
        print("  %d. %-24s %2d pts  diff %+7.2f  scored %7.2f" % (i, m, p, d, s))
    closest = sorted(season, key=lambda g: abs(g[3] - g[4]))[:6]
    print("closest matches of the season: " + "; ".join(
        "%d. %s-%s %.2f" % (r, h, v, abs(hp - vp)) for r, h, v, hp, vp in closest))

    for a, b in pairs:
        print("\n### %s - %s" % (a, b))
        for m in (a, b):
            gl = sorted(games.get(m, []))
            if not gl:
                print("  %s: no closed match yet" % m)
                continue
            line = " ".join("%d:%s%+.2f" % (r, "W" if x > y else "D" if x == y else "L", x - y)
                            for r, _, x, y in gl)
            ranks = [rank(r, x) for r, _, x, _ in gl]
            margins = [abs(x - y) for _, _, x, y in gl]
            streak, last = 0, None
            for _, _, x, y in reversed(gl):
                res = "W" if x > y else "D" if x == y else "L"
                if last is None or res == last:
                    streak, last = streak + 1, res
                else:
                    break
            best = max(gl, key=lambda g: g[2])
            print("  %s - table %d." % (m, order.index(m) + 1))
            print("    results:  " + line)
            print("    round rank (of %d): %s" % (field, ranks))
            print("    under 5 pts: %d of %d, median margin %.2f, current streak %d%s"
                  % (sum(x < 5 for x in margins), len(margins),
                     sorted(margins)[len(margins) // 2], streak, last))
            print("    season best %.2f (round %d), total %.2f"
                  % (best[2], best[0], sum(g[2] for g in gl)))
        met = [(r, x, y) for r, o, x, y in games.get(a, []) if o == b]
        print("  previous meetings: " + (", ".join(
            "%d. %.2f-%.2f" % (r, x, y) for r, x, y in met) or "none"))


def nb1_squads(rnd, pairs):
    hist = load("squad_history.json").get("rounds") or {}
    last = max((int(r) for r in hist if int(r) < rnd), default=None)
    heading("SQUADS, LAST ROUND (%s) - middle material, the state each "
            "manager decides FROM, never the coming line-up" % last)
    if last is None:
        return
    squads = hist[str(last)]
    for a, b in pairs:
        A = {p["id"]: p for p in squads.get(a) or []}
        B = {p["id"]: p for p in squads.get(b) or []}
        shared = sorted(set(A) & set(B))
        cap = lambda S: next((p["name"] for p in S.values() if p.get("cap")), "-")
        print("\n### %s - %s: %d shared, captains %s / %s"
              % (a, b, len(shared), cap(A), cap(B)))
        for i in shared:
            pa, pb = A[i], B[i]
            role = lambda p: "C" if p.get("cap") else "bench" if p.get("sub") else "XI"
            print("  %-28s %-8s %s / %s" % (pa["name"], pa.get("team", ""), role(pa), role(pb)))
    fixtures = os.path.join(HERE, "nb1-parositas-%d.txt" % rnd)
    print("\nreal NB I fixtures of round %d: %s" % (rnd, (
        "naplo/nb1-parositas-%d.txt" % rnd) if os.path.exists(fixtures) else
        "NOT RECORDED - look them up (two independent sources) and write "
        "naplo/nb1-parositas-%d.txt before writing" % rnd))


def run(script, *args):
    heading("DATA: naplo/%s %s" % (script, " ".join(args)))
    sys.stdout.flush()
    subprocess.run([sys.executable, os.path.join(HERE, script)] + list(args), check=False)


def main():
    if len(sys.argv) != 4 or sys.argv[1] not in ("nb1", "pl") \
            or sys.argv[3] not in RULES or not sys.argv[2].isdigit():
        sys.exit(__doc__)
    league, rnd, kind = sys.argv[1], int(sys.argv[2]), sys.argv[3]

    season, upcoming = nb1_season() if league == "nb1" else pl_season()
    pairs = upcoming.get(rnd) or []
    if kind == "preview" and not pairs:
        sys.exit("round %d has no open pairing - a preview is written for "
                 "the coming round only" % rnd)
    if kind == "summary" and not any(g[0] == rnd for g in season):
        sys.exit("round %d is not closed - a summary is written from a "
                 "final round only" % rnd)

    print_rules(kind)
    print_spent(league, rnd, kind)

    if kind == "preview":
        mirror(season, pairs)
        if league == "nb1":
            nb1_squads(rnd, pairs)
        else:
            run("draft-preview-harvest.py", str(rnd))
    elif kind == "summary":
        run("round-colour-harvest.py" if league == "nb1" else "draft-round-harvest.py",
            str(rnd))
        table = os.path.join(HERE, "%s-colour-%d.json" % (league, rnd))
        print("\ncolour table naplo/%s-colour-%d.json: %s" % (
            league, rnd, "present" if os.path.exists(table) else
            "MISSING - fetch the reports and fill it in the same step"))
    else:
        mirror(season, [])


if __name__ == "__main__":
    main()
