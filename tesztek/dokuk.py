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

# ---- D4: a valtozasnaplo bejegyzesei teljesek ----
naplo = json.loads(olvas("valtozasok.json"))
gond = []
for i, b in enumerate(naplo.get("bejegyzesek") or []):
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", b.get("datum") or ""):
        gond.append("%d. bejegyzes: rossz datum %r" % (i + 1, b.get("datum")))
    if b.get("tipus") not in ("funkcio", "bugfix"):
        gond.append("%d. bejegyzes: ismeretlen tipus %r" % (i + 1, b.get("tipus")))
    if not b.get("ligak") or not all(isinstance(x, str) and x for x in b["ligak"]):
        gond.append("%d. bejegyzes: hianyzo/rossz ligak" % (i + 1))
    for mezo in ("cim", "leiras"):
        if not (b.get(mezo) or "").strip():
            gond.append("%d. bejegyzes: ures %s" % (i + 1, mezo))
allit(not gond, "D4: a valtozasnaplo minden bejegyzese teljes"
      + ("" if not gond else " - " + "; ".join(gond)))

if hibak:
    print("\n%d allitas bukott." % len(hibak))
    sys.exit(1)
print("\nMind a negy allitas rendben.")
