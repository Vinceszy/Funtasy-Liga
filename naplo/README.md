# Mérési archívum

Egyszeri megfigyelések nyers naplói 2026 augusztusából. A fájlok azért maradnak,
mert a bennük lévő nyers adat
később még jól jöhet (pl. ha az FPL évközben viselkedést vált, van mihez
hasonlítani). A következtetések a fő README-be kerültek (3/b, „Automatikus
cserék", „Ki van még a pályán", bónusz-szakasz).

| fájl | mit mért | fő tanulság |
|---|---|---|
| `fpl-allapot.txt` + `fpl-figyelo.py` | az FPL forduló-jelzői negyedóránként | nincs napi zárás; a bónusz a forduló lockdownjakor véglegesedik (2026-08-25, 08:03–08:23 UTC, két lépésben) |
| `fpl-percek.txt` + `fpl-perc-meres.py` | játékos-percek élő meccs alatt, 2 percenként | a fixtures `minutes` mindig 0; a meccsóra a játékosok perceinek maximuma; a lecserélt játékos perce befagy; ~3 perc adatkésés |
| `fpl-cserek.txt` + `fpl-csere-meres.py` | a forduló végi automatikus cserék | az FPL átírja a pick `position`-jét és külön `subs` listát is ad; a zárás jelzője a `current_event_finished` |
| `proxy-meres.txt` + `proxy-meres.py` | 9 CORS-proxy + a két API közvetlenül, Origin-fejléccel (2026-08-27, élő leállás alatt) | az MLSZ és az FPL válaszában nincs ACAO (direkt böngésző-kérés sosem fog menni); a corsproxy.io 401-re váltott, az allorigins túlterhelt; a `proxy.cors.sh` mindkét API-ra jó — az út-lista a `funtasy.js` lekérőjében eszerint áll |
| `mlsz-adat.txt` + `mlsz-adat-meres.py` | mit ad az MLSZ API az NB1-hez | a meccs-objektumban VAN eredmény; „kezdő volt-e" adat NINCS; a tömeges perc-lekérdezés sorai nem köthetők játékoshoz |
| `mlsz-elo-meccs.txt` + `mlsz-elo-meccs-meres.py` | megkapható-e ÉLŐ fordulónál a meccs két klubja (2026-08-30) | igen, de **csak explicit** `games.home_team`/`games.away_team` include-dal (+2,5 KB, logó nélkül); külön meccs-végpont nincs (10 alak, mind 404); a birtokolt játékosokból csak 4/6 meccs jönne ki, hazai/vendég sehogy |
| `mlsz-dupla-meccs.txt` + `mlsz-dupla-meccs-meres.py` | mit küld az MLSZ, ha egy klubnak **két meccse** van egy fantasy fordulóban (pótolt, elmaradt meccs) — 2026-09-03, MLSZ 7. forduló, Fradi–Győr | **fut** |
