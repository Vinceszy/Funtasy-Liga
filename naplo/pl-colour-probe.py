#!/usr/bin/env python3
"""Where does Premier League colour come from?

The Hungarian side has a match report whose prose yields the categories in
colour-taxonomy.md. The English side has no such source wired up yet, and
"then we go without" is not an answer - a summary without colour is a table
with sentences around it.

This probe measures four candidates against the taxonomy:

  fotmob      structured, keyless. Already known to give per-minute events;
              the question here is whether its shotmap carries the MANNER of
              a goal, a missed big chance and a save - i.e. colour without
              any prose at all.
  pulselive   the league's own minute-by-minute text stream.
  guardian    the Content API (developer key "test" is public and documented).
  bbc         the report pages linked from a day's fixture list.

For every prose source the probe reports, per taxonomy tag, HOW MANY
sentences match it - and prints a few of those sentences to STANDARD OUTPUT
so they stay in the run log. Article text never enters the repository; the
log file gets urls, sizes and counts only.

Both filtered and unfiltered samples are printed. A filter that silently
matches nothing has fooled us before - an empty result must be visibly
empty, not absent.
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

AGENT = "FunTasy-survey (github.com/Vinceszy/Funtasy-Liga)"
LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pl-colour.txt")
DAYS = int(os.environ.get("PROBE_DAYS") or "10")

# The taxonomy's tags as English keywords. Deliberately broad: the probe asks
# whether there IS material, not for an exact classification.
TAGS = {
    "goal_manner": r"\b(header|headed|volley|bicycle kick|overhead kick|free[- ]kick|"
                   r"penalty|tap[- ]in|curled|curling|chipped|lobbed|drilled|thumped|"
                   r"side[- ]foot|back[- ]heel)\b",
    "luck":        r"\b(deflect\w*|rebound\w*|ricochet\w*|woodwork|the post|crossbar|"
                   r"own goal|fortunate|lucky|scuff\w*|fluke\w*)\b",
    "disputed":    r"\b(VAR|controversial|contentious|disallow\w*|offside|"
                   r"penalty appeal\w*|replays showed|harsh|should have been sent off|"
                   r"protest\w*|furious)\b",
    "big_miss":    r"\b(sitter|glaring miss|should have scored|squander\w*|wasted|"
                   r"open goal|somehow missed|blazed over|fired wide)\b",
    "keeper_save": r"\b(save[ds]?|parried|tipped (?:over|around|wide)|denied|"
                   r"palmed|one[- ]on[- ]one|point[- ]blank)\b",
    "match_picture": r"\b(dominat\w*|scrappy|end[- ]to[- ]end|cagey|tempo|"
                     r"pressure|sluggish|comfortable|one[- ]sided|stalemate)\b",
    "milestone":   r"\b(first goal|maiden|debut|milestone|hat[- ]trick|"
                   r"first time since|100th|50th)\b",
    "upset":       r"\b(upset|shock|giant[- ]killing|against the odds)\b",
    "history":     r"\b(unbeaten run|winless|streak|record|first win since|"
                   r"head[- ]to[- ]head)\b",
}


def fetch(url, extra_headers=None):
    headers = {"User-Agent": AGENT, "Accept": "*/*"}
    if extra_headers:
        headers.update(extra_headers)
    t = time.time()
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read(), int((time.time() - t) * 1000)
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:400], int((time.time() - t) * 1000)
    except Exception as e:                                   # noqa: BLE001
        return 0, ("%s: %s" % (type(e).__name__, e)).encode(), int((time.time() - t) * 1000)


def robots_allows(root, path):
    """The decision that applies to our own agent. The library rule is not
       used, because RobotFileParser's own 403 was once reported as the site's
       rule - so the raw text is interpreted here."""
    code, body, _ = fetch(root + "/robots.txt")
    if code != 200:
        return None, "robots.txt HTTP %s" % code
    text = body.decode("utf-8", "replace")
    disallowed, active = [], False
    for line in text.splitlines():
        s = line.split("#")[0].strip()
        if not s:
            continue
        k, _, v = s.partition(":")
        k, v = k.strip().lower(), v.strip()
        if k == "user-agent":
            active = v == "*"
        elif k == "disallow" and active and v:
            disallowed.append(v)
    blocking = [t for t in disallowed if path.startswith(t)]
    return (not blocking), ("disallowed by: %s" % blocking[0] if blocking else "no rule disallows it")


def plain_text(html):
    b = re.sub(r"(?is)<(script|style|nav|header|footer|aside)[^>]*>.*?</\1>", " ", html)
    b = re.sub(r"(?s)<[^>]+>", " ", b)
    for a, c in (("&nbsp;", " "), ("&amp;", "&"), ("&quot;", '"'), ("&#x27;", "'"),
                 ("&rsquo;", "'"), ("&eacute;", "e")):
        b = b.replace(a, c)
    return re.sub(r"\s+", " ", b).strip()


def sentences(t):
    return [m.strip() for m in re.split(r"(?<=[.!?])\s+", t) if 25 < len(m.strip()) < 400]


def tag_text(t, label):
    """How many sentences match per tag, and which. The matches go to STDOUT."""
    ms = sentences(t)
    found = {}
    for tag, pattern in TAGS.items():
        hit = [m for m in ms if re.search(pattern, m, re.I)]
        if hit:
            found[tag] = hit
    print("\n  == %s: %d sentences, %d tags matched ==" % (label, len(ms), len(found)))
    if not ms:
        print("     NO SENTENCES - extraction did not work on this page")
    for tag in TAGS:
        hit = found.get(tag, [])
        print("     %-14s %d" % (tag, len(hit)))
        for m in hit[:2]:
            print("        | %s" % m[:230])
    if ms:
        print("     -- unfiltered sample (first 3 sentences) --")
        for m in ms[:3]:
            print("        | %s" % m[:230])
    return {t: len(v) for t, v in found.items()}, len(ms)


def robots_word(allowed):
    return "ALLOWS" if allowed else "DISALLOWS" if allowed is False else "?"


# ---------------------------------------------------------------- fotmob
def fotmob(out):
    out.append("")
    out.append("--- fotmob: structured colour without a prose source ---")
    allowed, why = robots_allows("https://www.fotmob.com", "/api/data/matchDetails")
    out.append("  robots: %s (%s)" % (robots_word(allowed), why))
    if allowed is False:
        return
    match = None
    for day in range(1, DAYS + 1):
        d = time.strftime("%Y%m%d", time.gmtime(time.time() - day * 86400))
        code, body, ms = fetch("https://www.fotmob.com/api/data/matches?date=" + d)
        if code != 200:
            out.append("  %s: HTTP %s (%d ms)" % (d, code, ms))
            continue
        try:
            j = json.loads(body)
        except Exception:                                    # noqa: BLE001
            out.append("  %s: not json" % d)
            continue
        leagues = []
        for lg in j.get("leagues", []):
            leagues.append("%s / %s" % (lg.get("ccode"), lg.get("name")))
            if lg.get("ccode") == "ENG" and lg.get("name") == "Premier League":
                for m in lg.get("matches", []):
                    if (m.get("status") or {}).get("finished"):
                        match = (str(m.get("id")), m.get("home", {}).get("name"),
                                 m.get("away", {}).get("name"), d)
                        break
        out.append("  %s: %d leagues, finished PL match: %s" % (d, len(leagues), bool(match)))
        if not match and day == 1:
            out.append("    leagues seen that day (first 8): %s" % "; ".join(leagues[:8]))
        if match:
            break
    if not match:
        out.append("  NO finished PL match in the last %d days" % DAYS)
        return
    mid, h, v, d = match
    out.append("  match: %s - %s (%s, id=%s)" % (h, v, d, mid))
    code, body, ms = fetch("https://www.fotmob.com/api/data/matchDetails?matchId=" + mid)
    out.append("  matchDetails: HTTP %s, %d kb, %d ms" % (code, len(body) // 1024, ms))
    if code != 200:
        return
    j = json.loads(body)
    content = j.get("content") or {}
    out.append("  content keys: %s" % ", ".join(sorted(content.keys())))
    # 1) events
    ev = ((content.get("matchFacts") or {}).get("events") or {}).get("events") or []
    types = sorted({str(e.get("type")) for e in ev})
    out.append("  events: %d, types: %s" % (len(ev), ", ".join(types)))
    goal_keys = set()
    for e in ev:
        if e.get("type") == "Goal":
            goal_keys |= {k for k, x in e.items() if x not in (None, "", [], {})}
    out.append("  GOAL event keys: %s" % ", ".join(sorted(goal_keys)))
    print("\n  == fotmob goals (raw) ==")
    for e in ev:
        if e.get("type") == "Goal":
            print("     | %s" % json.dumps(e, ensure_ascii=False)[:400])
    # 2) shotmap: the MANNER of a goal, the missed big chance, the save
    sm = content.get("shotmap") or {}
    shots = sm.get("shots") if isinstance(sm, dict) else None
    if not isinstance(shots, list):
        shots = []
    out.append("  shotmap: %d shots" % len(shots))
    if shots:
        out.append("  shot keys: %s" % ", ".join(sorted(shots[0].keys())))
        for field in ("situation", "shotType", "eventType"):
            values = sorted({str(x.get(field)) for x in shots if x.get(field) is not None})
            out.append("    %-10s: %s" % (field, ", ".join(values) or "(none)"))
        big = [x for x in shots
               if (x.get("expectedGoals") or 0) >= 0.3 and str(x.get("eventType")) != "Goal"]
        out.append("    xG>=0.3 but no goal (missed big chance): %d" % len(big))
        saves = [x for x in shots if "save" in str(x.get("eventType")).lower()]
        out.append("    save-like events: %d" % len(saves))
        print("\n  == fotmob shotmap (first 5 shots, raw) ==")
        for x in shots[:5]:
            print("     | %s" % json.dumps({k: x.get(k) for k in
                  ("min", "playerName", "situation", "shotType", "eventType",
                   "expectedGoals", "isBlocked", "isOnTarget")}, ensure_ascii=False))
    # 3) whether there is prose commentary as well
    for key in ("liveticker", "commentary", "matchFacts"):
        r = content.get(key)
        if isinstance(r, dict):
            out.append("  %s subkeys: %s" % (key, ", ".join(sorted(r.keys()))[:200]))
    return match


# ---------------------------------------------------------------- pulselive
def pulselive(out):
    out.append("")
    out.append("--- premierleague (pulselive): the league's own minute-by-minute commentary ---")
    headers = {"Origin": "https://www.premierleague.com",
               "Referer": "https://www.premierleague.com/"}
    code, body, ms = fetch(
        "https://footballapi.pulselive.com/football/competitions/1/compseasons", headers)
    out.append("  compseasons: HTTP %s (%d ms)" % (code, ms))
    if code != 200:
        return
    j = json.loads(body)
    ids = [(str(c.get("id")).split(".")[0], c.get("label")) for c in j.get("content", [])]
    out.append("  latest seasons: %s" % "; ".join("%s=%s" % (b, a) for a, b in ids[:3]))
    if not ids:
        return
    sid = ids[0][0]
    url = ("https://footballapi.pulselive.com/football/fixtures?comps=1&compSeasons=%s"
           "&statuses=C&page=0&pageSize=5&sort=desc" % sid)
    code, body, ms = fetch(url, headers)
    out.append("  completed matches: HTTP %s (%d ms)" % (code, ms))
    if code != 200:
        out.append("  response: %s" % body[:160].decode("utf-8", "replace"))
        return
    fx = json.loads(body).get("content", [])
    out.append("  matches received: %d" % len(fx))
    if not fx:
        return
    f = fx[0]
    fid = str(f.get("id")).split(".")[0]
    teams = " - ".join((t.get("team") or {}).get("name", "?") for t in f.get("teams", []))
    out.append("  match: %s (id=%s)" % (teams, fid))
    for path in ("/football/fixtures/%s/textstream/EN?pageSize=200" % fid,
                 "/football/fixtures/%s/textstream/EN" % fid):
        code, body, ms = fetch("https://footballapi.pulselive.com" + path, headers)
        out.append("  textstream %s: HTTP %s, %d kb (%d ms)" % (path.split("?")[0][-30:], code,
                                                                len(body) // 1024, ms))
        if code == 200:
            try:
                e = json.loads(body).get("events", {}).get("content", [])
            except Exception:                                # noqa: BLE001
                e = []
            out.append("    entries: %d" % len(e))
            t = " ".join(x.get("text") or "" for x in e)
            if t.strip():
                counts, n = tag_text(t, "pulselive textstream")
                out.append("    tags: %s" % (json.dumps(counts) if counts else "NO MATCH"))
                out.append("    sentences: %d" % n)
            else:
                out.append("    NO text in the response")
            break


# ---------------------------------------------------------------- guardian
def guardian(out, match):
    out.append("")
    out.append("--- guardian content api (developer key: test) ---")
    allowed, why = robots_allows("https://content.guardianapis.com", "/search")
    out.append("  robots: %s (%s)" % (robots_word(allowed), why))
    if allowed is False:
        return
    q = "premier league match report"
    if match:
        q = "%s %s" % (match[1], match[2])
    url = ("https://content.guardianapis.com/search?q=%s&section=football"
           "&show-fields=bodyText&page-size=3&api-key=test"
           % urllib.parse.quote(q))
    code, body, ms = fetch(url)
    out.append("  search (%s): HTTP %s, %d kb (%d ms)" % (q, code, len(body) // 1024, ms))
    if code != 200:
        out.append("  response: %s" % body[:200].decode("utf-8", "replace"))
        return
    r = json.loads(body).get("response", {})
    articles = r.get("results", [])
    out.append("  hits: %s, returned: %d" % (r.get("total"), len(articles)))
    for c in articles[:2]:
        t = (c.get("fields") or {}).get("bodyText") or ""
        out.append("    %s | %d characters" % (c.get("webTitle", "?")[:70], len(t)))
        if t:
            counts, n = tag_text(t, "guardian: " + c.get("webTitle", "?")[:50])
            out.append("      tags: %s" % (json.dumps(counts) if counts else "NO MATCH"))


# ---------------------------------------------------------------- bbc
def bbc(out):
    out.append("")
    out.append("--- bbc sport ---")
    allowed, why = robots_allows("https://www.bbc.com", "/sport/football")
    out.append("  robots: %s (%s)" % (robots_word(allowed), why))
    if allowed is False:
        return
    for day in range(1, DAYS + 1):
        d = time.strftime("%Y-%m-%d", time.gmtime(time.time() - day * 86400))
        url = "https://www.bbc.com/sport/football/premier-league/scores-fixtures/" + d
        code, body, ms = fetch(url)
        if code != 200:
            out.append("  %s: HTTP %s (%d ms)" % (d, code, ms))
            continue
        html = body.decode("utf-8", "replace")
        links = sorted(set(re.findall(r'"(/sport/football/(?:articles|live)/[a-z0-9]+)"', html)))
        out.append("  %s: HTTP 200, %d kb, article links: %d" % (d, len(body) // 1024, len(links)))
        if not links:
            continue
        for l in links[:1]:
            code2, body2, ms2 = fetch("https://www.bbc.com" + l)
            out.append("    %s: HTTP %s, %d kb (%d ms)" % (l, code2, len(body2) // 1024, ms2))
            if code2 == 200:
                t = plain_text(body2.decode("utf-8", "replace"))
                counts, n = tag_text(t, "bbc " + l)
                out.append("      tags: %s" % (json.dumps(counts) if counts else "NO MATCH"))
        break


def main():
    out = ["", "=" * 70,
           "PROBE: %s UTC | Premier League colour sources" % time.strftime("%Y-%m-%d %H:%M")]
    match = None
    for f in (lambda: fotmob(out),):
        try:
            match = f()
        except Exception as e:                               # noqa: BLE001
            out.append("  ERROR: %s: %s" % (type(e).__name__, e))
    for f in (lambda: pulselive(out), lambda: guardian(out, match), lambda: bbc(out)):
        try:
            f()
        except Exception as e:                               # noqa: BLE001
            out.append("  ERROR: %s: %s" % (type(e).__name__, e))
    text_out = "\n".join(out) + "\n"
    print(text_out)
    header = ("Premier League colour sources probe.\n"
              "Written by naplo/pl-colour-probe.py. It stores NO article text:\n"
              "the matching sentences are visible only in the run log (stdout).\n")
    old = ""
    if os.path.exists(LOG):
        old = open(LOG, encoding="utf-8").read()
    else:
        old = header
    open(LOG, "w", encoding="utf-8").write(old.rstrip("\n") + "\n" + text_out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
