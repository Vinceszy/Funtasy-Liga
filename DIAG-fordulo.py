#!/usr/bin/env python3
"""EGYSZERI felderites, 3. kor: HOL van a fordulo-szintu lezartsag?

1-2. kor: nincs onallo rounds-vegpont (404), a verseny-objektum sincs
kozvetlenul (404), a competitions lista nem ad fordulo-informaciot.
Tehat ne talalgassuk a vegpontokat: toltsuk le az MLSZ SAJAT frontendjenek
JS-csomagjait, es olvassuk ki beloluk, milyen utvonalakat hiv. Ami ott
szerepel, az letezik. Csak olvas, semmit nem ir.
"""
import json, re, urllib.parse, urllib.request

API = "https://fantasy-api.mlsz.hu/"
WEB = "https://fantasy.mlsz.hu/"
HDRS = {"Accept": "*/*", "User-Agent": "Mozilla/5.0 funtasy-diag/1.0",
        "Referer": WEB}


def hoz(url, nyers=False, timeout=40):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=HDRS), timeout=timeout) as r:
            b = r.read()
            return r.status, (b.decode("utf-8", "replace") if nyers else json.loads(b.decode("utf-8")))
    except Exception as e:
        return getattr(e, "code", None) or ("%s: %s" % (type(e).__name__, e)), None


# ---------------------------------------------------------------- 1. a SPA
print("=== 1) Az MLSZ frontend JS-csomagjaiban szereplo API-utvonalak")
st, html = hoz(WEB, nyers=True)
print("    fooldal HTTP %s, %s byte" % (st, len(html or "")))
srcs = re.findall(r'<script[^>]+src="([^"]+)"', html or "")
srcs += re.findall(r'"(/(?:assets|js|_nuxt)/[^"]+\.js)"', html or "")
srcs = list(dict.fromkeys(srcs))
print("    talalt script-ek: %s" % (srcs[:20] or "nincs"))

MINTA = re.compile(r'''["'`](competitions?/[^"'`\s]{0,80}|/?(?:rounds?|games?|fixtures?|standings|deadline)[a-z0-9\-/_]{0,40})["'`]''')
utak, meret = set(), 0
for s in srcs[:12]:
    u = urllib.parse.urljoin(WEB, s)
    st2, js = hoz(u, nyers=True)
    if not js:
        print("    - %s -> HTTP %s" % (s[:80], st2))
        continue
    meret += len(js)
    # API-utvonalnak latszo sztringek
    for m in re.findall(MINTA, js):
        utak.add(m)
    # a "round" szot tartalmazo mezonevek
print("    letoltott JS: %s byte, talalt utvonal-jelolt: %s" % (meret, len(utak)))
for u in sorted(utak)[:120]:
    print("      %s" % u)

# ---------------------------------------------------------------- 2. tippek
print("\n=== 2) Kozvetlen vegpont-probak")
JELOLTEK = [
    "competitions/3/games",
    "competitions/3/games?filter%5Bround_id%5D=85",
    "games?filter%5Bround_id%5D=85",
    "competitions/3/rounds?page=1",
    "competition-rounds?filter%5Bcompetition_id%5D=3",
    "rounds?filter%5Bcompetition_id%5D=3",
    "competitions/3/fixtures",
    "competitions/3/settings",
    "competitions/3/deadline",
    "competitions/3/current-round",
    "competitions/3/statistics",
    "competitions/3/rankings?page=1&per_page=1",
]
for ut in JELOLTEK:
    st, j = hoz(API + ut)
    fej = json.dumps(j, ensure_ascii=False)[:400] if isinstance(j, dict) else ""
    print("    %-52s HTTP %-5s %s" % (ut[:52], st, fej))

print("\n--- vege ---")
