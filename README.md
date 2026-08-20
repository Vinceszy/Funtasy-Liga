# FunTasy Liga — H2H tabella az NB I Fantasy köré

Privát head-to-head liga követő oldal a **fantasy.mlsz.hu** (MLSZ NB I Fantasy) adataira
építve, 8 fős baráti ligához. Statikus oldal GitHub Pages-en: nincs build, nincs függőség,
az `index.html` önmagában fut. Az adatgyűjtést részben GitHub Actions, részben egy
böngészős könyvjelző végzi.

**Élő oldal:** https://vinceszy.github.io/Funtasy-Liga/

---

## 1. Mit tud az oldal

### Tabella
- 8 szakvezető, 33 fordulós körmérkőzéses H2H menetrend
- Pontozás: **győzelem 3 · döntetlen 1 · vereség 0**
- Holtverseny: **1) pont → 2) GK (pontkülönbség) → 3) RG (rúgott pont)**
  *(A liga korábbi Excel-táblája is GK-elsős volt. Ha ezen változtatni kell, egyetlen sort
  érint: a `computeTable()` végén a `.sort(...)`.)*
- Oszlopok: helyezés, név, M, GY, D, V, RG, KG, GK, Pont, Forma (utolsó 5 meccs pöttyökkel)
- A névre kattintva modal nyílik (lásd lentebb)

### Meccsek — két külön panel
- **„Legutóbbi forduló”** — automatikusan az utolsó lejátszottra áll
- **„Következő forduló”** — automatikusan a soron következőre áll
- Mindkettő külön lapozható (‹ › gombok + fordulóválasztó)
- A meccssorra kattintva a két érintett keret egymás mellett jelenik meg

### Egymás elleni mátrix
8×8 rács, minden párosításnál `GY/D/V` az eddigi meccsekből. Mobilon vízszintesen
görgethető, ragadós névoszloppal.

### Modal — három fül
1. **Aktuális keret** — a legutóbb mentett forduló kerete: posztonként rendezve
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

### Mobil
Teljes reszponzív átdolgozás: nincs vízszintes csúszkálás, és **minden oszlop megmarad** —
a táblázatok a saját dobozukban görgethetők, ragadós név-oszloppal. A modal telefonon
teljes képernyős, ragadós × gombbal.

---

## 2. Fájlok

| Fájl | Szerep |
|---|---|
| `index.html` | A teljes oldal — HTML + CSS + JS egyben. A menetrend a `SCHEDULE`, a tagok a `MEMBERS` konstansban vannak beégetve. |
| `results.json` | H2H eredmények archívuma: `{updated, schedule:{"1":[[hazai,vendég,hp,vp],...]}}`. Az oldal ebből tölt, felülírva a beégetett menetrendet. |
| `squads.json` | A legutóbb mentett forduló keretei (`{updated, squads:{név:[játékos,...]}}`) — az „Aktuális keret” fül forrása. |
| `squad_history.json` | Fordulónkénti keret-pillanatképek (`{updated, rounds:{"4":{név:[...]}}}`) — a „Szezon játékosai” fül forrása. |
| `collect.py` | GitHub Actions: az MLSZ ranglista-API-jából beírja a lejátszott fordulók H2H eredményeit a `results.json`-ba. |
| `.github/workflows/archive.yml` | 3 óránként futó munkafolyamat: lefuttatja a `collect.py`-t és commitolja a `results.json` változását. |
| `GOMB-bookmarklet.txt` | A heti keret-mentő könyvjelző (`javascript:` URL, benne `IDE_A_TOKEN` helyőrző). **Ezt kell a böngészőbe illeszteni.** |
| `GOMB-forras.js` | Ugyanaz olvasható forráskódként. **Módosítani ezt kell**, nem a fentit. |
| `GOMB-epites.py` | A `GOMB-forras.js`-ből újragenerálja a `GOMB-bookmarklet.txt`-t. |
| `KERET-MENTES.md` | Használati útmutató a könyvjelzőhöz (token létrehozása, beállítás, heti rutin). |
| `BACKFILL.md` | Elavult: a régi kézi pótlási módszer leírása és annak magyarázata, miért nem kell többé. |

---

## 3. Hogyan frissül az adat

### Automatikusan (GitHub Actions, 3 óránként)
`archive.yml` → `collect.py` → az MLSZ **ranglista-végpontja** minden IP-ről elérhető, tehát
a H2H eredmények (tabella, meccsek) teljesen automatikusan frissülnek. Nincs teendő.

### Hetente egy kattintással (könyvjelző)
A **keret-végpont** csak valódi böngészőből érhető el (lásd „Ismert korlátok”), ezért:

1. Megnyitod a **fantasy.mlsz.hu**-t
2. Rákattintasz a `Keret mentés` könyvjelzőre
3. A szkript megnézi, mely fordulók hiányoznak a `squad_history.json`-ból, csak azokat kéri
   le, és a GitHub API-n keresztül commitolja a `squad_history.json`-t és a `squads.json`-t

A könyvjelző egy **fine-grained personal access tokent** tartalmaz (csak a `Funtasy-Liga`
repóra, csak `Contents: Read and write` joggal). A repóban a token mindig helyőrző.

---

## 4. Az MLSZ Fantasy API — amit a fejlesztés során kiderítettünk

Base URL: `https://fantasy-api.mlsz.hu/competitions/3/`
Nincs hivatalos dokumentáció; az alábbiak kísérletezéssel derültek ki.

### Ranglista (minden IP-ről működik)
```
GET /rankings?include=user_team.user.id,summary_statistics,ranking,rounds,competition_rank
    &page=1&per_page=20&filter[search]={felhasználónév}
```
Visszaad: `user_team.user.id`, `user_team.round_statistics[]` (`round_id`, `round_number`,
`points`), összpont, helyezés.

### Keret (CSAK valódi böngészőből, bejelentkezve)
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

### Miért nem megy szerverről a keret-lekérés
GitHub Actionsből, proxykon át és Playwright-tal (valódi Chrome) is **403** — de a felhasználó
saját böngészőjéből működik. A ranglista-végpont viszont mindenhonnan elérhető.

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
- **A könyvjelző a böngésződ másolatából fut**, nem a repóból. A repóban lévő
  `GOMB-bookmarklet.txt` biztonsági mentés és dokumentáció — ha módosul, a böngészőben lévő
  könyvjelzőt **kézzel kell frissíteni**.

---

## 6. Ha módosítani kell

Nincs build lépés, nincs függőség: az `index.html` önmagában fut. A JS a fájl végén, egyetlen
`<script>` blokkban van. Fontosabb belépési pontok:

- `computeTable()` — tabella-logika és holtverseny-sorrend
- `renderMatches(which)` — a két meccspanel
- `showSquad(names, tab)` — a modal
- `squadHTML()` / `seasonHTML()` / `playersHTML()` — a három fül tartalma
- `boot()` — betöltés: `results.json` → render → csendes élő frissítés

**Vigyázat a CSS-osztálynevekkel:** a `.pos` a *pozitív számok zöld színe*, a poszt-címke
`.ppos`. Egyszer már ütköztek, és emiatt a GY/V eredmények dobozkaként jelentek meg.

**A könyvjelző módosítása:** szerkeszd a `GOMB-forras.js`-t, futtasd a
`python3 GOMB-epites.py`-t, majd frissítsd a böngészőben lévő könyvjelzőt az új tartalommal.
A `GOMB-bookmarklet.txt`-t soha ne szerkeszd kézzel.

---

## 7. Tervezett, még nem elkészült

- **FPL Draft aloldal** — az angol Fantasy Premier League Draft-liga (48093) követése külön
  `draft.html` oldalon, `collect_draft.py` gyűjtővel. A végpont
  (`https://draft.premierleague.com/api/league/48093/details`) egyszerre adja a résztvevőket,
  a teljes H2H menetrendet és az eredményeket, tehát menetrendet sem kellene kézzel bevinni.
  CORS-tiltás miatt böngészőből nem hívható, ezért szerveroldalon kellene futnia — **nyitott
  kérdés, hogy átmegy-e a lekérés a GitHub Actions adatközponti IP-jéről.**
  *Ez a rész még nincs feltöltve a repóba.*
- Kapitány-hatékonysági toplista
- „Padon hagyott pontok” toplista
- Ligán belüli tulajdonlási arányok
