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

1. Nyisd meg a `GOMB-bookmarklet.txt` fájlt, másold ki a **teljes tartalmát**
2. A másolt szövegben cseréld ki az `IDE_A_TOKEN` részt a saját tokenedre
   *(a szöveg elején van, `TOKEN%3D%27IDE_A_TOKEN%27` formában — csak az aposztrófok közötti
   nagybetűs részt írd át, magukat az aposztrófokat ne)*
3. Böngészőben: **Ctrl+Shift+O** (könyvjelzőkezelő) → jobb klikk → **Új könyvjelző**
   - **Név:** `Keret mentés`
   - **URL:** ide illeszd be a módosított szöveget
4. Húzd a könyvjelzősávra, hogy kéznél legyen

## 3. Használat (hetente ~10 másodperc)

1. Menj a **https://fantasy.mlsz.hu/** oldalra (elég betöltve lennie, bejelentkezve)
2. Kattints a **Keret mentés** könyvjelzőre
3. Jobb alul megjelenik a folyamat. A szkript **magától megállapítja**, mely fordulók
   hiányoznak a `squad_history.json`-ból, és csak azokat kéri le — nem kérdez semmit
4. Kész: a repóban frissül a `squad_history.json` és a `squads.json`

Ha már minden forduló megvan, ezt írja ki: *„Minden forduló naprakész (1–N).”* — ilyenkor
nem nyúl a repóhoz.

**Mikor futtasd?** A forduló lezárása után. Nem kell kapkodni: a keret fordulónként
visszamenőleg is lekérhető, tehát egy kihagyott hét később is pótolható.

**Visszamenőleges pótlás:** automatikus. A keret-végpont fogad egy `filter[round_id]`
paramétert (`round_id = 75 + 2 × fordulószám`), így a korábbi fordulók kerete is
pontosan lekérhető, nem csak a mostani. Ha több hetet hagysz ki, a következő kattintás
egyszerre pótolja mindet.

## Hibák

- *"Ezt a fantasy.mlsz.hu oldalon kell futtatni!"* → nem a jó oldalon vagy
- *401/403 a mentésnél* → a token lejárt vagy nincs Contents: write joga
- *Nem találom: <név>* → változott egy felhasználónév; írd át a könyvjelzőben és az `index.html`-ben is
