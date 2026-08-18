# Keret-mentés egy kattintással

Az MLSZ a keret-végpontot adatközponti IP-kről tiltja (403), ezért azt sem a GitHub,
sem proxy nem tudja lekérni — **csak a te böngésződ**. Ez a könyvjelző ezt oldja meg:
a fantasy.mlsz.hu-n futtatva lekéri mind a 8 keretet, és egyenesen a repóba menti.

A H2H-eredmények (tabella, meccsek) ettől függetlenül **automatikusan** frissülnek,
azzal nincs teendőd.

---

## 1. Token létrehozása (egyszeri, 2 perc)

1. GitHub → jobb felül a profilkép → **Settings**
2. Legalul: **Developer settings** → **Personal access tokens** → **Fine-grained tokens**
3. **Generate new token**
   - **Token name:** `funtasy-keret`
   - **Expiration:** válaszd a szezon végén túli dátumot (pl. 1 év)
   - **Repository access:** *Only select repositories* → **Funtasy-Liga**
   - **Permissions → Repository permissions → Contents:** állítsd **Read and write**-ra
     *(minden más maradjon "No access")*
4. **Generate token** → másold ki a `github_pat_...` kezdetű értéket

> Ez a token **csak ehhez az egy repóhoz** ad jogot, és csak fájlírásra.
> Bármikor visszavonható ugyanitt.

## 2. Könyvjelző létrehozása

1. Nyisd meg a `bookmarklet.txt` fájlt, másold ki a **teljes tartalmát**
2. A másolt szövegben cseréld ki az `IDE_JON_A_TOKEN` részt a saját tokenedre
   *(a szöveg elején van, `token%3A%27IDE_JON_A_TOKEN%27` formában — csak a nagybetűs részt írd át)*
3. Böngészőben: **Ctrl+Shift+O** (könyvjelzőkezelő) → jobb klikk → **Új könyvjelző**
   - **Név:** `Keret mentés`
   - **URL:** ide illeszd be a módosított szöveget
4. Húzd a könyvjelzősávra, hogy kéznél legyen

## 3. Használat (hetente ~10 másodperc)

1. Menj a **https://fantasy.mlsz.hu/** oldalra (elég betöltve lennie, bejelentkezve)
2. Kattints a **Keret mentés** könyvjelzőre
3. Jobb alul megjelenik a folyamat; a végén megkérdezi, **melyik fordulóhoz** mentse
   (alapból a jelenlegit ajánlja — Enter)
4. Kész: a repóban frissül a `squads.json` és a `squad_history.json`

**Mikor futtasd?** A forduló lezárása után, de az új piacnyitás előtt — akkor a keret
még az adott fordulós állapotot mutatja.

**Visszamenőleges pótlás:** korábbi fordulóhoz csak akkor tudsz menteni, ha a keret
azóta nem változott — a fordulószám kézzel átírható a kérdésnél.

## Hibák

- *"Ezt a fantasy.mlsz.hu oldalon kell futtatni!"* → nem a jó oldalon vagy
- *401/403 a mentésnél* → a token lejárt vagy nincs Contents: write joga
- *Nem találom: <név>* → változott egy felhasználónév; írd át a könyvjelzőben és az `index.html`-ben is
