# Mérési archívum

Egyszeri megfigyelések nyers naplói. A fájlok azért maradnak, mert a bennük lévő
nyers adat később még jól jöhet (pl. ha az FPL évközben viselkedést vált, van
mihez hasonlítani). A következtetések a fő README-be kerültek (3/b, „Automatikus
cserék", „Ki van még a pályán", bónusz-szakasz).

Minden mérés **egy** munkafolyamattal indul (`.github/workflows/naplo-meres.yml`):
a fejlesztői környezet hálózata minden külső forrást blokkol, ezért Actionsből
futnak. Paramétert a `kornyezet` bemenet ad át (`NÉV=érték` soronként).

A fordulónkénti **kitöltött szín-táblázat** is itt áll (`nb1-colour-<forduló>.json`):
soronként egy állítás `{játékos, perc, tag, mondat, horgony, meccs}` alakban. Az
írások ebből készülnek, nem a cikkek szövegéből — így minden mondat visszakereshető,
és a horgony dönti el, hogy tényként, hivatkozva vagy sehogy nem mondható ki. A
módszer egy helyen: `round-pipeline.md`.

Itt van két **szabály-dokumentum** is, nem mérés: a `summary-voice.md` (hogyan
szólhat egy meccsről szóló szöveg) és a `colour-taxonomy.md` (milyen tényt
nevezünk színnek, és melyik forrásból jöhet). Ezek a Nemzethy Sport írásaira
vonatkoznak.

| fájl | mit mért | fő tanulság |
|---|---|---|
| `fpl-allapot.txt` + `fpl-figyelo.py` | az FPL forduló-jelzői negyedóránként | nincs napi zárás; a bónusz a forduló lockdownjakor véglegesedik (2026-08-25, 08:03–08:23 UTC, két lépésben) |
| `fpl-percek.txt` + `fpl-perc-meres.py` | játékos-percek élő meccs alatt, 2 percenként | a fixtures `minutes` mindig 0; a meccsóra a játékosok perceinek maximuma; a lecserélt játékos perce befagy; ~3 perc adatkésés |
| `fpl-cserek.txt` + `fpl-csere-meres.py` | a forduló végi automatikus cserék | az FPL átírja a pick `position`-jét és külön `subs` listát is ad; a zárás jelzője a `current_event_finished` |
| `proxy-meres.txt` + `proxy-meres.py` | 9 CORS-proxy + a két API közvetlenül, Origin-fejléccel (2026-08-27, élő leállás alatt) | az MLSZ és az FPL válaszában nincs ACAO (direkt böngésző-kérés sosem fog menni); a corsproxy.io 401-re váltott, az allorigins túlterhelt; a `proxy.cors.sh` mindkét API-ra jó — az út-lista a `funtasy.js` lekérőjében eszerint áll |
| `mlsz-adat.txt` + `mlsz-adat-meres.py` | mit ad az MLSZ API az NB1-hez | a meccs-objektumban VAN eredmény; „kezdő volt-e" adat NINCS; a tömeges perc-lekérdezés sorai nem köthetők játékoshoz |
| `mlsz-elo-meccs.txt` + `mlsz-elo-meccs-meres.py` | megkapható-e ÉLŐ fordulónál a meccs két klubja (2026-08-30) | igen, de **csak explicit** `games.home_team`/`games.away_team` include-dal (+2,5 KB, logó nélkül); külön meccs-végpont nincs (10 alak, mind 404); a birtokolt játékosokból csak 4/6 meccs jönne ki, hazai/vendég sehogy |
| `ertekelesek.txt` + `ertekeles-lekeres.py` | mit mondtak az olvasók az írásokról (a Worker `/ertekelesek` végpontja) | a darabszám, az 1–4 eloszlás és cikkenkénti bontás kerül a naplóba; **az indokok csak a futás naplójában** látszanak, a repóba nem kerülnek be |
| `mlsz-jatekoslista.txt` + `mlsz-jatekoslista-meres.py` | van-e az MLSZ-nél **jövőbeli menetrend** (a profil következő ellenfeleihez), és mennyire pontos a játékos alappontja | önálló meccs-végpont nincs (~25 alak, mind 404); a játékos alappontja **mindig 0,25 többszöröse** (238 forduló, kivétel nélkül), tehát a padfelezés kerekítése visszaszámolható |
| `draft-round-harvest.py` | egy Draft-forduló fantasy-rétege a saját adatunkból (kezdők pontja, a padon maradt pont, nullázók, heti mozgás) — a `round-colour-harvest.py` PL-párja | hálózat nem kell hozzá; a Draftban nincs kapitány és nincs közös játékos, tehát a tét a felállítás és a waiver |
| `tarolo-meres.txt` + `tarolo-meres.py` | a Worker „utolsó ismert állás" tárolója végponttól végpontig | a tárolt válasz ~35× gyorsabban jön, mint a friss lekérés; változatlan adatnál az időbélyeg nem íródik újra |
| `fpl-profil.txt` + `fpl-profil-meres.py` | az FPL `detail` szövegének alakja (`BHA (A) 4-0`) | a számpár mindig **hazai–vendég** sorrendben áll, nem a játékos szemszögéből — enélkül minden idegenbeli meccs fordítva látszana |
| `match-event-sources.txt` + `match-event-sources.py`, `official-sources-probe.py` | van-e percre pontos meccs-esemény kulcs nélkül | a nagy adatszolgáltatók 403-at adnak vagy tiltják a robots-ban; a hivatalos oldalak szöveges közvetítése marad |
| `esemeny-forras.txt` + `esemeny-forras-meres.py` | ugyanez kulcsos szolgáltatóval (ESPN, API-Football) | kulcs nélkül 403; kulccsal is csak a nagy ligákra |
| `beszamolo-forras.txt` + `beszamolo-forras-meres.py`, `nemzetisport-meres.py`, `nso-content-probe.py` | magyar meccsbeszámolók elérhetősége az NB1-hez | a Nemzeti Sport **engedi** a cikkoldalakat (a `robots.txt` csak a `/hirdetesek`, `/cikk-elonezet`, `/publicapi` utat tiltja), és a `sitemapindex.xml` a cikkek gépi jegyzéke — **ez az NB1 színes forrása**. Az első mérés tévesen tiltást jelzett: az alapértelmezett urllib-ügynök 403-at kap a `robots.txt`-re, amire a `RobotFileParser` mindent tiltottnak vesz. A beszámolók szövege csak a futás naplójába kerül, a repóba soha |
| `pl-colour.txt` + `pl-colour-probe.py`, `pl-colour-harvest.py` (`pl-colour-4.json`), `round-colour-harvest.py` | honnan jöhet a PL-fordulók színezése kulcs nélkül | a FotMob engedi és **strukturáltan** adja (gól perce és módja, VAR, kihagyott helyzetek, védések); ebből készül a forduló gyűjtése |
| `draft-picks.txt` + `draft-picks-probe.py`, `draft-picks-harvest.py` | mit tudunk meg a saját draftunkról és a tranzakciókról | a `choices` kulcs nélkül elérhető (ebből lett a `draft_picks.json`); a waiver-előzmény **bejelentkezéshez kötött** (403), ezért nem gyűjtjük |
| `mlsz-dupla-meccs.txt` + `mlsz-dupla-meccs-meres.py` | mit küld az MLSZ, ha egy klubnak **két meccse** van egy fantasy fordulóban (pótolt, elmaradt meccs) — 2026-09-03, MLSZ 7. forduló | az ETO `current_round.games` listája **két elemű**: `3F` (ETO–FTC, szept. 3., a halasztott 3. fordulós meccs) és `7F` (ETO–HONVÉD, szept. 6.). Az MLSZ tehát a **pótlás napja szerinti** fordulóba teszi a meccset, de meghagyja rajta az **eredeti forduló számát**. Minden más klubnak 1 eleme volt. |
