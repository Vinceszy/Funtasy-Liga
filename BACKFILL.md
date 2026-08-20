# Visszamenőleges keret-gyűjtés — **ELAVULT, nincs rá szükség**

Ez a fájl korábban egy kézi konzolszkriptet tartalmazott, amivel a régebbi fordulók
kereteit lehetett pótolni: bemásolod a böngésző konzoljába, kimásolod a JSON-t, és
kézzel beilleszted a `squad_history.json`-ba.

**Ez a folyamat megszűnt.** A régi szkriptet azért távolítottuk el, mert mostanra nem
csak fölösleges, hanem működésképtelen is — és félrevezető lett volna bent hagyni.

## Miért nem kell többé

Kiderült, hogy a keret-végpont fogad egy `filter[round_id]` paramétert, és hogy

```
round_id = 75 + 2 × fordulószám        (1.→77, 2.→79, 3.→81, 4.→83, 5.→85)
```

Ezzel a **korábbi fordulók kerete is pontosan lekérhető**, nem csak az aktuális — épp
az a korlát szűnt meg, ami miatt ez a fájl készült.

A `GOMB-bookmarklet.txt` ezt magától elvégzi: megnézi, mely fordulók hiányoznak a
`squad_history.json`-ból, és egyetlen kattintással pótolja mindet. Lásd:
[`KERET-MENTES.md`](KERET-MENTES.md).

## Miért nem működne a régi szkript

Ha valaki egy régi másolatból mégis elővenné, három okból sem adna használható adatot:

1. **Nem küldött `filter[round_id]`-t** — a végpont enélkül ma **403 Forbidden**-nel
   válaszol. (Korábban enélkül is ment, menet közben szigorítottak rajta.)
2. **Rossz helyről olvasta a nevet.** A `competition_player.player` beágyazott objektumot
   kérte, pedig a név közvetlenül a `competition_player`-ben van (`first_name` /
   `last_name`).
3. **Hiányos rekordokat gyártott:** nem gyűjtött `pos`, `u21`, `hun` és `price` mezőt,
   amiket az oldal „Aktuális keret” és „Szezon játékosai” füle használ. A vele mentett
   fordulók poszt- és magyarszabály-információ nélkül maradtak volna.

## Ha valaha mégis kézzel kell

A működő, bizonyítottan jó lekérési logika olvasható formában itt van:
[`GOMB-forras.js`](GOMB-forras.js) — abból kimásolható a `fetch`-hívás a helyes
`include` listával és `round_id` számítással.
