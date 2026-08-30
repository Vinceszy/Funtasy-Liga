#!/usr/bin/env python3
"""EGYSZERI meres: megkaphato-e az ELO fordulo meccsenek KET KLUBJA?

BEJELENTETT HIBA: a 6. fordulo profil-soraban "-" all az ellenfel helyen,
pedig az eredmenyt tudjuk. Ok: elo fordulonal a keret-valasz meccs-objektuma
klub NELKUL jon, ezert a meccsek.json-ba "?" kerul (mind a hat meccsnel).
Lezart fordulonal a ket csapat teljes objektuma is jon - ezert volt jo az
1-5. fordulo, amit mar lezartan toltottunk le.

A kerdes: van-e ut, amivel ELOBEN is megvan a ket klub? ADDIG NEM allitunk
semmit, amig nem mertuk. Ot kerdes:

  A) Mit tartalmaz MA, elo fordulonal a meccs-objektum? (teljes kulcslista)
  B) Megjon-e a ket csapat, ha EXPLICIT keruk az include-ban? A repo sajat
     tapasztalata, hogy az MLSZ egyes beagyazott mezoket csak explicit
     keresre ad vissza - a current_round maga is pont igy viselkedett elo
     fordulonal (2026-08-21). Harom include-alakot probalunk, es merjuk a
     valasz meretet is (a lezart fordulos 118 KB-ot a base64 klublogo adja).
  C) Van-e KULON meccs-vegpont a mar ismert azonositora? A menetrend-
     vegpontokat 2026-08-25-en vegigmertuk (mind 404), de ott a JOVOBELI
     menetrendet kerestuk, listakent - egy KONKRET meccs lekerese nem volt
     kozte.
  D) Levezetheto-e sajat adatbol? Ugyanazt a meccset a KET klub jatekosai
     is hozzak, es minden jatekos-rekordban ott a sajat klubja. Ha mindket
     oldalrol van birtokolt jatekos, a ket klub kiderul - a hazai/vendeg
     oldal viszont NEM. Megmerjuk, hany meccsnel jonne ossze.
  E) A pont-bontas vegpontja (game-player-stats) tud-e a meccsrol? Ez a
     hivas a lenyilohoz amugy is megy, tehat ha tudja, ingyen van.

Csak olvas; a naplot a workflow commitolja.

ADATVEDELEM: a repo publikus. MLSZ user_id nem kerul a naploba; a base64
kepadatot levagjuk.
"""
import json, os, sys, urllib.parse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import collect

NAPLO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mlsz-elo-meccs.txt")
sorok = []
ki = sorok.append


def rovidit(v, hossz=120):
    if isinstance(v, dict):
        return {k: rovidit(x, hossz) for k, x in v.items()}
    if isinstance(v, list):
        return [rovidit(x, hossz) for x in v[:3]]
    if isinstance(v, str) and len(v) > hossz:
        return "<%d karakteres szoveg>" % len(v)
    return v


def keres(url):
    """(HTTP, json, meret) - a meretet a nyers valaszbol becsuljuk."""
    st, j = collect.api_get(url)
    meret = len(json.dumps(j)) if j is not None else 0
    return st, j, meret


# ---- melyik a most elo fordulo? ----
akt, _ = collect.versenyfordulok()
R = int(os.environ.get("MERES_FORDULO") or akt or 6)
ki("=== MERES: elo fordulo = %s. (MLSZ szerinti aktualis: %s) ===" % (R, akt))

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

egy_uid = next(iter(ids.values()))

# ---- A) a MAI meccs-objektum ----
ki("")
ki("=== A) elo fordulos meccs-objektum a JELENLEGI include-dal ===")
st, j, meret = keres(collect.BASE + "user-team-players-history?include="
                     + urllib.parse.quote(collect.INCLUDE
                         + ",competition_player.current_round.games")
                     + "&filter%5Buser_id%5D=" + str(egy_uid)
                     + "&filter%5Bround_id%5D=" + str(collect.rid(R)))
ki("HTTP %s, valasz ~%.1f KB" % (st, meret / 1024))
minta_id = None
for d in (j or {}).get("data") or []:
    cr = (d.get("competition_player") or {}).get("current_round") or {}
    for g in cr.get("games") or []:
        if isinstance(g, dict):
            ki("a meccs-objektum OSSZES kulcsa: %s" % sorted(g.keys()))
            ki(json.dumps(rovidit(g), ensure_ascii=False, indent=1))
            minta_id = g.get("id")
            break
    if minta_id:
        break
if not minta_id:
    ki("! egyetlen meccs-objektum sem jott vissza")

# ---- B) explicit csapat-include ----
ki("")
ki("=== B) megjon-e a ket csapat, ha EXPLICIT keruk? ===")
G = "competition_player.current_round.games"
for cimke, extra in [
        ("games.home_team + games.away_team", G + ".home_team," + G + ".away_team"),
        ("games.homeTeam + games.awayTeam", G + ".homeTeam," + G + ".awayTeam"),
        ("games.teams", G + ".teams")]:
    st, j, meret = keres(collect.BASE + "user-team-players-history?include="
                         + urllib.parse.quote(collect.INCLUDE + "," + G + "," + extra)
                         + "&filter%5Buser_id%5D=" + str(egy_uid)
                         + "&filter%5Bround_id%5D=" + str(collect.rid(R)))
    van = set()
    for d in (j or {}).get("data") or []:
        cr = (d.get("competition_player") or {}).get("current_round") or {}
        for g in cr.get("games") or []:
            if isinstance(g, dict):
                van |= {k for k in g.keys() if "team" in k.lower()}
    ki("  %-34s HTTP %-4s ~%6.1f KB  csapat-mezok: %s"
       % (cimke, st, meret / 1024, sorted(van) or "NINCS"))

# ---- B2) MI VAN a csapat-objektumban? (a nevet ebbol vesszuk) ----
ki("")
ki("=== B2) a mukodo include csapat-objektuma: mi van benne? ===")
st, j, meret = keres(collect.BASE + "user-team-players-history?include="
                     + urllib.parse.quote(collect.INCLUDE + "," + G
                         + "," + G + ".home_team," + G + ".away_team")
                     + "&filter%5Buser_id%5D=" + str(egy_uid)
                     + "&filter%5Bround_id%5D=" + str(collect.rid(R)))
ki("HTTP %s, valasz ~%.1f KB" % (st, meret / 1024))
kiirt = False
for d in (j or {}).get("data") or []:
    cr = (d.get("competition_player") or {}).get("current_round") or {}
    for g in cr.get("games") or []:
        if isinstance(g, dict) and g.get("home_team") and not kiirt:
            ki("a TELJES meccs-objektum (base64 levagva):")
            ki(json.dumps(rovidit(g), ensure_ascii=False, indent=1))
            ht = g.get("home_team") or {}
            ki("home_team kulcsai: %s" % sorted(ht.keys()))
            ki("van-e logo (ez hizlalta 118 KB-ra a lezart forduloas valaszt)? %s"
               % ("IGEN" if ht.get("logo") else "nincs"))
            ki("short_name=%r  name=%r" % (ht.get("short_name"), ht.get("name")))
            kiirt = True
    if kiirt:
        break
if not kiirt:
    ki("! egyetlen meccsnel sem jott csapat-objektum")

# ---- C) kulon meccs-vegpont a mar ismert azonositora ----
ki("")
ki("=== C) van-e KULON vegpont egy konkret meccsre? (id=%s) ===" % minta_id)
if minta_id:
    for ut in ["games/%s", "game/%s", "matches/%s", "match/%s", "fixtures/%s"]:
        for elotag, nev in ((collect.ROOT, "gyoker"), (collect.BASE, "competitions/3")):
            u = elotag + (ut % minta_id)
            st, j, meret = keres(u)
            ki("  %-14s %-22s HTTP %-4s %s"
               % (nev, ut % minta_id, st,
                  ("~%.1f KB" % (meret / 1024)) if st == 200 else ""))
            if st == 200 and j:
                ki(json.dumps(rovidit(j), ensure_ascii=False, indent=1)[:1200])

# ---- D) levezetheto-e a ket klub a sajat keretekbol? ----
ki("")
ki("=== D) a ket klub levezetese a birtokolt jatekosok klubjaibol ===")
meccs_klubjai = {}
for nev, uid in ids.items():
    st, j = collect.squad(uid, R, jatek=True)
    if st != 200 or not isinstance(j, dict):
        continue
    for d in j.get("data") or []:
        cp = d.get("competition_player") or {}
        klub = ((cp.get("team") or {}).get("short_name")
                or (cp.get("team") or {}).get("name"))
        cr = cp.get("current_round") or {}
        for g in cr.get("games") or []:
            if isinstance(g, dict) and g.get("id") is not None and klub:
                meccs_klubjai.setdefault(g["id"], set()).add(klub)
ki("meccsek, amikrol tudunk: %d" % len(meccs_klubjai))
ketto = 0
for gid, klubok in sorted(meccs_klubjai.items()):
    if len(klubok) >= 2:
        ketto += 1
    ki("  %s: %s" % (gid, " + ".join(sorted(klubok))))
ki("MINDKET oldal megvan: %d / %d meccsnel" % (ketto, len(meccs_klubjai)))
ki("(a hazai/vendeg oldal ebbol NEM derul ki)")

# ---- E) tud-e a meccsrol a pont-bontas vegpontja? ----
ki("")
ki("=== E) a game-player-stats valasz ismer-e meccset? ===")
cp_id = None
st, j = collect.squad(egy_uid, R, jatek=False)
for d in (j or {}).get("data") or []:
    cp_id = (d.get("competition_player") or {}).get("id")
    if cp_id:
        break
if cp_id:
    for inc in ["competition_stat_config", "competition_stat_config,game",
                "competition_stat_config,game.home_team,game.away_team"]:
        u = (collect.ROOT + "game-player-stats?include=" + urllib.parse.quote(inc)
             + "&filter%5Bcompetition_player_id%5D=" + str(cp_id)
             + "&filter%5Bround_id%5D=" + str(collect.rid(R)))
        st, j, meret = keres(u)
        kulcsok = set()
        for s in (j or {}).get("data") or []:
            kulcsok |= set(s.keys())
        ki("  include=%-48s HTTP %-4s kulcsok: %s" % (inc, st, sorted(kulcsok)))

open(NAPLO, "w", encoding="utf-8").write("\n".join(sorok) + "\n")
print("\n".join(sorok))
