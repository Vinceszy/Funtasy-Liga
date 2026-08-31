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

<!-- tartalomjegyzek: a tesztek/dokuk.py tartja karban, kezzel ne szerkeszd -->
<details>
<summary><b>Tartalom</b></summary>

- [1. Mit tud az oldal](#1-mit-tud-az-oldal)
  - [Tabella](#tabella)
  - [Meccsek — két külön panel](#meccsek--két-külön-panel)
  - [Egymás elleni mátrix](#egymás-elleni-mátrix)
  - [Modal — három fül](#modal--három-fül)
  - [A FunTasy PL oldal](#a-funtasy-pl-oldal)
  - [Pont-bontás (accordion) és a „még nem játszott” jelölés](#pont-bontás-accordion-és-a-még-nem-játszott-jelölés)
  - [Játékosprofil](#játékosprofil)
  - [A mezőny játékosai (főoldali lista)](#a-mezőny-játékosai-főoldali-lista)
  - [Zárási változások (mindkét liga)](#zárási-változások-mindkét-liga)
  - [A nyitott pont-bontás túléli a frissítést](#a-nyitott-pont-bontás-túléli-a-frissítést)
  - [Navigáció a modalon belül](#navigáció-a-modalon-belül)
  - [Mobil](#mobil)
- [2. Fájlok](#2-fájlok)
- [3. Hogyan frissül az adat](#3-hogyan-frissül-az-adat)
  - [Minden automatikusan megy (GitHub Actions, 3 óránként)](#minden-automatikusan-megy-github-actions-3-óránként)
  - [Az FPL Draft adatai (3 óránként, draft.yml)](#az-fpl-draft-adatai-3-óránként-draftyml)
  - [Élő frissítés a böngészőből (mindkét oldal)](#élő-frissítés-a-böngészőből-mindkét-oldal)
  - [A CORS-proxyk cserélhetők — és cserélni is kellett (mérve, 2026-08-27)](#a-cors-proxyk-cserélhetők--és-cserélni-is-kellett-mérve-2026-08-27)
  - [A betűkészlet nem állíthatja meg a lapot (mérve, 2026-08-27)](#a-betűkészlet-nem-állíthatja-meg-a-lapot-mérve-2026-08-27)
  - [Gyorsítótár: miért ragadt be a pontszám iPhone-on](#gyorsítótár-miért-ragadt-be-a-pontszám-iphone-on)
  - [„frissítés… 1,2 mp" — a néma számcsere ellen](#frissítés-12-mp--a-néma-számcsere-ellen)
  - [Fordulóhatár és lezárult PL-forduló: az élő réteget el kell dobni](#fordulóhatár-és-lezárult-pl-forduló-az-élő-réteget-el-kell-dobni)
  - [A főoldali lista és a meccs-adatlap nem mondhat mást](#a-főoldali-lista-és-a-meccs-adatlap-nem-mondhat-mást)
  - [Ami tudatosan következetlen maradt](#ami-tudatosan-következetlen-maradt)
  - [Tartalék: a böngészős könyvjelző](#tartalék-a-böngészős-könyvjelző)
- [3/b. A LEZÁRÁS — mi mit jelent, és hol dől el](#3b-a-lezárás--mi-mit-jelent-és-hol-dől-el)
  - [Amit a lezárás után is frissíteni KELL](#amit-a-lezárás-után-is-frissíteni-kell)
- [4. Az MLSZ Fantasy API — amit a fejlesztés során kiderítettünk](#4-az-mlsz-fantasy-api--amit-a-fejlesztés-során-kiderítettünk)
  - [Ranglista](#ranglista)
  - [Keret (bárhonnan működik — ha jól kérdezed)](#keret-bárhonnan-működik--ha-jól-kérdezed)
  - [Ki nem játszik a fordulóban (a meccslista)](#ki-nem-játszik-a-fordulóban-a-meccslista)
  - [Pont-bontás (game-player-stats)](#pont-bontás-game-player-stats)
  - [Játékostörzs és a szezon egésze (mérésekkel, 2026-08-25)](#játékostörzs-és-a-szezon-egésze-mérésekkel-2026-08-25)
  - [A játékos-adatlap végpontja (mérve, 2026-08-25)](#a-játékos-adatlap-végpontja-mérve-2026-08-25)
  - [A jövőbeli menetrend nem érhető el (mérve, 2026-08-25)](#a-jövőbeli-menetrend-nem-érhető-el-mérve-2026-08-25)
  - [Az árakról nincs előzmény (mérve, 2026-08-25)](#az-árakról-nincs-előzmény-mérve-2026-08-25)
  - [Amit a hivatalos szabályzat rögzít (fantasy.mlsz.hu, 2026-08-25)](#amit-a-hivatalos-szabályzat-rögzít-fantasymlszhu-2026-08-25)
  - [A pontszámítás kulcsa](#a-pontszámítás-kulcsa)
  - [A „szerverről tilos” tévhit története](#a-szerverről-tilos-tévhit-története)
  - [Forduló-lezárás és utólagos MLSZ-korrekciók](#forduló-lezárás-és-utólagos-mlsz-korrekciók)
  - [A bónuszpontok három állapota (PL)](#a-bónuszpontok-három-állapota-pl)
  - [Ki van még a pályán (PL)](#ki-van-még-a-pályán-pl)
  - [A meccs állása a pont-bontás fölött (PL és NB1)](#a-meccs-állása-a-pont-bontás-fölött-pl-és-nb1)
  - [Automatikus cserék a forduló zárásakor (PL)](#automatikus-cserék-a-forduló-zárásakor-pl)
  - [A zárás és a gyűjtés közötti rés (PL)](#a-zárás-és-a-gyűjtés-közötti-rés-pl)
  - [Név és monogram: a monogram sosem vágódik le](#név-és-monogram-a-monogram-sosem-vágódik-le)
  - [Kezdőállítási hatékonyság (KEZD%)](#kezdőállítási-hatékonyság-kezd)
  - [A pad sorrendje (PL) — és ami még nyitott](#a-pad-sorrendje-pl--és-ami-még-nyitott)
  - [Az FPL Draft API (draft.premierleague.com/api/) — mérésekkel igazolva](#az-fpl-draft-api-draftpremierleaguecomapi--mérésekkel-igazolva)
- [5. Ismert korlátok, buktatók](#5-ismert-korlátok-buktatók)
- [5/a4. A Guardiola mutató](#5a4-a-guardiola-mutató)
  - [A PL-en ugyanez, automatikus cserékkel](#a-pl-en-ugyanez-automatikus-cserékkel)
- [5/a5. A „Változtatások" fül](#5a5-a-változtatások-fül)
  - [A PL-en külön áll, amit az ember csinált, és amit a gép](#a-pl-en-külön-áll-amit-az-ember-csinált-és-amit-a-gép)
  - [Csak lezárt forduló](#csak-lezárt-forduló)
- [5/a. Miért van fordulónként külön keret-fájl](#5a-miért-van-fordulónként-külön-keret-fájl)
- [5/a3. A lezárt forduló bontása a repóból jön](#5a3-a-lezárt-forduló-bontása-a-repóból-jön)
  - [Az élő pont a tételes bontásból áll össze (PL)](#az-élő-pont-a-tételes-bontásból-áll-össze-pl)
  - [Élő forduló alatt a lap magától frissül](#élő-forduló-alatt-a-lap-magától-frissül)
  - [Írás csak akkor, ha tényleg változott](#írás-csak-akkor-ha-tényleg-változott)
- [5/a2. Változásnapló („Mi újult meg?")](#5a2-változásnapló-mi-újult-meg)
  - [A két oldal váza kézzel van kétszer leírva](#a-két-oldal-váza-kézzel-van-kétszer-leírva)
- [5/b. Tesztek](#5b-tesztek)
- [6. Ha módosítani kell](#6-ha-módosítani-kell)
  - [Új liga felvétele](#új-liga-felvétele)
- [7. Tervezett, még nem elkészült](#7-tervezett-még-nem-elkészült)

</details>

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

### Játékosprofil
Mindkét ligában. A **Szezon játékosai** listában egy névre kattintva megnyílik a játékos profilja. Fent az
alapadatok (poszt, klub, magyar/U21 jelölés, összpont, hány fordulóról van adat, ebből
hányban volt valakinek a keretében), alatta fordulónként egy sor: **ellenfél, a meccs
állása** (mindig hazai–vendég sorrendben, mellette hogy otthon vagy idegenben játszott),
a játékos **saját pontja**, és hogy **melyik szakvezetőnél** volt — kezdőként, padon vagy
kapitányként. Salary cap ligában ugyanaz a játékos egy fordulóban **több szakvezetőnél is**
lehet: ilyenkor mind ott van, mindegyik a maga szerepével. Ha senkinél sem volt, rövid
kötőjel áll ott — jövőbeli fordulónál pedig semmi, mert azt, hogy kinél *lesz*, nem tudjuk.

A felsorolás végén a **ligára vetített arányok**: a forduló kereteinek hány százalékában volt
benne (*keret*), hányban volt kezdő (*kezdő*) és hányban kapitány (*kapitány*). A nevező a
forduló **tényleges** keretszáma — ahány szakvezetőről mentett keret van —, nem beégetett 8,
így egy kimaradó keret nem húzza le az arányt. **A kapitány kezdőnek is számít**, tehát a három
szám egymásba ágyazódik: keret ≥ kezdő ≥ kapitány. Akinél senki sem volt, ott nincs arány-blokk.

**Meddig megy a lista?** A **PL-profil a szezon összes fordulóját** felsorolja: a lejátszott
sorokban a pont és az eredmény, a jövőbeliekben az ellenfél és a pálya (a Draft
`element-summary` `fixtures` tömbjéből). Az **NB1-profil csak a lejátszott fordulókat**
mutatja, mert ott a jövőbeli párosítás nem érhető el (lásd a 4. fejezetet) — ellenfél és
időpont nélküli üres sorokat nem írunk ki.

**Több meccs egy fordulóban.** A sor a klub **összes** meccsét mutatja az adott fordulóban,
nem az elsőt. A PL-ben ez a dupla forduló (egy klub kétszer játszik), az NB1-ben a pótolt,
korábban elhalasztott meccs hozhatja elő. Egy meccsnél az ellenfél és a pálya a név-cellában,
az állás a saját oszlopában áll (így a számok egymás alá igazodnak); kettőnél mindkét meccs
az állásával együtt a név-cellába kerül, és az állás-oszlop üres marad. Inkább legyen a ritka
eset máshogy tördelve, mint hogy a második meccs eltűnjön.

**Honnan jön az adat ligánként.** Az NB1-ben a fordulónkénti pont a keret-előzményből (a
gazdátlan fordulóké az MLSZ pont-bontásából), az ellenfél a `meccsek.json`-ból. A PL-ben
mind a kettő **egyetlen kérésből**: a Draft `element-summary/{id}` fordulónként adja a pontot
és egy `"BHA (A) 4-0"` alakú mezőt, amiben az ellenfél, a játékos csapatának pályája és az
állás **hazai–vendég** sorrendben szerepel. Ez utóbbit kimértük (`naplo/fpl-profil.txt`):
25 idegenbeli, nem döntetlen meccsen mind a 25 ezt igazolta, a „játékos csapata előre"
olvasatot egy sem — rossz választással minden idegenbeli eredmény megfordult volna.

**Ha az `element-summary` nem érhető el**, a PL-profil a **tárolt** fordulónkénti pontból
dolgozik (`draft_history.json` → `pts`): a pont és a szerep (kezdő/pad) megjelenik, csak az
ellenfél marad üres. Korábban ilyenkor minden sor kötőjel volt, a „Pont összesen" pedig 0 —
miközben az adat ott hevert a repóban. Az NB1-profil mindig is a tárolt adatból épült, a
tételes bontást pótolja utólag az API-ból; ez a két liga most ebben is egyformán működik.

**Ez az arány csak salary cap ligában jelenik meg**, és ezt a liga `tipus` mezője dönti el
(`funtasy.js` → `LIGAK`), nem a liga azonosítója. Draft ligában egy játékos pontosan egy
szakvezetőnél lehet — vagy senkinél —, tehát a *keret* mindig 1/N vagy 0 lenne, kapitány pedig
nincs is: a három szám nem mondana semmit. A szerep neve (kezdő / pad / kapitány) viszont ott
is látszik. A közös réteg ezért nem kész magyar szöveget kap, hanem `{nev, kezdo, kapitany}`
mezőket — így a szóhasználat és az arányszámítás is egy helyen áll.

A sorra kattintva a szokásos accordion nyílik le a **tételes pont-bontással** és a klub
meccsével — ugyanaz a lekérés és ugyanaz a gyorsítótár, mint a keret-nézetben.

Két dolog, ami könnyen félreérthető, ezért így csináljuk:

- **A pont a játékosé, nem a csapaté.** A tárolt heti pont már tartalmazza a kapitányi
  duplázást és a padfelezést; a profil ezeket **visszaszámolja**, mert különben ugyanaz a
  teljesítmény más számot mutatna aszerint, hogy kinél volt. A padnál az API a felezés után
  két tizedesre kerekít (0,75 → 0,38), így a puszta kétszerezés 0,01-gyel mellémenne — ezért
  a legközelebbi negyedre kerekítünk. Hogy ez helyes, azt kimértük: a játékosok alappontja
  377 összevetett fordulón **mindig 0,25 többszöröse** volt.
- **Amikor senkinél sem volt**, a pont sehol nincs eltárolva — ilyenkor (és csak ilyenkor)
  megy egy lekérés az MLSZ pont-bontás végpontjára. A profil ezt **nem várja meg**: azonnal
  megjelenik kötőjelekkel, a pontok a háttérben, **sorban** pótlódnak. Párhuzamosan kilőve
  a proxy eldobta a kéréseket — a profil percekig töltött, a lenyíló bontás elhasalt
  (bejelentett hiba, 2026-08-25).

### A mezőny játékosai (főoldali lista)
Mindkét liga főoldalán, a bal oszlop alján. A **teljes mezőny** benne van (NB1: 385,
PL: 612 játékos), a lista alapból a legtöbb pontot szerző 40-et mutatja — a keresés és a
szűrés viszont **mindig az egész mezőnyben fut**, különben pont arra lenne alkalmatlan,
amire kell: megtalálni egy hátrébb állót, és megnézni, kinél van.

Oszlopok: **#** (hányadik a jelenlegi nézetben — nem fix rangsor, átrendezéskor csak
számol), **Poszt**, **Játékos** (U21-jelöléssel), **Klub**, **Kinél van** (most kinél;
salary capben többen is lehetnek — a szakvezetőt **monogram** jelöli, így négy is
kifér, utána `+N`), **Keret%** és **Ár**
(mindkettő csak NB1 — a draftban egy játékos egy keretben van, és nem veszel játékost),
végül **Pont**.

- **A kereső** a névben *és* a klubban is keres, és **ékezet nélkül is talál**
  (`ljujic` → Ljujić): senki nem fog kalapos c-t írni a keresőbe.
- **Minden oszlop szűrhető** a maga módján: poszt / klub / kinél van legördülő
  (az értékek magából az adatból jönnek, tehát egy új klub vagy szakvezető magától
  megjelenik bennük), az árnál felső korlát („mi fér bele"), a pontnál és a Keret%-nál
  alsó. A „Kinél van" szűrőben a **Mindegy** a szűrő kikapcsolása, a **Valakinél** azt
  kérdezi, van-e egyáltalán gazdája, a **Senkinél** pedig a gazdátlanokat hozza — ez
  három különböző kérdés. A gazdátlan játékos cellájában rövid kötőjel áll, nem szó:
  az oszlop szűk, a felirat csak helyet foglalt.
- **Minden oszlop rendezhető** a fejlécre kattintva; újrakattintás megfordítja.
  Szöveges oszlop alapból növekvő, számos csökkenő.
- **Lapozható**: a lábléc mutatja, hol tartunk (`41–80 / 385`), és a nyilakkal lehet
  előre-hátra lépni. Szűrésre, keresésre és átrendezésre visszaugrik az első oldalra —
  különben egy szűkebb találati halmaznál egy üres oldalon ragadnánk.
- **Telefonon egyetlen oszlop sem tűnik el** — akkor szűrhetetlen és rendezhetetlen
  lenne. Helyette a sor **két sorra törik**: fent a sorszám, a poszt, a név és a pont,
  alatta a klub, a Keret%, az ár és a „kinél van", kiírt felirattal (magukban a számok
  nem mondanának semmit). A fejléccellák ugyanígy tördelnek, tehát a rendezés minden
  oszlopra megmarad. A törést egy külön elem (`.jltores`) végzi: az `order` önmagában
  nem tör sort.
- **Telefonon ez az utolsó blokk.** A rácsot ott egy oszlopos flexre váltjuk, a két
  burkoló `div` `display:contents`-szel eltűnik a layoutból, így a panelek közvetlen
  flex-elemek lesznek, és az `order` rájuk hat.

A sorra kattintva megnyílik a játékosprofil.

**A lista sorai ugyanazt a `.plr` osztályt viselik**, mint a keret-nézet sorai — így a
megjelenésük egységes, viszont egy oldal-szintű `.plr` lekérdezés (pl. egy tesztben)
ezeket is beszámolja. A modalra vonatkozó kereséseket ezért `#mBody`-ra kell szűkíteni.
(A különbségek-teszt pontosan ezen bukott el, amikor a lista bekerült.)

### Zárási változások (mindkét liga)
A hivatalos szabályzat szerint a pont minden meccs után megvan, de a **heti összeg csak a
forduló utolsó játéknapjának végén válik véglegessé** — a kettő között az MLSZ még
igazíthat. A gyűjtő ezt eddig átvezette, de nem őrizte meg; mostantól naplózza
(`zarasok_nb1.json`), mert utólag rekonstruálhatatlan.

Mindkét ligában van „Zárási változások" panel, **ugyanazon a helyen, ugyanazzal a címmel
és ugyanazzal a megjelenítéssel**: jobb oszlop, szakvezető szerint csoportosítva,
soronként poszt-címke, játékosnév + klub, `előtte → utána` érték és előjeles különbség. A
játékos neve a profilt, a szakvezető neve a keretet nyitja. Ahol nem volt változás, ott az
áll, hogy **nem történt változás** — a legördülőben minden eddigi forduló szerepel, nem
csak az, amelyikben volt, és a lapozó alapból a **legutolsó** fordulón áll. A fordulók
mindkét oldalon növekvő sorrendben állnak, tehát a `‹` visszafelé, a `›` előre lép.
(Korábban a PL-en fordítva volt: ott csökkenő volt a lista, és a két panelen a nyilak
ellenkező irányba vittek.)

**A HTML-t a közös réteg állítja elő** (`funtasy.js` → `FunTasy.zarasLista`); a két oldal
csak normalizált sorokat ad át. Ez azért így van, mert külön-külön megírva a két panel
egyszer már szétcsúszott (más cím, más elrendezés, más üres szöveg).

A **tárgya** ligánként más:

- **PL:** az FPL az utolsó meccs utáni reggelen véglegesíti a fordulót — ekkor rögzül a
  bónusz, és ekkor állnak be az automatikus cserék. Ezért van ott nézetváltó sor
  (Mind / Pontváltozás / Cserék).
- **NB1:** a pont minden meccs után megvan, de a heti összeg csak a forduló utolsó
  játéknapjának végén válik véglegessé — a kettő között az MLSZ még igazíthat. Automatikus
  csere nincs, tehát nézetváltó sor sincs.

Az NB1-ben az érték a játékos **saját** pontja (kapitányi duplázás és padfelezés
visszaszámolva), tehát ugyanaz a változás nem néz ki másképp aszerint, hogy kinél volt.
Csak **lement meccsű** játékosnál számít változásnak: a meccs közbeni pontketyegés nem hír.
Ugyanaz a játékos annyi blokkban jelenik meg, ahány keretben benne volt.

Kivétel az első három forduló három ismert esete, ahol csak a **változás mértékét** tudjuk,
a játékost nem. Azok a sorok „Ismeretlen játékos" névvel állnak ott (`nk:1` jelző, nem
kattinthatók, `előtte → utána` nélkül, csak az előjeles különbséggel), alattuk kiírt
magyarázattal.

A panel csak akkor jelenik meg, ha van benne adat: egy állandóan üres doboz azt sugallná,
hogy valami hiányzik.

### A nyitott pont-bontás túléli a frissítést

A meccs- és keret-nézet **utólag frissül**: beér a percre friss keret, a játszott percek, az
élő pontok. Ilyenkor a `#mBody` teljes tartalma újraépül — és a nyitott accordion eltűnt
alóla. A felhasználónak úgy nézett ki, mintha a „Bontás betöltése…" után **magától
visszazárt** volna, és újra meg kellene nyitnia. (Bejelentett hiba.)

Minden ilyen újrarajzolás mostantól a `FunTasy.accOrzo`-n megy át: megjegyzi, melyik sor volt
nyitva (a `data-*` jelzőiből képzett, sorrendtől független kulccsal) és mi állt a panelben,
majd az újrarajzolás után visszateszi. Így **nincs villanás és nincs újabb lekérés** sem.

**Csak a kész panelt szabad megőrizni.** Az első változat mindent visszatett — a
hibaüzenetet is. Egy átmeneti hálózati hiba így **beragadt**: a sor nyitva maradt, a
következő kattintás pedig becsukta ahelyett, hogy újrapróbálta volna, tehát a bontás csak
két kattintásra jött vissza. (Bejelentett hiba, a javítás javítása.) Ezért a panel az
**állapotát jelzőben hordozza** (`data-allapot`: `tolt` / `kesz` / `hiba`), nem a szövegéből
találgatjuk:

- `kesz` → változatlanul visszakerül;
- `tolt` → a régi kérés már az elavult sorra futna ki, ezért **újraindul** a betöltés;
- `hiba` → **nem** kerül vissza; a sor bezár, és egy kattintás újrapróbálja.

**A hibaüzenet megmondja az okot is.** A lekérő (`FunTasy.lekero`) több úton próbálkozik —
direkt kérés és CORS-proxyk, lásd „A CORS-proxyk cserélhetők" szakaszt —, és a
hibaüzenetbe beleírja, melyik miért nem ment
(`direkt:CORS · corsproxy:HTTP 429 · allorigins:időtúllépés`). Ez eddig elveszett: az
accordion csak annyit írt ki, hogy „A bontás lekérése nem sikerült", amiből sem a
felhasználó, sem a fejlesztő nem tudta eldönteni, hálózat-e, proxy-e vagy az API változott.
Mostantól a szöveg alatt halványan ott az ok.

Ez mindkét ligában több helyen fordul elő (élő keret, perc-utántöltés, élő pontok), ezért a
mechanika a közös rétegben van — külön-külön megírva pontosan egy helyen maradt volna ki.
Rögzítve: `tesztek/accordionorzes.teszt.js`.

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
| `naplo/` | **Mérési archívum** (lezárt egyszeri megfigyelések nyers naplói — lásd `naplo/README.md`). A hozzájuk tartozó workflow-k törölve; a következtetések ebben a README-ben vannak (3/b, „Automatikus cserék”, „Ki van még a pályán”, bónusz-szakasz). |
| `hatekonysag.json` | Kezdőállítási hatékonyság fordulónként (`{updated, rounds:{"1":{név:{sz, le}}}}`) — az NB1 KEZD% oszlopának és meccs-nézetének forrása. A gyűjtő minden futásnál az összes tárolt fordulóra újraszámolja (determinisztikus). A PL-nek nincs ilyen fájlja: ott a böngésző számol a már betöltött kerettörténetből. |
| `guardiola.json` | A **Guardiola mutató** fordulónként: `{rounds:{forduló:{szakvezető:{teny,alt,guard}}}}`. `guard` = a mostani keret pontja mínusz a múlt hetié ugyanebben a fordulóban. A gyűjtő számolja, mert a múlt heti kerethez az adott forduló **összes** játékosának nyers pontja kell (`bontasok/<forduló>.json`, fordulónként 40 KB) — a lapnak így elég ez a pár kilobájt. |
| `draft_pontok.json` | A PL **teljes mezőnyének** fordulónkénti pontja és perce: `{rounds:{gw:{element:[pont,perc]}}}`. A Guardiola mutatóhoz kell: a múlt heti keretben lehet olyan játékos, aki már **senkinél sincs** (GW1→GW2-ben 11 ilyen volt), és akkor a pontja sehol nem lenne meg. A perc az automatikus cserékhez. Csak az kerül bele, aki játszott vagy pontot szerzett. |
| `draft_guardiola.json` | Ugyanaz, mint a `guardiola.json`, csak a PL-re, `liga_id` kulccsal. |
| `keretvaltozasok.json` | A **Változtatások** fül adata fordulónként: ki került ki (`ki`), ki jött be (`be`), kinek változott a szerepe (`szerep`), és a magyarszabály különbsége (`bonusz`) — mindegyik mellett az, hogy **mennyit ért**. A tételek összege pontosan a `guard`; ezt a `stimmel` mező is jelzi. A lap ebből vezeti le a tabellában álló számot. |
| `draft_keretvaltozasok.json` | Ugyanaz a PL-re, `liga_id` kulccsal — plusz a `gepE`/`gepU`: mennyit hozott a **zárási automatikus csere** a régi és az új keretnek. A játékos-tételek csak azt tartalmazzák, amit az **ember** döntött; a gép hozadéka külön áll. Játékosnevet nem tárol: a lap a `draft_players.json`-ból oldja fel. |
| `zarasok.json` | A forduló-zárás változásai (`{updated, rounds:{"1":{csapat_id:{pont:[{e,elott,utan}], ki:[...], be:[...]}}}}`) — a főoldali „Zárási változások” panel forrása. A gyűjtő **pontosan egyszer**, a véglegesítő futásban írja: a zárás előtti tárolt pillanatkép és a friss állapot különbsége. Üres bejegyzés is eredmény („a zárás nem változtatott semmit”); régi pillanatkép nélkül (backfill) nem számolható. A `ki`/`be` külön listák — a pad-jelzőből nem tudható, ki kinek a helyére állt be, ezért **párosítást nem állítunk**; elemeik `{e, pts}` alakúak, mert a beállt játékos pontja mondja meg, mit hozott a csere (a régi, csak azonosítót tartalmazó alakot a lap még elfogadja). A GW1 a git-történetből lett pótolva. |
| `meccsek.json` | Fordulónkénti NB1-meccsek (`{updated, rounds:{"5":[{id,h,v,hp,vp,vege,start}]}}`) — a pont-részletező fölötti meccs-sor forrása. A gyűjtő írja a keret-válaszokban utazó meccs-objektumokból; **eredmény csak lezárt meccsről kerül bele** (részállást a 3 óránként futó gyűjtő véglegesként örökítene meg). A hiányzó vagy befejezetlen meccsű fordulót meccslistával kéri újra, a már teljeset csak akkor, ha a forduló hivatalos pontja változott (ez a **pótolt meccs** esete — az elhalasztott meccs nincs benne a listában, tehát „befejezetlenként” nem látszana). **Nem a forduló összes meccse:** csak azoké a kluboké, amelyeknek van játékosuk valamelyik keretben — a részletező fölötti sorhoz ennyi kell. |
| `jatekosok.json` | A mezőny **összes** játékosa (`{players:{id:{n,t,p,u21,pts,ar}}}`) — a főoldali lista és keresés forrása. A gyűjtő írja, egy kérésből. |
| `bontasok/<forduló>.json` | A forduló **tételes pont-bontása** minden játékosra (`{round, bontasok:{cp-azonosító:[{n,v,p}]}}`): mi adta ki a heti pontot — gól, gólpassz, játszott perc… A gyűjtő a forduló lezárásakor **egyszer** kéri le mind a 385 játékosra, és MLSZ-korrekció után újra. Az `updated` mező szándékosan nincs benne (lásd `keretek/`). |
| `zarasok_nb1.json` | Fordulónként azok a **meccs utáni pontigazítások**, amiket az MLSZ a forduló véglegesítése előtt vezetett át. Alakja a PL `zarasok.json`-jáét követi, hogy ugyanaz a megjelenítés szolgálhassa ki: `{rounds:{forduló:{szakvezető:{pont:[{n,cp,pos,tm,elott,utan,d}]}}}}`. Az `nk:1` jelzőt viselő sor azt jelenti, hogy a játékos nem ismert: ott név helyett „Ismeretlen játékos" áll, és `elott`/`utan` helyett `dl` (a változás mértéke). Élesben ritka esemény: a fájl üres vázként létezik, és csak akkor bővül, ha tényleg történt igazítás — a panel is csak akkor jelenik meg. |
| `arak.json` | Az árak **változásai** (`{arak:{id:[[dátum, ár], …]}}`). Csak akkor bővül, ha egy ár tényleg megváltozott. |
| `valtozasok.json` | A változásnapló bejegyzései (`{bejegyzesek:[{datum, tipus, ligak, cim, leiras}]}`). **Kézzel írjuk**, nem gyűjtő tölti. |
| `valtozasok-vazlat.json` | **Még nem publikált** naplóbejegyzések, ugyanabban a formában. A napló oldala ezt nem olvassa; a kész bejegyzés innen kerül át a `valtozasok.json`-ba. |
| `valtozasok/index.html` | A változásnapló oldala („Mi újult meg?"). |
| `collect.py` | GitHub Actions: H2H eredmények (ranglista-végpont) **és** keretek (keret-végpont) gyűjtése, forduló-lezárás megállapítása, kimaradt fordulók pótlása. |
| `collect_draft.py` | GitHub Actions: az FPL Draft liga adatai. A résztvevők valódi nevét és az `entry_id`-t kiszűri (a repó publikus). |
| `draft.json` | Az FPL Draft liga adatai (résztvevők, menetrend, eredmények) — a `pl/index.html` forrása. |
| `draft_players.json` | FPL játékos-törzs: `{players: {id: {n: név, t: klub, p: poszt}}, teams: {csapat_id: rövidnév}}`. A `teams` a fixtures-válasz csapat-azonosítóinak feloldásához kell (kinek kezdődött el a meccse). |
| `draft_squads.json` | A jelenlegi FPL-keretek (tulajdonlás): `{liga_id: [játékos_id,...]}`. |
| `draft_history.json` | Fordulónkénti FPL-keretek pontokkal (`{rounds:{gw:{liga_id:[{e,b,pts},...]}}, kesz:[...]}`) — a GW1 indulásától gyűlik. A **`veglegesek`** lista mondja meg, mely RÉGI fordulók véglegesek: azokat a gyűjtő nem kéri le többé. Az aktuális fordulót minden körben lekéri, a zárás után is (lásd „3/b. A lezárás”). |
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

### A CORS-proxyk cserélhetők — és cserélni is kellett (mérve, 2026-08-27)

A böngésző az MLSZ/FPL API-t közvetlenül nem érheti el (a válaszban nincs
`Access-Control-Allow-Origin` — ezt mértük, nem hisszük), ezért minden élő lekérés
proxyn megy át. 2026-08-27-én **a két akkori proxy egyszerre halt meg**: a `corsproxy.io`
401-re váltott (regisztrációhoz kötötték a szolgáltatást), az `allorigins` túlterhelt volt
(522). Mivel minden élő kérés ezen a kettőn múlt, **mindkét liga** élő része — pont-bontás,
élő pontok, élő keret — egyszerre állt le. A tárolt adatot ez nem érintette.

A tanulság: egy ingyenes proxy bármikor eltűnhet, ezért **több független út kell**. A
kilenc jelöltet végigmérő futás (`naplo/proxy-meres.py` → `naplo/proxy-meres.txt`) alapján
az út-sorrend most: `direkt` → `proxy.cors.sh` → `allorigins /raw` → `allorigins /get`
(ez **csomagolva** adja a választ, `{contents: "..."}` — a lekérő kibontja) → `cors.lol` →
`corsproxy.io` (a sor végén, hátha visszaengedik). Az első siker után a lekérő a bevált
úton marad. A láncot a `tesztek/lekero.teszt.js` rögzíti — benne pont a 2026-08-27-i
hibakép: corsproxy 401 + néma allorigins mellett a cors.sh-nak kell kiszolgálnia.

Ha megint minden út elhasal, a pont-bontás hibaüzenete felsorolja, melyik miért
(`direkt:CORS · corsproxy:HTTP 401 · …`) — ebből lehet diagnosztizálni, kézre esik
képernyőképen is.

**Saját proxy (Cloudflare Worker).** A tartós megoldás a saját közvetítő: a
`tartalek/proxy-worker.js`-ben élő Cloudflare Worker (ingyenes terv, bankkártya nem
kell, a napi 100 000-es keret a forgalmunk sokszorosa). A worker **a repóhoz van kötve**:
a Cloudflare minden `main`-re érkező push után lefuttatja az `npx wrangler deploy`-t, ami
a gyökérbeli `wrangler.toml` alapján a worker-kódot telepíti — kézzel soha nem kell kódot
másolni, a worker együtt változik az oldallal. Csak a két ismert API-t szolgálja ki és csak
ennek az oldalnak, tehát nem lehet visszaélni vele; az MLSZ-válaszokat 60 másodpercig a
Cloudflare peremhálója gyorsítótárazza, így akárhányan nézik ugyanazt, az MLSZ felé
percenként egy kérés megy. A Worker URL-je a `funtasy.js` elején álló `SAJAT_PROXY`
konstansba kerül — amíg üres, a lekérő kihagyja, és a publikus proxyk viszik (utána is
ott maradnak tartaléknak).

### A betűkészlet nem állíthatja meg a lapot (mérve, 2026-08-27)

A három betűcsalád (Inter, JetBrains Mono, Archivo Black) a Google Fontsról jön. Sokáig
sima `<link rel="stylesheet">`-tel — ami **renderelést blokkoló**: amíg a Google nem
válaszol, a lapon *semmi* nincs. Kimérve: ha a `fonts.googleapis.com` nem elérhető, a
`DOMContentLoaded` **57 ms helyett 12 640 ms**. Mobilon, gyenge hálón pont az a helyzet,
amikor az ember megnézné az állást.

Mostantól az ív **aszinkron** (`media="print"` + `onload="this.media='all'"`, mellette
`<noscript>`-ág annak, akinél nincs JS), és a `fonts.gstatic.com`-ra is megy `preconnect` —
a betűfájlok onnan jönnek. Ugyanezzel a méréssel a lap **216 ms** alatt kirajzolódik akkor
is, ha a betűkészlet-szolgáltatás egyáltalán nem válaszol.

A másik fele a CSS-ben van: a három családnak **tartalék-sora** van, és mindegyik egy
változón át megy (`--fo`, `--mono`, `--cim` a `:root`-ban). Enélkül a `display=swap` a
böngésző alapértelmezésével (talpas Times) festene először, más betűszélességgel — a
táblázat ugrana egyet a webfont megérkezésekor. A változók egyben a korábbi **60+ helyre
beírt** betűnevet is egy helyre húzták.

Rögzítve: `tesztek/betukeszlet.teszt.js`.

**JavaScript nélkül** eddig csak az üres váz látszott — panel-címek, üres táblázatok, egy szó
magyarázat nélkül. Mostantól minden oldal tetején `<noscript>`-figyelmeztetés áll, hogy a
táblázatokat a böngésző tölti fel, tehát JS kell hozzá. Ugyanaz az elv, mint a státuszsornál:
ha valami hiányzik, azt az oldal **mondja meg**, ne a látogató találgassa.

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

## 3/b. A LEZÁRÁS — mi mit jelent, és hol dől el

**Ezt olvasd el, mielőtt bármelyik lezárás-logikához hozzányúlsz.** A „lezárult" szó a
projektben **négy különböző dolgot** jelent, külön jelzőkkel és külön következményekkel.
Egyszer már abból lett hiba, hogy az egyiket a többi ismerete nélkül írtam át.

| mit zárunk le | liga | miből dől el | mire hat |
|---|---|---|---|
| **egy meccs** | NB1 | a meccslista `status == "completed"` — de csak a `meccsAllapot` időkorlátaival együtt hihető | a részletező üzenete, a `meccsek.json` eredménye, a játszott perc sora |
| **egy meccs** | PL | `started` → `finished_provisional` → `finished` (három állapot) | a perc-oszlop „vége", a bónusz jelölése |
| **egy forduló** | NB1 | mindenki játszott (`played` vagy `nogame`) **és** minden meccs lement; biztonsági háló: az MLSZ továbblépett (`mlsz_lezarta`) | bekerül-e a tabellába, vagy `provisional` marad |
| **egy forduló** | PL | a `game` végpont **`current_event_finished`** mezője | az automatikus cserék bekerülése, a bónusz véglegessége, a státuszsor |

**A PL forduló-zárás egyetlen pillanat, több jelzővel.** Mérve (2026-08-25, 08:03 és
08:23 UTC között) **egyszerre** billent át mind: `current_event_finished` → igaz, a H2H
meccsek `finished`-re, az `event-status` `points` `p`-ről `r`-re, a `bonus_added` igazra.
Ezért olvassa a gyűjtő a `current_event_finished`-ből, az oldal bónusz-jelzése pedig a
`points === "r" || bonus_added`-ből — **ugyanazt az eseményt**, két végpontról (a Draftnak
nincs `event-status`-a, az a klasszikus FPL-ről jön). Ha valaha eltérnének, az mérésre
való, nem tippelésre.

**A `current_event` ilyenkor MÉG a régi forduló** — a zárás nem forduló-váltás. Aki ezt
összekeveri, az a cseréket veszíti el (lásd lentebb).

### Amit a lezárás után is frissíteni KELL

| forrás | meddig frissül | miért |
|---|---|---|
| NB1 keret + pont | az aktuális **és az előző** forduló minden körben, plusz körbeforgó ellenőrzés négy régi fordulóra (`ellenorzendo`) | az MLSZ utólag korrigál |
| PL keret + pont | az **aktuális** forduló minden körben (a zárás után is, amíg a `current_event` tovább nem lép), plusz minden forduló, ami nincs a `draft_history.json` `veglegesek` listájában | az FPL a záráskor automatikus cseréket hajt végre, és utólag is korrigálhat |
| PL meccseredmény | a `draft.json` `schedule`/`standings` az FPL saját válaszából, minden körben | ez a hivatalos eredmény, nem mi számoljuk |
| NB1 meccseredmény | a `meccsek.json` addig kéri újra a fordulót, amíg van benne eredmény nélküli meccs | részállást nem tárolunk |

A véglegesítő futás **melléktermékként a zárási különbséget is elmenti** (`zarasok.json`):
a zárás előtti tárolt pillanatkép és a friss állapot eltérése — ebből él a főoldali
„Zárási változások" panel. A pillanatkép legfeljebb 3 órával a zárás előtti; a mérés
szerint (GW1) a lefújás és a zárás között semmi nem változik, tehát ez a különbség
ténylegesen a lockdown műve.

**Amit soha ne csinálj:** ne szüntesd meg az „aktuális fordulót minden körben lekérjük"
szabályt azzal az indokkal, hogy a forduló már lezárult. Az a szabály **nem** a zárásról
szól, hanem az utólagos korrekciókról — a zárás utáni egy hét különben vakon maradna.
Ez pontosan egyszer már megtörtént (2026-08-25), és a saját tesztem rögzítette a hibás
viselkedést, mielőtt észrevettük volna.

**Névhasználat.** A `collect_draft.py`-ban a `kesz` **meccset** jelent (`atalakit`), a
fordulók listája ezért `veglegesek`. Ugyanez a csapda volt a `.pos`/`.ppos` és a
`.meccsfej` esetében is: ha egy szónak már van jelentése a kódban, ne adj neki másikat.

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

#### A két klubot külön kell kérni (mérve, 2026-08-30)

Élő fordulónál a meccs-objektum **csak** `id`, `start_at`, `status`, `home_score`,
`away_score` és `round_number` — **klub nélkül**. A gyűjtő ilyenkor `"?"`-et írt a
`meccsek.json`-ba, és mivel az oldal a játékos klubjára szűrve keresi a meccset, a
profilban kötőjel állt az ellenfél helyén, holott az eredmény megvolt. Ez a 6. fordulónál
derült ki: a `meccsek.json` csak 08-24 óta létezik, előtte az 1–5. fordulót már **lezártan**
töltöttük le, csapatostul.

A megoldás: a két csapatot **explicit kérjük** az include-ban. Amit a mérés adott
(`naplo/mlsz-elo-meccs.txt`, élő 6. forduló):

| Amit kértünk | Eredmény |
|---|---|
| `games.home_team` + `games.away_team` | **működik** — 22,3 KB → 24,8 KB (+2,5 KB) |
| `games.homeTeam` / `games.awayTeam` | a mező meg sem jelenik |
| `games.teams` | a mező meg sem jelenik |
| `games/<id>`, `matches/<id>`, `fixtures/<id>` a gyökéren és `competitions/3` alatt | mind a tíz alak **404** |
| a birtokolt játékosok saját klubjaiból levezetve | csak 4/6 meccs, és a hazai/vendég oldal sehogy |

A csapat-objektum itt **sovány** (`id`, `name`, `short_name`, `color_hex`), **logó nélkül** —
tehát ez nem a fenti 118 KB-os hízás, csak +2,5 KB. A pont-bontás végpontja (ami a lenyílóhoz
amúgy is megy) semmilyen include-dal nem tud a meccsről.

**Vissza nem évülő védelem:** a `"?"` klubú meccs is hiányosnak számít, tehát a forduló addig
marad az újrakérendők közt, amíg valódi név nem érkezik. Enélkül, ha egy forduló összes meccse
lement, mialatt a nevek még `"?"`-ek voltak, a forduló kikerült volna az újrakérendők közül, és
az MLSZ továbblépése után **soha többé** nem kértük volna le — a `"?"` véglegesen bent ragadt
volna. Rögzítve: `tesztek/gyujto_meccsek.py` M7 és M8, mindkettő bizonyítottan bukik a régi kódon.

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

### Játékostörzs és a szezon egésze (mérésekkel, 2026-08-25)
A játékosprofilhoz két dolgot kerestünk: a **teljes játékostörzset** (a kereséshez) és
minden játékos **fordulónkénti pontját**. Amit a mérések hoztak (`naplo/mlsz-jatekoslista.txt`):

| Kérdés | Válasz |
|---|---|
| Van teljes játékoslista? | **Igen:** `competitions/3/players?include=team,position,summary_statistics` — 385 játékos, klub, poszt, `is_u21`, `injury_status`, `market_price`, `competition_points`. |
| Egy kérésből? | **Igen**, `per_page=500`-zal (alapból 15/lap, 26 lap). A `page[size]`-t eldobja. |
| Ad fordulónkénti pontot? | **Nem.** A `weekly_points` mindig az **aktuális** fordulóé, és a végpont `filter[round_id]`-re **400**-at ad. |
| A pont-bontás lekérhető forduló-szűrő nélkül? | **Igen**, akkor az egész szezon jön — **de csak az első 50 sor.** |
| Lehet lapozni rajta? | **Nem.** Sem `page`, sem `page[number]`, sem `offset`, sem `page[offset]`, sem `per_page`/`limit`/`page[size]` — mind ugyanazt az első lapot adja vissza. Egy szezon ~109 sor, tehát **a teljes szezon egy kérésből nem hozható le**; fordulónként viszont ~22 sor, ami elfér egy lapon. A profil ezért fordulónként kérdez, és csak akkor, ha muszáj. |

**A pontok felbontása 0,25.** 377 (játékos, forduló) párra összevetettük a bontás-sorok
összegét a keret-fájlok tárolt heti pontjával: **238 pontosan egyezett**, 123 esetben a
bontás üres volt — de mind a 123-nál a tárolt érték is 0 volt (ez az MLSZ ismert
viselkedése: 0 pontos játékosra üres bontást ad). A maradék **16 eltérés mind pontosan
0,01** volt, és mind **pados** játékos: a felezés utáni két tizedesre kerekítés miatt.
Ebből következik, hogy az alappont mindig 0,25 többszöröse — a visszaszámolásnál ezért
kerekítünk negyedre.

### A játékos-adatlap végpontja (mérve, 2026-08-25)
`GET competitions/3/players/{competition_player_id}` — **nincs `data` burok**, a mezők a
gyökérben állnak (ezen csúszott el az első mérés: a `data`-t néztem, és üresnek látszott).
Amit ad a törzs-soron felül:

- `countries` — ebből derül ki, hogy magyar-e a játékos (a listás törzs ezt nem adja);
- `rounds` — fordulónkénti sor `market_price`-szal, `is_played`-del és a forduló
  objektumával: vagyis **a múltbeli árak visszamenőleg is megvannak**, játékosonként egy
  kéréssel. Az `arak.json` ettől függetlenül hasznos: az finomabb felbontású (a forduló
  közbeni változásokat is rögzíti);
- `extended_summary_statistics` — hazai/idegenbeli átlagok (jelenleg nem használjuk).

**Amit NEM ad: a jövőbeli ellenfelet.** A `rounds` csak az eddigi fordulókat sorolja, és
ellenfél nincs benne.

### A jövőbeli menetrend nem érhető el (mérve, 2026-08-25)
Emiatt az **NB1-profil csak a lejátszott fordulókat sorolja fel** — a PL-profil előre is
megy, mert ott a Draft adja a hátralévő meccseket. Huszonhét üres sor ellenfél és időpont
nélkül nem információ, csak zaj; ha a menetrend előkerül, az NB1 is előre megy majd.
Az MLSZ fantasy felülete mutat ilyen táblát („Következő mérkőzések"), tehát
az adat létezik — de a hozzá tartozó végpontot nem sikerült megtalálni. Ami 404-et adott:
`games`, `matches`, `fixtures`, `competitions/3/games`, `competitions/3/schedule`,
`competitions/3/game-days`, `competitions/3/rounds`, `competitions/3/teams`,
`competitions/3/teams/{id}[/games]`, `teams/{id}[/games|/next-games]`,
`games?filter[team_id]`, `rounds?filter[competition_id]`. A keret-végpont jövőbeli
`round_id`-val HTTP 200-at ad, de **üres listát** (a keret csak elindult fordulóra
létezik), a `competitions?include=rounds` pedig csak a **már elkezdődött** fordulókat
sorolja (mérés idején 6-ot), lapmérettől függetlenül.

A következő lépés a felület JS-bundle-jének visszafejtése lenne — ugyanaz a módszer,
amivel a pont-bontás végpontja megkerült. A PL-oldalon ez a gond nincs: ott a Draft
`element-summary` `fixtures` tömbje adja a hátralévő meccseket, ellenfél-azonosítóval és
pálya-jelzéssel.

### Az árakról nincs előzmény (mérve, 2026-08-25)
A törzs a `current_round.market_price` mezőben a **mostani** árat adja. Ár-előzményt az
MLSZ **sehol nem ad**: a `players` végpont az `include=rounds` / `player_rounds` /
`market_prices` / `price_history` / `prices` kéréseket **némán elnyeli** (a válasz sorai
egyetlen új mezőt sem kapnak), az önálló `market-prices`, `player-market-prices`,
`competition-player-rounds`, `player-rounds`, `price-history` végpontok pedig **404**-et.

Ezért a gyűjtő maga naplózza az árakat (`arak.json`), és **csak a változásokat**: a
gyűjtő 3 óránként fut, minden futás feljegyzése napi nyolc azonos sort jelentene. Egy
játékos sora `[[dátum, ár], …]`. A hiányzó vagy nulla árat nem tekintjük változásnak —
különben egy API-hiba hamis „0-ra esett" bejegyzést írna be, amit utólag nem lehetne
megkülönböztetni a valóditól (ugyanaz a logika, mint a 0–0 védelem a `results.json`-nál).
**A listás törzs végpontja nem ad ár-előzményt** — a *játékos-adatlap* `rounds` tömbje
viszont igen, fordulónkénti bontásban (lásd fentebb), tehát a múlt játékosonként egy
kéréssel pótolható. Az `arak.json` ettől függetlenül hasznos: az minden gyűjtő-futásnál
figyel, tehát a forduló KÖZBENI változást is rögzíti, amit a fordulónkénti bontás nem.

### Amit a hivatalos szabályzat rögzít (fantasy.mlsz.hu, 2026-08-25)
A szabályzat több, addig csak mérésből ismert viselkedést megerősít — és a „zárási
változások" kérdését el is dönti:

- **„A heti összpontszám az adott forduló utolsó játéknapjának végén válik véglegessé."**
  Vagyis az NB1-ben a zárás pillanatában **tervezetten semmi nem változik** — nincs
  másnapi bónusz-véglegesítés, mint az FPL-ben. Utólagos módosítás csak hibajavítás
  lehetne (a pontozás a STATS adatbázisából jön), ilyet pedig még nem figyeltünk meg.
- **Halasztott meccs:** a játékosok az eredeti héten nem szereznek pontot; a pont **azon
  a héten** jár, amikor a meccset ténylegesen lejátsszák — annak alapján, hogy a játékos
  benne van-e a **pótlás hetének** piaczárásig kialakított keretében. Ezért fordulhat elő,
  hogy valaki egy héten két meccs után is pontot szerez — a profil fordulónkénti sora
  ezért kezel több meccset.
- **Árváltozás csak piacnyitáskor:** a játékosok ára „minden hétkezdet (piacnyitás) során
  változhat" — tehát hetente egyszer, nem folyamatosan. A piac az előző forduló utolsó
  játéknapjának **másnapján, reggel 10-kor** nyit, és a forduló első meccse előtt
  **2 órával** zár. Az `arak.json` 3 óránkénti figyelése ezt bőven elkapja.
- **A pad kötelező összetétele** (1 kapus + 1 védő + 1 középpályás + 1 csatár), a kezdő
  formáció-korlátai (1 kapus, 3–5 védő, 3–5 középpályás, 1–3 csatár), a kapitány ×2, a
  csere ×0,5 és a magyarszabály (+10, legalább 5 magyar kezdő, köztük U21-es) — mind
  hivatalosan is így van, ahogy a KEZD% számítás használja.
- **Egy valós klubból legfeljebb 3 játékos** lehet egy keretben; hetente **3 csere**
  (téli és válogatott szünetben korlátlan).

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

> A négy különböző „lezárás" áttekintése a **3/b** szakaszban van — ott látszik, melyik
> jelző mire hat. Ez a szakasz csak az NB1 forduló-lezárásának részleteit adja.
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
- **Az MLSZ utólag korrigál** — három megfigyelt esetünk van. 2026-08-20-án a
  fantasy.mlsz.hu már más hivatalos fordulóösszeget mutatott Csendinél, mint amit a
  lezáráskor rögzítettünk (1. forduló +1, 2. +1, 3. −2,5; képernyőképpel igazolva).
  **Hogy melyik játékosnál mozdult a pont, ez a három eset nem visszakereshető**, és nem is
  lesz: a `squad_history.json` első játékos-szintű pillanatképe 2026-08-18 12:19-ből van, és
  már az — és utána mindegyik — a JAVÍTOTT összegeket adja ki (38,00 / 42,88 / 42,88 alap +
  10 bónusz = 48 / 52,88 / 52,88). A régi értékek csak a `results.json` csapatösszegében
  éltek, bontás nélkül. A `zarasok_nb1.json`-ban ezért „Ismeretlen játékos" névvel állnak
  (`nk:1`), és csak a változás mértéke (`dl`: +1, +1, −2,5) — nevet nem találunk ki hozzájuk.
  A 08-20-i szinkron óta (3 óránkénti összevetéssel) nem volt újabb ilyen.

#### A szakvezetőt a felhasználóneve azonosítja — és ha nem, arról szólunk

A gyűjtő a ranglista-végponton **névre keres** (`filter[search]`), majd a találatok közül azt
veszi, akinek a `username`-je pontosan egyezik. Ha nincs pontos egyezés, a lista első elemét
használja — ez azért kell, mert a válasz nem mindig hozza a `username` mezőt.

Ez a visszaesési út **csendben** működött, pedig ha valaha félrekeresne, egy **másik
szakvezető pontjait** írná be a tabellába — pont az a „csendes, hihető, rossz" hibafajta,
ami ellen a többi védelem is szól. Mostantól a futásnapló kiírja (`stderr`), ha a fallbackra
került sor, és azt is, hány találat volt. A viselkedés nem változott, csak láthatóvá vált.

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

> A harmadik állapotot a **forduló** zárása adja — ugyanaz az esemény, amiből a gyűjtő
> az automatikus cseréket veszi (3/b). Két végpontról olvassuk, mert a Draftnak nincs
> `event-status`-a.

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

**Mérve, lezárva (2026-08-25):** napi zárás NINCS — a napok napokig `p`-n álltak, és
mind a forduló lockdownjakor váltottak `r`-re (08:03–08:23 UTC, két lépésben: előbb a
pontok/bónusz, ~15 perccel később a `current_event_finished`). A nyers napló:
`naplo/fpl-allapot.txt` (archívum).

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

### Ki van még a pályán (PL)

A pont mellett ott a játékos percei és az, hogy kezdőként lépett-e pályára — a keretben
és a meccs nézetében, **fejléccel** (`perc · meccs · kezdő · pont`), mert a címkézetlen
szám elsőre rejtély:

| oszlop | mit mutat | mikor |
|---|---|---|
| `perc` | a játékos lejátszott percei (`stats.minutes`) | mindig |
| `meccs` | a meccsóra, lefújás után `vége` | **csak az élő fordulóban** |
| `kezdő` | `K`, ha kezdőként lépett pályára, egyébként `–` | mindig |

**Lezárt fordulóban a meccsóra elmarad** — ott minden meccs lement, tehát mindenkinél
`vége` állna. A fejléc is két oszlopra rövidül. Az adat forrása ilyenkor **nem** az élő
lekérés (`LIVEPERC`), hanem az adott forduló saját `event/{gw}/live` válasza
(`regiPercBetolt` → `REGIPERC[gw]`) — ugyanaz a kérés, amiből a pont-részletező is jön,
fordulónként gyorsítótárazva, tehát nincs miatta plusz lekérés. Aszinkron, ezért a modal
**előbb jön fel, mint a percek**, és az adat megérkeztével rajzolja újra magát
(`percUtantoltes`); az újrarajzolás csak akkor fut le, ha közben nem lépett máshova a
néző. A `draft_history.json` percet nem tárol, ezért kell a lekérés.

**Akinek nincs adata, annál üresek a cellák, és ez nem csúsztat el semmit:** a `.pts`
jobbra zárt és utolsó, a `.nm` pedig `flex:1`, tehát a pont oszlopa akkor is a helyén
marad, ha a perc-cellák hiányoznak (élő fordulóban ez a még el nem kezdődött meccsek
játékosainál látszik).

**Nyers értékeket mutatunk, nem értelmezünk a néző helyett.** A „lecserélve" felirathoz
tűréshatár kellene, és egy egyperces csúszás a két végpont között hamis állítást szülne.
A két számból magától látszik, pályán van-e: ha egyeznek, igen.

**A meccsóra a játékosok perceinek maximuma**, klubonként összegyűjtve — nem a fixtures
`minutes` mezője. Élő meccs alatt mérve (2026-08-24) az **mindig 0**, még a lement
meccseknél is. A játékosok percei viszont együtt ketyegnek: 15 mintában, fél óra alatt a
futó meccs minden pályán lévő kezdője ugyanazt a számot mutatta. Ez nem becslés: 11
kezdővel és legfeljebb 5 cserével mindig marad valaki, aki végigjátssza a meccset.
A `perccellak.teszt.js` mockjában a `minutes` **szándékosan 0** — ha valaki visszatenné a
meccs saját mezőjét, a teszt bukik.

**A lecserélt játékos percei megállnak** — mérve: egy lement meccsen a kezdők 81', 80',
75'… értéken álltak (ekkor cserélték le őket), a csereként beállók pedig 28', 22', 20'…
értéken. 15 mintában, fél óra alatt egyetlen szám sem változott.

**A meccsóra 45-nél és 90-nél megáll**, ezért a 90 önmagában nem árulja el, vége van-e a
meccsnek — ott a cella `vége`-t ír.

**Dupla fordulóban mindkét meccs értéke szerepel**, `|` elválasztóval. A `kezdő` oszlop
ilyenkor nem bontható meccsre: az `explain` **csak pontot érő tételeket** tartalmaz, a
`starts` sosem szerepel benne.

**Az adat késése ~3 perc** a valós időhöz képest (mérve, stabilan): 19:14:47-kor 12' a
valós 14.8 helyett, 19:43:00-kor 40' a valós 43.0 helyett.

Fejléc csak ott jelenik meg, ahol van is perc-cella (élő forduló, elkezdődött meccs) —
lezárt fordulóban nincs mit címkézni. A címke nem lehet szélesebb a saját oszlopánál,
különben elcsúszik a számoktól; a teszt középpontra méri.

### A meccs állása a pont-bontás fölött (PL és NB1)

A játékosra kattintva a pontok fölött egy sor: `ARS 2–1 BRE · 70. perc`. Lefújás után
`vége`, el nem kezdődött meccsnél nincs állás, csak a két klub — **0–0-t nem írunk ki**,
mert az állítás lenne, nem adat. Kettős fordulóban mindkét meccs külön sort kap.

Az állás a **fixtures** válasz `team_h_score` / `team_a_score` mezőjéből jön:

- **élő fordulóban** a már meglévő `LIVEMECCS`-ből, tehát nincs miatta plusz lekérés;
- **lezárt fordulóban** egy fordulónként gyorsítótárazott `event/{gw}/fixtures` kérésből
  (`forduloMeccsei` → `REGIFX`). Itt nem kell utántöltés, mint a perc-oszlopoknál: a
  `bontasHTML` amúgy is aszinkron, tehát mire a lenyíló tartalma elkészül, ez is megvan.

A fixtures válasz értelmezése **egy helyen** él (`meccsRekord`), hogy az élő és a lezárt
forduló ne csússzon el egymástól.

**Az NB1-en ugyanez a sor** a `meccsek.json`-ból jön (a gyűjtő tölti, lásd a fájl-táblázatot),
a jobb oldali címke pedig a már meglévő `meccsAllapot`-ból (időkorlátokkal védve) — a
kirajzolás közös (`FunTasy.bontasMeccsSor`), az adat-előállítás ligánkénti adapter.
Az NB1 részletezője emellett **első sorként a játszott percet** is mutatja: a "Játszott
perc" sor eddig ki volt szűrve (0 pontot ér), pedig megjön — aki 60 percnél kevesebbet
játszott, annak a perce sosem látszott. A sor **csak lement meccsnél** kerül be: az
állapot-kaput (előtte/fut → szöveges üzenet) nem kerülheti meg. 0 percnél az üzenet
marad ("Nem lépett pályára"), mert az többet mond.

**Miért a lenyílóban, és nem oszlopban.** Kimérve (360px): egy állás-oszlop a névnek
maradó helyet 112 → 70px-re vinné, tehát a nevek látható része csonkulna; a név alatti
második sor a sormagasságot 31 → 51px-re. A lenyíló ezzel szemben ingyen van, és ott az
állás a bontást is olvashatóvá teszi (a „Kapott gólok 3" az `AVL 0–3 BHA` alatt már
mond valamit). A keretlistában a *pillantásra* szóló kérdésre — kezdett-e, pályán
van-e még — a perc-oszlopok felelnek, azt ez nem váltja ki.

### Automatikus cserék a forduló zárásakor (PL)

Az FPL a forduló végén **automatikus cseréket** hajt végre: a nem játszó kezdő helyére
beállítja az első beférőt a padról — ezért számít a pad sorrendje. Mérve
(2026-08-25, `naplo/fpl-cserek.txt`):

- **Az FPL átírja a pick `position` mezőjét** (a becserélt 12→11 alá kerül, a kikerülő a
  helyére a padra), és **külön `subs` listát is ad** (`{element_in, element_out, event}`).
  A gyűjtőnk a `position`-ből számolja a `b` (pad) jelzőt, tehát magától rendbe jön —
  **ha időben újra lekéri a fordulót.**
- **Ez a lockdownkor történik**, nem a meccs után: 08:03 és 08:23 UTC között billent át
  minden egyszerre (H2H `finished`, `points` → `r`, `bonus_added`, `current_event_finished`).
- **A `current_event` ilyenkor MÉG a régi forduló** — a zárás jelzése a `game` végpont
  **`current_event_finished`** mezője. (A `processing_status` és a `waivers_processed`
  végig változatlan maradt, azok mást jelentenek.)

Ezért a gyűjtő addig kéri újra a fordulót, amíg nem tudja biztosan, hogy lezárult:
a `draft_history.json` **`veglegesek`** listája tartja számon a véglegesített fordulókat.
Egy forduló akkor kerül bele, ha az FPL már túllépett rajta, **vagy** ő az aktuális, de
`current_event_finished` — és csak akkor, ha abban a futásban **minden csapat** kerete
megjött (különben egy elhasalt lekérés a csere előtti állapotot rögzítené véglegesnek).

**Az aktuális fordulót ettől függetlenül minden körben lekérjük**, a zárás után is —
a `veglegesek` lista csak a *régi* fordulókról dönt. Lásd „3/b. A lezárás": ez a szabály
nem a zárásról szól, hanem az utólagos korrekciókról. Rögzíti: `gyujto_draftzaras.py`.

2026-08-25-én ez **csak azon múlt**, hogy a futás hat perccel a zárás után esett.

### A zárás és a gyűjtés közötti rés (PL)

Az FPL a fordulót a **lockdownkor** zárja le egyszerre — mérve 2026-08-25-én 08:03 és
08:23 UTC között billent át minden: a H2H meccsek `finished`-re, a `points` `p`-ről
`r`-re, a `bonus_added` igazra, a `current_event_finished` igazra. A gyűjtőnk viszont
3 óránként fut, tehát van egy rés, amikor a `game` végpont már lezártat mond, de a
tárolt `draft.json`-ban még a zárás előtti állás van.

Ebben a résben a státuszsor korábban **„Naprakész · ellenőrizve <most>"**-ot írt: a
kiírt idő a *lekérésé* volt, nem az *adaté* — vagyis pont akkor állította magáról, hogy
naprakész, amikor bizonyíthatóan nem volt az. Most megmondja, hogy a forduló lezárult,
az eredmény a következő adatfrissítéssel jön, és a **tárolt** állás idejét írja ki.
Rögzíti: `zarasires.teszt.js`.

Az NB1-en ez a rés nem áll fenn: ott a gyűjtő maga dönti el a lezárást, és ugyanabban a
futásban írja be az eredményt is.

### Név és monogram: a monogram sosem vágódik le

A csapatnév mellett álló monogram (`.mgr`) **szűk helyen az azonosító** — ezért nem a
sor végén vágjuk le, hanem a nevet rövidítjük. A pár közös (`nevMgr` a `funtasy.js`-ben):
a név `.nv`-be kerül (ellipszis, zsugorodik), a monogram `flex:none`. A konténerek
(`td.name`, `.match .h/.v`) flexek, nem `text-align`-nal igazítanak.

Mobilon a szélesség-korlát a **néven** van (`td.name .nv{max-width:42vw}`), nem a cellán:
a `td` `max-width`-je table-layout alatt nem korlátoz megbízhatóan, és a hosszú név
kitolta a monogramot a cellából (mérve: a 30 monogramból egy túlnyúlt).

### Kezdőállítási hatékonyság (KEZD%)

**Mit mér:** a keretből elérhető pontok hány százalékát hozta a ténylegesen beállított
kezdő. `szerzett / lehető`, ahol a lehető a keret **utólag ismert** pontjaiból számolt
legjobb érvényes felállítás. A tabella KEZD% oszlopa a lezárt fordulók összesítése
(ugyanabból a körből, amiből a tabella számol — élő/ideiglenes forduló nem számít bele);
a meccs-nézet fejlécében és az egymás elleni listában fordulónként áll.

**NB1** (a gyűjtő számolja, `collect.py hatekonysag` → `hatekonysag.json`):
- A pad kötelezően 1 kapus + 1 védő + 1 középpályás + 1 csatár —
  formációválasztás tehát nincs. Az optimum **mégsem** posztonkénti minimum: a
  magyarszabály (+10) függ attól, ki ül a padon, ezért a ~160 pad-kombinációt
  végigpróbáljuk, mindegyikhez a legjobb kezdő a kapitány.
- A tárolt `week` már kész érték (kapitányi ×2, pad ×0,5) — a nyers pontot a `cap`/`sub`
  jelzőből fejtjük vissza. A szerzett a `keret_osszeg` (= a hivatalos fordulópont).

**PL** (a böngésző számolja, `plHatekonysag` a `pl/index.html`-ben):
- A legjobb **érvényes** kezdő 11: pontosan 1 kapus, 3–5 védő, 1–3 csatár, a középpályás
  a maradék (2–5). A Draftban nincs kapitány, a pad pontja nem számít.
- Élő fordulóra a tabella nem számol (csak lejátszott meccsekre aggregál); a meccs-modal
  élő meccsen a friss pontokból számol, „élő" jelöléssel.

A megjelenítés közös (`opts.kezd` hook a `FunTasy.create`-ben: tabella-oszlop, h2h-jel,
`fordulokHTML`; `FunTasy.kezdParHTML` a meccs-fejléc kétoldalt igazított sora) — a
számítás ligánkénti adapter. A **Fordulók fül is közös** (`T.fordulokHTML`): a PL és az
NB1 korábban két majdnem azonos példányban tartotta (`fordulokHTML` / `seasonHTML`),
ebből lett a kimaradó NB1-es KEZD% — az ilyen kettőzés pontosan az, amiről a
6. fejezet közösítés-szabálya szól. Ugyanez történt a **zárási változások** paneljével is:
két külön példányból két különböző kinézet lett, ezért a HTML most közös
(`FunTasy.zarasLista`), és a két oldal csak normalizált sorokat ad át.

A **játékosprofil megnyitása** is közös (`FunTasy.profilNezo`): a cím, a felirat, a
betöltés-jelzés, az elavultság-védelem (amíg tölt, nyitható másik — a később beérő válasz
nem írhatja felül az újabbat) és a hibaüzenet egy helyen van. A két oldal csak azt adja meg,
hogy a kulcsból hogyan lesz név és adat, és hogy a kirajzolás után van-e még pótolnivaló
(az NB1-en a gazdátlan fordulók pontja utólag, sorban töltődik).

### A pad sorrendje (PL) — és ami még nyitott

**A pad sorrendje az FPL csere-sorrendje**, nem díszítés: a forduló végén az FPL az első
olyan padost állítja be a nem játszó kezdő helyére, aki formációlag befér. Ezért a padot
**úgy hagyjuk, ahogy jött** — a kezdőket viszont továbbra is poszt szerint rendezzük, ott
a sorrendnek nincs jelentése. (Korábban a padot is poszt szerint rendeztük, és ezzel pont
azt az információt dobtuk el, amiért nézni kell. A `padsorrend.teszt.js` rögzíti.)

Az adat végig jó volt: a gyűjtő a `picks` API-sorrendjében írja ki a keretet, tehát a
`draft_history.json` a 12–15. helyeket az FPL sorrendjében őrzi. A `position` mezőt maga
nem tárolja, csak a `b` (pad) jelzőt — a sorrendet a **lista sorrendje** hordozza.

**Nyitott kérdés: mi történik a fordulózáráskor.** Az FPL ilyenkor végrehajtja az
automatikus cseréket. Amit biztosan tudunk:

- **A tabella nem érintett.** A `draft.json` `standings` és `schedule` mezője az FPL saját
  `league/{id}/details` végpontjáról jön, tehát a hivatalos eredményt mutatja, a cserékkel
  együtt. Ezt nem mi számoljuk.
- **A „Kezdők" összeg viszont a mi számításunk** a tárolt `b` jelzőből, és csak akkor
  követi a cserét, ha a gyűjtő újra lekéri a fordulót.
- **A gyűjtő ma csak az aktuális fordulót kéri le újra** (plusz azokat, amikből hiányzik
  csapat). Amint a `current_event` továbblép, a lezárt forduló **befagy** — azzal a
  keretbeosztással és pontokkal, ami épp akkor volt benne. Ha a csere vagy a bónusz
  véglegesítése a váltás után történik, az a forduló nálunk örökre a váltás előtti
  állapotot mutatja, a „Szezon játékosai" fülön is.

Ezt a kérdést a mérés azóta megválaszolta — lásd az „Automatikus cserék a forduló
zárásakor" szakaszt: az FPL **átírja** a `position`-t (és külön `subs` listát is ad),
a gyűjtő pedig a `veglegesek` listával gondoskodik róla, hogy a csere utáni állapot
kerüljön be.

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
- `element-summary/{element_id}` — **egy játékos egész szezonja EGY kérésből** (mérve
  2026-08-25): a `history` tömbben fordulónként `event`, `total_points`, minden statisztika,
  és egy `detail` mező `"AVL (H) 4-0"` alakban — vagyis az ellenfél, a pálya és a végeredmény
  együtt. A `fixtures` a hátralévő meccseket adja. Ez a PL-oldali játékosprofil forrása;
  a gyűjtőnek nem kerül semmibe, mert a böngésző kéri le, akkor, amikor kell.
  **A klasszikus FPL (`fantasy.premierleague.com/api/element-summary/{id}/`) NEM használható
  helyette:** ugyanaz az útvonal létezik, de az **azonosítók nem egyeznek** a Drafttal. A
  mérésben öt játékosból négynél véletlenül stimmelt a pont, az ötödiknél viszont 1 vs 14 —
  egy felületes ellenőrzés tehát átengedte volna. Mindig a Draft saját végpontját használjuk.
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
- **NB1 szezon közbeni klubváltás — a játékosprofil ellenfél-oszlopa.** A keret-rekord
  fordulónként tárolja a játékos klubját (`team`), tehát azokra a fordulókra, amikor a
  játékos **valakinek a keretében volt**, a profil a helyes klubot — és így a helyes
  ellenfelet — használja. A gond csak azoknál a fordulóknál marad, amikor **senkinél sem
  volt**: ott nincs eltárolt klub, és a pont-bontás sorai sem árulják el (csak a fordulót
  mondják meg), ezért a profil a játékos **mostani** klubjából keresi ki az ellenfelet.
  Aki a szezon közben klubot vált, annál az ilyen — váltás előtti, senkinél sem töltött —
  fordulóknál rossz ellenfél jelenne meg. A téli átigazolási időszakig ez nem fordulhat elő;
  **akkor viszont kezelni kell** — vagy egy klubváltást is rögzítő adatforrásból, vagy ha
  addigra az MLSZ API maga adja a fordulónkénti klubot. A PL-oldalon ez a gond nincs: ott a
  Draft `element-summary` `detail` mezője (`"AVL (H) 4-0"`) magával hozza az ellenfelet.

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

## 5/a4. A Guardiola mutató

**Mennyivel hozott többet a keretváltoztatás, mint ha hozzá sem nyúlsz?**
`guard` = a **mostani** keret pontja mínusz a **múlt heti** kerete **ugyanebben** a
fordulóban. Negatív érték: a változtatás pontba került.

Az alternatíva szó szerint „mi lett volna, ha hozzá sem nyúlok": ugyanaz a 15 játékos,
**ugyanazokban a szerepekben** — aki kezdő volt, kezdő marad, aki a padon ült, ott marad,
a kapitány ugyanaz. **Nem** a régi keretből kihozható legjobb felállítás: azt a KEZD% méri,
és a kettő keveredne.

**Mindkét oldal ugyanazzal a függvénnyel számol** (`keret_osszeg`), tehát a magyarszabály és
a kerekítés is egyformán játszik — a különbség tisztán a keretváltozás műve. Ez nem
formaság: a tárolt `week` a pados játékosnál az API már felezve-kerekített értéke
(0,75 → 0,38), a bontásból számolt nyers pont viszont nem — ha a két oldal máshonnan
dolgozna, a **változatlan** keret is „+0,01"-et mutatna. Ezért a `teny` egy centtel eltérhet
a hivatalos fordulóponttól; a **mutató** viszont pontos, és azt írjuk ki.

Szándékosan **nem** a hivatalos fordulópontból vonunk: abban egy utólagos MLSZ-korrekció is
benne lenne, az pedig nem a szakvezető döntése.

Nincs érték az **első** fordulóra (nincs mihez hasonlítani) és a még **le nem zárt**
fordulóra (nincs meg a `bontasok/<forduló>.json`).

**A bontás a valaha birtokolt játékosokra is kiterjed.** A játékostörzs (`players` végpont)
csak a *mostani* mezőnyt adja: aki elmegy a bajnokságból, abból kiesik — a keret-előzményben
viszont ott marad. Ezek a játékosok korábban kimaradtak a bontásból, és 0 ponttal
szerepeltek a mutatóban, **holott játszottak**: Skribek az 1. és a 3. fordulóban 3,25 nyers
pontot szerzett. A mutató így annak a javára csúszott, aki éppen megvált tőle (a 2–6.
fordulóban 94 eladásból 6-ot érintett). Ezért a gyűjtő a `squad_history.json`-ban szereplő
**összes** játékosra lekéri a bontást, a már meglévő fájlokat pedig **csak kiegészíti** a
hiányzó néhány játékossal — nem kéri le újra mind a 385-öt. Ha ezután mégis hiányzik valaki,
az elhasalt kérés, nem hiányzó játékos: a gyűjtő ilyenkor a hibakimenetre írja a nevét.

**A mutató a bontás-gyűjtés UTÁN számolódik, nem előtte.** Amíg előtte állt, egy futásban
frissen pótolt bontás már nem számított bele: a mutató eggyel lemaradt, és csak a következő
futás hozta helyre. Élesben meg is történt — a pótlás kiment, a `guardiola.json` változatlan
maradt. A javítás mérete nem elhanyagolható: a 2. fordulóban Bence értéke +3,00-ról −25,50-re
került (a múlt heti csapatkapitánya volt az a játékos, aki hiányzott a bontásból, tehát a
pontja duplán számít).

Megjelenik a **meccssorok** pontja mellett, a **Fordulók** fülön oszlopként, és a
**tabellában** kumuláltan — ugyanabból a körből, amiből a tabella is számol.

### A PL-en ugyanez, automatikus cserékkel

A Draftban nincs kapitány, és a pad pontja nem számít — viszont a forduló végén az FPL
**automatikus cserét** hajt végre: a pályára sem lépett kezdő helyére beáll az első olyan
padon ülő, aki játszott **és** akivel a felállás érvényes marad (1 kapus, 3–5 védő, 2–5
középpályás, 1–3 csatár). Ettől lesz a kapus csak kapussal cserélhető: két kapus nem
érvényes felállás.

**Ezt az alternatívára is alkalmazzuk.** A valódi eredményben a cserék benne vannak (a
tárolt keret már a zárás utáni állapot); ha az alternatívát csere nélkül számolnánk, a múlt
heti keretet alulmérnénk, és a mutató szisztematikusan a változtatás javára torzulna.

A pad **sorrendje** dönt, és azt az FPL-től kapjuk (picks 12–15) — soha nem rendezzük át.

Ha a játékos-poszt adat hiányzik (elhasalt `bootstrap-static`), a gyűjtő **nem számol
újra**: enélkül a formáció-ellenőrzés mindig hamis lenne, egyetlen csere sem menne végbe,
és a mutató csendben rossz értéket adna. Ilyenkor a korábbi fájl marad érvényben.

Rögzítve: `tesztek/gyujto_guardiola.py` (NB1) és `tesztek/gyujto_draftguardiola.py` (PL).

## 5/a5. A „Változtatások" fül

**A Guardiola mutató levezetése**, tételesen: minden fordulónál ott áll, kit adott el, kit vett
meg és kinek változott a szerepe a szakvezető — és hogy **melyik mennyit ért**. A blokk alján
az összeg, ami **pontosan** a forduló GUARD értéke. Ez a fül egész értelme: a tabellában álló
számot ne kelljen elhinni, hanem le lehessen ellenőrizni.

Négyféle tétel:

| Tétel | Mivel számít |
|---|---|
| **eladva** | a **múlt heti** szerepével (kapitány duplán, pad felezve) — ennyit hozott volna, ha hozzá sem nyúl |
| **megvéve** | a **mostani** szerepével |
| **szerepváltás** | végig bent volt, de kezdő ↔ pad ↔ kapitány mozdult: a két érték különbsége |
| **magyarszabály** | ha a változtatástól megjött vagy elveszett a 10 pont — az nem egy játékoson látszik, hanem a kereten |

**A változtatás nélküli forduló is kilátszik**, üresen. Ha kihagynánk, a néző azt hinné, hogy
hiányzik az adat — pedig épp az a válasz, hogy a szakvezető hozzá sem nyúlt a kerethez, és a
mutatója ezért 0.

### A PL-en külön áll, amit az ember csinált, és amit a gép

A Draftban a forduló végén az FPL **automatikus cserét** hajt végre. Az nem a szakvezető
érdeme vagy hibája, egyben mutatva viszont úgy tűnne, hogy jól variált — holott a gép tette
helyre a keretet (vagy fordítva). Ezért a PL-en a számítás kettéválik:

- **ember:** minden játékos a **megnevezett** szerepével számít — a kezdő a pontjával, a padon
  ülő nullával, akkor is, ha végül beállt;
- **gép:** a keret tényleges pontja (automatikus cserékkel) mínusz a fenti összeg. Ez pontosan
  a zárási csere hozadéka, és külön sorban áll: *„Automatikus csere a záráskor"*.

A kettő összege a keret pontja, tehát a levezetés maradék nélkül kijön. A fül a részösszeget
is kiírja (*„A te döntéseid"*), hogy egy pillantással látszódjon, mi kinek a műve.

### Csak lezárt forduló

A fül **ugyanazt a feltételt** használja, mint a Fordulók fül és a tabella: élő vagy még le nem
zárt fordulóra nincs érték. A feltétel egy helyen él (`FunTasy.guardErtek`), mert három hely
használja — és amíg külön-külön döntött, elő is állt, hogy a PL 2. fordulója a Fordulók fülön
még üres volt, a Változtatások fülön viszont már állt benne szám.

Rögzítve: `tesztek/gyujto_keretvaltozas.py` (NB1), `tesztek/gyujto_draftkeretvaltozas.py` (PL)
és `tesztek/valtoztatasok.teszt.js` — az utóbbi **minden szakvezetőnél és minden fordulónál**
összeveti a sorok összegét, a blokk „Összesen" sorát, a Fordulók fül GUARD oszlopát és a
tabella GUA celláját.

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

**Ami viszont még nyitott az NB1-en is:** a *játékosprofil* továbbra is a teljes
`squad_history.json`-t tölti le (most 121 KB, a szezon végén ~797 KB), mert minden
fordulóra szüksége van. Amit ténylegesen használ belőle, az fordulónként öt mező játékosonként
— abból egy külön index ~162 KB lenne az egész szezonra, vagyis **80%-kal kevesebb**. Ez új
adatfájl, tehát a formátumot előbb el kell dönteni; addig marad a mostani megoldás.

## 5/a3. A lezárt forduló bontása a repóból jön

A **tételes bontás** („mi adta ki a 9,75 pontot") sokáig kizárólag a böngészőből, kattintásra,
élő MLSZ-hívással jött. Két baja volt ennek:

- **hálózat-függő**: ha az MLSZ vagy a közvetítő éppen nem válaszolt, a lenyíló hibát írt —
  pedig a lezárt forduló bontása már sosem változik;
- **lassú a profilban**: a soha nem birtokolt játékosnál a profil fordulónként egy-egy külön
  kérést lő ki, sorban (ezért „pótlódnak" a pontok utólag).

Mostantól a gyűjtő a forduló **lezárásakor egyszer** lekéri mind a 385 játékos bontását
(`bontasok/<forduló>.json`), és az oldal lezárt fordulónál onnan olvas — azonnal, hálózattól
függetlenül. Az **élő forduló marad az élő úton**: ott a bontás még változik.

Miért a teljes mezőny, és nem csak a birtokolt játékosok: a főoldali listából bárki profilja
megnyitható. **Ez egyik kvótánkat sem terheli**: a gyűjtő a GitHub szerveréről közvetlenül
kéri az MLSZ-t (CORS csak böngészőben létezik, közvetítő itt nincs) — az ára fordulónként
egyszeri ~3 perc futásidő és ~40 KB a repóban.

**Csak a pontot érő sorokat tároljuk** — plusz a „Játszott perc" sort. Az MLSZ minden
játszott játékosra mind a **22** statisztika-sort visszaadja, a nullás értékűeket is; 385
játékossal az 141 KB fordulónként, a szezon végére 4,5 MB. Az oldal viszont csak a pontot
érő sorokat mutatja, és a „Játszott perc"-et külön (abból dől el a „nem lépett pályára" /
„lejátszotta, pont nélkül" üzenet is). Szűrve **40 KB** fordulónként, a szezonra 1,3 MB.
Ez a szűrés **visszafordítható**: a `game-player-stats` a régi fordulókra is válaszol
(eddig épp ezen múlt az egész bontás), tehát a kihagyott nyers értékek bármikor újra
lekérhetők — az árnaplónál pont ezért *nem* lehetett szűrni, az árat visszamenőleg senki
nem adja vissza.

**Mi számít lezártnak:** a **tárolt** állapotból dől el (minden meccs eredményes, és a
forduló nincs az ideiglenesek közt) — nem abból, hogy a gyűjtő melyik forduló keretét kérte
le éppen ebben a futásban. Enélkül a bevezetéskor csak az utolsó fordulóhoz készült volna
bontás, a korábbiakhoz soha.

Két részlet, ami fontos:

- **Félig kész fájlt nem írunk ki.** Ha a kérések több mint 10%-a elhasal, a fájl nem
  készül el, és a következő futás újrapróbálja. Egy hiányos fájl rosszabb a hiányzónál —
  azt sosem próbálnánk újra.
- **A korrekció itt sem évül el.** Ha a körbeforgó újraellenőrzés egy régi forduló
  eredményét javítja, annak a bontását is újrahúzza.

Ha a fájl hiányzik (a bevezetés előtti forduló, vagy még nem futott a gyűjtő), az oldal
csendben visszaesik az élő lekérésre. Rögzítve: `tesztek/gyujto_bontasok.py` és
`tesztek/taroltbontas.teszt.js`.

### Az élő pont a tételes bontásból áll össze (PL)

**Bejelentett hiba (2026-08-30, GW2):** egy játékos sora 1 pontot és 9 percet mutatott,
a pontrészletezője viszont 90 percet, gólt és bónuszt — összesen 8-at. A meccsek addigra
lementek, tehát a **részletezés** volt a valóság.

Nem a mi hibánk volt: **a hivatalos FPL-app ugyanezt az ellentmondást mutatta** — a pályán
1 pont, a játékosra kattintva 8. Az FPL a `stats.total_points`-ot és az `explain`
eseménylistát **külön tartja**, és az összesítő beragadt.

Hogy az `explain` a hiteles, két dolog mondja meg. Egy: **a meccsek addigra lementek**.
Kettő: a **90 játszott perc** csak lejátszott meccsből jöhet, a `stats` 9 perce viszont a
meccs bármely pillanatában előállhat — a percszám monoton nő, tehát a kisebbik a lemaradt.

> **Amivel NEM lehet érvelni: a bónusszal.** Első nekifutásra azt írtam, hogy „bónusz csak
> lefújás után jár", tehát a bónusz-sor bizonyítja a lement meccset. Ez **téves**: az FPL a
> bónuszt a meccs alatt is számolja a BPS-táblából, és beteszi az `explain`-be — lásd
> a fenti „A bónuszpontok három állapota" szakaszt, amit épp ezért írtunk meg.

Ezért az élő pontot (és a percet) mostantól **mi adjuk össze az `explain`-ből**, nem az
összesítőt vesszük át. Normális esetben a kettő egyezik, tehát ez semmit nem változtat;
eltéréskor viszont az esemény-alapú érték nyer — és ez a csapat összegére és az élő
meccsállásra is átüt. Ha egy játékoshoz nincs `explain` (még nem lépett pályára), marad a
`stats`.

**Ugyanez a szabály a gyűjtőben is.** Ez nem szépségkérdés: a lezárt fordulót a gyűjtő
**soha többé nem kéri le** (`veglegesek`), és az oldal onnantól nem élőben számol, hanem a
**mentett** számot mutatja. Ami a lezárás pillanatában bekerült, az véglegesen bent marad —
az FPL a régi fordulót nem adja vissza. Ha csak az oldalt javítottuk volna, ma jó számot
látnánk, a lezárás után viszont a beragadt érték jönne elő, örökre.

A gyűjtőben ez a `collect_draft.py` → `jatekos_pont()`, a lapon a `fetchLivePts` — a kettőnek
**ugyanazt a számot kell adnia**: amit a látogató lát, azt kell archiválni is. Eltéréskor a
gyűjtő a futás naplójába **hangosan kiírja**, hány játékosnál tért el a két forrás; ha ez
rendszeressé válik, onnan derül ki.

**Visszaesés mindkét helyen:** ha az `explain` üres (a játékos nem lépett pályára) vagy az FPL
átalakítja a szerkezetét, egyetlen sort sem találunk, és marad a `stats` összesítője. Egy
API-változás így a **régi viselkedést** adja vissza, nem nullákat. A pontot és a percet külön
tartjuk számon: lehet pontot érő sor perc-sor nélkül, és ott a 0 perc hamis lenne.

Rögzítve: `tesztek/eloosszeg.teszt.js` (lap) és `tesztek/gyujto_pontforras.py` (gyűjtő) —
beragadt összesítő mellett 8 pont és 90 perc, az élő állás 88 (11 kezdő), a hibás 11 sehol;
üres vagy ismeretlen szerkezetű bontásnál a `stats` marad; dupla fordulónál a két meccs
összeadódik. Mindkettő a régi kódon bizonyítottan bukik.

### Élő forduló alatt a lap magától frissül

**Bejelentett hiba (2026-08-30, PL):** a nyitva hagyott lap a **betöltéskori** állást
mutatta. A LEE–BRE meccs a 9. percnél állt, amikor az oldal betöltődött, és a sorok ott is
maradtak — percek, meccsóra, pontok egyaránt. A lenyíló bontás viszont **kattintáskor** saját,
friss lekérést indít, ezért az már 90 percet mutatott: ugyanazon a képernyőn mondott ellent
egymásnak a sor (9 perc, 1 pont) és a panelje (90 perc, 2 pont). **A panel volt a helyes.**

Az élő réteget eddig csak három dolog frissítette: a betöltés, a lapra való visszaváltás
(`FunTasy.ujraLathatokor`), és egy meccs vagy keret megnyitása. Időzített frissítés
**szándékosan** nem volt — és akkor ez helyes döntés is volt: publikus közvetítőkön mentünk,
és egy nyitva hagyott lap percenkénti lekérésekkel verte volna őket.

**A saját Cloudflare Workerünk 60 másodperces peremgyorsítótárával ez az indok megszűnt:**
akárhányan nézik ugyanazt a fordulót, az API felé percenként egy kérés megy ki. Ezért a
`FunTasy.eloFrissito` mindkét oldalon percenként újrafuttatja az élő lekérést — de **csak
akkor**, ha van folyó forduló, és **csak** látható lapon. Fordulók között és háttérbe tett
lapon egyetlen kérés sem megy ki.

Rögzítve: `tesztek/eloora.teszt.js` — élő fordulónál a kiírt állás kattintás nélkül vált
44-ről 99-re; lezárt fordulónál egyetlen ismételt kérés sem megy ki. A régi kódon
bizonyítottan bukik.

### Írás csak akkor, ha tényleg változott

Minden kimeneti fájlra ugyanaz a szabály: **az `updated` mező nem ok az írásra**. Ha csak
az időbélyeg változna, a fájl nem íródik újra — különben a repó három óránként hízna a
semmiért, és a git-történetben nem lehetne megtalálni, mikor változott tényleg valami.

Ez kétszer csúszott el:

- a `results.json` feltétele **listát hasonlított halmazhoz** (`provisional != regi_prov`),
  ami sosem egyenlő — az utolsó 36 commitjából 30-ban csak az időbélyeg változott;
- a `squads.json` kiírását a **teljes előzmény** változása nyitotta, pedig a fájl csak az
  utolsó forduló keretét tartalmazza — egy régi forduló korrekciója így változatlan
  tartalommal írta újra (14-ből 2 alkalommal).

Mindkettőt teszt fedi (`tesztek/gyujto_ideiglenes.py`, C3 és C4): a C3 a gyűjtőt kétszer
futtatja változatlan adaton, és **egyetlen** kimeneti fájl sem változhat — nem csak a
`results.json`, hanem minden, amit a futás után talál. A `stamp()` helyére számláló kerül,
különben a másodperc-pontosságú időbélyeg elrejtené a fölösleges írást.

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
  a végső állapot kerül be; a közbenső próbálkozások a használót nem érdeklik. **Ez az
  utólagos igazításokra is áll:** ami egy frissen élesített funkción még aznap (vagy másnap
  az első visszajelzésre) igazítás, az nem külön bugfix-bejegyzés — a funkció bejegyzése
  írja le a végállapotot. (Egyszer már becsúszott egy külön „a panel a helyére állt"
  bejegyzés; törölni kellett.)
- **Dátumozva**, naponként csoportosítva, a legfrissebb elöl. A napló 2026-08-23 estétől
  indul, a korábbi változások nincsenek benne.
- **Összevonáskor a bejegyzést ÚJRA KELL FOGALMAZNI, nem hozzáfűzni.** Ha egy meglévő
  bejegyzéshez újabb rész kerül, a leírás nem bővül egy odabiggyesztett mondattal: az
  egészet újra kell írni úgy, hogy egy szövegként olvasható legyen. A hozzáfűzött mondatok
  sorozatából felsorolás lesz, amiből a használó nem érti, mi a lényeg.
- **Több szakaszban készülő funkciónál a bejegyzés a VÉGÉN megy ki**, nem szakaszonként.
  Ellenkező utasítás híján ez az alap. Ha egy funkciót azért bontunk szakaszokra, hogy
  közben látni lehessen — az még nem kész funkció: a napló szakaszonként átírva
  félkész állapotot mutatna annak, aki épp megnyitja. A készülő szöveg addig a
  `valtozasok-vazlat.json`-ban áll (a napló oldala ezt nem olvassa), és amikor az utolsó
  szakasz is kész, egy mozdulattal átkerül. Ugyanaz az alaki ellenőrzés vonatkozik rá
  (`tesztek/dokuk.py`, D5), tehát nem tud félig megírva elaludni.

Az adat a `valtozasok.json`-ban van, kézzel bővítjük (a még nem publikált szöveg a `valtozasok-vazlat.json`-ban). A szűrők a `LIGAK` listából
készülnek, tehát egy új liga felvétele itt sem igényel külön munkát.

**Hogyan legyen megfogalmazva egy bejegyzés**

- **A cím azt mondja meg, mi igaz mostantól**, a mondat pedig azt, hogy ez mit jelent a
  használónak és hol látja. Példa: *„Az elmaradt meccs játékosainál kötőjel áll 0 helyett"*.
- **Nincs benne első személy, és nincs hivatkozás a fejlesztés menetére.** A napló nem
  arról szól, ki mit mondott vagy hogyan derült ki — csak arról, mi változott az oldalon.
  (Egy naplóbejegyzés arról, hogy korábban hol hangzott el ugyanez, a használót nem
  érdekli — őt az érdekli, mi változott az oldalon.)
- **Tárgyszerű, nem dramatizál.** Nem *„nem kapnak többé hamis 0-t"*, hanem az, ami
  ténylegesen látszik a soron.
- **A beszélgetésben elhangzott szavakat nem vesszük át szó szerint.** Az, ahogy egy
  hibáról beszélünk, nem ugyanaz, ahogy a naplóba le kell írni; a megfogalmazást minden
  bejegyzésnél újra végig kell gondolni.

Elérés: a kezdőlapról (kártya) és minden oldal **láblécéből** (`FunTasy.renderLablec`).
A naplón magán nincs lábléc, mert önmagára mutatna.

### A két oldal váza kézzel van kétszer leírva

Nincs build és nincs sablon, tehát a `<head>`, a fejléc, a panel-keretek és a lábléc
**mindkét liga-oldalon külön ott áll**. Ez tud szétcsúszni — meg is tette: a zárási
változások panelje egy ideig más címmel, más oszlopban és más elrendezéssel állt a két
oldalon. Ilyenkor nem elég „figyelni rá": a `tesztek/ligavaz.teszt.js` géppel nézi, hogy a
`<head>` mind a négy oldalon azonos (a címen és az útvonal-előtagon kívül), a panelek
sorrendje és oszlopa gépen és mobilon ugyanaz, és a tabella fejléce is egyezik — csak a
résztvevő oszlopa fut más néven (Szakvezető / Csapat).

Ha új panel kerül az egyik oldalra, a teszt addig bukik, amíg a másikra is oda nem kerül.
Ez a szándék: **ami mindkét ligában van, az nézzen ki ugyanúgy.**

## 5/b. Tesztek

```bash
tesztek/futtat.sh
```

Elindít egy helyi kiszolgálót a repó gyökerére, lefuttat mindent — a doksi-konzisztencia
ellenőrzését, a gyűjtő-teszteket, majd a böngészős teszteket **párhuzamosan** (3 munkás;
a két időzítést mérő teszt a végén, egyedül fut) —, és összegez; a kilépőkód a bukott
tesztek száma. `PARHUZAM=1` a régi soros mód. A tesztek darabszámát szándékosan nem írjuk
ide: kétszer is elavult. Tesztenkénti bontás: `tesztek/README.md`.

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

**Mielőtt lezárás-logikához nyúlsz, olvasd el a 3/b szakaszt.** Négy különböző dolgot
hívunk „lezárásnak", külön jelzőkkel; egyszer már abból lett hiba, hogy az egyiket a
többi ismerete nélkül írtam át — és a hozzá írt teszt a hibás viselkedést rögzítette,
nem fogta meg. Ha egy tesztet a kód alá igazítasz, állj meg: valószínűleg az elvárás
rossz, nem a kód.

**A dokumentáció-frissítés nem opcionális lépés, és nem is bizalmi kérdés többé:** a
`tesztek/dokuk.py` a tesztsor részeként ellenőrzi, hogy minden teszt- és adatfájl
dokumentálva van, a fájl-táblázat nem hivatkozik törölt fájlra, és a változásnapló
bejegyzései teljesek. (Azért született, mert a doksi-szerkesztés kétszer hasalt el
csendben.)

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
- **Az NB1 következő ellenfelei a profilban.** A PL-oldalon ott a hátralévő fordulók
  ellenfele, az NB1-en nincs: az MLSZ API-ban nem találtunk jövőbeli menetrendet
  (~25 végpont-alak, mind 404), pedig a fantasy.mlsz.hu saját játékosoldala mutatja.
  A következő lépés a frontend-bundle visszafejtése, hogy meglegyen, honnan kéri le.
- **Az „Ismeretlen játékos" sorok azonosítása** a pontigazítás-panelen (1–3. forduló).
  A repóból nem visszakereshető; ha valakinek megvan a korabeli képernyőkép, abból igen.
