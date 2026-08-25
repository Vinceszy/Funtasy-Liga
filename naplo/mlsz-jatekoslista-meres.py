#!/usr/bin/env python3
"""EGYSZERI meres a jatekosprofil-funkciohoz.

EDDIGI EREDMENY (naplo/mlsz-jatekoslista.txt):
  1. kor: megvan a teljes jatekostorzs - competitions/3/players
     (385 jatekos, klub, poszt, u21, serules, ar, competition_points).
  2. kor: a torzs NEM fogad filter[round_id]-t (400); a per_page viszont MEGY.
  3. kor: a pontbontas-vegpont fordulo-szuro NELKUL is mukodik - egy keres
     (3 lap) egy jatekos EGESZ szezonjanak teteles bontasat adja.

4. KOR - a profil KOZPONTI FELTEVESE. A profil fordulonkenti pontszamat a
bontas-sorok osszegebol szamolnank ki, mert az fuggetlen attol, kinel volt
a jatekos (nincs benne se kapitanyi duplazas, se padfelezes). Ha ez az
osszeg NEM egyezik a keret-fajlokban tarolt `week` ertekkel (a kapitanysagot
es a padot visszaszamolva), akkor az egesz szamitas mas alapra kell.

Ezt NEM hisszuk el, hanem OSSZEVETJUK: minden mentett fordulo minden mentett
jatekosara. A konteneres fejlesztoi gepbol az MLSZ nem erheto el, ezert fut
ez GitHub Actionsbol.

Csak olvas; a naplot a workflow commitolja.
ADATVEDELEM: a labdarugok neve nyilvanos adat, az mehet a naploba.
"""
import glob, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import collect  # api_get, ROOT, rid

GYOKER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAPLO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mlsz-jatekoslista.txt")
sorok = []
ki = sorok.append

ki("# 4. KOR - a profil kozponti feltevese: a bontas-sorok osszege = a")
ki("# jatekos ALAPPONTJA az adott forduloban (kapitanysag/pad nelkul).")
ki("# Osszevetes: keretek/<f>.json `week` / (cap?2:1) / (sub?0.5:1).")
ki("")

# ---- 1) minden mentett jatekos minden mentett forduloban ----
keret = {}                      # (id, fordulo) -> (nev, alappont)
for ut in sorted(glob.glob(os.path.join(GYOKER, "keretek", "*.json"))):
    j = json.load(open(ut, encoding="utf-8"))
    r = int(j["round"])
    for lista in j["squads"].values():
        for p in lista:
            if not p.get("id"):
                continue
            alap = (p.get("week") or 0)
            if p.get("cap"):
                alap /= 2.0
            if p.get("sub"):
                alap *= 2.0
            # ugyanaz a jatekos tobb keretben is lehet - ugyanaz az alappont
            keret[(p["id"], r)] = (p["name"], round(alap, 4))

jatekosok = sorted({i for i, _ in keret})
ki("## %d kulonbozo jatekos, %d (jatekos, fordulo) par a keret-fajlokban."
   % (len(jatekosok), len(keret)))

# ---- 2) elobb: HOGYAN jon meg egy jatekos EGESZ szezonja? ----
# Egy lapra 50 sor fer, egy szezon ~109 - tehat vagy nagyobb lapmeret kell,
# vagy lapozas. Ha rossz parameternevvel "lapoznank", az API az 1. lapot
# adna vissza ujra, a pontok duplazodnanak, es a meres HAMIS elterest
# jelentene. Ezert eloszor kimerjuk, aztan hasznaljuk.
CP = "game-player-stats?include=competition_stat_config&filter%5Bcompetition_player_id%5D="


def elso_sor(j):
    d = (j or {}).get("data") or []
    return json.dumps(d[0], sort_keys=True) if d else None


probe = jatekosok[0]
st, lap1 = collect.api_get(collect.ROOT + CP + str(probe))
osszesen = ((lap1 or {}).get("meta") or {}).get("total")
ki("### A probe-jatekos (%s) szezonja %s sor, egy lapon %d fer el."
   % (probe, osszesen, len(((lap1 or {}).get("data") or []))))

# Elobb a lapmeret: ha felmeheto, LAPOZNI SEM KELL (a torzsvegponton a
# per_page mukodott - itt is ezt probaljuk elsokent).
LAPMERET = None
for par in ("per_page=200", "limit=200", "page%5Bsize%5D=200"):
    st2, j2 = collect.api_get(collect.ROOT + CP + str(probe) + "&" + par)
    n = len((j2 or {}).get("data") or [])
    ki("=== lapmeret %-20s -> HTTP %s | sorok=%d" % (par, st2, n))
    if st2 == 200 and osszesen and n >= osszesen and LAPMERET is None:
        LAPMERET = par

# Ha a lapmeret nem megy, marad a lapozas - de csak akkor, ha tenyleg lapoz.
LAPPAR = None
if LAPMERET is None:
    for nev_par in ("page=", "page%5Bnumber%5D=", "offset=", "page%5Boffset%5D="):
        ertek = "50" if "offset" in nev_par else "2"
        st2, j2 = collect.api_get(collect.ROOT + CP + str(probe) + "&" + nev_par + ertek)
        egyezo = elso_sor(j2) == elso_sor(lap1)
        ki("=== lapozas %-22s -> HTTP %s | %s"
           % (nev_par + ertek, st2, "AZONOS (nem lapoz)" if egyezo else "eltero (LAPOZ)"))
        if st2 == 200 and not egyezo and LAPPAR is None:
            LAPPAR = nev_par + ("50" if "offset" in nev_par else "")

if LAPMERET is None and LAPPAR is None:
    ki("")
    ki("### Sem lapmeret, sem lapozas. Marad a fordulonkenti lekeres:")
    ki("### fordulonkent 22 sor, ami elfér egy lapon - a profil tehat")
    ki("### fordulonkent egy kerest jelent, nem egyet az egesz szezonra.")
    ki("### A meres innentol FORDULONKENT ker le, ugy ellenorzi a feltevest.")
ki("")

egyezik = elter = hianyzik = 0
gondok = []
for i, cp in enumerate(jatekosok):
    osszes = []
    if LAPMERET:
        st, j = collect.api_get(collect.ROOT + CP + str(cp) + "&" + LAPMERET)
        osszes = (j or {}).get("data") or []
        if st != 200:
            gondok.append("jatekos %s: HTTP %s (lapmeret)" % (cp, st))
    elif LAPPAR:
        lap = 1
        while True:
            u = collect.ROOT + CP + str(cp)
            if lap > 1:
                u += "&" + (LAPPAR if LAPPAR.endswith("50") else LAPPAR + str(lap))
            st, j = collect.api_get(u)
            if st != 200 or not isinstance(j, dict):
                gondok.append("jatekos %s: HTTP %s a %d. lapon" % (cp, st, lap))
                break
            osszes += j.get("data") or []
            meta = j.get("meta") or {}
            if lap >= (meta.get("last_page") or 1):
                break
            lap += 1
    else:
        # fordulonkent: 22 sor/fordulo, biztosan elfér egy lapon
        for r_ in sorted({r for c, r in keret if c == cp}):
            st, j = collect.api_get(collect.ROOT + CP + str(cp)
                                    + "&filter%5Bround_id%5D=" + str(collect.rid(r_)))
            if st != 200 or not isinstance(j, dict):
                gondok.append("jatekos %s, %d. f: HTTP %s" % (cp, r_, st))
                continue
            osszes += j.get("data") or []
    # fordulonkenti osszeg
    per_fordulo = {}
    for s in osszes:
        r = (s.get("round_id") - 75) // 2 if s.get("round_id") else None
        if r is None:
            continue
        per_fordulo[r] = round(per_fordulo.get(r, 0) + (s.get("points") or 0), 4)
    for (cp2, r), (nev, alap) in keret.items():
        if cp2 != cp:
            continue
        van = per_fordulo.get(r)
        if van is None:
            hianyzik += 1
            if len(gondok) < 25:
                gondok.append("%s (%s), %d. f: a bontas URES, a keretben %s" % (nev, cp, r, alap))
        elif abs(van - alap) < 0.005:
            egyezik += 1
        else:
            elter += 1
            if len(gondok) < 25:
                gondok.append("%s (%s), %d. f: bontas=%s, keret=%s" % (nev, cp, r, van, alap))

ki("")
ki("### EREDMENY: egyezik=%d | ELTER=%d | ures bontas=%d" % (egyezik, elter, hianyzik))
if gondok:
    ki("")
    ki("### Reszletek (max 25):")
    for g in gondok:
        ki("  " + g)
else:
    ki("")
    ki("### Egyetlen elteres sincs - a feltevés áll.")

with open(NAPLO, "w", encoding="utf-8") as f:
    f.write("\n".join(sorok) + "\n")
print("\n".join(sorok))
