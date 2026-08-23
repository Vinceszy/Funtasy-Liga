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

# a sor-komponens TELJESEN: mit ir a ket oszlop
for szo, elotte, utana in (("hasBonusAdded", 200, 1400),
                           ("Bonus Points", 300, 1500),
                           ("l:`Live`", 200, 600)):
    print("\n=== %s (%sx)" % (szo, js.count(szo)))
    for m in list(re.finditer(re.escape(szo), js))[:2]:
        print("    %s" % js[max(0, m.start() - elotte):m.start() + utana].replace("\n", " "))
        print("    " + "-" * 60)

print("\n--- vege ---")
