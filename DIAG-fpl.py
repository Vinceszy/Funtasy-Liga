#!/usr/bin/env python3
"""EGYSZERI felderites: MI rajzolja a Draft "PROVISIONAL" feliratat?

Vince kepen a Draft "Current team" lapjan egy naponkenti tablazat all:
  Day | Match Points | Bonus Points
es a lejatszott napoknal PROVISIONAL. Ket oszlop van, es az event-status is
ket mezot ad naponkent (points, bonus_added) - konnyen lehet, hogy amit
eddig neztem (points), az a BAL oszlop, a bonusz meg a masik.

Ne talalgassuk: toltsuk le a Draft frontend JS-csomagjat, es nezzuk meg, mi
donti el a "PROVISIONAL" feliratot. Csak olvas.
"""
import json, re, urllib.parse, urllib.request

WEB = "https://draft.premierleague.com/"
HDRS = {"Accept": "*/*", "User-Agent": "Mozilla/5.0 funtasy-diag/1.0"}


def hoz(url, nyers=True, timeout=60):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=HDRS), timeout=timeout) as r:
            b = r.read()
            return r.status, (b.decode("utf-8", "replace") if nyers else json.loads(b.decode("utf-8")))
    except Exception as e:
        return getattr(e, "code", None) or ("%s: %s" % (type(e).__name__, e)), None


st, html = hoz(WEB)
print("=== fooldal HTTP %s, %s byte" % (st, len(html or "")))
srcs = re.findall(r'<script[^>]+src="([^"]+)"', html or "")
srcs += re.findall(r'"(/static/[^"]+\.js)"', html or "")
srcs = list(dict.fromkeys(srcs))
print("    script-ek: %s" % srcs[:12])

js = ""
for s in srcs[:10]:
    st2, t = hoz(urllib.parse.urljoin(WEB, s))
    if t:
        js += "\n" + t
        print("    + %s (%s byte)" % (s[:70], len(t)))
print("=== osszes JS: %s byte" % len(js))

for szo in ("PROVISIONAL", "Provisional", "provisional", "Bonus Points", "Match Points",
            "bonus_added", "event-status", "eventStatus"):
    db = js.count(szo)
    print("\n=== %-14s %sx" % (szo, db))
    if not db:
        continue
    latott = set()
    for m in list(re.finditer(re.escape(szo), js))[:6]:
        k = js[max(0, m.start() - 180):m.start() + 180].replace("\n", " ")
        if k in latott:
            continue
        latott.add(k)
        print("    ...%s..." % k)

print("\n--- vege ---")
