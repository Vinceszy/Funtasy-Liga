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
NAPOK = int(os.environ.get("PROBE_DAYS") or "10")

# A taxonomia cimkei angol kulcsszavakkal. Szandekosan bo: a meres arra megy,
# hogy VAN-E anyag, nem arra, hogy pontosan osztalyozzon.
CIMKEK = {
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


def keres(url, fejlec=None):
    fej = {"User-Agent": AGENT, "Accept": "*/*"}
    if fejlec:
        fej.update(fejlec)
    t = time.time()
    req = urllib.request.Request(url, headers=fej)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read(), int((time.time() - t) * 1000)
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:400], int((time.time() - t) * 1000)
    except Exception as e:                                   # noqa: BLE001
        return 0, ("%s: %s" % (type(e).__name__, e)).encode(), int((time.time() - t) * 1000)


def robots_engedi(gyoker, ut):
    """A sajat ugynokunkre vonatkozo dontes. A konyvtar-szabalyt kulon irjuk ki,
       mert a RobotFileParser sajat 403-at mar egyszer a site szabalyakent
       jelentettuk - ezert itt a nyers szoveget ertelmezzuk."""
    code, body, _ = keres(gyoker + "/robots.txt")
    if code != 200:
        return None, "robots.txt HTTP %s" % code
    szoveg = body.decode("utf-8", "replace")
    tilt, aktiv = [], False
    for sor in szoveg.splitlines():
        s = sor.split("#")[0].strip()
        if not s:
            continue
        k, _, v = s.partition(":")
        k, v = k.strip().lower(), v.strip()
        if k == "user-agent":
            aktiv = v == "*"
        elif k == "disallow" and aktiv and v:
            tilt.append(v)
    rossz = [t for t in tilt if ut.startswith(t)]
    return (not rossz), ("tiltja: %s" % rossz[0] if rossz else "nincs ra tilto szabaly")


def szoveg(html):
    b = re.sub(r"(?is)<(script|style|nav|header|footer|aside)[^>]*>.*?</\1>", " ", html)
    b = re.sub(r"(?s)<[^>]+>", " ", b)
    for a, c in (("&nbsp;", " "), ("&amp;", "&"), ("&quot;", '"'), ("&#x27;", "'"),
                 ("&rsquo;", "'"), ("&eacute;", "e")):
        b = b.replace(a, c)
    return re.sub(r"\s+", " ", b).strip()


def mondatok(t):
    return [m.strip() for m in re.split(r"(?<=[.!?])\s+", t) if 25 < len(m.strip()) < 400]


def cimkez(t, cimke):
    """Cimkenkent hany mondat talal, es melyek. A talalatok a STDOUT-ra mennek."""
    ms = mondatok(t)
    talalt = {}
    for tag, minta in CIMKEK.items():
        hit = [m for m in ms if re.search(minta, m, re.I)]
        if hit:
            talalt[tag] = hit
    print("\n  == %s: %d mondat, %d cimke talalt ==" % (cimke, len(ms), len(talalt)))
    if not ms:
        print("     NINCS MONDAT - a kinyeres nem mukodott ezen az oldalon")
    for tag in CIMKEK:
        hit = talalt.get(tag, [])
        print("     %-14s %d" % (tag, len(hit)))
        for m in hit[:2]:
            print("        | %s" % m[:230])
    if ms:
        print("     -- szuretlen minta (elso 3 mondat) --")
        for m in ms[:3]:
            print("        | %s" % m[:230])
    return {t: len(v) for t, v in talalt.items()}, len(ms)


# ---------------------------------------------------------------- fotmob
def fotmob(out):
    out.append("")
    out.append("--- fotmob: strukturalt szin prozai forras nelkul ---")
    eng, mier = robots_engedi("https://www.fotmob.com", "/api/data/matchDetails")
    out.append("  robots: %s (%s)" % ("ENGEDI" if eng else "TILTJA" if eng is False else "?", mier))
    if eng is False:
        return
    meccs = None
    for nap in range(1, NAPOK + 1):
        d = time.strftime("%Y%m%d", time.gmtime(time.time() - nap * 86400))
        code, body, ms = keres("https://www.fotmob.com/api/data/matches?date=" + d)
        if code != 200:
            out.append("  %s: HTTP %s (%d ms)" % (d, code, ms))
            continue
        try:
            j = json.loads(body)
        except Exception:                                    # noqa: BLE001
            out.append("  %s: nem json" % d)
            continue
        ligak = []
        for lg in j.get("leagues", []):
            ligak.append("%s / %s" % (lg.get("ccode"), lg.get("name")))
            if lg.get("ccode") == "ENG" and lg.get("name") == "Premier League":
                for m in lg.get("matches", []):
                    if (m.get("status") or {}).get("finished"):
                        meccs = (str(m.get("id")), m.get("home", {}).get("name"),
                                 m.get("away", {}).get("name"), d)
                        break
        out.append("  %s: %d liga, PL-lezart meccs: %s" % (d, len(ligak), bool(meccs)))
        if not meccs and nap == 1:
            out.append("    a napon latott ligak (elso 8): %s" % "; ".join(ligak[:8]))
        if meccs:
            break
    if not meccs:
        out.append("  NINCS lezart PL-meccs az utolso %d napban" % NAPOK)
        return
    mid, h, v, d = meccs
    out.append("  meccs: %s - %s (%s, id=%s)" % (h, v, d, mid))
    code, body, ms = keres("https://www.fotmob.com/api/data/matchDetails?matchId=" + mid)
    out.append("  matchDetails: HTTP %s, %d kb, %d ms" % (code, len(body) // 1024, ms))
    if code != 200:
        return
    j = json.loads(body)
    tart = j.get("content") or {}
    out.append("  content kulcsai: %s" % ", ".join(sorted(tart.keys())))
    # 1) esemenyek
    ev = ((tart.get("matchFacts") or {}).get("events") or {}).get("events") or []
    tipusok = sorted({str(e.get("type")) for e in ev})
    out.append("  esemenyek: %d db, tipusok: %s" % (len(ev), ", ".join(tipusok)))
    golkulcs = set()
    for e in ev:
        if e.get("type") == "Goal":
            golkulcs |= {k for k, x in e.items() if x not in (None, "", [], {})}
    out.append("  GOL-esemeny kulcsai: %s" % ", ".join(sorted(golkulcs)))
    print("\n  == fotmob golok (nyers) ==")
    for e in ev:
        if e.get("type") == "Goal":
            print("     | %s" % json.dumps(e, ensure_ascii=False)[:400])
    # 2) shotmap: a gol MODJA, a kihagyott nagy helyzet, a vedes
    sm = tart.get("shotmap") or {}
    lovesek = sm.get("shots") if isinstance(sm, dict) else None
    if not isinstance(lovesek, list):
        lovesek = []
    out.append("  shotmap: %d loves" % len(lovesek))
    if lovesek:
        out.append("  loves-kulcsok: %s" % ", ".join(sorted(lovesek[0].keys())))
        for mezo in ("situation", "shotType", "eventType"):
            ertekek = sorted({str(x.get(mezo)) for x in lovesek if x.get(mezo) is not None})
            out.append("    %-10s: %s" % (mezo, ", ".join(ertekek) or "(nincs)"))
        nagy = [x for x in lovesek
                if (x.get("expectedGoals") or 0) >= 0.3 and str(x.get("eventType")) != "Goal"]
        out.append("    xG>=0.3 de nem gol (kihagyott nagy helyzet): %d" % len(nagy))
        vedes = [x for x in lovesek if "save" in str(x.get("eventType")).lower()]
        out.append("    kapusvedes-jellegu esemeny: %d" % len(vedes))
        print("\n  == fotmob shotmap (elso 5 loves, nyersen) ==")
        for x in lovesek[:5]:
            print("     | %s" % json.dumps({k: x.get(k) for k in
                  ("min", "playerName", "situation", "shotType", "eventType",
                   "expectedGoals", "isBlocked", "isOnTarget")}, ensure_ascii=False))
    # 3) van-e prozai kommentar is
    for kulcs in ("liveticker", "commentary", "matchFacts"):
        r = tart.get(kulcs)
        if isinstance(r, dict):
            out.append("  %s alkulcsai: %s" % (kulcs, ", ".join(sorted(r.keys()))[:200]))
    return meccs


# ---------------------------------------------------------------- pulselive
def pulselive(out):
    out.append("")
    out.append("--- premierleague (pulselive): sajat perces kommentar ---")
    fej = {"Origin": "https://www.premierleague.com",
           "Referer": "https://www.premierleague.com/"}
    code, body, ms = keres(
        "https://footballapi.pulselive.com/football/competitions/1/compseasons", fej)
    out.append("  compseasons: HTTP %s (%d ms)" % (code, ms))
    if code != 200:
        return
    j = json.loads(body)
    idk = [(str(c.get("id")).split(".")[0], c.get("label")) for c in j.get("content", [])]
    out.append("  legujabb szezonok: %s" % "; ".join("%s=%s" % (b, a) for a, b in idk[:3]))
    if not idk:
        return
    sid = idk[0][0]
    url = ("https://footballapi.pulselive.com/football/fixtures?comps=1&compSeasons=%s"
           "&statuses=C&page=0&pageSize=5&sort=desc" % sid)
    code, body, ms = keres(url, fej)
    out.append("  lezart meccsek: HTTP %s (%d ms)" % (code, ms))
    if code != 200:
        out.append("  valasz: %s" % body[:160].decode("utf-8", "replace"))
        return
    fx = json.loads(body).get("content", [])
    out.append("  kapott meccs: %d" % len(fx))
    if not fx:
        return
    f = fx[0]
    fid = str(f.get("id")).split(".")[0]
    csapatok = " - ".join((t.get("team") or {}).get("name", "?") for t in f.get("teams", []))
    out.append("  meccs: %s (id=%s)" % (csapatok, fid))
    for ut in ("/football/fixtures/%s/textstream/EN?pageSize=200" % fid,
               "/football/fixtures/%s/textstream/EN" % fid):
        code, body, ms = keres("https://footballapi.pulselive.com" + ut, fej)
        out.append("  textstream %s: HTTP %s, %d kb (%d ms)" % (ut.split("?")[0][-30:], code,
                                                                len(body) // 1024, ms))
        if code == 200:
            try:
                e = json.loads(body).get("events", {}).get("content", [])
            except Exception:                                # noqa: BLE001
                e = []
            out.append("    bejegyzes: %d" % len(e))
            t = " ".join(x.get("text") or "" for x in e)
            if t.strip():
                szam, db = cimkez(t, "pulselive textstream")
                out.append("    cimkek: %s" % (json.dumps(szam) if szam else "NINCS TALALAT"))
                out.append("    mondat: %d" % db)
            else:
                out.append("    NINCS szoveg a valaszban")
            break


# ---------------------------------------------------------------- guardian
def guardian(out, meccs):
    out.append("")
    out.append("--- guardian content api (fejlesztoi kulcs: test) ---")
    eng, mier = robots_engedi("https://content.guardianapis.com", "/search")
    out.append("  robots: %s (%s)" % ("ENGEDI" if eng else "TILTJA" if eng is False else "?", mier))
    if eng is False:
        return
    q = "premier league match report"
    if meccs:
        q = "%s %s" % (meccs[1], meccs[2])
    url = ("https://content.guardianapis.com/search?q=%s&section=football"
           "&show-fields=bodyText&page-size=3&api-key=test"
           % urllib.parse.quote(q))
    code, body, ms = keres(url)
    out.append("  kereses (%s): HTTP %s, %d kb (%d ms)" % (q, code, len(body) // 1024, ms))
    if code != 200:
        out.append("  valasz: %s" % body[:200].decode("utf-8", "replace"))
        return
    r = json.loads(body).get("response", {})
    cikkek = r.get("results", [])
    out.append("  talalat: %s, visszaadva: %d" % (r.get("total"), len(cikkek)))
    for c in cikkek[:2]:
        t = (c.get("fields") or {}).get("bodyText") or ""
        out.append("    %s | %d karakter" % (c.get("webTitle", "?")[:70], len(t)))
        if t:
            szam, db = cimkez(t, "guardian: " + c.get("webTitle", "?")[:50])
            out.append("      cimkek: %s" % (json.dumps(szam) if szam else "NINCS TALALAT"))


# ---------------------------------------------------------------- bbc
def bbc(out):
    out.append("")
    out.append("--- bbc sport ---")
    eng, mier = robots_engedi("https://www.bbc.com", "/sport/football")
    out.append("  robots: %s (%s)" % ("ENGEDI" if eng else "TILTJA" if eng is False else "?", mier))
    if eng is False:
        return
    for nap in range(1, NAPOK + 1):
        d = time.strftime("%Y-%m-%d", time.gmtime(time.time() - nap * 86400))
        url = "https://www.bbc.com/sport/football/premier-league/scores-fixtures/" + d
        code, body, ms = keres(url)
        if code != 200:
            out.append("  %s: HTTP %s (%d ms)" % (d, code, ms))
            continue
        html = body.decode("utf-8", "replace")
        linkek = sorted(set(re.findall(r'"(/sport/football/(?:articles|live)/[a-z0-9]+)"', html)))
        out.append("  %s: HTTP 200, %d kb, cikk-link: %d" % (d, len(body) // 1024, len(linkek)))
        if not linkek:
            continue
        for l in linkek[:1]:
            code2, body2, ms2 = keres("https://www.bbc.com" + l)
            out.append("    %s: HTTP %s, %d kb (%d ms)" % (l, code2, len(body2) // 1024, ms2))
            if code2 == 200:
                t = szoveg(body2.decode("utf-8", "replace"))
                szam, db = cimkez(t, "bbc " + l)
                out.append("      cimkek: %s" % (json.dumps(szam) if szam else "NINCS TALALAT"))
        break


def main():
    out = ["", "=" * 70,
           "PROBE: %s UTC | Premier League colour sources" % time.strftime("%Y-%m-%d %H:%M")]
    meccs = None
    for f in (lambda: fotmob(out),):
        try:
            meccs = f()
        except Exception as e:                               # noqa: BLE001
            out.append("  HIBA: %s: %s" % (type(e).__name__, e))
    for f in (lambda: pulselive(out), lambda: guardian(out, meccs), lambda: bbc(out)):
        try:
            f()
        except Exception as e:                               # noqa: BLE001
            out.append("  HIBA: %s: %s" % (type(e).__name__, e))
    szoveg_ki = "\n".join(out) + "\n"
    print(szoveg_ki)
    fej = ("Premier League szin-forrasok merese.\n"
           "A fajlt a naplo/pl-colour-probe.py irja. Cikkszoveget NEM tarol:\n"
           "a talalt mondatok csak a futas naplojaban (stdout) latszanak.\n")
    regi = ""
    if os.path.exists(LOG):
        regi = open(LOG, encoding="utf-8").read()
    else:
        regi = fej
    open(LOG, "w", encoding="utf-8").write(regi.rstrip("\n") + "\n" + szoveg_ki)
    return 0


if __name__ == "__main__":
    sys.exit(main())
