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
- **„Különbségek” nézet (csak salary cap ligában, tehát az NB1-en):** az állás alatti
  kapcsoló két csoportra bontja a kereteket — **közös** és **eltérő** játékosokra —, mert
  a közösek pontja kiüti egymást, a meccset az eltérők döntik el.

  **A bal/jobb szerkezet végig megmarad** (bal oszlop az egyik szakvezető, jobb a másik):
  asztali gépen a közös játékosok **mindkét oszlopban** ott vannak, ugyanazokkal a
  számokkal. A szem azonnal látja, hogy a két rész egyezik; ha külön blokkba emelnénk,
  megtörne a megszokott elrendezés. **Mobilon** viszont az oszlopok egymás alá kerülnek,
  ott a duplikálás csak hosszabbítaná a lapot: egy közös blokk áll elöl, utána a két
  szakvezető a saját eltérő játékosaival. A váltást CSS végzi, nincs átméretezés-figyelés.

  Minden csoport alatt **összesítő sor** áll (a keret-fejléccel azonos megjelenéssel):
  *Közös összesen*, *Eltérő összesen*, végül *<név> összesen* — az utolsó a csapat teljes
  fordulópontszáma, és a fenti kettő összege pontosan ezt adja ki.

  **Az azonossághoz nem elég a névegyezés:** a kapitányság és a kezdő/pad szerep is
  számít, mert azoktól más a játékos pontja (Szalai kezdőként 10, kapitányként 20 — az nem
  azonos tétel). **A magyarszabály (+10) ugyanúgy tétel:** ha mindkét keret megkapja, a
  közös csoportba kerül; ha csak az egyik, akkor mindkét oldalon az eltérők közé (a
  másiknál 0-val).

  A PL-oldalon szándékosan nincs ilyen nézet: draft ligában egy játékos egy csapatban
  lehet, tehát közös tétel nem is fordulhat elő.

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

### A FunTasy PL oldal
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
  pedig egy súgósor áll („Kattints egy játékosra a pontjai részletezéséhez.”). A nyíl azért a név után van és nem
  a sor végén, mert ott védett: a szűk oszlopban az ellipszis előbb a klub-címkét vágja le.
  Egérrel a sor ki is világosodik, de a nyíl a lényeg — **telefonon nincs hover**.
- **Ha nincs pontot érő esemény, az üzenet megmondja, miért** — hét eset, mert a 0-nak
  többféle oka lehet: *a klubnak nincs meccse ebben a fordulóban* (elmaradt/elhalasztott,
  a PL-en üres forduló), *a meccs még nem kezdődött el* (a kezdés időpontjával),
  *a meccs elmaradt, új időpontja nincs kitűzve*, *a meccs zajlik, eddig nincs pontot érő
  eseménye*, *a meccs véget ért, de a pontok feldolgozása még tart*, *lejátszotta a
  meccset pont nélkül*, vagy *nem lépett pályára*. Az elsőt a forduló meccslistája mondja
  meg (lásd lent), a következőket a kezdési idő, a meccs állapota és a lejátszottság, az
  utolsó kettőt a bontás játszott-perc sora (ez 0 perccel is megjön, ha a játékos végig a
  kispadon ült).

  Két helyen az **idő** is számít a szövegben. A „nincs meccse" lezárt fordulóban múlt
  időben áll, mert a „nem játszik" hetekkel később hamis. A „még nem kezdődött el" pedig
  csak addig szól kezdési időpontról, amíg a dátum a jövőben van: az MLSZ éjfélt ír a
  kitűzetlen kezdésre, és az a nap el is múlhat — onnantól a mondat elmaradt meccsről
  szól, nem ígér kezdést.

  **Az `is_played` NEM azt jelenti, hogy a meccsnek vége.** Az MLSZ már a meccs *közben*
  igazra billenti. Emiatt írtuk élő forduló alatt gyakorlatilag mindenkire, hogy
  „lejátszotta a meccset, pontot érő esemény nélkül" — miközben a meccs javában ment.

  Élő fordulóban ezért a **meccs állapota** dönt, nem a lejátszottság. Egyetlen helyen,
  a `meccsAllapot()`-ban, négy értékkel: *előtte* / *fut* / *utána* / *ismeretlen* — így a
  játékos sora és a pont-bontás soha nem mondhat mást ugyanarról a meccsről.

  A szabály **két időkorláton** áll, és mindkettőnek konkrét oka van:

  - **100 perc alatt a `vege` jelzést nem hisszük el.** Egy meccs 2×45 perc + szünet +
    hosszabbítás, tehát ennyi idő alatt fizikailag nem érhet véget. Azt ugyanis *nem
    tudtuk ellenőrizni*, hogy az MLSZ mikor billenti át a meccslista `completed` mezőjét —
    ha ugyanúgy tenné, mint az `is_played`-del (menet közben), akkor egy naiv javítás
    semmit nem oldana meg. Így a javítás **független ettől a nyitott kérdéstől**.
  - **180 perc után nem állítjuk, hogy fut**, akkor sem, ha `vege` jelzés nem érkezett.
    A `vege` ugyanis nem mindig áll rendelkezésre (a 2026-08-21 előtti keret-rekordokban
    nincs is ilyen mező).

  Ha nincs kitűzött kezdési idő (az MLSZ ilyenkor éjfélt ír), a meccset **nem** tekintjük
  elkezdettnek.

  **Mért tény: az MLSZ a 0 pontos játékosra ÜRES pont-bontást ad vissza.** Bizonyíték:
  Heitor (Újpest) 0 ponttal üres listát kapott, miközben klubtársa, Ljujić — ugyanabból a
  meccsből — 1,75-öt, tehát a meccs fel volt dolgozva. Az üres bontás tehát **nem** jelent
  feldolgozatlan meccset. Egy ideig erre alapoztunk („a lejátszotta állításhoz kell egy
  bontás-sor"), és emiatt a valóban 0 pontos, rég lement meccsű játékosra azt írtuk, hogy
  „a pontok feldolgozása még tart". A meccs közbeni tévedés ellen nem ez véd, hanem a
  fenti állapot-kapu.

  **A lefújás és a pontok megjelenése között is idő telik el.** A PL-en az FPL **két
  lépésben** zárja a meccset: a `finished_provisional` a lefújáskor igaz, a `finished`
  csak a bónuszpontok véglegesítésekor — ezért a kettő közül bármelyik elég ahhoz, hogy
  lejátszottnak vegyük. (Enélkül a már lejátszott meccsre is azt írtuk: „a meccs zajlik".)

- **A „meccs zajlik" szövege ligánként más, mert a forrás is más** (`eloPontok` mező a
  `LIGAK`-ban). A PL-en az FPL percről percre adja a pontot, tehát a 0 tényleg azt jelenti,
  hogy *eddig* nem volt pontot érő eseménye. Az MLSZ viszont csak a meccs után rögzíti a
  pontokat, ott ilyen állapot sosem áll elő — ezért az NB1-en az „eddig nincs pontot érő
  eseménye" hamis ígéret volt, és helyette az áll, hogy *az MLSZ a pontokat a meccs végén
  rögzíti*.
- **Ahol a kezdés időpontja még nincs kitűzve**, ott csak a dátum jelenik meg
  („kezdés: aug. 29. (időpont még nincs kitűzve)") — az MLSZ ilyenkor éjfélt ír, amit
  hiba lenne valódi kezdésként kiírni.
- **Élő forduló közben a 0 pontos játékosoknál kötőjel áll, ha nincs róluk adat.** Két
  ilyen eset van: aki még nem játszott (a meccse el sem kezdődött), és — **csak az
  NB1-en** — akinek a meccse épp fut. Az MLSZ ugyanis a pontokat csak a meccs után
  rögzíti (`eloPontok: false`), tehát a 0 ott nem „nulla pontot szerzett", hanem
  „még nincs róla adat" — kötőjelként őszinte. A PL-en fordítva: az FPL percről percre
  ad pontot, ezért ott a futó meccs 0-ja valódi 0, és **számként** marad. A kötőjel
  magyarázata egérrel elolvasható (`title`).

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
| `squads.json` | A legutóbbi elérhető forduló keretei (`{updated, round, squads:{név:[játékos,...]}}`) — az „Aktuális keret” fül forrása; a `round` mondja meg, hányadik fordulóé. A játékos-rekord a könyvjelző mezőin felül `id`-t (MLSZ játékos-azonosító, a pont-bontáshoz), `played`-et („játszott már?”), `start`-ot (az adott fordulós meccsének kezdése), `vege: true`-t (a meccse már lement, akkor is, ha a pontok még nincsenek feldolgozva) és — ha a klubnak nincs meccse a fordulóban — `nogame: true`-t is tartalmaz. A régebbi, e mezők nélküli rekordokat az oldal tolerálja, de a gyűjtő nem hagyja őket úgy: az olyan fordulót, amelynek a rekordjaiban nincs `played`, egyszer újra lekéri a meccslistával együtt, és pótolja a hiányzó mezőket. |
| `squad_history.json` | Fordulónkénti keret-pillanatképek (`{updated, rounds:{"4":{név:[...]}}}`) — a „Szezon játékosai” fül forrása. A rekord-formátum a `squads.json`-éval azonos. |
| `naplo/fpl-figyelo.py` | **Ideiglenes megfigyelés:** negyedóránként naplózza az FPL forduló-állapotát, csak változáskor ír sort (`naplo/fpl-allapot.txt`). Azt nézzük vele, tényleg csak a forduló zárásakor véglegesedik-e a bónusz. Ha megvan a válasz, törölhető. |
| `valtozasok.json` | A változásnapló bejegyzései (`{bejegyzesek:[{datum, tipus, ligak, cim, leiras}]}`). **Kézzel írjuk**, nem gyűjtő tölti. |
| `valtozasok/index.html` | A változásnapló oldala („Mi újult meg?"). |
| `collect.py` | GitHub Actions: H2H eredmények (ranglista-végpont) **és** keretek (keret-végpont) gyűjtése, forduló-lezárás megállapítása, kimaradt fordulók pótlása. |
| `collect_draft.py` | GitHub Actions: az FPL Draft liga adatai. A résztvevők valódi nevét és az `entry_id`-t kiszűri (a repó publikus). |
| `draft.json` | Az FPL Draft liga adatai (résztvevők, menetrend, eredmények) — a `pl/index.html` forrása. |
| `draft_players.json` | FPL játékos-törzs: `{players: {id: {n: név, t: klub, p: poszt}}, teams: {csapat_id: rövidnév}}`. A `teams` a fixtures-válasz csapat-azonosítóinak feloldásához kell (kinek kezdődött el a meccse). |
| `draft_squads.json` | A jelenlegi FPL-keretek (tulajdonlás): `{liga_id: [játékos_id,...]}`. |
| `draft_history.json` | Fordulónkénti FPL-keretek pontokkal (`{rounds:{gw:{liga_id:[{e,b,pts},...]}}}`) — a GW1 indulásától gyűlik. |
| `keretek/<forduló>.json` | Egy forduló keretei külön fájlban (`{round, squads}`). A meccs-nézet **ezt** tölti le, nem a teljes előzményt. |
| `.github/workflows/archive.yml` | 3 óránként futó munkafolyamat: `collect.py` + commit. |
| `.github/workflows/draft.yml` | 3 óránként futó (és kézzel is indítható) munkafolyamat: `collect_draft.py` + commit. |
| `tartalek/` | Minden, ami nem kell a napi működéshez: a tartalék könyvjelző (`GOMB-bookmarklet.txt`, forrása és építője), az útmutatója (`KERET-MENTES.md`) és az elavult kézi pótlás leírása (`BACKFILL.md`). A weboldal és a gyűjtők semmit nem olvasnak innen. |

---

## 3. Hogyan frissül az adat

### Minden automatikusan megy (GitHub Actions, 3 óránként)

Az `archive.yml` a `collect.py`-t futtatja, ami **mindent** frissít, teendő nélkül:

1. **H2H eredmények** a ranglista-végpontról (hivatalos fordulópontszámok — ez a tabella
   egyetlen forrása).
2. **Régi fordulók újraellenőrzése**: a ranglista alapból csak a két legfrissebb fordulót
   adja vissza, tehát egy régi forduló utólagos korrekciójáról magától nem értesülnénk.
   Ezért minden futás **négy régi fordulót** kér le újra, körbeforgó sorrendben (lásd
   *Önjavítás* lentebb).
3. **Keretek** a keret-végpontról: az aktuális forduló (élő játékos-pontokkal), az utolsó
   lezárt, minden hiányzó forduló — és minden olyan régi forduló, amelynek a pontszáma
   ebben a futásban változott (akkor ugyanis a keret-pillanatkép is elavult). **Egy régi,
   újra lekért forduló ettől nem lehet „ideiglenes"**: ideiglenessé csak a most zajló vagy
   éppen most zárult forduló válhat. Enélkül egyetlen elhasalt keret-lekérés kivehetett
   volna egy hetekkel korábbi, lejátszott fordulót a tabellából.

   **A hiányos adat nem jelent „még tart"-ot.** A gyűjtő külön kezeli a „tudjuk, hogy a
   forduló még tart" és a „nem tudtuk lekérdezni" esetet. Amit nem tudott kiértékelni (403,
   elhasalt keret-lekérés), ott a forduló **korábbi** ideiglenes-állapota marad érvényben —
   sem újat nem talál ki, sem meglévőt nem töröl találgatásból. Enélkül két irányba is
   romolhatott az adat: egy hibás futás vagy kivett a tabellából egy lezárt fordulót, vagy
   — súlyosabb — kiürítette a `provisional` listát, és akkor az élő forduló
   **részeredménye véglegesként számított volna be**.
4. **Forduló-lezárás**: egy forduló akkor végleges, ha minden játékosnak, **akinek van
   meccse**, lement a meccse. Ehhez két jelzés kell együtt: `is_played`, **és** a meccslista
   `completed` státusza. Csak az `is_played`-re támaszkodni hibás volt: az MLSZ már a meccs
   *közben* igazra billenti, tehát amint a forduló utolsó meccse elkezdődött, mindenki
   „játszott" lett — a gyűjtő lezártnak minősítette a fordulót, és a **félig kész eredmény
   véglegesként került a tabellába**. Akinek **nincs meccse** a fordulóban (halasztás), az
   nem számít bele — lásd lentebb, hogy miért. Mögötte biztonsági háló áll: ha a
   játékos-szintű kép mégsem áll össze, de az MLSZ már továbblépett a fordulón, a gyűjtő
   akkor is lezárja. Amíg a forduló nem végleges, a `provisional` listában van, és az oldal
   nem számolja a tabellába.
5. **Keresztellenőrzés**: a keretekből számolt pontszámot összeveti a hivatalossal. Ha
   eltér, **nem jelzést ír, hanem javít**: újra lekéri a hivatalos értéket az adott
   fordulóra, és azt vezeti át.

### Az FPL Draft adatai (3 óránként, draft.yml)

A `collect_draft.py` a liga-adatokon túl a játékos-törzset, a jelenlegi kereteket
(tulajdonlás) és — a GW1 indulásától — a fordulónkénti kereteket gyűjti, pontokkal.
A résztvevők valódi neve és `entry_id`-ja soha nem kerülhet a repóba (mentés előtti szűrő).

### Élő frissítés a böngészőből (mindkét oldal)

Betöltéskor mindkét oldal percre friss adatot kér CORS-proxykon át: az NB1 a
ranglista-végpontról az eredményeket (és kattintásra a kereteket), a PL a játékosonkénti
élő pontokat, amikből a meccsállásokat összegzi. Hiba esetén a tárolt (3 óránként
frissülő) állapot marad.

**Visszatéréskor újra lekér** (`FunTasy.ujraLathatokor`). Ez sokáig hiányzott: az élő
állást csak a betöltés kérte le, egyszer. Asztali gépen ez nem tűnt fel, mert oda
általában friss betöltéssel térünk vissza — **mobilon viszont nem töltünk újra**, csak
visszaváltunk a lapra, amit a böngésző memóriából állít vissza. Így a főoldali meccslista
a betöltéskori álláson fagyott (39 pont), miközben a meccs-adatlap — aminek van saját,
nyitáskori lekérése — már a frisset mutatta (38). A segítő a `visibilitychange`, a
bfcache-es `pageshow` és a `focus` eseményre futtatja újra a frissítést, legfeljebb
30 másodpercenként, és sosem párhuzamosan.

**Időzített frissítés szándékosan nincs:** nyitva hagyott lapon nem megy lekérés a
proxykon át (mobilon adat és akku). Ha nézni akarod, hogy változik, vissza kell térni
a laphoz — vagy újratölteni.

### Gyorsítótár: miért ragadt be a pontszám iPhone-on

Az élő lekérések sokáig **gyorsítótár-törés nélkül** mentek, és a `fetch` sem kapott
`cache` beállítást. Emiatt állt elő, hogy iPhone-on *akárhányszor újratöltve* ugyanaz a
játékos-pont jött vissza, miközben másik eszközön már a friss. Ez **megosztott**
gyorsítótár volt (a CORS-proxyké), nem a készüléké — ezért nem is oldotta meg az
újratöltés.

Három rétegben törjük:

| Réteg | Hogyan |
|---|---|
| böngésző | `cache:'no-store'` **minden** élő lekérésen (a repóból jövő JSON-oknak eddig is volt `?t=` bélyegük) |
| CORS-proxy | a proxy URL-je `&_=<időbélyeg>`-et kap, tehát a proxy gyorsítótárkulcsa mindig más |
| FPL | a **belső** URL is kap `fpl_=<időbélyeg>`-et (az FPL az ismeretlen paramétert figyelmen kívül hagyja) |

Az **MLSZ saját URL-jéhez szándékosan nem nyúlunk**: nincs igazolva, hogy tűr egy
ismeretlen paramétert, és ott a `no-store` amúgy is elég — a direkt kérés és az MLSZ
között nincs megosztott gyorsítótár.

Az NB1 pont-bontásának gyorsítótára is kapott lejáratot: **élő fordulóban 60 másodperc**
(lezárt forduló bontása már nem változik), ahogy a PL-en is.

### „frissítés… 1,2 mp" — a néma számcsere ellen

A meccs-adatlap és (élő fordulóban) a keret-nézet **először a tárolt számokkal rajzol**,
és amikor a percre friss lekérés megjön, kicseréli őket. Gyors hálón ez észre sem vehető;
lassún viszont vagy régi adatot nézel anélkül, hogy tudnád, vagy a számok az orrod előtt
ugranak át.

Fix küszöböt nem lehet jól megválasztani — a lekérés ideje a hálózattól és a CORS-proxytól
függ, és ugyanazon a készüléken is szór. Ezért a jelzés **magát méri**: csak akkor jelenik
meg, ha a lekérés fél másodpercnél tovább tart, és kiírja, mennyi ideje fut
(`FunTasy.lassuJelzo`). Gyors válasznál soha nem látszik, tehát nem villog feleslegesen —
lassúnál viszont a kiírt idő egyben mérés is arról, mennyibe kerül valójában egy lekérés.

Három helyen van ilyen csere, mindhárom kapott jelzést: az NB1 élő meccs-adatlapja, az NB1
keret-nézete élő forduló közben, és a PL meccs-adatlapja.

### Fordulóhatár és lezárult PL-forduló: az élő réteget el kell dobni

Ha a forduló azóta zárult le, hogy a lapot betöltötted (például háttérben volt a fül), a
visszatéréskori frissítés a státuszsávot naprakészre állítja — de a meccslistában bent
maradnának a legutolsó lekérés számai **„élő" felirattal**, holott már végleges eredmény
jár oda. Ezért ilyenkor az élő réteg törlődik, és a lista a tárolt eredményre esik vissza
(azt a gyűjtő írja be a következő körben).

Ugyanez kell **fordulóhatáron** is: amikor az API átlép a következő fordulóra, az előzőt
el kell engedni. Két baj származna belőle. Egyrészt a régi forduló panelja „élő"
jelöléssel ragadna bent. Másrészt — és ez a rosszabb — a `LIVEPTS` és a `LIVEFX` csak
**sikeres** lekéréskor frissül, tehát ha az új forduló első lekérése elhasal, az *előző*
forduló pontjai jelentek volna meg az újé gyanánt, „élő állás" felirattal.

### A főoldali lista és a meccs-adatlap nem mondhat mást

A meccs-adatlap megnyitáskor **saját** élő lekérést indít, a főoldali lista viszont csak
betöltéskor és visszatéréskor számol. Így fordulhatott elő, hogy a listán 39 pont állt,
rákattintva viszont 38 (a játékos időközben pontot bukott). Mostantól amit az adatlap
lekér, azzal a **mögöttes lista is frissül** (`eloAllasFrissit`) — ugyanabból az adatból
két különböző szám nem jöhet ki, és plusz hálózati kérésbe sem kerül. Ugyanez vonatkozik a
csapat **keret-nézetére** is, aminek szintén van saját élő lekérése.

### Ami tudatosan következetlen maradt

A meccs vége után, amíg az MLSZ nem tette be a pontokat, a **sor 0-t mutat**, a pont-bontás
viszont megmondja az igazat („a pontok feldolgozása még tart"). Kötőjelet azért nem teszünk
oda, mert a sor nem tudhatja, megérkezett-e már a bontás — kideríteni csak játékosonkénti
lekéréssel lehetne (15 játékos × 8 keret fordulónként). Mivel a bontásból egy kattintással
kiderül az igazság, ez nem éri meg a bonyolítást.

**A státuszsáv szövegei közösek** (`funtasy.js` → `FunTasy.statusz`), hogy a két oldal
ne beszéljen kétféleképpen ugyanarról az állapotról:

| Állapot | Szöveg |
|---|---|
| lekérés közben | *Élő állás lekérése…* |
| élő forduló, friss adattal | *Élő állás — 5. forduló · frissítve 21:07 (a tabella csak lezárt fordulókból számol)* |
| nincs folyamatban lévő forduló | *Naprakész · ellenőrizve 21:07* |
| a lekérés elhasalt, forduló közben | *Automata lekérés hiba: az állások a forduló végén frissülnek.* |
| a lekérés elhasalt, nyugalmi időszakban | *Az élő frissítés most nem elérhető — a tárolt állás látható (mentve: aug. 21. 19:14).* |

A „frissítve" itt **mindig az élő ellenőrzés ideje**, a „mentve" pedig a tárolt fájl kora.
Korábban a PL a fájl korát írta ki „Frissítve" néven, az NB1 viszont az ellenőrzés idejét
— ugyanaz a szó két különböző dolgot jelentett.

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
fordulóbeli** meccsét (`start_at`, `status`, `round_number`). A „nincs meccse" **két
alakban** jön, és mindkettőt kezelni kell:

1. **Üres lista** — az élő fordulónál ez jön (mérve: Honvéd, 5. forduló).
2. **Másik forduló meccse** — régi fordulónál az API a klub **legutóbbi** meccsére esik
   vissza a hiányzó helyett. Ezt maga a meccs árulja el: a `round_number` mezője `"3F"` /
   `"5F"` alakú, és ha nem a kért fordulóra mutat, akkor a klubnak nincs meccse benne.
   (Mérve: a 3. fordulóra lekért ETO-játékosoknál a meccs `round_number`-e `"5F"`.)

**Fontos csapda:** a `first_played_at` egyik esetben sem használható. Vagy a klub
**következő** meccsére mutat — ez okozta a „furcsa kezdési időpont" hibát (Csontos, 5.
forduló: aug. 29. 00:00, ami valójában a 6. forduló dátuma) —, vagy egy **éjféles
helyőrzőre**, aminek a napja akár már el is múlt: a 3. fordulós ETO-játékosoknál
`2026-08-15T00:00`, amitől az oldal hetekkel később is azt írta, hogy „a meccs még nem
kezdődött el — kezdés: aug. 15.". Ha a helyőrző napja elmúlt, a dátum nem kezdési
időpont többé, hanem annyit jelent, hogy a meccs elmaradt és újat nem tűztek ki.

**Az include ára fordulófüggő** (mérve, 15 játékos):

| A forduló állapota | Alap | `games`-szel |
|---|---|---|
| élő (a meccsek `scheduled`) | 17,8 KB | 19,7 KB |
| lezárt (a meccsek `completed`) | 17,5 KB | 118,8 KB |

A különbség oka: a **lejátszott** meccs mellé az API a két csapat teljes objektumát is
beteszi, benne a klublogóval, base64 képadatként. Ezért a gyűjtő a meccslistát rendes
esetben **csak az élő fordulóra** kéri; a lezártakhoz a forduló alatt már elmentett
jelzés marad meg (`collect.py` → `orokit_meccsjelzok()`). Egy kivétel van: a régi
formátumú fordulót (nincs a rekordokban `played`) a gyűjtő **egyszer** meccslistával
együtt kéri le, hogy a hiányzó jelzések bekerüljenek.

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
  meccsét. **Egy forduló akkor zárult le, ha mindenki játszott, akinek volt meccse** — és a
  meccse `completed` státuszú.

#### Akinek nincs meccse, az nem akaszthatja meg a lezárást

Sokáig azt hittük, hogy a halasztott meccs játékosait az MLSZ lejátszottnak jelöli 0
ponttal, tehát a halasztás magától megoldódik. **A 2026-08-23-i mérés ezt megcáfolta:**

| eset | `is_played` | meccslista |
|---|---|---|
| 5. forduló, Honvéd (nincs meccse, élő forduló) | `false` | üres |
| 3. forduló, ETO (nem volt meccse, régi forduló) | `true`, 0 ponttal | a klub **legutóbbi** meccse |

A régi fordulónál látott `true` tehát nem a forduló lezárásából jön: ha a klubnak nem volt
meccse abban a fordulóban, az API a klub **legutóbbi** meccsére esik vissza (ugyanaz a
visszaesés, ami a „furcsa kezdési időpont" hibát okozta), és onnan örökli a jelzést is. Az
`is_played` tehát nem akkor billen át, amikor a forduló véget ér, hanem amikor **a klub
legközelebb pályára lép** — ami egy egész hetet is csúszhat.

Ezért a lezárás-vizsgálat kihagyja azt, akinek nincs meccse (`nogame`). Enélkül az 5.
forduló a Honvéd következő meccséig, nagyjából egy hétig a `provisional` listában maradt
volna, pedig minden meccse lement. A jelzést a **tárolt keretből** olvassa, nem a friss
válaszból: a meccslistát rendes esetben csak az élő fordulóra kérjük le (a lezárthoz
hatszor akkora válasz jönne), utána az `orokit_meccsjelzok()` hozza át a korábbi
pillanatképből.

#### Biztonsági háló: az MLSZ saját forduló-objektuma

Ha a játékos-szintű kép mégsem áll össze, a fordulónak akkor sem szabad örökre nyitva
maradnia. A tartalék jelzés az MLSZ saját forduló-objektuma. **Önálló forduló-végpont
nincs** (`rounds`, `competitions/3/rounds`, `competition-rounds` — mind 404); a fordulólista
a **versenylistán** keresztül jön, ugyanazzal a hívással, amit az MLSZ frontendje használ:

```
GET https://fantasy-api.mlsz.hu/competitions?include=rounds,current_round
```

Egy forduló mezői: `id`, `round_number`, `start_at`, `end_at`, `is_transfers_closed`,
`closed_transfers_at`. **Lezártság-jelző nincs köztük** — az MLSZ-nél a forduló naptári
határ (az egyik `end_at`-je a következő `start_at`-je), és az `end_at` elteltével lép
tovább a `current_round`. Ezért csak háló, nem elsődleges forrás.

A szabály: a `current_round` az erősebb jel. Ha az MLSZ szerint **még ez** az aktuális
forduló, akkor az `end_at` eltelte sem zárja le — a futó fordulót lezárni a rosszabb téves
lépés, mert a félig kész eredmény csendben bekerülne a tabellába. Az `end_at` csak akkor
dönt, ha a `current_round` egyáltalán nem jött meg.
- **Az MLSZ utólag korrigálhat** játékos-statisztikát, és átvezeti a hivatalos
  fordulóösszegre is. Megtörtént: Csendi 1–3. fordulós pontjai a lezárás után változtak
  (+1, +1, −2,5).

#### Önjavítás: ha az MLSZ korrigál, a gyűjtő is korrigál

A `collect.py` nem jelzést ír a naplóba, hanem **átvezeti a változást — mindenhol**.
Három egymást kiegészítő fogása van:

1. **Körbeforgó újraellenőrzés.** A ranglista-végpont alapból csak a két legfrissebb
   fordulót adja vissza, ezért minden futás **négy régi fordulót** kér le újra
   (`ellenorzendo()`), a három óránkénti ciklushoz igazított kezdőponttal. Napi nyolc futás
   × négy forduló = 32 ellenőrzés, a lista pedig legfeljebb 31 elemű (az utolsó két
   fordulót amúgy is minden futás lekéri), tehát **egy napon belül** körbeér. A lekért
   érték felülírja a tároltat (`setdefault` helyett értékadás): a végpont az igazság.
2. **A javított forduló keretei is frissülnek.** Ha egy régi forduló pontszáma változott,
   a hozzá tartozó keret-pillanatkép is elavult, ezért a gyűjtő azt is újra lekéri
   (`celok |= valtozott`) — így a pont-bontás és a „Különbségek” nézet számlája is a
   javított adattal jön ki.
3. **A keresztellenőrzés is javít.** Ha a keretből számolt összeg eltér a tárolt
   hivatalostól, a gyűjtő **újra lekéri a hivatalos értéket** arra a fordulóra, és ha
   tényleg változott, beírja a `results.json`-ba (`beir_eredmeny()`). ELTÉRÉS-figyelmeztetés
   már csak akkor megy a naplóba, ha a két forrás az újralekérés után **sem** egyezik —
   az valódi ellentmondás, nem korrekció.

Ehhez tartozott egy régi hiba is: a `rankings()` a `round_id` paramétert
`"...filter%5Bround_id%5D=%d" % round_id` módon fűzte a linkre, amiben a `%5B`-t a Python
formázó jelnek olvasta (`ValueError`). A backfill-ág addig sosem futott le élesben, ezért
nem derült ki; a körbeforgó ellenőrzés viszont minden futásban használja, így javítva
lett (sztring-összefűzésre).

### A bónuszpontok három állapota (PL)

A bónusz nem úgy végleges, mint a többi pont. Az FPL **a meccs alatt is számolja** a
BPS-táblából, és bele is teszi a `live` végpont `explain` mezőjébe (`stat: "bonus"`) —
tehát az oldalunk kiírja, miközben még változhat. Három állapot van, a meccs jelzőiből:

| állapot | miből látszik | mit jelent |
|---|---|---|
| a meccs alatt még változik | a meccs `started`, de még nem `finished_provisional` | percről percre változhat |
| lefújva — a forduló végéig még változhat | a meccs `finished_provisional`, de a forduló még nincs lezárva | rögzült, de az Opta felülvizsgálata még módosíthatja |
| végleges | a forduló le van zárva (`points: "r"` vagy `bonus_added`) | innentől nem változik |

A pont-bontásban a bónusz sora **színt és rövid szöveget** kap az első két állapotban; a
harmadik szándékosan **jelöletlen**. A szezon nagy részében minden bónusz végleges, így a
jelölés ritka, és ezért feltűnő. Szín önmagában sosem áll: minden jelöléshez tartozik
szöveg is.

**A harmadik állapotot a NAP mondja meg, nem a meccs.** Az FPL naponta zár: az adott este
egyszerre nézi át az aznapi összes meccset, és onnantól a bónusz fix. Erre külön végpont
van — de **csak a klasszikus FPL-ben**, a Draftban `event-status` 404-et ad:

```
GET https://fantasy.premierleague.com/api/event-status/
{"status":[{"bonus_added":false,"date":"2026-08-21","event":1,"points":"p"}, ...]}
```

**A mezők jelentését a Draft frontendjének forrásából olvastuk ki** (2026-08-24), tehát
nem tippelés. Ez rajzolja azt a naponkénti táblázatot, amit a Draft „Current team" lapja
mutat:

```js
o7 = { "": ``, l: `Live`, p: `Provisional`, r: `Confirmed` }
<td>{ points === 'r' ? <Kiemelt>Confirmed</Kiemelt> : (o7[points] || <>&nbsp;</>) }</td>
<td>{ bonus_added && <span>Added</span> }</td>
```

| oszlop | mező | értékek |
|---|---|---|
| Match Points | `points` | `""` (üres) → `l` **Live** → `p` **Provisional** → `r` **Confirmed** |
| Bonus Points | `bonus_added` | igaz esetén **„Added"** |

**A `"p"` (Provisional) NEM a véglegesítés jele, hanem az előtte lévő állapot.** Ez a
legkönnyebben félreolvasható pont az egészben — magyarul a „provisional" szó azt sugallja,
hogy már lezárult valami.

**2026/27-től nincs napi zárás.** A forduló „lockdown"-ja — amikor a pontok véglegessé
válnak — az utolsó meccs **utáni nap 09:00 UK**-kor van; korábban ez a lefújás után egy
órával volt. A haladék azért kell, hogy az Opta utólagos felülvizsgálata még
beleszámíthasson a bónuszba és a védekező pontokba. Ezért szól a jelölés a **forduló**
végéig, nem a napéig.

Ezt megerősíti a mérés is: 2026-08-23 este, négy lekérésben 21:04 és 22:06 UTC között
mind a kilenc lejátszott meccs `finished_provisional` volt, egyik sem `finished`, minden
nap `points: "p"`, és sehol nem volt `bonus_added` — pedig a pénteki meccs két nappal
korábban lement. A GW1 zárása kedden 09:00 UK-kor lesz.

A kód szerint véglegesnek az számít, ha az FPL **bármelyik** jelzője kimondja: `points`
`"r"`, vagy `bonus_added`. Mindkettő pozitív állítás a véglegességről. Tartalékként a
meccs `finished` mezője marad, ha a napi adat nem jön meg — pontatlanabb (tovább hagyja
kint a jelölést), de nem állít valótlant.

**Hogy tényleg így megy-e, azt figyeljük:** a `naplo/fpl-figyelo.py` negyedóránként
lekéri az állapotot, és **csak változáskor** ír egy sort a `naplo/fpl-allapot.txt`-be.
Ebből utólag látszik, mikor billen át melyik mező — és az is, ha mégis vannak napi
zárások. Ideiglenes megfigyelés; ha megvan a válasz, a `naplo/` és a hozzá tartozó
workflow törölhető.

**A napi lekérést nem várjuk meg.** Másodlagos jelzés, csak a bónusz sorának jelöléséhez
kell, amit a felhasználó kattintásra lát — ha a pontfrissítés megvárná, egy lassú vagy
elhasalt lekérés a főfrissítést is lassítaná (a „frissítés…" jelzés akkor is felvillanna,
amikor a pontok már rég megjöttek).

**A sort a saját meccséhez kötjük.** Az `explain` fordulónként meccsekre bontva jön,
`[[stat-lista, meccs_id]]` alakban — a második elem a meccs azonosítója. Ez dupla
fordulónál számít, ahol egy játékosnak két meccse van, és a kettő külön állapotban lehet
(mérve: az egyik lefújva, a másik még megy). Klub szerint összevonva ez elmosódna, ezért
a bónusz állapota **meccsenként** (`LIVEMECCS`) áll, nem klubonként (`LIVEFX`).

**Zsákutca, hogy ne kelljen újra megjárni:** a meccs saját `stats` tömbjében is van egy
`bonus` tétel (a három legjobb BPS), de az **mindig ott van**, tehát a megléte nem jelzi,
hogy a bónuszt véglegesítették. A Draft API-ban ez a tömb `{s, h, a}` alakú, nincs benne
`identifier` kulcs, mint a klasszikus FPL-ben.

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
- **A régi keret-rekordokban nem volt `id`, `played`, `start` és `nogame` mező** (ezek
  2026-08-21-én kerültek be). Emiatt az oldal a pont-bontáshoz élő lekérést volt kénytelen
  indítani, és a „nincs meccse" jelölés teljesen hiányzott — a 3. fordulós ETO-játékosoknál
  ezért írta az oldal egy már elmúlt helyőrző dátummal, hogy a meccs még nem kezdődött el.
  A gyűjtő azóta **egyszer újra lekéri** az ilyen fordulót, a meccslistával együtt, és a
  hiányzó mezőket pótolja; utána a feltétel már nem teljesül, tehát nem ismétlődik.
- **A „nincs meccse a fordulóban" jelzés a forduló alatt rögzül**, és a lezárás után már
  nem kérjük le újra a meccslistát (hatszor akkora válasz jönne), hanem az
  `orokit_meccsjelzok()` hozza át a korábbi pillanatképből.
- **A pont-bontás sorait a magyar eseménynév azonosítja** (pl. a „nem lépett pályára”
  eset a „Játszott perc” sor 0 értékéből derül ki). Az API nem ad stabil kulcsot ezekhez,
  úgyhogy ha az MLSZ átnevez egy eseményt, az oldal a részletesebb üzenet helyett az
  általánosabbra esik vissza — hibát nem okoz, de a szövegek pontatlanabbak lesznek.
- **Élő lekérés a böngészőből:** az oldal betöltéskor közvetlenül is lekéri a friss
  eredményeket (CORS-proxykon át). Ha ez elromlik, a státuszsávban jelzi (a szövegeket
  lásd a 3. fejezetben), és a tárolt (3 óránként frissülő) adat marad látható.

---

## 5/a. Miért van fordulónként külön keret-fájl

A `squad_history.json` fordulónként ~19 KB-tal nő: 5 forduló után 95 KB, a 33 fordulós
szezon végére **~630 KB**. Az oldalnak viszont egy meccs megnyitásához **egyetlen forduló**
keretei kellenek — az egészet letölteni pazarlás, mobilneten érezhetően az.

Ezért a gyűjtő fordulónként is kiírja a kereteket (`keretek/<forduló>.json`), és a
meccs-nézet onnan olvas. Most 95 KB helyett 24 KB, a szezon végén 630 KB helyett
**változatlanul ~24 KB**.

Két részlet, ami fontos:

- **A fordulónkénti fájlokban nincs időbélyeg.** Ha benne lenne, minden gyűjtő-futásnál
  mind a 33 fájl megváltozna, és a repó feleslegesen hízna. Így egy forduló fájlja csak
  akkor változik, ha a keretek tényleg változtak.
- **Van visszaesési út.** Ha a fordulónkénti fájl hiányzik (régi commit, elgépelt út), az
  oldal a teljes előzményre esik vissza — lassabb lesz, de nem romlik el. Teszt fedi
  mindkét ágat.

A teljes előzmény megmarad: a gyűjtő abból tudja, mi hiányzik, és a „Szezon játékosai" fül
is az egészet igényli — az viszont ritkán megnyitott, tudatosan nehéz nézet.

**A PL-oldalon ez még nincs meg:** a `draft_history.json` minden betöltéskor lejön (most
4 KB, a 38. fordulóra ~159 KB). Kisebb tét, és ott a `HIST` több helyen szinkron használt,
tehát invazívabb átalakítás — külön körben érdemes.

## 5/a2. Változásnapló („Mi újult meg?")

Felhasználói napló, nem technikai: **csak az kerül bele, amit a használó lát vagy
érzékel**. Ami tisztán háttérmunka (átszervezés, gyűjtő-belső, teszt), az nem.

- **Két típus:** *új funkció* és *javítás*.
- **A liga címke, nem kategória.** Egy bejegyzéshez több liga is tartozhat, és
  **bármelyikre szűrve előjön**. Ez azért fontos, mert nem mindenki játszik minden
  ligában — és minél több liga lesz, annál kevésbé.
- **A ligák külön kapcsolhatók, több is egyszerre.** Aki két ligában játszik, mindkettőt
  kijelölheti, és akkor mindkettő bejegyzéseit látja (a kijelöltek között VAGY van). A
  „Mind" gomb nem egy választás a többi mellett, hanem a kijelölések törlése. A típus
  ezzel szemben egy választás, mert a két típus kizárja egymást.
- **Egy nap, egy téma, egy bejegyzés.** Ha egy megoldás több nekifutásból állt össze, csak
  a végső állapot kerül be; a közbenső próbálkozások a használót nem érdeklik.
- **Dátumozva**, naponként csoportosítva, a legfrissebb elöl. A napló 2026-08-23 estétől
  indul, a korábbi változások nincsenek benne.

Az adat a `valtozasok.json`-ban van, kézzel bővítjük. A szűrők a `LIGAK` listából
készülnek, tehát egy új liga felvétele itt sem igényel külön munkát.

**Hogyan legyen megfogalmazva egy bejegyzés**

- **A cím azt mondja meg, mi igaz mostantól**, a mondat pedig azt, hogy ez mit jelent a
  használónak és hol látja. Példa: *„Az elmaradt meccs játékosainál kötőjel áll 0 helyett"*.
- **Nincs benne első személy, és nincs hivatkozás a fejlesztés menetére.** A napló nem
  arról szól, ki mit mondott vagy hogyan derült ki — csak arról, mi változott az oldalon.
  (Első nekifutásra ez a mondat került bele: *„Eddig chatben mondtam el, mi változott"* —
  ennek egy felhasználói naplóban nincs helye.)
- **Tárgyszerű, nem dramatizál.** Nem *„nem kapnak többé hamis 0-t"*, hanem az, ami
  ténylegesen látszik a soron.
- **A beszélgetésben elhangzott szavakat nem vesszük át szó szerint.** Az, ahogy egy
  hibáról beszélünk, nem ugyanaz, ahogy a naplóba le kell írni; a megfogalmazást minden
  bejegyzésnél újra végig kell gondolni.

Elérés: a kezdőlapról (kártya) és minden oldal **láblécéből** (`FunTasy.renderLablec`).
A naplón magán nincs lábléc, mert önmagára mutatna.

## 5/b. Tesztek

```bash
tesztek/futtat.sh
```

Elindít egy helyi kiszolgálót a repó gyökerére, lefuttat mindent (3 gyűjtő- és 13
böngészős tesztet), és összegez; a kilépőkód a bukott tesztek száma. Tesztenkénti
bontás: `tesztek/README.md`.

Két elv, amit érdemes megtartani:

- **Nincsenek fixtúra-másolatok** — minden teszt a repóban lévő **valódi** adaton fut.
  Korábban lemásolt JSON-ok álltak külön könyvtárakban; azok elavultak, és a teszt akkor
  is zöld maradt, ha közben a valódi adat megváltozott.
- **A különleges állapotokat a teszt állítja elő menet közben** (a Playwright elfogja a
  kérést és átírja a választ), nem tárolt fájlból. Így holnap is ugyanazt méri.

A legtöbbet két teszt adja: az `allapotter.teszt.js` a „0 pont" logika **mind az 576
kombinációját** végigfuttatja öt invariánssal (ez talált meg olyan hibákat, amikre nem
gondoltunk tesztet írni), a `tabella.teszt.js` pedig **függetlenül újraszámolja** a
tabellát és a mátrixot a nyers adatból.

## 6. Ha módosítani kell

Nincs build lépés, nincs függőség. A kód három rétegben él:

- **`funtasy.css`** — a közös stíluslap (mindkét oldal ezt tölti; itt van minden szín,
  rács, táblázat- és modal-stílus).
- **`funtasy.js`** — a közös réteg. **Ami nem liga-specifikus, ide tartozik**, és ez nem
  kozmetika: korábban tizenkét azonos nevű függvény élt külön példányban a két
  liga-oldalon, és emiatt ugyanazt a hibát többször kellett javítani (a
  gyorsítótár-törést két különböző alakú `apiGet`-be; a „listán 39, ráváltva 38"
  eltérést előbb a meccs-adatlapon, majd külön a keret-nézetben). Egy harmadik liga ezt
  megháromszorozta volna. Most **kettő** maradt külön (`bontasHTML`, `nincsPontUzenet`) —
  azok valóban ligánként mások, mert más API-ból jönnek.

  A közösbe került, ligától független darabok:

  | Hívás | Mit ad |
  |---|---|
  | `FunTasy.lekero({...})` | lekérés CORS-proxyn át: három útvonal sorban, a bevált megjegyzése, gyorsítótár-törés három rétegben. Beállítható, hogy a **belső** URL is kapjon-e időbélyeget (az FPL tűri, az MLSZ-nél nincs igazolva), mi számít érvényes válasznak, és teljes kudarcnál dobjon-e. |
  | `FunTasy.nezetVerem({...})` | a modal és a benne lapozás (`mutat` / `vissza` / `nyit` / `zar`). |
  | `FunTasy.allasHTML(...)` | az eredménysor doboza. |
  | `FunTasy.eloKereso(LIVE)` | élő állás kikeresése a live rétegből. |
  | `FunTasy.hibajelzo({...})` | a státuszsáv hibaüzenete; a „van-e élő forduló" kérdést a hívó dönti el. |
  | `FunTasy.h2hNezo({...})` | az egymás elleni nézet; a névfeloldás beállítható. |
  | `FunTasy.ujraLathatokor(fn)` | újrafrissítés, amikor a lap ismét látszik. |
  | `FunTasy.lassuJelzo(cel)` | a „frissítés… N mp" jelző lassú lekérésnél. |
  | `FunTasy.accToggle/accTable` | a pont-bontás accordion mechanikája. |

  Emellett `FunTasy.create({...})` kapja a konfigurációt
  (menetrend, résztvevők, elemazonosítók), és adja a `computeTable`, `renderTable`,
  `renderMatches`, `renderMatrix` függvényeket, az élő-jelölést és az egymás elleni
  lista építőjét (`h2hHTML` — a mátrix-cella kattintása nyitja, `onMatrixClick`).
  A create-en kívül itt él a pont-bontás accordion közös mechanikája is
  (`FunTasy.accToggle` — nyit/zár/egyszerre egy panel; `FunTasy.accTable` — a bontás
  táblázata); a tartalmat az oldalak saját `bontasHTML`-je adja, mert a forrás más
  (NB1: MLSZ `game-player-stats`, PL: FPL `event/{gw}/live` explain). Szintén itt van a
  `FunTasy.ujraLathatokor(frissites)`: a lapra visszatérve újra lefuttatja az élő
  lekérést (fojtással, párhuzamos futás nélkül) — enélkül mobilon befagy az állás.
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

1. Egy új bejegyzés a `funtasy.js` **`LIGAK`** listájába. Ebből az **egy** listából
   készül a ligaváltó sáv minden oldal tetején, a kezdőlap kártyája és a liga-oldal
   alcíme is — máshol nem kell hozzányúlni. Mezők:

   | Mező | Mire való |
   |---|---|
   | `id` | rövid azonosító, egyben a body-osztályok és a kártya alapja (`nb1`, `pl`) |
   | `nev` | rövid név a ligaváltó sávban és a kártya tetején (`NB1`) |
   | `mappa` | a webhely gyökeréhez képest (`nb1/`) |
   | `cim` | a liga-oldal alcímének eleje (`NB1 salary cap fantasy`) |
   | `leiras` | a folytatás: résztvevők, fordulók (`privát head-to-head · 8 csapat · 33 forduló`) |
   | `tipus` | **játékmód** — `salary-cap` vagy `draft`, lásd lentebb |
   | `tipusNev` | ennek olvasható neve a kártyán (`Salary cap`) |
   | `tema` | a `body` osztálya a színvilághoz (`liga-nb1`) |
   | `eloPontok` | ad-e a forrás pontot **meccs közben** (FPL: igen, MLSZ: csak a meccs után). Ettől függ, mit szabad írni a 0 pontos játékosról a meccs alatt. |
2. Új mappa a saját `index.html`-lel. A közös fájlokra `../funtasy.css?v=N` és
   `../funtasy.js?v=N` hivatkozik, az adatra `../valami.json`, a sávot pedig egy sor
   rajzolja ki: `FunTasy.renderNav('<azonosító>','../')`.
3. Ha új témaszínek kellenek: egy `body.liga-<azonosító>` blokk a `funtasy.css`-ben
   (a változónevek maradnak, csak az értékük más), és a kártya színe a
   `.ligakartya[data-liga="<azonosító>"]` szabályokban.

A linkek **relatívak** (`../pl/`), mert a GitHub Pages aloldalon szolgál ki
(`/Funtasy-Liga/`), tehát abszolút `/pl/` út rossz helyre mutatna.

**A ligatípus nem címke, hanem tulajdonság.** Két játékmód van, és a szabályaik érdemben
eltérnek — erre az oldalak külön megoldást adhatnak:

| Típus | Mit jelent |
|---|---|
| `salary-cap` | közös játékospiac árkerettel; ugyanaz a játékos több csapatban is lehet; van kapitány (×2) és cserepad-felezés (NB1) |
| `draft` | kizárólagos tulajdon: egy játékos egy csapatban; nincs kapitány, a pad pontjai nem számítanak (PL) |

A típus két helyen fogható meg: a `body` megkapja a `tipus-<érték>` osztályt (CSS-ből
használható), JS-ből pedig `FunTasy.liga('nb1').tipus` kérdezhető le. Mindkettőt a
`FunTasy.renderNav(...)` állítja be, ugyanaz a hívás, ami a ligaváltó sávot kirajzolja.

**A kezdőlapnak saját, semleges színvilága van** (`body.kezdolap`: grafit alap, ezüstös
kiemelés). Enélkül az alapértelmezett palettát használná, vagyis úgy nézne ki, mintha az
NB1 oldala volna. Így a lapon a két ligaszín (zöld / lila) az egyetlen színfolt.

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
