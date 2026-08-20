# FunTasy Liga — H2H tabella az NB I Fantasy köré

Privát head-to-head liga követő oldal a **fantasy.mlsz.hu** (MLSZ NB I Fantasy) adataira
építve, 8 fős baráti ligához. Statikus oldal GitHub Pages-en: nincs build, nincs függőség.
Az adatgyűjtés **teljesen automatikus** (GitHub Actions, 3 óránként) — a böngészős
könyvjelző már csak tartalék.

**FunTasy NB1 (élő oldal):** https://vinceszy.github.io/Funtasy-Liga/
**FunTasy PL (rejtett aloldal, a főoldal nem hivatkozik rá):** https://vinceszy.github.io/Funtasy-Liga/draft.html

A résztvevőket mindkét oldalon a **monogram** azonosítja (a név mögött) — személyenként
azonos a két ligában, ez lesz a kulcs a majdani összesítő oldalhoz.

---

## 1. Mit tud az oldal

### Tabella
- 8 szakvezető, 33 fordulós körmérkőzéses H2H menetrend
- Pontozás: **győzelem 3 · döntetlen 1 · vereség 0**
- Holtverseny az NB1-ben: **1) pont → 2) KÜL (pontkülönbség) → 3) SP (szerzett pont)**;
  a PL-ben az FPL alappontozása szerint **a szerzett pont az első** holtverseny-szempont
  (a `tiebreak: 'rg'` opció a `draft.html`-ben)
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
- A meccssorra kattintva a két érintett keret egymás mellett jelenik meg
- **Élő (még tartó) meccsre kattintva** a két keret jön, játékosonkénti élő pontokkal:
  azonnal a tárolt (legfeljebb 3 órás) állapot, majd a háttérben percre frissre cserélve.
  Ha a fordulóhoz még semmilyen keret-adat nincs, tartalékként ez a szöveg jön:
  *„A meccs még tart, a keretek által szerzett pontok a forduló zárta után elérhetőek.”*

### Egymás elleni mátrix
8×8 rács, minden párosításnál `GY/D/V` az eddigi meccsekből. Mobilon vízszintesen
görgethető, ragadós névoszloppal. **A cellára kattintva** modal nyílik a két csapat
összes egymás elleni párosításával: lejátszott meccsek eredménnyel és GY/D/V-vel
(a sor-játékos szemszögéből), élő meccs élő jelöléssel, jövőbeliek időponttal —
a sorra kattintva a meccspanel az adott fordulóra ugrik. Mindkét oldalon így működik.

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
   pontja, GY/D/V), fent a mérleggel. Sorra kattintva bezárul a modal, és a „Legutóbbi
   forduló” panel arra a fordulóra ugrik.
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

### Mobil
Teljes reszponzív átdolgozás: nincs vízszintes csúszkálás, és **minden oszlop megmarad** —
a táblázatok a saját dobozukban görgethetők, ragadós név-oszloppal. A modal telefonon
teljes képernyős, ragadós × gombbal.

---

## 2. Fájlok

| Fájl | Szerep |
|---|---|
| `index.html` | A főoldal. Csak az oldalspecifikus HTML + JS van benne; a menetrend a `SCHEDULE`, a tagok a `MEMBERS` konstansban beégetve. |
| `funtasy.css` | A közös stíluslap (`index.html` és `draft.html` is ezt tölti). |
| `funtasy.js` | A közös motor: tabella, meccspanelek, mátrix, élő-jelölés (`FunTasy.create(...)`). |
| `results.json` | H2H eredmények archívuma: `{updated, provisional:[...], schedule:{"1":[[hazai,vendég,hp,vp],...]}}`. Az oldal ebből tölt, felülírva a beégetett menetrendet. A `provisional` a még le nem zárult fordulók listája. |
| `squads.json` | A legutóbbi elérhető forduló keretei (`{updated, round, squads:{név:[játékos,...]}}`) — az „Aktuális keret” fül forrása; a `round` mondja meg, hányadik fordulóé. |
| `squad_history.json` | Fordulónkénti keret-pillanatképek (`{updated, rounds:{"4":{név:[...]}}}`) — a „Szezon játékosai” fül forrása. |
| `collect.py` | GitHub Actions: H2H eredmények (ranglista-végpont) **és** keretek (keret-végpont) gyűjtése, forduló-lezárás megállapítása, kimaradt fordulók pótlása. |
| `collect_draft.py` | GitHub Actions: az FPL Draft liga adatai. A résztvevők valódi nevét és az `entry_id`-t kiszűri (a repó publikus). |
| `draft.json` | Az FPL Draft liga adatai (résztvevők, menetrend, eredmények) — a `draft.html` forrása. |
| `draft_players.json` | FPL játékos-törzs: `{id: {n: név, t: klub, p: poszt}}` (599 játékos). |
| `draft_squads.json` | A jelenlegi FPL-keretek (tulajdonlás): `{liga_id: [játékos_id,...]}`. |
| `draft_history.json` | Fordulónkénti FPL-keretek pontokkal (`{rounds:{gw:{liga_id:[{e,b,pts},...]}}}`) — a GW1 indulásától gyűlik. |
| `draft.html` | Az FPL Draft aloldal. A stílusa az `index.html`-ével közös (`funtasy.css`). |
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

**Működő include (bizonyított):**
```
position,position.alternatives,competition_player,competition_player.team,
competition_player.countries,summary_statistics
```

**Fontos:** a név **közvetlenül a `competition_player`-ben** van (`first_name`/`last_name`),
NEM egy beágyazott `player` objektumban. A poszt a `position.monogram` (K/H/KP/CS).

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
- `event/{gw}/live` — játékosonkénti heti pontok; nyilvános, ebből megy az élő állás
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
- **`index.html` / `draft.html`** — csak az oldalspecifikus rész: konfiguráció, betöltés
  és élő frissítés, meg az oldal saját modalja (a főoldalon `showSquad` / `squadHTML` /
  `seasonHTML` / `playersHTML`, a PL-en `showTeam` / `showMatch` / `keretHTML` /
  `fordulokHTML` / `jatekosokHTML`).

**Vigyázat a CSS-osztálynevekkel:** a `.pos` a *pozitív számok zöld színe*, a poszt-címke
`.ppos`. Egyszer már ütköztek, és emiatt a GY/V eredmények dobozkaként jelentek meg.

**A tartalék könyvjelző módosítása:** szerkeszd a `tartalek/GOMB-forras.js`-t, futtasd a
mappában a `python3 GOMB-epites.py`-t, majd frissítsd a böngészőben lévő könyvjelzőt az új
tartalommal. A `GOMB-bookmarklet.txt`-t soha ne szerkeszd kézzel.

---

## 7. Tervezett, még nem elkészült

- Összesítő oldal a két liga (NB1 + PL) közös követésére — a résztvevők összekötése
  (a `draft.html` `NEVEK` konstansa és a közös monogramok) már megvan
- Kapitány-hatékonysági toplista
- „Padon hagyott pontok” toplista
- Ligán belüli tulajdonlási arányok
