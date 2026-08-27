#!/usr/bin/env python3
"""A dokumentacio konzisztenciaja - a tesztsor resze.

MIERT LETEZIK: a kodot tesztek orzik, az eles adatfajlokat a push elotti
diff-ellenorzes - a dokumentaciot viszont sokaig semmi. A doksi-szerkesztes
ketszer hasalt el csendben (a szerkeszto script hibaja a tobbparancsos
kimenet kozepen elveszett), es csak kezi atnezes vette eszre. A kezi
ellenorzes terheles alatt csuszik el; ez a teszt azota kenyszeriti ki.

Amit ellenoriz:
  D1: minden tesztfajlnak van sora a tesztek/README.md tablazataban.
  D2: a repo gyokereben minden .json adatfajlnak van sora a fo README
      fajl-tablazataban - egy uj adatfajl dokumentacio nelkul bukik.
  D3: a fo README fajl-tablazata nem hivatkozik nem letezo fajlra.
  D4: a valtozasok.json minden bejegyzese teljes es jol formazott
      (datum, ismert tipus, legalabb egy liga, cim, leiras).
  D5: ugyanez a valtozasok-vazlat.json meg nem publikalt bejegyzeseire.
"""
import glob, json, os, re, sys

GYOKER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
hibak = []


def allit(felt, cimke):
    print(("OK   " if felt else "HIBA ") + cimke)
    if not felt:
        hibak.append(cimke)


def olvas(ut):
    with open(os.path.join(GYOKER, ut), encoding="utf-8") as f:
        return f.read()


# ---- D1: minden teszt dokumentalva ----
teszt_readme = olvas("tesztek/README.md")
tesztek = sorted(os.path.basename(f) for f in
                 glob.glob(os.path.join(GYOKER, "tesztek", "*.teszt.js"))
                 + glob.glob(os.path.join(GYOKER, "tesztek", "gyujto_*.py")))
hianyzo = [t for t in tesztek if "`%s`" % t not in teszt_readme]
allit(not hianyzo, "D1: minden tesztfajlnak van sora a tesztek/README-ben"
      + ("" if not hianyzo else " - HIANYZIK: %s" % ", ".join(hianyzo)))

# ---- D2: minden gyokerbeli adatfajl dokumentalva ----
readme = olvas("README.md")
adatfajlok = sorted(os.path.basename(f) for f in
                    glob.glob(os.path.join(GYOKER, "*.json")))
hianyzo = [f for f in adatfajlok if "`%s`" % f not in readme]
allit(not hianyzo, "D2: minden adatfajlnak van sora a README fajl-tablazataban"
      + ("" if not hianyzo else " - HIANYZIK: %s" % ", ".join(hianyzo)))

# ---- D3: a fajl-tablazat nem hivatkozik nem letezore ----
# A "## 2. Fajlok" tablazat soraibol az elso oszlop hivatkozasai. A
# fordulonkenti sablon-utakat (keretek/<fordulo>.json) kihagyjuk.
tabla = re.search(r"## 2\. Fájlok(.*?)\n## ", readme, re.S)
rossz = []
if tabla:
    for ut in re.findall(r"^\| `([^`<]+)` \|", tabla.group(1), re.M):
        teljes = os.path.join(GYOKER, ut)
        if not (os.path.exists(teljes) or os.path.isdir(teljes.rstrip("/"))):
            rossz.append(ut)
allit(tabla is not None and not rossz,
      "D3: a README fajl-tablazata csak letezo fajlra hivatkozik"
      + ("" if not rossz else " - NEM LETEZIK: %s" % ", ".join(rossz)))

# ---- D4/D5: a naplo es a vazlat bejegyzesei teljesek ----
def bejegyzes_gondok(bejegyzesek):
    gond = []
    for i, b in enumerate(bejegyzesek or []):
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", b.get("datum") or ""):
            gond.append("%d. bejegyzes: rossz datum %r" % (i + 1, b.get("datum")))
        if b.get("tipus") not in ("funkcio", "bugfix"):
            gond.append("%d. bejegyzes: ismeretlen tipus %r" % (i + 1, b.get("tipus")))
        if not b.get("ligak") or not all(isinstance(x, str) and x for x in b["ligak"]):
            gond.append("%d. bejegyzes: hianyzo/rossz ligak" % (i + 1))
        for mezo in ("cim", "leiras"):
            if not (b.get(mezo) or "").strip():
                gond.append("%d. bejegyzes: ures %s" % (i + 1, mezo))
    return gond


naplo = json.loads(olvas("valtozasok.json"))
gond = bejegyzes_gondok(naplo.get("bejegyzesek"))
allit(not gond, "D4: a valtozasnaplo minden bejegyzese teljes"
      + ("" if not gond else " - " + "; ".join(gond)))

# A vazlat-fajl a MEG NEM PUBLIKALT bejegyzeseket orzi (tobb szakaszban
# keszulo funkcional a naplo csak a vegen megy ki). Ugyanaz az alaki
# elvaras all ra, hogy a kesz szakasz vegen csak at kelljen mozgatni - es
# hogy egy felig megirt vazlat ne aludjon el evekig eszrevetlenul.
try:
    vazlat = json.loads(olvas("valtozasok-vazlat.json")).get("bejegyzesek")
except FileNotFoundError:
    vazlat = []
gond = bejegyzes_gondok(vazlat)
allit(not gond, "D5: a valtozasnaplo-vazlat minden bejegyzese teljes"
      + ("" if not gond else " - " + "; ".join(gond)))

# D6: a ?v=N gyorsitotar-jelzo MINDEN oldalon ugyanaz.
# A GitHub Pages 1-2 percig gyorsitataroz; a verzioszamot kezzel emeljuk
# minden kiadasnal. Ha csak az egyik oldalon emelkedik, az a masikon REGI
# funtasy.js/css-t hagy - ott a felhasznalo hetekig regi kodot lat, es a
# hibajelentese ertelmezhetetlen lesz. Ezt gepnek kell nezni, nem szemnek.
import re as _re
_verziok = {}
for _f in ("index.html", "nb1/index.html", "pl/index.html", "valtozasok/index.html"):
    for _m in _re.findall(r'(funtasy\.(?:js|css))\?v=(\d+)', olvas(_f)):
        _verziok.setdefault(_m[1], []).append("%s -> %s" % (_f, _m[0]))
allit(len(_verziok) == 1,
      "D6: minden oldal ugyanazt a ?v= verziot hivatkozza"
      + ("" if len(_verziok) == 1
         else " - eltero verziok: " + "; ".join("v=%s (%s)" % (v, ", ".join(h))
                                                for v, h in sorted(_verziok.items()))))

# D7: a README tartalomjegyzeke egyezik a tenyleges cimekkel.
# A fajl 1500+ soros; jegyzek nelkul kereshetetlen, elavult jegyzekkel meg
# felrevezeto. Ezert a jegyzek NEM kezi munka: itt keszul ujra a cimekbol, es
# ha eltert, a teszt kiirja a helyes szoveget - be lehet masolni.
_JELOLES = "<!-- tartalomjegyzek: a tesztek/dokuk.py tartja karban, kezzel ne szerkeszd -->"


def _slug(cim):
    t = cim.strip().lower()
    for x in ("\u201e", '"', "\u201d"):
        t = t.replace(x, "")
    t = re.sub(r"[^\w\s\u00c0-\u024f-]", "", t, flags=re.UNICODE)
    return t.replace(" ", "-")


def _cimek(szoveg):
    ki, kod = [], False
    for l in szoveg.split("\n"):
        if l.startswith("```"):
            kod = not kod
            continue
        if kod:
            continue
        if l.startswith("## "):
            ki.append((2, l[3:].strip()))
        elif l.startswith("### "):
            ki.append((3, l[4:].strip()))
    return ki


def _jegyzek(szoveg):
    sorok = [_JELOLES, "<details>", "<summary><b>Tartalom</b></summary>", ""]
    for sz, c in _cimek(szoveg):
        sorok.append("%s- [%s](#%s)" % ("  " * (sz - 2), c, _slug(c)))
    return "\n".join(sorok + ["", "</details>"])


_readme = olvas("README.md")
if _JELOLES not in _readme:
    allit(False, "D7: a README-ben nincs tartalomjegyzek (a jelolo hianyzik)")
else:
    _eleje = _readme.index(_JELOLES)
    _vege = _readme.index("</details>", _eleje) + len("</details>")
    _mostani = _readme[_eleje:_vege]
    _kell = _jegyzek(_readme)
    # "python3 tesztek/dokuk.py --javit" ujrairja a jegyzeket. Igy egy uj
    # cim utan nem kell kezzel masolgatni - es nem is fog elmaradni.
    if _mostani != _kell and "--javit" in sys.argv:
        with open(os.path.join(GYOKER, "README.md"), "w", encoding="utf-8") as _f:
            _f.write(_readme[:_eleje] + _kell + _readme[_vege:])
        print("  . README tartalomjegyzek ujrairva (--javit)")
        _mostani = _kell
    allit(_mostani == _kell,
          "D7: a README tartalomjegyzeke egyezik a cimekkel"
          + ("" if _mostani == _kell else
             " - futtasd: python3 tesztek/dokuk.py --javit"))

if hibak:
    print("\n%d allitas bukott." % len(hibak))
    sys.exit(1)
print("\nMind a het allitas rendben.")
