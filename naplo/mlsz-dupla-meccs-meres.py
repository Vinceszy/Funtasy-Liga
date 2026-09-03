#!/usr/bin/env python3
"""EGYSZERI meres: mit kuld az MLSZ, ha egy klubnak KET meccse van egy
fantasy forduloban?

BEJELENTETT HIBA (2026-09-03): az MLSZ fantasy 7. forduloja NEM csak a 7.
jateknap - benne van egy ELMARADT, potolt meccs is (Fradi-Gyor, szept. 3.).
A gyujto ezt nem tudja: a meccsek.json 7. forduloja hat meccset ismer
(szept. 4-6.), a szept. 3-it egyaltalan nem, es MIND A KILENC ETO-jatekos
`nogame: True` jelolest kapott - vagyis a gyujto szerint az ETO-nak NINCS
meccse a forduloban, holott KETTO van.

A GYANU a kodban (collect.py jatek_mezok): a fuggveny csak a `games[0]`-t
nezi, es ha annak a round_number-e nem a kert fordulo, azonnal "nincs
meccse"-t mond. Ha a potolt meccs az EREDETI fordulo szamat viszi (pl.
"2F"), es az all a lista elejen, akkor a klub OSSZES tobbi meccse elveszik.

DE NEM ALLITUNK SEMMIT, AMIG NEM MERTUK. Kerdesek:

  A) Hany elem van egy ETO-jatekos current_round.games listajaban, es
     mi az egyes elemek round_number / start_at / status erteke?
  B) Ugyanez egy FTC-jatekosra (a masik erintett klub).
  C) Ugyanez egy NEM erintett klub jatekosara (kontroll: ott egy elem van-e).
  D) Mit mond a MOSTANI jatek_mezok() ezekre a valaszokra?
  E) A potolt meccsen szerepel-e a ket klub (home_team/away_team), es
     egyaltalan ott van-e a listaban?

Csak olvas; a naplot a workflow commitolja.

ADATVEDELEM: a repo publikus. MLSZ user_id nem kerul a naploba; a base64
kepadatot levagjuk.
"""
import json, os, sys, urllib.parse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import collect

NAPLO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mlsz-dupla-meccs.txt")
sorok = []
ki = sorok.append


def rovidit(v, hossz=80):
    if isinstance(v, dict):
        return {k: rovidit(x, hossz) for k, x in v.items()}
    if isinstance(v, list):
        return [rovidit(x, hossz) for x in v]
    if isinstance(v, str) and len(v) > hossz:
        return "<%d karakteres szoveg>" % len(v)
    return v


akt, _ = collect.versenyfordulok()
R = int(os.environ.get("MERES_FORDULO") or akt or 7)
ki("=== MERES: klub KET meccsel egy forduloban - %s. fordulo ===" % R)
ki("(MLSZ szerinti aktualis fordulo: %s)" % akt)

ids = {}
for nev, uname in collect.MEMBERS.items():
    row = collect.rankings(uname)
    uid = (((row or {}).get("user_team") or {}).get("user") or {}).get("id")
    if uid:
        ids[nev] = uid
ki("elert resztvevok: %d / %d" % (len(ids), len(collect.MEMBERS)))
if not ids:
    ki("! a ranglista nem valaszolt - a meres nem futtathato")
    open(NAPLO, "w", encoding="utf-8").write("\n".join(sorok) + "\n")
    raise SystemExit(0)

GAMES = collect.GAMES
inc = (collect.INCLUDE + "," + GAMES + "," + GAMES + ".home_team,"
       + GAMES + ".away_team")

# Minden resztvevo keretet vegignezzuk, es klubonkent egy jatekost valasztunk.
klub_minta = {}          # rovid klubnev -> (jatekosnev, games lista)
for nev, uid in ids.items():
    st, j = collect.api_get(
        collect.BASE + "user-team-players-history?include=" + urllib.parse.quote(inc)
        + "&filter%5Buser_id%5D=" + str(uid)
        + "&filter%5Bround_id%5D=" + str(collect.rid(R)))
    if st != 200 or not j:
        continue
    for d in (j.get("data") or []):
        cp = d.get("competition_player") or {}
        team = (cp.get("team") or {}).get("short_name") or ""
        cr = cp.get("current_round") or {}
        if team and team not in klub_minta:
            klub_minta[team] = (cp.get("last_name") or "?", cr.get("games"))

ki("")
ki("=== A-C) klubonkent a current_round.games lista ===")
for team in sorted(klub_minta):
    nev_, games = klub_minta[team]
    if games is None:
        ki("%-8s %-22s games: NINCS (nem jott vissza a mezo)" % (team, nev_))
        continue
    ki("%-8s %-22s games: %d elem" % (team, nev_, len(games)))
    for g in games:
        g = g or {}
        h = (g.get("home_team") or {}).get("short_name") or "?"
        v = (g.get("away_team") or {}).get("short_name") or "?"
        ki("           round_number=%-6s start=%-26s status=%-12s %s - %s"
           % (g.get("round_number"), g.get("start_at"), g.get("status"), h, v))
    # D) mit mond a mostani logika
    ki("           MOSTANI jatek_mezok(fordulo=%s) -> %s"
       % (R, collect.jatek_mezok({"games": games}, R)))

ki("")
ki("=== E) van-e szept. 3-i meccs BARMELYIK klub listajaban? ===")
talalt = []
for team, (nev_, games) in klub_minta.items():
    for g in (games or []):
        s = (g or {}).get("start_at") or ""
        if s[:10] == "2026-09-03":
            talalt.append((team, rovidit(g)))
if talalt:
    for team, g in talalt:
        ki("%s: %s" % (team, json.dumps(g, ensure_ascii=False)))
else:
    ki("NINCS szept. 3-i meccs egyetlen klub listajaban sem.")

ki("")
ki("=== KOVETKEZTETES ===")
tobb = [t for t, (_, g) in klub_minta.items() if g and len(g) > 1]
ki("tobb meccses klub a listaban: %s" % (", ".join(sorted(tobb)) or "nincs"))
nogame = [t for t, (_, g) in klub_minta.items()
          if g is not None and collect.jatek_mezok({"games": g}, R).get("nogame")]
ki("a mostani logika szerint 'nincs meccse': %s" % (", ".join(sorted(nogame)) or "nincs"))

open(NAPLO, "w", encoding="utf-8").write("\n".join(sorok) + "\n")
print("\n".join(sorok))
