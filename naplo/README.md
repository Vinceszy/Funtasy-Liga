# Mérési archívum

Egyszeri megfigyelések nyers naplói 2026 augusztusából. **A mérések lezárultak,
a workflow-k törölve** — a fájlok azért maradnak, mert a bennük lévő nyers adat
később még jól jöhet (pl. ha az FPL évközben viselkedést vált, van mihez
hasonlítani). A következtetések a fő README-be kerültek (3/b, „Automatikus
cserék", „Ki van még a pályán", bónusz-szakasz).

| fájl | mit mért | fő tanulság |
|---|---|---|
| `fpl-allapot.txt` + `fpl-figyelo.py` | az FPL forduló-jelzői negyedóránként | nincs napi zárás; a bónusz a forduló lockdownjakor véglegesedik (2026-08-25, 08:03–08:23 UTC, két lépésben) |
| `fpl-percek.txt` + `fpl-perc-meres.py` | játékos-percek élő meccs alatt, 2 percenként | a fixtures `minutes` mindig 0; a meccsóra a játékosok perceinek maximuma; a lecserélt játékos perce befagy; ~3 perc adatkésés |
| `fpl-cserek.txt` + `fpl-csere-meres.py` | a forduló végi automatikus cserék | az FPL átírja a pick `position`-jét és külön `subs` listát is ad; a zárás jelzője a `current_event_finished` |
| `mlsz-adat.txt` + `mlsz-adat-meres.py` | mit ad az MLSZ API az NB1-hez | a meccs-objektumban VAN eredmény; „kezdő volt-e" adat NINCS; a tömeges perc-lekérdezés sorai nem köthetők játékoshoz |
