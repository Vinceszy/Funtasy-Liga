# Funtasy Liga

Két H2H fantasy-liga oldala, GitHub Pages, `main`-ről. Nincs build.
Az `nb1/` az MLSZ-es, fizetési sapkás liga becenevekkel; a `pl/` az FPL Draft
csapatnevekkel. A közös réteg a `funtasy.js` és a `funtasy.css`, verzióval
(`?v=N`, a szám a `verzio.json`-ban).

## Mielőtt bármilyen cikket írnál — kötelező

Ez nem ajánlás. A stílusszabályok és a módszer azért vannak leírva, mert
egyszer már mindegyikért fizettünk egy újraírást. Aki fejből ír, ugyanazt a
hibát követi el másodszor is.

Írás előtt, minden alkalommal, végig kell olvasni:

1. `naplo/summary-voice.md` — a hang és a tiltások. Ez a hosszabb, és ez az,
   amit a legkönnyebb elfelejteni.
2. `naplo/round-pipeline.md` — a három réteg, a források, a sorrend, és hogy
   melyik adat hol van (az automatikus cserék például **csak** a
   `zarasok.json`-ban).

Utána, és csak utána:

- Összefoglalóhoz: `naplo/draft-round-harvest.py <fordulo>` (Draft) vagy
  `naplo/round-colour-harvest.py <fordulo>` (NB1), plusz a forduló
  színestáblája (`naplo/<liga>-colour-<fordulo>.json`).
- Beharangozóhoz: `naplo/draft-preview-harvest.py <fordulo>`. A beharangozó
  nem a múlt heti eredményről szól, hanem arról, ami a jövő hetit eldöntheti.
- A számokat a saját adatunkból kell ellenőrizni, nem emlékezetből.

**Semmi nem megy ki élesre, amíg Vince le nem okézza a szöveget.** A kész
szöveg ide, a beszélgetésbe kerül, nem vázlatfájlba.

## Az olvasó ebben a ligában játszik

Tudja, mi az automatikus csere, mikor zár a keret, és hogy a pad nem ér
pontot. Ezeket tilos elmagyarázni neki. A szabály következményét írjuk le,
nem a szabályt.

## Ellenőrzés

`bash tesztek/futtat.sh` futtat mindent. A dokumentáció és a cikkek
konzisztenciáját a `tesztek/dokuk.py` őrzi (D1–D14); a színestáblát a
`naplo/colour-check.py`.

## Mérések

A fejlesztői gép minden külső hosztot blokkol. Ami hálózatot igényel, az
Actionsből megy: `.github/workflows/naplo-meres.yml`, a `naplo/*.py`
szkriptekkel. **Egy mérés eredményét azonnal rögzíteni kell** a megfelelő
táblába — ami csak a futási naplóban marad, azt a következő munkamenet újra
lekéri.
