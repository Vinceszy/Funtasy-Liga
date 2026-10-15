# Saving the squads with one click — FALLBACK

**Normally this is not needed.** The squads are collected automatically by GitHub
Actions too (`collect.py`, `.github/workflows/archive.yml`): hourly at :17 UTC from
Thursday to Monday (the match days), every 3 hours at :17 UTC on Tuesday and
Wednesday. The squad endpoint works from a server as well — a 403 from it is caused
not by an IP block but by a missing `filter[round_id]` parameter.

This bookmarklet is needed if the server-side collection breaks (e.g. the MLSZ really
blocks data-centre IPs): run on fantasy.mlsz.hu, it fetches all 8 squads and saves them
straight into the repository.

*Small differences from the server-side collection: the bookmarklet does not write the
`round` field of `squads.json` (the label on the page's „Aktuális keret" (Current squad)
tab then appears without a round number), and the player records lack the `id`,
`played`, `start` and `nogame` fields (used by the points-breakdown accordion, the „még
nem játszott" (not played yet) dash and the match-status messages). None of this breaks
anything — the page works without these fields and resolves the breakdown by name —,
and the **next server-side run fills them in**: the collector looks specifically for
a round whose records have no `played`, and fetches it again, together with the match
list.*

---

## 1. Creating the token (once, 2 minutes)

1. GitHub → profile picture top right → **Settings**
2. At the bottom: **Developer settings** → **Personal access tokens** → **Fine-grained tokens**
3. **Generate new token**
   - **Token name:** `funtasy-keret`
   - **Expiration:** pick a date beyond the end of the season (e.g. 1 year)
   - **Repository access:** *Only select repositories* → **Funtasy-Liga**
   - **Permissions → Repository permissions → Contents:** set it to **Read and write**
     *(everything else stays "No access")*
4. **Generate token** → copy the value starting with `github_pat_...`

> This token grants rights **only to this one repository**, and only for writing files.
> It can be revoked at any time in the same place.

## 2. Creating the bookmark

1. Open the `GOMB-bookmarklet.txt` file and copy its **entire content**
2. In the copied text, replace the `IDE_A_TOKEN` part with your own token
   *(it is near the start, in the form `TOKEN%3D%27IDE_A_TOKEN%27` — rewrite only the
   upper-case part between the apostrophes, not the apostrophes themselves)*
3. In the browser: **Ctrl+Shift+O** (bookmark manager) → right click → **New bookmark**
   - **Name:** `Keret mentés`
   - **URL:** paste the modified text here
4. Drag it onto the bookmarks bar so it is at hand

## 3. Use (when it is needed as a fallback, ~10 seconds)

1. Go to **https://fantasy.mlsz.hu/** (it is enough for it to be loaded, logged in)
2. Click the **Keret mentés** bookmark
3. The progress appears bottom right. The script **works out by itself** which rounds
   are missing from `squad_history.json`, and fetches only those — it asks nothing
4. Done: `squad_history.json` and `squads.json` are updated in the repository

If every round is already there, it prints: *„Minden forduló naprakész (1–N).”*
(every round up to date) — and then it does not touch the repository.

**When to run it?** After the round has closed. There is no hurry: the squad can be
fetched round by round retroactively too, so a missed week can be filled in later.

**Retroactive backfill:** automatic. The squad endpoint accepts a `filter[round_id]`
parameter (`round_id = 75 + 2 × round number`), so the squads of earlier rounds can be
fetched exactly too, not only the current one. If you miss several weeks, the next
click fills in all of them at once.

## Errors

- *„Ezt a fantasy.mlsz.hu oldalon kell futtatni!”* (this has to run on fantasy.mlsz.hu)
  → you are not on the right page
- *401/403 when saving* (`Hiba: squad_history.json: HTTP 401`) → the token has expired
  or has no Contents: write permission
- *A fantasy username has changed* → the bookmarklet gives NO error for this: it looks
  each manager up with the rankings search, and if no row has exactly that username it
  takes the first hit of the search — so another user's squad may be saved under the
  manager's name —, and if the search finds nothing, that manager is skipped without a
  word. The roster lives in THREE places, all of them have to be updated: `collect.py`
  (`MEMBERS` — this is the primary one, the collection depends on it),
  `nb1/index.html` (`MEMBERS`), and the bookmarklet (the `M` constant in
  `GOMB-forras.js`, then rebuild with `bookmarklet-build.py` and replace the bookmark
  in the browser)
