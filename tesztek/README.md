# Tesztek

```bash
tesztek/futtat.sh            # parhuzamosan (alap: 3 munkas), ~5 perc
PARHUZAM=1 tesztek/futtat.sh # regi soros mod (hibakereseshez), ~11 perc
```

A böngészős tesztek párhuzamosan futnak, mert egymástól függetlenek — kivéve a két
**időzítést mérő** tesztet (`frissjelzo`, `visszateres`): azok a sor végén, egyedül
futnak, mert párhuzamos terhelés alatt hamisan bukhatnának. A párhuzamosság előfeltétele
volt, hogy a `jsonAtir` lemezről olvasson (lásd a `kozos.js`-t).

Elindít egy helyi kiszolgálót a repó gyökerére, lefuttatja az összes tesztet, és
összegez. A kilépőkód a bukott tesztek száma, tehát CI-ból is használható.

Környezeti változók: `PORT` (alap: 8910), `PLAYWRIGHT_MODUL`, `CHROME_UT`.

## Két elv

- **Nincsenek fixtúra-másolatok.** Minden teszt a repóban lévő **valódi** adaton fut.
  Korábban lemásolt JSON-ok álltak külön könyvtárakban; azok elavultak, és a teszt akkor
  is zöld maradt, ha közben a valódi adat megváltozott.
- **A különleges állapotokat a teszt állítja elő menet közben** — a Playwright elfogja a
  kérést és átírja a választ, a gyűjtő-teszteknél pedig az `api_get` van kicserélve.
  Nem tárolt fájlból, tehát holnap is ugyanazt méri.
- **Minden állítás a közös `jo()`-n megy át.** Ha egy teszt maga írja ki, hogy „HIBA",
  a futtató csak a kilépőkódot látja — és zöldnek hiszi a bukott tesztet. A
  `nullapont.teszt.js` így takart el hat bukott állítást; a saját `hibak` tömbje
  árnyékolta a közöset, és a kilépőkód csak a lap JS-hibáit nézte.

## Az élő út mérése: `bontasKi`

A lezárt forduló bontása a repóból jön (`bontasok/<forduló>.json`), és **ez az
elsődleges út**. Ezért aki az **élő** utat méri — a lekérő proxy-láncát, a hibaüzenetet,
a profil sorban pótlódó pontjait —, annak a tárolt fájlt is el kell vágnia, különben a
lap oda sem jut el, és a teszt némán mást mér, mint amit hisz. Erre való a
`kozos.js` `bontasKi(page)` segédje; a tárolt utat mérő `taroltbontas.teszt.js`
értelemszerűen nem hívja.

Ez a hiányzó fájl esete élesben is előfordul: a bevezetés előtti forduló, illetve az a
játékos, aki már nincs a jelenlegi 385-ös törzsben (öt ilyen van a `squad_history`-ban).

> **Az útvonal-mintában a záró `*` nem elhagyható.** A lap gyorsítótár-törővel kéri a
> fájlt (`bontasok/4.json?t=…`), a Playwright pedig a glob-ot a **teljes** URL-re
> illeszti — `**/bontasok/*.json` a kérdőjeles végen nem illeszkedik, és a teszt némán a
> valódi fájlt kapja. Minden adatfájl-útvonal ezért `*`-ra végződik.

## Gyűjtő-tesztek (Python, hálózat nélkül)

Az `api_get`-et mock váltja ki, a `collect.py` egy ideiglenes könyvtárban fut.

| fájl | mit ellenőriz |
|---|---|
| `gyujto_onjavitas.py` | Ha az MLSZ utólag korrigál egy régi fordulót, a gyűjtő átvezeti-e — az eredménybe, a keretbe és a keresztellenőrzésbe is. Ez találta meg a `rankings()` `%5B`-formázási hibáját, ami miatt a backfill-ág élesben sosem futott le. |
| `gyujto_ideiglenes.py` | A `provisional` lista kezelése: mi kerül bele, mi kerül ki, és mi marad változatlan hiányos adatnál. Ellenőrzi azt is, hogy változatlan adatnál a gyűjtő **egyetlen kimeneti fájlt sem** ír újra — nem csak a `results.json`-t, hanem mindet, amit a futás után talál (a `stamp()` helyére számláló kerül, különben a másodperc-pontosságú időbélyeg elrejtené a felesleges írást). Azért az összeset, mert a „csak ha változott” logika fájlonként külön van megírva, és pont ez a széthúzottság rejtette el a `results.json` hibáját. Külön eset arra is, hogy egy **régi** forduló korrekciója ne írja újra a `squads.json`-t: az csak az utolsó forduló keretét tartalmazza, a kiírás feltétele viszont a teljes előzmény változása volt. |
| `gyujto_pontforras.py` | A **mentett** fordulópont a tételes bontásból (`explain`) áll össze, nem az FPL beragadható összesítőjéből — ugyanaz a szabály, mint a lapon. Ez azért kritikus, mert a lezárt fordulót a gyűjtő soha többé nem kéri le, és onnantól a mentett szám látszik. Üres vagy ismeretlen szerkezetű bontásnál a `stats` marad a forrás (API-változásnál a régi viselkedés, nem nullák); dupla fordulónál a két meccs összeadódik. |
| `gyujto_lezaras.py` | A forduló-lezárás kilenc esete (lásd lent). |
| `gyujto_guardiola.py` | A **Guardiola mutató**: változatlan keretnél **pontosan 0** (a legkönnyebben elromló állítás — ha a két oldal máshonnan számol, a pados felezés 0,01-et csúszik, és a mutató „+0,01"-et írna, holott a szakvezető hozzá sem nyúlt); a múlt heti **szerepek** számítanak (kapitány, pad); a magyarszabály az alternatívára is jár; első fordulóra és bontás nélkül nincs érték; a bontásból hiányzó játékos 0 pontot ad. |
| `gyujto_draftguardiola.py` | Ugyanez a PL-en, az **automatikus cserékkel**: a nem játszó kezdő helyére az első olyan pados áll be, aki játszott és akivel a felállás érvényes marad (a kapust csak kapus válthatja); a pad **sorrendje** dönt; ha egy pados sem játszott, nincs csere. |
| `gyujto_keretvaltozas.py` | A **Változtatások** fül adata (NB1): az eladott játékos a múlt heti, a megvett a mostani szerepével számít, a szerepváltás külön tétel, a magyarszabály különbsége szintén. A legfontosabb állítás (**K5**): a tételek összege **pontosan** a Guardiola mutató — kerekítési maradék nélkül, a pad felezésénél is. |
| `gyujto_draftkeretvaltozas.py` | Ugyanez a PL-en, azzal a többlettel, hogy **kettéválik, mit csinált az ember és mit javított rajta a gép**: a játékos-tételek a *megnevezett* szerepet nézik (pad = 0), a zárási automatikus csere hozadéka külön áll. **P5**: ember + gép = a mutató. |

### `gyujto_lezaras.py` esetei

| eset | állítás |
|---|---|
| R1 | Az **első** futásnál, amikor még nincs korábbi `provisional` bejegyzés, egy elhasalt keret-lekérés után se írja véglegesnek a fordulót. |
| R2 | Ha a forduló utolsó meccse **még tart**, de az MLSZ már mindenkire `is_played=true`-t ad, a forduló ideiglenes marad. |
| kontroll | Ha a meccs **lement** (`completed`), a forduló viszont lezárul. |
| R3 | Akinek **nincs meccse** a fordulóban (halasztás), az nem akasztja meg a lezárást. |
| R3b | Ugyanez akkor is, ha a forduló már nem az aktuális, tehát a meccslistát nem kérjük le — a jelzés a **tárolt** keretből jön. |
| R4 | **Biztonsági háló:** ha a játékos-szintű kép nem áll össze, de az MLSZ már továbblépett a fordulón, akkor is lezárul. |
| R5 | …de amíg az MLSZ szerint **ez** az aktuális forduló, a háló nem sül el. |
| R6 | Ha a meccslistában **másik forduló** meccse jön vissza (régi fordulónál az API a klub legutóbbi meccsére esik vissza), az is „nincs meccse" — és annak a meccsnek az állapota nem akaszthatja meg a lezárást. |
| R7 | A **régi formátumú** keretet (nincs benne `played`) a gyűjtő újra lekéri, és a pótolt rekordban ott az `id`, a `played` és a `nogame` is. |

## Böngészős tesztek (Playwright)

| fájl | mit ellenőriz |
|---|---|
| `accordionorzes.teszt.js` | A nyitott pont-bontás nem tűnhet el a háttérben beérő frissítéstől. Bejelentett hiba volt: a részletező „betöltése” után magától visszazárt. Nem a bontás zárta be — a nézet utólag újrarajzolódik (percre friss keret, játszott percek, élő pontok), és a teljes `#mBody` újraépül. A teszt megnyitja a bontást a meccs- és a keret-nézetben, kiváltja az újrarajzolást, és ellenőrzi, hogy a sor és a panel **tartalma** is ugyanaz marad; zárt állapotban pedig nem nyit meg semmit. Rögzíti a javítás javítását is: **hibás** panelt nem őrzünk meg (egy átmeneti hálózati hiba különben beragadt, és a következő kattintás csak becsukta a sort), **betöltés közbeni** újrarajzolásnál pedig újraindul a lekérés (különben a jelzésen ragadt volna). |
| `allapotter.teszt.js` | A „mit írjunk a 0 pontos játékosról" logika **teljes állapottere**: mind az 576 kombináció, öt invariánssal. Ez talált meg olyan hibákat, amikre nem gondoltunk tesztet írni. |
| `taroltbontas.teszt.js` | A lezárt forduló bontása a repóból jön (`bontasok/<r>.json`), élő MLSZ-lekérés **nélkül**; hiányzó fájlnál csendes visszaesés az élő útra; élő fordulónál viszont az élő lekérés nyer (ott a bontás még változik). |
| `valtoztatasok.teszt.js` | A **Változtatások** fül mindkét ligán. Nem azt méri, hogy „látszik a lista", hanem hogy **minden szám egyezik mindennel**: a sorok különbségeinek összege = a blokk „Összesen" sora = a blokk fejlécében álló GUARD = a Fordulók fülön álló GUARD, és mindezek fordulónkénti összege = a tabella GUA oszlopa. A PL-en külön nézi, hogy „A te döntéseid" részösszeg a játékos-sorokkal egyezik, és hogy ember + gép = a mutató. Azt is nézi, hogy a fordulók **növekvő** sorrendben állnak, és hogy a közös megjelenítő a **régi, címkézetlen** adatalakot is kirajzolja (a `?v=` az oldal HTML-jét nem frissíti, tehát régi lap találkozhat új `funtasy.js`-sel — élesben elő is állt). Külön méri a **folyamatban lévő** fordulót is: a blokk ott van, a fejlécében „még nincs pontszám”, és **egyetlen szám sincs benne** — se a sorokban, se összesenként. Mivel a PL-en még nincs lezárt forduló, a menetrendet menet közben kiegészíti, hogy a lezárt állapot is mérve legyen; a pont nélküli állapothoz pedig kiveszi a legutóbbi forduló eredményét. |
| `tabella.teszt.js` | A tabellát és a H2H-mátrixot **függetlenül újraszámolja** a `results.json`-ból, és összeveti azzal, amit az oldal kirajzol.  Emellett azt is, hogy vízszintes görgetésnél a helyezés, a név és a fejléc egyaránt ragad — és hogy a **névcella valódi táblázat-cella marad** (a flex a benne lévő `.nevsor`-on van). Ez nem kozmetika: flexes cellán iPhone-on nem működik a `position:sticky`, és a nevek elcsúsztak a számok alá. |
| `dokuk.py` | A dokumentáció konzisztenciája: minden tesztfájlnak és gyökérbeli adatfájlnak van sora a README-kben, a fájl-táblázat csak létező fájlra hivatkozik, a változásnapló bejegyzései teljesek. Azért létezik, mert a doksi-szerkesztés kétszer hasalt el csendben — a kézi ellenőrzés terhelés alatt csúszik el, ez kényszeríti ki. Ellenőrzi azt is, hogy minden oldal ugyanazt a `?v=` gyorsítótár-verziót hivatkozza (ha csak az egyiken emelkedik, a másikon régi `funtasy.js`/`css` marad), és hogy a README tartalomjegyzéke egyezik a tényleges címekkel — a jegyzék nem kézi munka, `python3 tesztek/dokuk.py --javit` újraírja. |
| `gyujto_hatekonysag.py` | Az NB1 kezdőállítási hatékonyság számítása: a nyers pont visszafejtése a cap/sub jelzőből, posztonkénti pad, a tökéletes felállítás 100%, a lehető nem függ a tényleges felállítástól, hiányos keretre nincs érték. |
| `kezdhatekonysag.teszt.js` | A KEZD% a lapokon: a PL számítása kézzel kiszámolt kereten (a legjobb **érvényes** formáció — 6 védő nem számolható), a tabella-oszlop mindkét ligában, az NB1 összesítés csak a lezárt fordulókból (az ideiglenes kimarad, a hiányzó érték nem 0). |
| `gyujto_jatekostorzs.py` | A játékostörzs leképezése (hiányos mezők, azonosító nélküli sor, hibás válasz) és az árnapló: csak változásnál keletkezik új bejegyzés, a korábbi érték megmarad, a hiányzó vagy nulla ár nem ír hamis árzuhanást. |
| `gyujto_zarasnb1.py` | A meccs utáni pontigazítás naplózása (`collect.py` `zaras_valtozas`): csak lement meccsnél számít változásnak, a kapitányi duplázás és a padfelezés vissza van számolva (negyedre kerekítve), ugyanaz a változás minden érintett szakvezetőnél megjelenik (a PL-panellel egyezően), ugyanaz a futás kétszer nem duplázódik, a későbbi újabb igazítást nem nyeli el a dedup, és hiányzó adatból nem talál ki változást. |
| `zarasnb1.teszt.js` | A „Zárási változások" panel (NB1): üres vagy hiányzó adatnál rejtve marad, a legördülőben minden lejátszott forduló szerepel (ahol nem volt változás, ott ez van kiírva), alapból a legutolsó fordulón áll a lapozó, szakvezető szerint csoportosít, soronként a konkrét játékos nevével és klubjával, a régi/új érték és az előjeles különbség is látszik (csökkenés és növekedés külön színnel), a játékos neve a profilt, a szakvezetőé a keretet nyitja, az ismeretlen játékos sora pedig csak a változás mértékét mutatja, és nem kattintható. |
| `jatekosprofil.teszt.js` | A játékosprofil (NB1): a „Szezon játékosai" sorai megnyitják és viszik a cp-azonosítót, a fordulósor az ellenfelet, az állást (hazai–vendég sorrendben) és a játékos **saját** pontját mutatja, a pados értékből visszaszámolt alappont nem csúszik el 0,01-gyel, egy fordulóban több szakvezető is megjelenik a saját szerepével, a ligára vetített keret/kezdő/kapitány arányok jó nevezővel készülnek, a kapitányt kezdőnek is számolják, és **csak salary cap ligában** jelennek meg (draftban nem), a lenyíló a bontást hozza (és az alján a „Teljes játékosprofil" sor, a profilon belül viszont nem), a vissza gomb a listára tér vissza, és NB1-en nincsenek üres jövőbeli sorok (PL-en viszont ott a hátralévő forduló az ellenfelével). A főoldali lista: ékezet nélküli keresés, a „+N" nem vágódik le, minden oszlopnak van szűrője, a „Valakinél"/„Senkinél" külön szűr, a Keret% százalékot mutat, a lapozás folytatja a sorszámozást (kereséskor visszaugrik az első oldalra), és a szűrő-legördülő monogramot mutat, miközben a szűrt érték a teljes név marad. PL: a `detail` állása hazai–vendég sorrendben kerül ki (idegenbeli meccsen bizonyítottan bukik, ha megfordul), dupla fordulóban mindkét meccs látszik és a pontok összeadódnak, a gazdátlan forduló rövid jelet kap (jövőbelinél semmit — azt nem tudhatjuk), és a soha nem birtokolt játékos profilja a lassú API bevárása nélkül jelenik meg, a pontok sorban pótlódnak. Rögzíti azt is, hogy az FPL-lekérés kimaradásakor a PL-profil a **tárolt** pontot mutatja (nem kötőjelet), és a „Pont összesen” nem esik 0-ra. |
| `eloosszeg.teszt.js` | Az élő pont és perc a tételes bontásból (`explain`) áll össze, nem az FPL beragadható összesítőjéből: 1 pont/9 perc helyett 8 pont/90 perc, és az élő meccsállás is ebből számol; üres bontásnál a `stats` marad a forrás. |
| `eloora.teszt.js` | Élő forduló alatt a lap magától frissül (időzítő): újra lekér kattintás nélkül, a kiírt állás 44-ről 99-re vált, lezárt fordulónál egyetlen ismételt kérés sem megy ki. |
| `zarasblokk.teszt.js` | A Zárási változások panel a PL főoldalon: csak adat mellett látszik, a három nézet (Mind / Pontváltozás / Cserék) külön és együtt is működik, a fordulók között lapozni lehet, üres nézethez saját üzenet jár, a ki/be külön sorokban áll (párosítást nem állítunk). |
| `zarasires.teszt.js` | A zárás és a gyűjtés közötti rés a PL-en: ha az FPL szerint a forduló lezárult, de a tárolt adatban még nincs eredmény, a státuszsor **nem ír „naprakész”-t**, hanem megmondja, mi hiányzik, és a **tárolt** állás idejét írja ki (nem a lekérését). A teszt mindkét állapotot kimondja, nem a valós adatra támaszkodik. |
| `gyujto_bontasok.py` | A lezárt fordulók tételes bontásának mentése (`collect.py` `bontasok_gyujtes`): lezárt fordulóhoz készül fájl, a még tartóhoz nem; másodszorra egyetlen lekérés sincs; MLSZ-korrekció után újra lekéri; sok hibás kérésnél **nem** ír ki félig kész fájlt; a pont nélküli játékos üres listával szerepel (ez más, mint a hiányzás). Ellenőrzi a lezártság forrását is (a **tárolt** menetrendből és az ideiglenesek listájából, nem a futás célfordulóiból), és a sorszűrést (a 0 pontos sorok kimaradnak, a „Játszott perc" marad). |
| `gyujto_draftzaras.py` | A draft-gyűjtő forduló-véglegesítése: a le nem zárt fordulót teljes keret mellett is újra lekéri, a **lockdown után** még egyszer (ekkor jön be az automatikus csere), utána soha többé — és hiányos lekérés után **nem** jelöli késznek. A mock a valós mérést követi: záráskor a `current_event` még a régi forduló. Külön eset arra, amikor a **tárolt** adat már teljes, de a záráskori lekérés hasal el — a véglegesítés ezért azt nézi, hogy **ebben a futásban** jött-e be minden csapat. |
| `gyujto_meccsek.py` | A gyűjtő meccsgyűjtése (`meccsek.json`): id szerinti összevonás, **eredmény csak lezárt meccsről** (a futó meccs pontszámát akkor sem tárolja, ha az API küldi), a visszaeső meccs kimarad, a teljes forduló nem kér többé meccslistát, a futó meccsű igen — és a **pótolt meccs** is bekerül: ha a forduló hivatalos pontja változik, újra megy a meccslistás lekérés (az elhalasztott meccs nincs benne a listában, tehát „befejezetlenként” nem látszana). |
| `nb1meccs.teszt.js` | A meccs-sor a NB1 részletezője fölött: lezárt meccsnél eredmény + „vége", el nem kezdődöttnél **nincs kitalált 0–0**, az időkorláton belül „a meccs zajlik"; dupla meccsű klubnál két sor; nogame játékosnál nincs sor; a Játszott perc a táblázat első sora. |
| `forduloelott.teszt.js` | A leadási határidő után, de az első sípszó előtt is látszik **mindkét keret** (pont helyett kötőjellel), „élő" jelzés és KEZD% sor nélkül — jövőbeli fordulónál viszont marad az üzenet, mert oda nincs mentett keret. Nem a naptárra támaszkodik: a menetrendből menet közben kiveszi egy lezárt forduló eredményét, és a tárolt keretet is a sípszó előtti állapotra állítja. |
| `nullapont.teszt.js` | A négy „0 pont" állapot és a kattinthatóság-jelzés mindkét oldalon. Az **élő forduló előfeltételét maga állítja be** (`provisional`): lezárt fordulóban a „zajlik" állapotokra más — és helyes — üzenet jár, tehát a valós adatra hagyva a teszt a gyűjtő első lezárása után mást mérne. |
| `meccsallapot.teszt.js` | A `meccsAllapot()` négy értéke és a két időkorlát (100 / 180 perc); a lejárt éjféles helyőrző (nem ígér kezdési időt); a `round_number`-ből felismert „nincs meccse". |
| `uzenetek.teszt.js` | Gyorsítótár-kerülés az élő lekéréseknél, és hogy meccs közben nem írjuk, hogy „lejátszotta pont nélkül". A mockolt élő sort a **teljes kezdési időbélyeghez** köti, nem a napjához: meccsnapon a tárolt sor ugyanarra a napra esik, és a teszt egy másik meccs üzenetét mérte volna (2026-08-27-én meg is tette). |
| `visszateres.teszt.js` | A lap láthatóvá válásakor újra lekér-e (`FunTasy.ujraLathatokor`) — egységteszt és e2e is. |
| `frissjelzo.teszt.js` | A „frissítés…" jelzés lassú lekérésnél megjelenik, gyorsnál nem villan fel. Az élő fordulót előfeltételként rögzíti (`provisional:[5]`), nem a betöltési frissítés beérkezésétől reméli — ez kb. minden harmadik futásban flake-et okozott. |
| `keretbetoltes.teszt.js` | A meccs megnyitása a **fordulónkénti** keret-fájlt tölti-e le a teljes előzmény helyett — és a visszaesési út is működik-e. |
| `kulonbseg.teszt.js` | A Különbségek nézet szerkezete gépen (két oszlop) és mobilon (közös blokk + két oszlop). |
| `lekero.teszt.js` | A lekérő tartalék-útjai (2026-08-27: a corsproxy.io 401-re váltott, az allorigins túlterhelt volt — minden élő lekérés leállt mindkét ligában). Rögzíti, hogy a lánc végigesik a következő útig (corsproxy 401 + néma allorigins mellett a cors.sh szolgál ki), a csomagolt allorigins-válasz (`{contents:"…"}`) kibontva jelenik meg, és ha minden út elhasal, a hibaüzenet felsorolja őket. |
| `ligavaz.teszt.js` | A két liga-oldal váza ugyanaz: a `<head>` mind a négy oldalon azonos (a cím és az útvonal-előtag kivételével), a panelek ugyanabban a sorrendben és ugyanabban az oszlopban állnak gépen és mobilon, és a tabella fejléce is azonos — csak a résztvevő oszlopa fut más néven (Szakvezető / Csapat). Azért létezik, mert a két oldal külön fájl, a közös rész kézzel van kétszer leírva, és szét is csúszott már: a zárási panel más címmel, más oszlopban és más elrendezéssel állt a két oldalon. |
| `magyarszabaly.teszt.js` | A magyarszabály (+10) hol jelenik meg: közös tétel, ha mindkét keret kapja, különben mindkét oldalon az eltérők közt. |
| `betukeszlet.teszt.js` | A betűkészlet-ív nem blokkolhatja a renderelést: minden oldalon `media="print"` + `onload` (és `<noscript>`-ág), preconnect a `fonts.gstatic.com`-ra, a CSS-ben sehol nincs közvetlenül beírt betűnév (mind a `--fo`/`--mono`/`--cim` változókon át megy, tartalék-sorral). Végül élesben: nem válaszoló `fonts.googleapis.com` mellett is kirajzolódik a tabella. Azért létezik, mert ez mérve **12 640 ms** volt 57 ms helyett — addig a lapon semmi nem látszott. |
| `bonuszallapot.teszt.js` | A bónusz három állapota a PL-en: a meccs alatt még változik, lefújva a napzárásig nem hivatalos, napzárás után jelöletlen. A harmadikat a **nap** dönti el, nem a meccs — a teszt kifejezetten olyan meccset is tartalmaz, ami lefújt (`finished: false`), de már lezárt napon van. Dupla fordulónál a két sor külön állapotot kaphat; és ha a napi adat nem jön meg, a jelölés bent marad. |
| `meccsfej.teszt.js` | A meccs állása a pont-bontás fölött: futó meccsnél a meccsóra, lefújva `vége`, el nem kezdődött meccsnél **nincs 0–0**, kettős fordulóban két sor. Ellenőrzi, hogy a fejléc a táblázat fölött áll, és hogy a lezárt forduló meccslistája fordulónként **egyszer** töltődik le (a teszt számolja a fixtures-kéréseket). |
| `padsorrend.teszt.js` | A pad **az FPL sorrendjében** áll (ez a csere-sorrend: a forduló végén az első beférő padost állítja be a nem játszó kezdő helyére), a kezdők viszont poszt szerint rendezve. A teszt pad-sorrendje szándékosan olyan, amit egyetlen poszt-rendezés sem ad vissza — és ezt külön állítás is ellenőrzi, hogy ne legyen triviálisan igaz. |
| `perccellak.teszt.js` | A három perc-oszlop az élő fordulóban: pályán lévő kezdő, lecserélt, becserélt, be nem állt játékos; lefújt meccsnél `vége`; el nem kezdődött meccsnél nincs cella. A meccsóra a **játékosok** perceiből jön — a mockban a fixtures `minutes` szándékosan 0, mert az FPL sosem tölti ki. Az oszlopnevek középpontra mérve a maguk oszlopa fölött állnak gépen és mobilon is. Lezárt fordulóban a meccsóra és a fejlécből a `meccs` oszlop is elmarad, az adat pedig utólag töltődik be — a teszt végpontól végpontig ellenőrzi, hogy a modal előbb jön fel, mint a percek, és az adat megérkeztével magától újrarajzolódik. |
| `valtozasnaplo.teszt.js` | A változásnapló két szűrője. A liga **címke, és több is kijelölhető**: a mindkét ligát érintő bejegyzés bármelyikre szűrve előjön, két ligát kijelölve pedig mindkettőé látszik.  Ellenőrzi a belső margókat is (a `.panel`-nek nincs sajátja, a sávok adják — ez egyszer elcsúszott), a lábléc-linket mindhárom oldalon, és hogy a naplón nincs. |
| `szurkites.teszt.js` | A közös játékosok halványítása gépen és mobilon — és hogy a halvány sor is nyitható marad. |

## A naptártól függő állandó előbb-utóbb elavul

Egy szezon közben a tesztek alatt **mozog az adat**, és a beégetett szám vagy a „legelső tárolt
forduló" előbb-utóbb mást jelent. Hat állítás bukott így egyszerre, egyik sem termékhiba:

| Teszt | Mit feltételezett | Mi lett belőle |
|---|---|---|
| `frissjelzo`, `eloora`, `visszateres`, `eloosszeg`, `meccsallapot` | az **első** tárolt forduló az élő | a főoldal a **legutóbbit** listázza, tehát a kattintás nem-élő meccsre ment, és a mérés csendben semmit nem mért |
| `zarasnb1` | az utolsó lejátszott forduló az **5.** | a 6. lezárásával a lapozó a 6.-on állt |
| `valtoztatasok` | 120 ms elég a lista kirajzolásához | ahogy nőtt az adat, kicsúszott az ablakból |

A szabály ezekre: **az előfeltételt ki kell mondani, nem a repó pillanatnyi állapotából
örökölni.** Vagy az adatból számoljuk (a legfrissebb tárolt forduló, `T.lastPlayedRound()`,
a lejátszott fordulók listája), vagy menet közben mi állítjuk elő (`jsonAtir`-ral kivesszük a
forduló eredményét). Fix várakozás helyett pedig **állapotra** várunk.

## Az élő fordulót mérő tesztek a LEGFRISSEBB tárolt fordulót teszik élővé

Négy teszt (`frissjelzo`, `eloora`, `visszateres`, és részben `valtoztatasok`) azon áll, hogy a
PL-oldalon éppen fut egy forduló. Amíg egyetlen tárolt forduló volt, mindegy volt, melyiket
tették élővé — az volt az egyetlen. **A 2. forduló lezárásával ez szétvált:** a főoldal a
legutóbbi fordulót listázza, a tesztek viszont az *elsőt* tették élővé, tehát a kattintás egy
nem-élő meccsre ment, és a mérés csendben semmit nem mért (a jelzés meg sem jelent, az élő
állás nem íródott ki). Négy állítás bukott, egyik sem termékhiba.

Mostantól mindegyik a **legfrissebb** tárolt fordulót teszi élővé, és ahol kell, az eredményt
is kiveszi a menetrendből (`jsonAtir`) — vagyis az előfeltételt **kimondja**, nem a repó
pillanatnyi állapotából örökli. Ugyanez a szabály minden élő fordulót mérő tesztre: a
naptártól függő előfeltevés előbb-utóbb elavul, és akkor a teszt nem hibát jelez, hanem
elhallgat.
