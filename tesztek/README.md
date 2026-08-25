# Tesztek

```bash
tesztek/futtat.sh
```

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

## Gyűjtő-tesztek (Python, hálózat nélkül)

Az `api_get`-et mock váltja ki, a `collect.py` egy ideiglenes könyvtárban fut.

| fájl | mit ellenőriz |
|---|---|
| `gyujto_onjavitas.py` | Ha az MLSZ utólag korrigál egy régi fordulót, a gyűjtő átvezeti-e — az eredménybe, a keretbe és a keresztellenőrzésbe is. Ez találta meg a `rankings()` `%5B`-formázási hibáját, ami miatt a backfill-ág élesben sosem futott le. |
| `gyujto_ideiglenes.py` | A `provisional` lista kezelése: mi kerül bele, mi kerül ki, és mi marad változatlan hiányos adatnál. |
| `gyujto_lezaras.py` | A forduló-lezárás kilenc esete (lásd lent). |

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
| `allapotter.teszt.js` | A „mit írjunk a 0 pontos játékosról" logika **teljes állapottere**: mind az 576 kombináció, öt invariánssal. Ez talált meg olyan hibákat, amikre nem gondoltunk tesztet írni. |
| `tabella.teszt.js` | A tabellát és a H2H-mátrixot **függetlenül újraszámolja** a `results.json`-ból, és összeveti azzal, amit az oldal kirajzol. |
| `zarasires.teszt.js` | A zárás és a gyűjtés közötti rés a PL-en: ha az FPL szerint a forduló lezárult, de a tárolt adatban még nincs eredmény, a státuszsor **nem ír „naprakész”-t**, hanem megmondja, mi hiányzik, és a **tárolt** állás idejét írja ki (nem a lekérését). A teszt mindkét állapotot kimondja, nem a valós adatra támaszkodik. |
| `gyujto_draftzaras.py` | A draft-gyűjtő forduló-véglegesítése: a le nem zárt fordulót teljes keret mellett is újra lekéri, a **lockdown után** még egyszer (ekkor jön be az automatikus csere), utána soha többé — és hiányos lekérés után **nem** jelöli késznek. A mock a valós mérést követi: záráskor a `current_event` még a régi forduló. Külön eset arra, amikor a **tárolt** adat már teljes, de a záráskori lekérés hasal el — a véglegesítés ezért azt nézi, hogy **ebben a futásban** jött-e be minden csapat. |
| `gyujto_meccsek.py` | A gyűjtő meccsgyűjtése (`meccsek.json`): id szerinti összevonás, **eredmény csak lezárt meccsről** (a futó meccs pontszámát akkor sem tárolja, ha az API küldi), a visszaeső meccs kimarad, a teljes forduló nem kér többé meccslistát, a futó meccsű igen — és a **pótolt meccs** is bekerül: ha a forduló hivatalos pontja változik, újra megy a meccslistás lekérés (az elhalasztott meccs nincs benne a listában, tehát „befejezetlenként” nem látszana). |
| `nb1meccs.teszt.js` | A meccs-sor a NB1 részletezője fölött: lezárt meccsnél eredmény + „vége", el nem kezdődöttnél **nincs kitalált 0–0**, az időkorláton belül „a meccs zajlik"; dupla meccsű klubnál két sor; nogame játékosnál nincs sor; a Játszott perc a táblázat első sora. |
| `nullapont.teszt.js` | A négy „0 pont" állapot és a kattinthatóság-jelzés mindkét oldalon. Az **élő forduló előfeltételét maga állítja be** (`provisional`): lezárt fordulóban a „zajlik" állapotokra más — és helyes — üzenet jár, tehát a valós adatra hagyva a teszt a gyűjtő első lezárása után mást mérne. |
| `meccsallapot.teszt.js` | A `meccsAllapot()` négy értéke és a két időkorlát (100 / 180 perc); a lejárt éjféles helyőrző (nem ígér kezdési időt); a `round_number`-ből felismert „nincs meccse". |
| `uzenetek.teszt.js` | Gyorsítótár-kerülés az élő lekéréseknél, és hogy meccs közben nem írjuk, hogy „lejátszotta pont nélkül". |
| `visszateres.teszt.js` | A lap láthatóvá válásakor újra lekér-e (`FunTasy.ujraLathatokor`) — egységteszt és e2e is. |
| `frissjelzo.teszt.js` | A „frissítés…" jelzés lassú lekérésnél megjelenik, gyorsnál nem villan fel. |
| `keretbetoltes.teszt.js` | A meccs megnyitása a **fordulónkénti** keret-fájlt tölti-e le a teljes előzmény helyett — és a visszaesési út is működik-e. |
| `kulonbseg.teszt.js` | A Különbségek nézet szerkezete gépen (két oszlop) és mobilon (közös blokk + két oszlop). |
| `magyarszabaly.teszt.js` | A magyarszabály (+10) hol jelenik meg: közös tétel, ha mindkét keret kapja, különben mindkét oldalon az eltérők közt. |
| `bonuszallapot.teszt.js` | A bónusz három állapota a PL-en: a meccs alatt még változik, lefújva a napzárásig nem hivatalos, napzárás után jelöletlen. A harmadikat a **nap** dönti el, nem a meccs — a teszt kifejezetten olyan meccset is tartalmaz, ami lefújt (`finished: false`), de már lezárt napon van. Dupla fordulónál a két sor külön állapotot kaphat; és ha a napi adat nem jön meg, a jelölés bent marad. |
| `meccsfej.teszt.js` | A meccs állása a pont-bontás fölött: futó meccsnél a meccsóra, lefújva `vége`, el nem kezdődött meccsnél **nincs 0–0**, kettős fordulóban két sor. Ellenőrzi, hogy a fejléc a táblázat fölött áll, és hogy a lezárt forduló meccslistája fordulónként **egyszer** töltődik le (a teszt számolja a fixtures-kéréseket). |
| `padsorrend.teszt.js` | A pad **az FPL sorrendjében** áll (ez a csere-sorrend: a forduló végén az első beférő padost állítja be a nem játszó kezdő helyére), a kezdők viszont poszt szerint rendezve. A teszt pad-sorrendje szándékosan olyan, amit egyetlen poszt-rendezés sem ad vissza — és ezt külön állítás is ellenőrzi, hogy ne legyen triviálisan igaz. |
| `perccellak.teszt.js` | A három perc-oszlop az élő fordulóban: pályán lévő kezdő, lecserélt, becserélt, be nem állt játékos; lefújt meccsnél `vége`; el nem kezdődött meccsnél nincs cella. A meccsóra a **játékosok** perceiből jön — a mockban a fixtures `minutes` szándékosan 0, mert az FPL sosem tölti ki. Az oszlopnevek középpontra mérve a maguk oszlopa fölött állnak gépen és mobilon is. Lezárt fordulóban a meccsóra és a fejlécből a `meccs` oszlop is elmarad, az adat pedig utólag töltődik be — a teszt végpontól végpontig ellenőrzi, hogy a modal előbb jön fel, mint a percek, és az adat megérkeztével magától újrarajzolódik. |
| `valtozasnaplo.teszt.js` | A változásnapló két szűrője. A liga **címke, és több is kijelölhető**: a mindkét ligát érintő bejegyzés bármelyikre szűrve előjön, két ligát kijelölve pedig mindkettőé látszik.  Ellenőrzi a belső margókat is (a `.panel`-nek nincs sajátja, a sávok adják — ez egyszer elcsúszott), a lábléc-linket mindhárom oldalon, és hogy a naplón nincs. |
| `szurkites.teszt.js` | A közös játékosok halványítása gépen és mobilon — és hogy a halvány sor is nyitható marad. |
