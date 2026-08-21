# FunTasy — privát fantasy-ligák H2H követése

Privát head-to-head liga követő oldalak baráti ligákhoz: a **fantasy.mlsz.hu** (MLSZ NB I
Fantasy) és az **FPL Draft** adataira építve. Statikus oldal GitHub Pages-en: nincs build,
nincs függőség. Az adatgyűjtés **teljesen automatikus** (GitHub Actions, 3 óránként) — a
böngészős könyvjelző már csak tartalék.

| Oldal | Cím |
|---|---|
| Kezdőlap (ligaválasztó) | https://vinceszy.github.io/Funtasy-Liga/ |
| FunTasy NB1 | https://vinceszy.github.io/Funtasy-Liga/nb1/ |
| FunTasy PL | https://vinceszy.github.io/Funtasy-Liga/pl/ |

A régi `draft.html` cím átirányít a `/pl/`-re, hogy a korábbi linkek ne haljanak el.

A résztvevőket mindkét oldalon a **monogram** azonosítja (a név mögött) — személyenként
azonos a két ligában, ez lesz a kulcs a majdani összesítő oldalhoz.

---

## 1. Mit tud az oldal

### Tabella
- 8 szakvezető, 33 fordulós körmérkőzéses H2H menetrend
- Pontozás: **győzelem 3 · döntetlen 1 · vereség 0**
- Holtverseny az NB1-ben: **1) pont → 2) KÜL (pontkülönbség) → 3) SP (szerzett pont)**;
  a PL-ben az FPL alappontozása szerint **a szerzett pont az első** holtverseny-szempont
  (a `tiebreak: 'rg'` opció a `pl/index.html`-ben)
  *(A liga korábbi Excel-táblája is pontkülönbség-elsős volt. Ha ezen változtatni kell,
  egyetlen sort érint: a `funtasy.js`-ben a `computeTable()` végén a `.sort(...)`.)*
- **A tabella csak lezárt fordulókból számol.** A folyamatban lévő forduló eredményei a
  meccspanelen látszanak, „élő” jelöléssel — a tabellát nem mozgatják, amíg a forduló
  le nem zárul.
- Oszlopok: helyezés, név, M, GY, D, V, SP (szerzett pont), KP (kapott pont),
  KÜL (pontkülönbség), Pont, Forma (utolsó 5 meccs pöttyökkel)
- A névre kattintva modal nyílik (lásd lentebb)

### Meccsek — két külön panel
- **„Legutóbbi forduló”** — automatikusan az utolsó lejátszottra áll
- **„Következő forduló”** — automatikusan a soron következőre áll
- Mindkettő külön lapozható (‹ › gombok + fordulóválasztó)
- A meccssorra kattintva a két érintett keret egymás mellett jelenik meg —
  **fordulóhűen**: az adott forduló akkori keretei, az akkori pontokkal, a fejlécben a
  hivatalos fordulópontszámmal (jövőbeli fordulónál magyarázó szöveg)
- **Élő (még tartó) meccsre kattintva** a két keret jön, játékosonkénti élő pontokkal:
  azonnal a tárolt (legfeljebb 3 órás) állapot, majd a háttérben percre frissre cserélve.
- **A meccs adatlapjának tetején eredménysor áll** (`Bazsa 41 : 36,63 Vince`), a főoldali
  meccspanelekkel azonos megjelenéssel; élő meccsnél szaggatott kerettel és `élő` jelvénnyel.
  Enélkül az állás csak a két keret-oszlop fejlécében szerepelt külön-külön. Az eredménysor
  és az oszlopfejlécek **ugyanabból a számításból** jönnek, tehát nem mondhatnak mást.
  Ha a fordulóhoz még semmilyen keret-adat nincs, tartalékként ez a szöveg jön:
  *„A meccs még tart, a keretek által szerzett pontok a forduló zárta után elérhetőek.”*

### Egymás elleni mátrix
8×8 rács, minden párosításnál `GY/D/V` az eddigi meccsekből. Mobilon vízszintesen
görgethető, ragadós névoszloppal. **A cellára kattintva** modal nyílik a két csapat
összes egymás elleni párosításával: lejátszott meccsek eredménnyel és GY/D/V-vel
(a sor-játékos szemszögéből), élő meccs élő jelöléssel, jövőbeliek „— : —"-mal.
A sorra kattintva a meccs részletei nyílnak meg. Mindkét oldalon így működik.

### Modal — három fül
1. **Aktuális keret** — lezárt fordulónál a legutóbbi forduló kerete, a fejlécben a
   **hivatalos fordulópontszámmal**; élő forduló közben az élő meccskeret, megnyitáskor
   **percre frissre** húzott pontokkal (a felirat ilyenkor „élő pontösszeg"-et mond).
   Posztonként rendezve
   (GK → DEF → MID → ST), magyar játékosoknál piros-fehér-zöld zászlócska (CSS-ből rajzolva,
   **nem emoji** — a Windows Chrome a zászló-emoji helyett „HU” betűpárt mutatna), U21-eseknél
   kék `U21` címke, kapitánynál `C ×2`. Külön **magyarszabály-sáv** (hány magyar kezdő, ebből
   hány U21, jár-e a +10), a fejlécben a **hivatalos fordulópontszám**, és külön összegsor a
   kezdőkre és a padra.
2. **Fordulók** — a szakvezető teljes szezonja fordulónként (ellenfél, saját pont, ellenfél
   pontja, GY/D/V), fent a mérleggel. Sorra kattintva a meccs részletei nyílnak meg.
   A **folyamatban lévő forduló sorában az élő állás** látszik `élő` jelöléssel; a mérlegbe
   (GY/D/V) nem számít bele, ahogy a tabellába sem.
3. **Szezon játékosai** — minden játékos, aki valaha a keretben volt, a nála termelt ponttal,
   hány fordulóban volt nála, hányszor kezdő/pados, hányszor kapitány. Fent: hány fordulóban
   teljesült a magyarszabály (+10-ek összege), a magyar játékosok pontja, ebből az U21-eseké.

### A FunTasy PL aloldal
Ugyanaz a felépítés (tabella, meccspanelek, mátrix, modal három füllel, élő állások),
a Premier League lila színvilágában, az FPL Draft sajátosságaival:
- csapatnevek + monogram (a mátrixban csak monogramok), holtversenynél a szerzett pont dönt
- nincs kapitány és magyarszabály; a pad pontjai nem számítanak a csapatnak
- élő állás forduló közben: a kezdőcsapatok a forduló indulásakor rögzülnek (a repóban
  vannak), a böngésző csak a nyilvános játékos-pontokat kéri le percre frissen, és abból
  összegez minden meccset
- a „Szezon játékosai" fül és a meccs-keretek a GW1 indulásától gyűlnek

### Pont-bontás (accordion) és a „még nem játszott” jelölés
Mindkét oldalon, minden keret-nézetben (aktuális keret, meccs-keretek, élő meccs):

- **A játékos sorára kattintva** a sor alatt kinyílik a pont-bontás: esemény, érték, pont
  (pl. „Győzelem · 1 · 3”, „Percek a pályán (több, mint 60 perc) · 90 · 2”). Csak a pontot
  érő sorok látszanak, ahogy az MLSZ felülete is mutatja. A kapitány ×2 és a pad ×0,5 külön
  sorként jelenik meg, mert a kiírt heti pont ezeket már tartalmazza, a bontás sorai viszont
  a nyers értékek. Újrakattintás zár; másik játékosra kattintva az előző bezárul — egyszerre
  egy panel van nyitva. A bontást a böngésző kéri le kattintáskor (ugyanazokon a
  CORS-proxykon át, mint minden élő lekérés), és a megnyitott játékosokét megjegyzi.
- **A kattinthatóságot a név után álló kis nyíl (▼) jelzi**, ami nyitáskor átfordul, fölötte
  pedig egy súgósor áll („A játékos nevére kattintva…”). A nyíl azért a név után van és nem
  a sor végén, mert ott védett: a szűk oszlopban az ellipszis előbb a klub-címkét vágja le.
  Egérrel a sor ki is világosodik, de a nyíl a lényeg — **telefonon nincs hover**.
- **Ha nincs pontot érő esemény, az üzenet megmondja, miért** — hat eset, mert a 0-nak
  többféle oka lehet: *a klubnak nincs meccse ebben a fordulóban* (elmaradt/elhalasztott,
  a PL-en üres forduló), *a meccs még nem kezdődött el* (a kezdés időpontjával),
  *a meccs zajlik, eddig nincs pontot érő eseménye*, *a meccs véget ért, de a pontok
  feldolgozása még tart*, *lejátszotta a meccset pont nélkül*, vagy *nem lépett pályára*. Az elsőt a forduló meccslistája mondja meg (lásd lent),
  a következőket a kezdési idő, a meccs állapota és a lejátszottság, az utolsó kettőt a
  bontás játszott-perc sora (ez 0 perccel is megjön, ha a játékos végig a kispadon ült).

  **A lefújás és a pontok megjelenése között idő telik el**, és ez mindkét ligában
  megtévesztő tud lenni. Az NB1-en az `is_played` órákkal a meccs vége után vált át, ezért
  a meccslista `status` mezőjét is eltesszük (`vege`) — abból tudjuk, hogy a meccsnek már
  vége, csak a pontok nincsenek meg. A PL-en az FPL **két lépésben** zárja a meccset:
  a `finished_provisional` a lefújáskor igaz, a `finished` csak a bónuszpontok
  véglegesítésekor — ezért a kettő közül bármelyik elég ahhoz, hogy lejátszottnak vegyük.
  (Enélkül a már lejátszott meccsre is azt írtuk: „a meccs zajlik".)
- **Ahol a kezdés időpontja még nincs kitűzve**, ott csak a dátum jelenik meg
  („kezdés: aug. 29. (időpont még nincs kitűzve)") — az MLSZ ilyenkor éjfélt ír, amit
  hiba lenne valódi kezdésként kiírni.
- **Élő forduló közben a 0 pontos játékosok kétfélék**: aki még nem játszott (a meccse el
  sem kezdődött), annak a pontja helyén **kötőjel** áll; aki épp játszik vagy már játszott
  és 0-n áll, annál **0** — a fantasy-oldalak szokása szerint. Az NB1-en ezt a keret-válasz
  `is_played` és `first_played_at` mezője adja, a PL-en a forduló meccs-állapotai (fixtures).

### Navigáció a modalon belül
A modal kis böngészőként működik: a listák soraira kattintva a tartalom cserélődik
(pl. Fordulók → egy meccs két kerete), és a fejlécben megjelenő **‹ vissza** gomb az
előző nézetre lép. Az ×, a félrekattintás és az Escape mindig az egészet zárja.
Nincs modal a modalban. Mindkét oldalon ugyanígy működik.

### Mobil
Teljes reszponzív átdolgozás: nincs vízszintes csúszkálás, és **minden oszlop megmarad** —
a táblázatok a saját dobozukban görgethetők, ragadós név-oszloppal. A modal telefonon
teljes képernyős, ragadós × gombbal.

---

## 2. Fájlok

| Fájl | Szerep |
|---|---|
| `index.html` | **Kezdőlap: ligaválasztó.** A kártyákat a `funtasy.js` `LIGAK` listájából rajzolja, saját adatot nem tölt. |
| `nb1/index.html` | A FunTasy NB1 oldal (korábban a gyökér `index.html`). Csak az oldalspecifikus HTML + JS; a menetrend a `SCHEDULE`, a tagok a `MEMBERS` konstansban beégetve. |
| `pl/index.html` | A FunTasy PL oldal (korábban `draft.html`). |
| `draft.html` | Átirányító a régi PL-címről a `/pl/`-re. Új hivatkozás ne ide mutasson. |
| `funtasy.css` | A közös stíluslap (mindhárom oldal ezt tölti). |
| `funtasy.js` | A közös motor: tabella, meccspanelek, mátrix, élő-jelölés (`FunTasy.create(...)`), a pont-bontás accordionja és a **ligalista** (`LIGAK`), amiből a ligaváltó sáv és a kezdőlap kártyái készülnek. |
| `results.json` | H2H eredmények archívuma: `{updated, provisional:[...], schedule:{"1":[[hazai,vendég,hp,vp],...]}}`. Az oldal ebből tölt, felülírva a beégetett menetrendet. A `provisional` a még le nem zárult fordulók listája. |
| `squads.json` | A legutóbbi elérhető forduló keretei (`{updated, round, squads:{név:[játékos,...]}}`) — az „Aktuális keret” fül forrása; a `round` mondja meg, hányadik fordulóé. A játékos-rekord a könyvjelző mezőin felül `id`-t (MLSZ játékos-azonosító, a pont-bontáshoz), `played`-et („játszott már?”), `start`-ot (az adott fordulós meccsének kezdése), `vege: true`-t (a meccse már lement, akkor is, ha a pontok még nincsenek feldolgozva) és — ha a klubnak nincs meccse a fordulóban — `nogame: true`-t is tartalmaz. A régebbi, e mezők nélküli rekordokat az oldal tolerálja. |
| `squad_history.json` | Fordulónkénti keret-pillanatképek (`{updated, rounds:{"4":{név:[...]}}}`) — a „Szezon játékosai” fül forrása. A rekord-formátum a `squads.json`-éval azonos. |
| `collect.py` | GitHub Actions: H2H eredmények (ranglista-végpont) **és** keretek (keret-végpont) gyűjtése, forduló-lezárás megállapítása, kimaradt fordulók pótlása. |
| `collect_draft.py` | GitHub Actions: az FPL Draft liga adatai. A résztvevők valódi nevét és az `entry_id`-t kiszűri (a repó publikus). |
| `draft.json` | Az FPL Draft liga adatai (résztvevők, menetrend, eredmények) — a `pl/index.html` forrása. |
| `draft_players.json` | FPL játékos-törzs: `{players: {id: {n: név, t: klub, p: poszt}}, teams: {csapat_id: rövidnév}}`. A `teams` a fixtures-válasz csapat-azonosítóinak feloldásához kell (kinek kezdődött el a meccse). |
| `draft_squads.json` | A jelenlegi FPL-keretek (tulajdonlás): `{liga_id: [játékos_id,...]}`. |
| `draft_history.json` | Fordulónkénti FPL-keretek pontokkal (`{rounds:{gw:{liga_id:[{e,b,pts},...]}}}`) — a GW1 indulásától gyűlik. |
| `.github/workflows/archive.yml` | 3 óránként futó munkafolyamat: `collect.py` + commit. |
| `.github/workflows/draft.yml` | 3 óránként futó (és kézzel is indítható) munkafolyamat: `collect_draft.py` + commit. |
| `tartalek/` | Minden, ami nem kell a napi működéshez: a tartalék könyvjelző (`GOMB-bookmarklet.txt`, forrása és építője), az útmutatója (`KERET-MENTES.md`) és az elavult kézi pótlás leírása (`BACKFILL.md`). A weboldal és a gyűjtők semmit nem olvasnak innen. |

---

## 3. Hogyan frissül az adat

### Minden automatikusan megy (GitHub Actions, 3 óránként)

Az `archive.yml` a `collect.py`-t futtatja, ami **mindent** frissít, teendő nélkül:

1. **H2H eredmények** a ranglista-végpontról (hivatalos fordulópontszámok — ez a tabella
   egyetlen forrása).
2. **Keretek** a keret-végpontról: az aktuális forduló (élő játékos-pontokkal), az utolsó
   lezárt (hogy az utólagos MLSZ-korrekciók átjöjjenek), és minden hiányzó forduló.
3. **Forduló-lezárás**: egy forduló akkor végleges, ha minden szakvezető minden játékosa
   lejátszotta a meccsét (`is_played`). Addig a forduló a `provisional` listában van, és az
   oldal nem számolja a tabellába.
4. **Keresztellenőrzés**: a keretekből számolt pontszámot összeveti a hivatalossal, és a
   naplóban jelzi, ha az MLSZ utólag korrigált.

### Az FPL Draft adatai (3 óránként, draft.yml)

A `collect_draft.py` a liga-adatokon túl a játékos-törzset, a jelenlegi kereteket
(tulajdonlás) és — a GW1 indulásától — a fordulónkénti kereteket gyűjti, pontokkal.
A résztvevők valódi neve és `entry_id`-ja soha nem kerülhet a repóba (mentés előtti szűrő).

### Élő frissítés a böngészőből (mindkét oldal)

Betöltéskor mindkét oldal percre friss adatot kér CORS-proxykon át: az NB1 a
ranglista-végpontról az eredményeket (és kattintásra a kereteket), a PL a játékosonkénti
élő pontokat, amikből a meccsállásokat összegzi. Hiba esetén a tárolt (3 óránként
frissülő) állapot marad, a státuszsávban jelzéssel; folyamatban lévő fordulónál a szöveg:
*„Automata lekérés hiba: az állások a forduló végén frissülnek."*

### Tartalék: a böngészős könyvjelző

Ha a szerveroldali gyűjtés elromlana (pl. az MLSZ tényleg letiltaná az adatközponti
IP-ket), a keretek a `Keret mentés` könyvjelzővel menthetők a böngésződből — beállítása:
[`tartalek/KERET-MENTES.md`](tartalek/KERET-MENTES.md). A könyvjelző fine-grained tokent használ (csak erre
a repóra, csak `Contents: Read and write`); a repóban a token mindig helyőrző.

---

## 4. Az MLSZ Fantasy API — amit a fejlesztés során kiderítettünk

Base URL: `https://fantasy-api.mlsz.hu/competitions/3/`
Nincs hivatalos dokumentáció; az alábbiak kísérletezéssel derültek ki.

### Ranglista
```
GET /rankings?include=user_team.user.id,summary_statistics,ranking,rounds,competition_rank
    &page=1&per_page=20&filter[search]={felhasználónév}
```
Visszaad: `user_team.user.id`, `user_team.round_statistics[]` (`round_id`, `round_number`,
`points`), összpont, helyezés.

**Alapból csak az utolsó lezárt és az aktuális fordulót adja vissza.** Régebbi forduló a
`&filter[round_id]={rid}` paraméterrel kérhető le (a válasz az adott fordulót **és** az
előzőt tartalmazza) — így egy kimaradt forduló hivatalos pontjai utólag is pótolhatók.

### Keret (bárhonnan működik — ha jól kérdezed)
```
GET /user-team-players-history?include={INCLUDE}&filter[user_id]={id}&filter[round_id]={rid}
```

**Három buktató, mindegyik órákat vitt el:**

1. **`filter[round_id]` kötelező.** Enélkül 403 Forbidden. (Kezdetben enélkül is működött,
   majd szigorítottak rajta menet közben — ez okozta a „hirtelen elromlott” élményt.)
2. **`round_id = 75 + 2 × fordulószám`** (1.→77, 2.→79, 3.→81, 4.→83, 5.→85). Ezzel a
   **korábbi fordulók keretei visszamenőleg is lekérhetők**, nem csak az aktuális.
3. **A `position` reláció csak akkor jön vissza, ha a `position.alternatives`-t is bekéred.**
   Enélkül a `position` mező egyszerűen hiányzik a válaszból, hibaüzenet nélkül.
4. **A `competition_player.current_round` reláció élő fordulónál csak explicit include-dal
   jön vissza** (lezárt fordulónál enélkül is megjelenik). Belőle jön az `is_played`
   („játszott már?” jelzés és forduló-lezárás) és a `first_played_at` (a játékos adott
   fordulós meccsének kezdése) — ezért kötelező eleme az include-nak.

**Működő include (bizonyított):**
```
position,position.alternatives,competition_player,competition_player.team,
competition_player.countries,competition_player.current_round,summary_statistics
```

**Fontos:** a név **közvetlenül a `competition_player`-ben** van (`first_name`/`last_name`),
NEM egy beágyazott `player` objektumban. A poszt a `position.monogram` (K/H/KP/CS).

### Ki nem játszik a fordulóban (a meccslista)
A `competition_player.current_round.games` include játékosonként megadja a klub **adott
fordulóbeli** meccsét (`start_at`, `status`, `round_number`). Ha a lista **üres**, a
klubnak nincs meccse abban a fordulóban — ez a biztos jelzés az elmaradt/elhalasztott
fordulóra (mérve: Honvéd, 5. forduló).

**Fontos csapda:** ilyenkor a `first_played_at` a klub **következő** meccsére mutat, egy
másik forduló időpontjára. Ebből tehát nem szabad a fordulóra következtetni — ez okozta
a „furcsa kezdési időpont" hibát (Csontos, 5. forduló: aug. 29. 00:00, ami valójában a
6. forduló dátuma, kitűzött időpont nélkül).

**Az include ára fordulófüggő** (mérve, 15 játékos):

| A forduló állapota | Alap | `games`-szel |
|---|---|---|
| élő (a meccsek `scheduled`) | 17,8 KB | 19,7 KB |
| lezárt (a meccsek `completed`) | 17,5 KB | 118,8 KB |

A különbség oka: a **lejátszott** meccs mellé az API a két csapat teljes objektumát is
beteszi, benne a klublogóval, base64 képadatként. Ezért a gyűjtő a meccslistát **csak az
élő fordulóra** kéri; a lezártakhoz a forduló alatt már elmentett jelzés marad meg
(`collect.py` → `orokit_nogame`).

### Pont-bontás (game-player-stats)
A felület játékos-modalja ezt hívja (a bundle-ből visszafejtve, 2026-08-21):
```
GET https://fantasy-api.mlsz.hu/game-player-stats
    ?include=competition_stat_config
    &filter[competition_player_id]={cp_id}&filter[round_id]={rid}
```
**A `competitions/3/` előtag NÉLKÜL** — közvetlenül az API gyökerén él. Fordulónként
22 sort ad: `{value, points, round_id, competition_stat_config:{name}}` — a `name` a
magyar eseménynév („Győzelem”, „Kulcspasszok”, „Percek a pályán (több, mint 60 perc)”…).
A felület a 0 pontos sorokat elrejti, a kapitány ×2 / csere ×0,5 sort a kliens teszi
hozzá — mi is így csináljuk. A `cp_id` a keret-válasz `competition_player.id` mezője
(az új keret-rekordokban `id` néven tárolva; a régiekhez az oldal név alapján oldja fel
a forduló keretéből). Bárhonnan, bejelentkezés nélkül működik.

Létezik még: `GET competitions/3/stat-configs` (a 10 szezonstatisztika-kategória neve) és
`stat-leaders` (toplisták) — jelenleg egyiket sem használjuk.

### A pontszámítás kulcsa
A `weekly_points` **már kész érték**: tartalmazza a kapitányi duplázást és a pad felezését.
A csapat fordulópontszáma tehát:

```
összes játékos weekly_points összege + (magyarszabály teljesül ? 10 : 0)
```

Ellenőrizve a 4. fordulón két csapaton: 67,5 (kezdők) + 3,75 (pad) + 10 = **81,25** ✓,
illetve 63,25 + 2,5 + 10 = **75,75** ✓ — mindkettő pontosan a hivatalos pontszám.
**Soha ne szorozz újra ×2-vel a kapitánynál és ne felezz a padnál.**

### A „szerverről tilos” tévhit története
Sokáig azt hittük, a keret-végpont adatközponti IP-kről tiltott: GitHub Actionsből,
proxykon át és Playwright-tal is 403 jött. 2026-08-20-án kiderült: **a 403-at a hiányzó
`filter[round_id]` okozta** — a szerveres próbák még a paraméter felfedezése előtt
készültek. Helyes kéréssel a végpont bárhonnan, **bejelentkezés nélkül** működik
(bizonyíték: ugyanarról a gépről, ugyanabban a másodpercben paraméter nélkül 403,
paraméterrel 200). Egy megkötés maradt: **a még el nem kezdődött forduló keretei 403-at
adnak** — piaczárásig titkosak.

### Forduló-lezárás és utólagos MLSZ-korrekciók
- A keret-válasz `current_round.is_played` mezője megmondja, lejátszotta-e a játékos a
  meccsét. **Egy forduló akkor zárult le, ha mindenkinél mindenki játszott.** A halasztott
  meccs játékosait az MLSZ lejátszottnak jelöli 0 ponttal (igazolva a 3. fordulós
  ETO–Fradi esetén), tehát a halasztás nem akasztja meg a lezárást.
- **Az MLSZ utólag korrigálhat** játékos-statisztikát, és átvezeti a hivatalos
  fordulóösszegre is. Megtörtént: Csendi 1–3. fordulós pontjai a lezárás után változtak
  (+1, +1, −2,5). Ezért a `collect.py` mindig a lekért értékhez szinkronizál, és a
  keretből számolt összeget összeveti a hivatalossal — eltérésnél a naplóban jelez.

### Az FPL Draft API (draft.premierleague.com/api/) — mérésekkel igazolva

- `league/{id}/details` — résztvevők, menetrend, eredmények; **a valódi neveket is
  tartalmazza**, ezért nyers válasz soha nem kerül a repóba
- `bootstrap-static` — játekos-törzs (599 játékos, klubok, posztok)
- `league/{id}/element-status` — ki birtokolja most az adott játékost; az `owner` mező
  azonosító-terét futáskor kell felismerni (liga-id vagy entry_id lehet)
- `entry/{entry_id}/event/{gw}` — heti keret (kezdő/pad); **a forduló indulásáig 404-et
  ad**, ez várható viselkedés
- `event/{gw}/live` — játékosonkénti heti pontok; nyilvános, ebből megy az élő állás.
  Az elemek `explain` mezője a kész pont-bontás (esemény, érték, pont — angol nevekkel;
  az oldal a `stat` kulcs alapján fordítja magyarra). A még nem játszott játékosnál is van
  `explain` (0 perccel), ezért a „játszott már?” jelzéshez nem elég — arra a fixtures való.
- `event/{gw}/fixtures` — a forduló meccsei `started` / `finished` állapottal,
  `kickoff_time`-mal és csapat-azonosítókkal; ebből tudjuk, kinek kezdődött már el a
  meccse (kötőjel vs 0) és mikor kezdődik. Az oldal klubonként **összevonja** az
  állapotokat: „indult", ha bármelyik meccse elkezdődött, „kész", ha mindegyik lement —
  dupla fordulón ugyanis egy klubnak két meccse van. Ha egy klub **egyáltalán nem
  szerepel** a forduló meccsei között, akkor üres fordulója van (blank gameweek): a
  játékosai kötőjelet kapnak, és a bontás is ezt írja ki
- `game` — `current_event`: a folyamatban lévő forduló száma (vagy null)

---

## 5. Ismert korlátok, buktatók

- **A GitHub Pages gyorsítótáraz** — feltöltés után 1-2 percig a régi fájl jöhet. Ctrl+F5.
- **A `results.json`-ba 0–0 nem kerülhet be**: a le nem zárt forduló minden játékosnál 0 pontot
  ad, amit a rendszer lejátszott döntetlennek hinne. A `collect.py`-ban van rá védelem
  (`if not hp and not vp: continue`). Ez egy már majdnem bekövetkezett adatrontás volt.
- **A mentett `price` a lekérés pillanatának piaci ára**, nem az adott fordulóé. Visszamenőleg
  pótolt fordulóknál tehát nem historikus érték. Az oldal jelenleg nem jeleníti meg, de
  árfolyam-statisztikát erre a mezőre építeni nem szabad.
- **Halasztott meccsek:** a Ferencváros európai kupaszereplése miatt az ellenfelének fordulója
  elmaradhat. Ilyenkor az érintett klub játékosai 0 pontot kapnak.
- **A könyvjelző (tartalék) a böngésződ másolatából fut**, nem a repóból. Ha a
  `tartalek/GOMB-bookmarklet.txt` módosul, a böngészőben lévő könyvjelzőt kézzel kell frissíteni.
- **A PL-en a GW első óráiban** (amíg a gyűjtő először le nem tárolja a forduló kereteit,
  legfeljebb ~3 óra) élő meccsállás még nem számolható — utána percre pontos.
- **A régi keret-rekordokban nincs `id`, `played` és `start` mező** (a pont-bontás és a
  „még nem játszott” jelölés 2026-08-21-én került be). A bontás náluk is működik (az oldal
  név alapján oldja fel az azonosítót a forduló keretéből), de a kötőjel-jelölés csak az
  új gyűjtésű adatoknál él — a régi 0-k számként látszanak, ami lezárt fordulónál helyes is.
- **A „nincs meccse a fordulóban" jelzés a forduló alatt rögzül**, és a lezárás után már
  nem frissül (a lezárt fordulóra nem kérjük le a meccslistát, mert hatszor akkora
  válasz jönne). Ez helyes is: az MLSZ az elmaradt meccs játékosait lejátszottnak jelöli
  0 ponttal, tehát a pótlás nem ír már a forduló pontjaiba.
- **A pont-bontás sorait a magyar eseménynév azonosítja** (pl. a „nem lépett pályára”
  eset a „Játszott perc” sor 0 értékéből derül ki). Az API nem ad stabil kulcsot ezekhez,
  úgyhogy ha az MLSZ átnevez egy eseményt, az oldal a részletesebb üzenet helyett az
  általánosabbra esik vissza — hibát nem okoz, de a szövegek pontatlanabbak lesznek.
- **Élő lekérés a böngészőből:** az oldal betöltéskor közvetlenül is lekéri a friss
  eredményeket (CORS-proxykon át). Ha ez elromlik, a státuszsávban jelzi; folyamatban
  lévő fordulónál a szöveg: *„Automata lekérés hiba: az állások a forduló végén
  frissülnek.”* A tárolt (3 óránként frissülő) adat ilyenkor is látszik.

---

## 6. Ha módosítani kell

Nincs build lépés, nincs függőség. A kód három rétegben él:

- **`funtasy.css`** — a közös stíluslap (mindkét oldal ezt tölti; itt van minden szín,
  rács, táblázat- és modal-stílus).
- **`funtasy.js`** — a közös motor: `FunTasy.create({...})` kapja a konfigurációt
  (menetrend, résztvevők, elemazonosítók), és adja a `computeTable`, `renderTable`,
  `renderMatches`, `renderMatrix` függvényeket, az élő-jelölést és az egymás elleni
  lista építőjét (`h2hHTML` — a mátrix-cella kattintása nyitja, `onMatrixClick`).
  A create-en kívül itt él a pont-bontás accordion közös mechanikája is
  (`FunTasy.accToggle` — nyit/zár/egyszerre egy panel; `FunTasy.accTable` — a bontás
  táblázata); a tartalmat az oldalak saját `bontasHTML`-je adja, mert a forrás más
  (NB1: MLSZ `game-player-stats`, PL: FPL `event/{gw}/live` explain).
- **`nb1/index.html` / `pl/index.html`** — csak az oldalspecifikus rész: konfiguráció, betöltés
  és élő frissítés, meg az oldal saját modalja (a főoldalon `showSquad` / `showMatchRound` /
  `squadHTML` / `seasonHTML` / `playersHTML`, a PL-en `showTeam` / `showMatch` /
  `keretHTML` / `fordulokHTML` / `jatekosokHTML`). A modalon belüli lapozást mindkét
  oldalon ugyanaz a kis nézet-verem viszi (`vShow` / `vBack`): a belépési pont `root`,
  a fülváltás `replace`, a listából nyíló nézet `push` — a vissza gomb ebből él.

### Új liga felvétele

A webhely szerkezete mappánként egy liga, hogy a cím a ligáról szóljon és bővíthető legyen:

```
/            index.html      – kezdőlap (ligaválasztó)
/nb1/        index.html      – FunTasy NB1
/pl/         index.html      – FunTasy PL
             funtasy.css/js  – közös réteg (a gyökérben)
             *.json          – adatfájlok (a gyökérben, az oldalak ../ úton érik el)
```

Új liga hozzáadása:

1. Egy új bejegyzés a `funtasy.js` **`LIGAK`** listájába (azonosító, név, mappa, cím,
   leírás, téma). Ebből az **egy** listából készül a ligaváltó sáv minden oldal tetején
   **és** a kezdőlap kártyája — máshol nem kell hozzányúlni.
2. Új mappa a saját `index.html`-lel. A közös fájlokra `../funtasy.css?v=N` és
   `../funtasy.js?v=N` hivatkozik, az adatra `../valami.json`, a sávot pedig egy sor
   rajzolja ki: `FunTasy.renderNav('<azonosító>','../')`.
3. Ha új témaszínek kellenek: egy `body.liga-<azonosító>` blokk a `funtasy.css`-ben
   (a változónevek maradnak, csak az értékük más), és a kártya színe a
   `.ligakartya[data-liga="<azonosító>"]` szabályokban.

A linkek **relatívak** (`../pl/`), mert a GitHub Pages aloldalon szolgál ki
(`/Funtasy-Liga/`), tehát abszolút `/pl/` út rossz helyre mutatna.

**Verziójelzés:** a két oldal a közös fájlokat `funtasy.css?v=N` / `funtasy.js?v=N`
formában tölti. **Ha a `funtasy.css` vagy a `funtasy.js` változik, a `?v=` számot mindkét
oldalon léptetni kell** — különben a böngészők a régi motort tölthetik az új oldal alá
(oldal/motor verziócsúszás: az új HTML régi JS-sel fut, nehezen felismerhető hibákkal).

**Vigyázat a CSS-osztálynevekkel:** a `.pos` a *pozitív számok zöld színe*, a poszt-címke
`.ppos`. Egyszer már ütköztek, és emiatt a GY/V eredmények dobozkaként jelentek meg.

**A tartalék könyvjelző módosítása:** szerkeszd a `tartalek/GOMB-forras.js`-t, futtasd a
mappában a `python3 GOMB-epites.py`-t, majd frissítsd a böngészőben lévő könyvjelzőt az új
tartalommal. A `GOMB-bookmarklet.txt`-t soha ne szerkeszd kézzel.

---

## 7. Tervezett, még nem elkészült

- Összesítő oldal a két liga (NB1 + PL) közös követésére — a résztvevők összekötése
  (a `pl/index.html` `NEVEK` konstansa és a közös monogramok) már megvan
- Kapitány-hatékonysági toplista
- „Padon hagyott pontok” toplista
- Ligán belüli tulajdonlási arányok
