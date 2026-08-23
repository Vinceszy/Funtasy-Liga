#!/usr/bin/env python3
"""EGYSZERI felderites, 4. kor: mit tud a FORDULOROL az MLSZ frontendje?

A 3. kor letoltotte a frontend JS-csomagjat (1,5 MB), de a mintam tul szuk
volt: minifikalva a vegpontok osszefuzessel epulnek. Most:
  a) osszeszedjuk a csomagbol az OSSZES "round"-ot tartalmazo azonositot
     (mezonevek!), es minden "competitions/" elofordulas kornyeket,
  b) megnezzuk, mit ad a ranglista a KOVETKEZO fordulora.
Csak olvas.
"""
import json, re, urllib.parse, urllib.request

API = "https://fantasy-api.mlsz.hu/"
WEB = "https://fantasy.mlsz.hu/"
HDRS = {"Accept": "*/*", "User-Agent": "Mozilla/5.0 funtasy-diag/1.0", "Referer": WEB}


def hoz(url, nyers=False, timeout=60):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=HDRS), timeout=timeout) as r:
            b = r.read()
            return r.status, (b.decode("utf-8", "replace") if nyers else json.loads(b.decode("utf-8")))
    except Exception as e:
        return getattr(e, "code", None) or ("%s: %s" % (type(e).__name__, e)), None


st, html = hoz(WEB, nyers=True)
srcs = [s for s in re.findall(r'<script[^>]+src="([^"]+)"', html or "") if "mlsz.hu" in s or s.startswith("/")]
js = ""
for s in srcs:
    st2, t = hoz(urllib.parse.urljoin(WEB, s), nyers=True)
    if t:
        js += t
print("=== JS-csomag: %s byte" % len(js))

print("\n=== 1) Minden 'round'-ot tartalmazo azonosito a csomagban")
azon = sorted(set(re.findall(r'\b[A-Za-z_]*[Rr]ound[A-Za-z_]*\b', js)))
for a in azon:
    print("      %-38s %sx" % (a, js.count(a)))

print("\n=== 2) A 'competitions' szo minden elofordulasanak kornyeke")
latott = set()
for m in re.finditer(r'competitions', js):
    k = js[max(0, m.start() - 90):m.start() + 110].replace("\n", " ")
    kulcs = re.sub(r'[A-Za-z_$][A-Za-z0-9_$]{0,2}(?=[,)\]}])', '#', k)
    if kulcs in latott:
        continue
    latott.add(kulcs)
    print("      ...%s..." % k)
    if len(latott) > 40:
        break

print("\n=== 3) Lezartsagra utalo mezonevek")
for minta in (r'\bis_[a-z_]*\b', r'\b[a-z_]*closed[a-z_]*\b', r'\b[a-z_]*finish[a-z_]*\b',
              r'\b[a-z_]*deadline[a-z_]*\b', r'\b[a-z_]*status[a-z_]*\b'):
    tal = sorted(set(x for x in re.findall(minta, js) if len(x) > 4))
    print("    %-24s %s" % (minta, tal[:40]))

print("\n=== 4) A ranglista a kovetkezo fordulokra")
for r_no in (4, 5, 6, 7):
    rid = 75 + 2 * r_no
    st, j = hoz(API + "rankings?include=user_team.user.id,summary_statistics,ranking,rounds,"
                "competition_rank&page=1&per_page=1&filter%5Bround_id%5D=" + str(rid))
    d = ((j or {}).get("data") or [{}])[0]
    ut_ = d.get("user_team") or {}
    print("    fordulo %s (round_id=%s) HTTP %-5s pont=%-8s fordulok=%s" % (
        r_no, rid, st, d.get("points"),
        [(s.get("round_number"), s.get("points")) for s in (ut_.get("round_statistics") or [])]))

print("\n=== 5) A ranglista teljes user_team objektuma (elso helyezett)")
st, j = hoz(API + "rankings?include=user_team.user.id,summary_statistics,ranking,rounds,"
            "competition_rank&page=1&per_page=1")
d = ((j or {}).get("data") or [{}])[0]
print("    data kulcsok: %s" % sorted(d))
print("    user_team kulcsok: %s" % sorted(d.get("user_team") or {}))
print("    round_statistics[0]: %s" % json.dumps(((d.get("user_team") or {}).get("round_statistics") or [{}])[0], ensure_ascii=False))
print("    meta: %s" % json.dumps((j or {}).get("meta"), ensure_ascii=False)[:400])

print("\n--- vege ---")
