#!/usr/bin/env python3
"""EGYSZERI meres a jatekosprofil-funkciohoz - 5. kor.

EDDIGI EREDMENY (naplo/mlsz-jatekoslista.txt korabbi korei):
  - a teljes torzs egy keresbol megjon: competitions/3/players?per_page=500
    (385 jatekos, klub, poszt, u21, serules, ar, competition_points);
  - fordulora nem szurheto, a pontbontas nem lapozhato;
  - a bontas-sorok osszege = a jatekos alappontja (377 fordulon merve).

EZ A KOR EGYETLEN KERDEST DONT EL: a torzs `id` mezoje UGYANAZ-e, mint
amit a keret-rekordokban `id` neven tarolunk (a competition_player.id)?
A fooldali kereso ezen all: ha a talalatra kattintva rossz azonositoval
nyitnank profilt, a bontas mas jatekost mutatna - csendben, hihetoen.

Az osszevetes a repo keret-fajljaibol tortenik: minden mentett jatekosra
megnezzuk, hogy a torzsben ugyanazzal az azonositoval ugyanaz a NEV all-e.

Csak olvas; a naplot a workflow commitolja.
ADATVEDELEM: a labdarugok neve nyilvanos adat, az mehet a naploba.
"""
import glob, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import collect

GYOKER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAPLO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mlsz-jatekoslista.txt")
sorok = []
ki = sorok.append

ki("# 5. KOR: a torzs `id`-je ugyanaz-e, mint a keret-rekordok `id`-je?")
ki("# A fooldali kereso ezen all: rossz azonosito eseten a talalat MAS")
ki("# jatekos bontasat nyitna meg - csendben, hihetoen.")
ki("")

st, j = collect.api_get(collect.BASE + "players?include=team,position,summary_statistics&per_page=500")
adat = (j or {}).get("data") if isinstance(j, dict) else None
if not isinstance(adat, list) or not adat:
    ki("### A torzs nem johetett le (HTTP %s) - a meres nem folytathato." % st)
    with open(NAPLO, "w", encoding="utf-8") as f:
        f.write("\n".join(sorok) + "\n")
    print("\n".join(sorok))
    sys.exit(0)

ki("### A torzs %d sort adott (HTTP %s). Egy sor kulcsai:" % (len(adat), st))
ki("    %s" % sorted(adat[0].keys()))

torzs = {}
for p in adat:
    nev = " ".join(x for x in (p.get("first_name"), p.get("last_name")) if x)
    torzs[p.get("id")] = nev
ki("")

# a keret-fajlokban tarolt (id -> nev) parok
keret = {}
for ut in sorted(glob.glob(os.path.join(GYOKER, "keretek", "*.json"))):
    for lista in json.load(open(ut, encoding="utf-8"))["squads"].values():
        for p in lista:
            if p.get("id"):
                keret[p["id"]] = p["name"]

egyezik, elter, hianyzik = 0, 0, 0
gondok = []
for cp, nev in sorted(keret.items()):
    tnev = torzs.get(cp)
    if tnev is None:
        hianyzik += 1
        if len(gondok) < 20:
            gondok.append("%s (id=%s): NINCS a torzsben" % (nev, cp))
    elif tnev.strip() == nev.strip():
        egyezik += 1
    else:
        elter += 1
        if len(gondok) < 20:
            gondok.append("id=%s: keretben %r, torzsben %r" % (cp, nev, tnev))

ki("### %d mentett jatekos osszevetve a torzzsel:" % len(keret))
ki("###   ugyanaz a nev ugyanazon az azonositon: %d" % egyezik)
ki("###   MAS nev ugyanazon az azonositon:       %d" % elter)
ki("###   az azonosito nincs a torzsben:         %d" % hianyzik)
if gondok:
    ki("")
    ki("### Reszletek (max 20):")
    for g in gondok:
        ki("  " + g)
else:
    ki("")
    ki("### Egyetlen elteres sincs - a torzs `id`-je a competition_player.id.")

# a torzs egy teljes sora, hogy lassuk, mit erdemes elmenteni
ki("")
ki("### Egy teljes torzs-sor (a mentendo mezokhoz):")
ki(json.dumps(adat[0], ensure_ascii=False, indent=1)[:1800])

with open(NAPLO, "w", encoding="utf-8") as f:
    f.write("\n".join(sorok) + "\n")
print("\n".join(sorok))
