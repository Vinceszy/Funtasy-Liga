# FunTasy — head-to-head tracking for private fantasy leagues

Head-to-head league tracker pages for private leagues among friends, built on the data of
**fantasy.mlsz.hu** (MLSZ NB I Fantasy) and **FPL Draft**. A static site on GitHub Pages: no
build, no dependencies. Data collection is **fully automatic** (GitHub Actions, UTC: NB1
hourly on match days (Thursday–Monday) and every 3 hours on Tuesday–Wednesday; PL every 3
hours plus hourly in the late-morning closing window, 07:00–13:00 — see section 3) — the
browser bookmarklet is only a fallback.

| Page | URL |
|---|---|
| Home (league picker) | https://vinceszy.github.io/Funtasy-Liga/ |
| FunTasy NB1 | https://vinceszy.github.io/Funtasy-Liga/nb1/ |
| FunTasy PL | https://vinceszy.github.io/Funtasy-Liga/pl/ |

The old `draft.html` address redirects to `/pl/`, so older links keep working.

On both pages the participants are identified by their **monogram** (after the name) — the
same for a person in both leagues; it will be the key of the planned combined page.

<!-- table of contents: maintained by tests/doc_checks.py, do not edit by hand -->
<details>
<summary><b>Contents</b></summary>

- [1. What the site does](#1-what-the-site-does)
  - [Table](#table)
  - [Matches — two separate panels](#matches--two-separate-panels)
  - [Head-to-head matrix](#head-to-head-matrix)
  - [Modal — three tabs](#modal--three-tabs)
  - [The FunTasy PL page](#the-funtasy-pl-page)
  - [Points breakdown (accordion) and the "not played yet" marking](#points-breakdown-accordion-and-the-not-played-yet-marking)
  - [Player profile](#player-profile)
  - [The field's players (main page list)](#the-fields-players-main-page-list)
  - [Closing changes (both leagues)](#closing-changes-both-leagues)
  - [The open points breakdown survives the refresh](#the-open-points-breakdown-survives-the-refresh)
  - [Navigation inside the modal](#navigation-inside-the-modal)
  - [Mobile](#mobile)
- [2. Files](#2-files)
- [3. How the data is updated](#3-how-the-data-is-updated)
  - [Everything runs automatically (GitHub Actions, hourly on match days)](#everything-runs-automatically-github-actions-hourly-on-match-days)
  - [The FPL Draft data (draft.yml)](#the-fpl-draft-data-draftyml)
  - [Live refresh from the browser (both pages)](#live-refresh-from-the-browser-both-pages)
  - [The last known score — "if somebody has already fetched it, let me see that"](#the-last-known-score--if-somebody-has-already-fetched-it-let-me-see-that)
  - [The NB1 live fetch runs in two rounds, not eight (measured)](#the-nb1-live-fetch-runs-in-two-rounds-not-eight-measured)
  - [The CORS proxies are interchangeable — a free proxy can disappear (measured)](#the-cors-proxies-are-interchangeable--a-free-proxy-can-disappear-measured)
  - [The fonts cannot stop the page (measured)](#the-fonts-cannot-stop-the-page-measured)
  - [Cache: why the score got stuck on an iPhone](#cache-why-the-score-got-stuck-on-an-iphone)
  - [„frissítés… 1,2 mp" — against the silent number swap](#frissítés-12-mp--against-the-silent-number-swap)
  - [Round boundary and a closed PL round: the live layer must be dropped](#round-boundary-and-a-closed-pl-round-the-live-layer-must-be-dropped)
  - [The main page list and the match sheet cannot disagree](#the-main-page-list-and-the-match-sheet-cannot-disagree)
  - [What is deliberately left inconsistent](#what-is-deliberately-left-inconsistent)
  - [Fallback: the browser bookmarklet](#fallback-the-browser-bookmarklet)
- [3/b. CLOSING — what means what, and where it is decided](#3b-closing--what-means-what-and-where-it-is-decided)
  - [What MUST still be updated after the close](#what-must-still-be-updated-after-the-close)
- [4. The MLSZ Fantasy API — what is known about it](#4-the-mlsz-fantasy-api--what-is-known-about-it)
  - [Rankings](#rankings)
  - [Squad (works from anywhere — if you ask the right way)](#squad-works-from-anywhere--if-you-ask-the-right-way)
  - [Who is not playing in the round (the match list)](#who-is-not-playing-in-the-round-the-match-list)
  - [Points breakdown (game-player-stats)](#points-breakdown-game-player-stats)
  - [Player master data and the whole season (with measurements)](#player-master-data-and-the-whole-season-with-measurements)
  - [The player detail endpoint (measured)](#the-player-detail-endpoint-measured)
  - [The future schedule is not available (measured)](#the-future-schedule-is-not-available-measured)
  - [There is no price history (measured)](#there-is-no-price-history-measured)
  - [What the official rules state (fantasy.mlsz.hu)](#what-the-official-rules-state-fantasymlszhu)
  - [The key to the points calculation](#the-key-to-the-points-calculation)
  - [The “blocked from servers” misconception](#the-blocked-from-servers-misconception)
  - [Round closing and later MLSZ corrections](#round-closing-and-later-mlsz-corrections)
  - [The three states of bonus points (PL)](#the-three-states-of-bonus-points-pl)
  - [Who is still on the pitch (PL)](#who-is-still-on-the-pitch-pl)
  - [The match score above the points breakdown (PL and NB1)](#the-match-score-above-the-points-breakdown-pl-and-nb1)
  - [Automatic substitutions at the round's close (PL)](#automatic-substitutions-at-the-rounds-close-pl)
  - [The gap between closing and collection (PL)](#the-gap-between-closing-and-collection-pl)
  - [The gap between the start and collection (PL) — the browser backfills the squads](#the-gap-between-the-start-and-collection-pl--the-browser-backfills-the-squads)
  - [Name and monogram: the monogram is never cut off](#name-and-monogram-the-monogram-is-never-cut-off)
  - [Line-up efficiency (KEZD%)](#line-up-efficiency-kezd)
  - [The bench order (PL) — and what is still open](#the-bench-order-pl--and-what-is-still-open)
  - [The FPL Draft API (draft.premierleague.com/api/) — verified by measurement](#the-fpl-draft-api-draftpremierleaguecomapi--verified-by-measurement)
- [4/c. A club can have two matches in one round](#4c-a-club-can-have-two-matches-in-one-round)
  - [The closing panel goes up to the CLOSED rounds](#the-closing-panel-goes-up-to-the-closed-rounds)
  - [What the collector writes, the workflow commits too](#what-the-collector-writes-the-workflow-commits-too)
  - [A stale page reloads itself](#a-stale-page-reloads-itself)
  - [Shared players are paired by ID, not by name](#shared-players-are-paired-by-id-not-by-name)
- [5. Known limitations and pitfalls](#5-known-limitations-and-pitfalls)
- [5/a4. The Guardiola measure](#5a4-the-guardiola-measure)
  - [The same on PL, with automatic substitutions](#the-same-on-pl-with-automatic-substitutions)
- [5/a5. The „Változtatások" (Changes) tab](#5a5-the-változtatások-changes-tab)
  - [On PL, what the manager did and what the machine did stand apart](#on-pl-what-the-manager-did-and-what-the-machine-did-stand-apart)
  - [The round in progress is shown without points](#the-round-in-progress-is-shown-without-points)
  - [One gate decides when there is a score](#one-gate-decides-when-there-is-a-score)
  - [On horizontal scroll, the position and the name stay put](#on-horizontal-scroll-the-position-and-the-name-stay-put)
  - [The shared layer understands both data shapes — and this is not a convenience](#the-shared-layer-understands-both-data-shapes--and-this-is-not-a-convenience)
- [5/a6. The squads are visible before kick-off](#5a6-the-squads-are-visible-before-kick-off)
- [5/a. Why there is a separate squad file per round](#5a-why-there-is-a-separate-squad-file-per-round)
- [5/a3. A closed round's breakdown comes from the repository](#5a3-a-closed-rounds-breakdown-comes-from-the-repository)
  - [Live points are summed from the itemised breakdown (PL)](#live-points-are-summed-from-the-itemised-breakdown-pl)
  - [During a live round the page refreshes itself](#during-a-live-round-the-page-refreshes-itself)
  - [Write only when something really changed](#write-only-when-something-really-changed)
  - [An interrupted write cannot be read as "no history"](#an-interrupted-write-cannot-be-read-as-no-history)
- [5/a2. Changelog („Mi újult meg?" — What's new?)](#5a2-changelog-mi-újult-meg--whats-new)
  - [The frame of the two pages is written twice by hand](#the-frame-of-the-two-pages-is-written-twice-by-hand)
- [5/a7. The magazine is in publication order](#5a7-the-magazine-is-in-publication-order)
  - [The weekly column does not belong to a pairing](#the-weekly-column-does-not-belong-to-a-pairing)
- [5/b. Tests](#5b-tests)
- [6. Making changes](#6-making-changes)
  - [Adding a new league](#adding-a-new-league)
- [7. Planned, not yet built](#7-planned-not-yet-built)

</details>

---

## 1. What the site does

### Table
- 8 managers, a 33-round round-robin H2H schedule
- Scoring: **win 3 · draw 1 · loss 0**
- Tiebreak in the NB1: **1) points → 2) KÜL (points difference) → 3) SP (points scored)**;
  in the PL, following FPL's default scoring, **points scored comes first** as the
  tiebreaker (the `tiebreak: 'rg'` option in `pl/index.html`)
  *(The league's original Excel table also put points difference first. If this has to
  change, it is a single line: the `.sort(...)` at the end of `computeTable` in `funtasy.js`.)*
- **The table counts closed rounds only.** The results of the round in progress show on
  the match panel, marked „élő” (live) — they do not move the table until the round
  closes.
- Columns: rank, name, M (matches), GY (wins), D (draws), V (losses), SP (points scored),
  KP (points conceded), KÜL (points difference), Pont (points), Forma (form: the last 5
  matches as dots)
- Clicking a name opens a modal (see below)

### Matches — two separate panels
- **„Legutóbbi forduló”** (Last round) — set automatically to the last one played
- **„Következő forduló”** (Next round) — set automatically to the upcoming one
- Each can be paged on its own (‹ › buttons + round picker)
- Clicking a match row shows the two squads involved side by side — **true to the round**:
  the squads of that round as they were then, with the points of then, and the official
  round score in the header (for a future round, an explanatory text)
- **Clicking a live (still running) match** brings up the two squads with live points per
  player: immediately the stored state (at most 3 hours old), then replaced in the
  background by minute-fresh data.
- **The match sheet starts with a score line** (`Bazsa 41 : 36,63 Vince`), looking the same
  as the match panels of the main page; for a live match with a dashed border and an `élő`
  badge. Without it the score would only appear separately, in the headers of the two squad
  columns. The score line and the column headers come **from the same calculation**, so they
  cannot disagree. If there is no squad data for the round at all, this fallback text is
  shown: *„A meccs még tart, a keretek által szerzett pontok a forduló zárta után
  elérhetőek.”* (The match is still on; the points scored by the squads are available after
  the round closes.)
- **„Különbségek” (Differences) view (salary cap leagues only, i.e. the NB1):** the switch
  under the score splits the squads into two groups — **shared** and **different**
  players —, because the points of the shared ones cancel out; the match is decided by the
  different ones.

  **The left/right structure is kept throughout** (left column one manager, right column
  the other): on desktop the shared players are in **both columns**, with the same numbers.
  The eye sees at once that the two parts match; lifting them into a separate block would
  break the familiar layout. **On mobile**, however, the columns stack, and there the
  duplication would only make the page longer: one shared block comes first, then the two
  managers with their own different players. CSS does the switch; there is no resize
  listener.

  Every group ends with a **total row** (styled like the squad header): *Közös összesen*
  (Shared total), *Eltérő összesen* (Different total), finally *<név> összesen* (<name>
  total) — the last one is the team's full round score, and the two above add up to exactly
  that.

  **A matching name is not enough for identity:** captaincy and the starter/bench role
  count too, because they change the player's points (Szalai as a starter 10, as captain
  20 — that is not the same item). **The Hungarian rule (+10) is an item too:** if both
  squads get it, it goes into the shared group; if only one does, it goes among the
  different items on both sides (with 0 for the other).

  The PL page deliberately has no such view: in a draft league a player can be in only one
  team, so a shared item cannot occur.

### Head-to-head matrix
An 8×8 grid, `GY/D/V` (win/draw/loss) for every pairing from the matches so far. On mobile it
scrolls horizontally, with a sticky name column. **Clicking a cell** opens a modal with all
head-to-head pairings of the two teams: matches played with their result and GY/D/V (from
the row player's point of view), a live match with the live marking, future ones with
„— : —". Clicking a row opens the match details. It works the same way on both pages.

### Modal — three tabs
1. **Aktuális keret** (Current squad) — for a closed round the squad of the last round,
   with the **official round score** in the header; during a live round the live match
   squad, with points pulled **minute-fresh** on opening (the label then says „élő
   pontösszeg" (live points total)). Sorted by position
   (GK → DEF → MID → ST), Hungarian players with a small red-white-green flag (drawn in CSS,
   **not an emoji** — Chrome on Windows would show the letter pair "HU" instead of the flag
   emoji), u21 players with a blue `U21` label, the captain with `C ×2`. A separate
   **Hungarian rule bar** (how many Hungarian starters, how many of them u21, whether the +10
   is due), the **official round score** in the header, and separate total rows for the
   starters and the bench.
2. **Fordulók** (Rounds) — the manager's whole season round by round (opponent, own points,
   opponent's points, GY/D/V), with the record at the top. Clicking a row opens the match
   details. The **row of the round in progress shows the live score**, marked `élő`; it does
   not count in the record (GY/D/V), just as it does not count in the table.
3. **Szezon játékosai** (Season's players) — every player who was ever in the squad, with
   the points he produced there, how many rounds he was there, how many times starter /
   bench, how many times captain. At the top: in how many rounds the Hungarian rule was met
   (the sum of the +10s), the points of the Hungarian players, and of those the u21 players'.

### The FunTasy PL page
The same structure (table, match panels, matrix, modal with three tabs, live scores), in the
Premier League's purple colours, with the specifics of FPL Draft:
- team names + monogram (only monograms in the matrix); on a tie the points scored decide
- no captain and no Hungarian rule; bench points do not count for the team
- live score during a round: the line-ups are fixed when the round starts (they are in the
  repository), the browser only fetches the public player points minute-fresh, and sums
  every match from them
- the „Szezon játékosai" tab and the match squads accumulate from the start of GW1

### Points breakdown (accordion) and the "not played yet" marking
On both pages, in every squad view (current squad, match squads, live match):

- **Clicking a player's row** opens the points breakdown under the row: event, value, points
  (e.g. „Győzelem · 1 · 3” (Win), „Percek a pályán (több, mint 60 perc) · 90 · 2” (Minutes
  on the pitch, more than 60)). Only the rows worth points are shown, just as the MLSZ
  interface shows them. The captain ×2 and the bench ×0.5 appear as separate rows, because
  the weekly points shown already contain them, while the breakdown rows are the raw values.
  Clicking again closes it; clicking another player closes the previous one — one panel is
  open at a time. The browser fetches the breakdown on click (through the same CORS proxies
  as every live fetch) and remembers the ones opened.
- **A small arrow (▼) after the name shows that the row is clickable**; it turns over when
  open, and a hint line stands above the list („Kattints egy játékosra a pontjai
  részletezéséhez.” (Click a player for the details of his points.)). The arrow is after the
  name and not at the end of the row because it is safe there: in the narrow column the
  ellipsis cuts the club label first. With a mouse the row also lights up, but the arrow is
  what matters — **there is no hover on a phone**.
- **If there is no event worth points, the message says why** — seven cases, because a 0
  can have several causes: *the club has no match in this round* (called off / postponed,
  an empty round on the PL), *the match has not started yet* (with the kick-off time),
  *the match was called off, no new date set*, *the match is on, no event worth points so
  far*, *the match is over, but the points are still being processed*, *played the match
  without points*, or *did not take the pitch*. The first comes from the round's match list
  (see below), the next ones from the kick-off time, the match state and the played flag,
  the last two from the minutes-played row of the breakdown (it arrives with 0 minutes too,
  if the player sat on the bench throughout).

  In two places **time** matters in the text as well. "No match" is in the past tense for
  a closed round, because "is not playing" is false weeks later. And "has not started yet"
  only talks about a kick-off time while the date is in the future: the MLSZ writes
  midnight for an unscheduled kick-off, and that day can pass — from then on the sentence
  is about a called-off match and promises no kick-off.

  **`is_played` does NOT mean the match is over.** The MLSZ flips it to true already
  *during* the match. Trusting it, the page would say for practically everybody during a
  live round that they "played the match without an event worth points" — while the match
  was in full swing.

  So in a live round the **match state** decides, not the played flag. In a single place,
  `matchState` (in `nb1/index.html`), with four values: *elotte* (before) / *fut*
  (running) / *utana* (after) / *ismeretlen* (unknown) — so the player's row and the points
  breakdown can never say different things about the same match.

  The rule rests on **two time limits**, and each has a concrete reason:

  - **Under 100 minutes the `vege` (ended) signal is not believed.** A match is 2×45
    minutes + half-time + stoppage time, so it physically cannot end in that time. It
    could *not be checked* when the MLSZ flips the match list's `completed` field — if it
    did it the same way as `is_played` (during the match), a naive fix would solve nothing.
    So the fix is **independent of this open question**.
  - **After 180 minutes we do not claim it is running**, even if no `vege` signal has
    arrived. `vege` is not always available (the earliest squad records do not even have
    such a field).

  If no kick-off time is set (the MLSZ then writes midnight), the match is **not** treated
  as started.

  **Measured fact: for a player with 0 points the MLSZ returns an EMPTY points
  breakdown.** Evidence: Heitor (Újpest) with 0 points got an empty list, while his
  teammate Ljujić — from the same match — got 1.75, so the match had been processed. An
  empty breakdown therefore does **not** mean an unprocessed match. Building on that
  ("the played claim needs a breakdown row") makes the page say „a pontok feldolgozása még
  tart" (the points are still being processed) for a player who really scored 0 in a match
  long finished. What protects against the during-the-match error is not this but the state
  gate above.

  **Time passes between the final whistle and the points appearing, too.** On the PL, the
  FPL closes a match **in two steps**: `finished_provisional` is true at the final whistle,
  `finished` only when the bonus points are finalised — so either of the two is enough to
  take the match as played. (Without this, a match already played would be described as „a
  meccs zajlik" (the match is on).)

- **The "match is on" text differs by league, because the source differs** (the
  `livePoints` field in `LEAGUES`). On the PL, the FPL gives points minute by minute, so a 0
  really means there has been no event worth points *so far*. The MLSZ, however, records the
  points only after the match, so that state never occurs there — on the NB1, "no event
  worth points so far" would be a false promise, and instead the text says that *the points
  only go in at the end of the match*. **The sentence comes from the shared layer**
  (`FunTasy.MESSAGES.duringMatch(leagueId)`), the page does not write it for itself: in two
  copies the two would drift apart.
- **Where the kick-off time is not set yet**, only the date is shown („kezdés: aug. 29.
  (időpont még nincs kitűzve)" (kick-off: 29 Aug, time not set yet)) — the MLSZ writes
  midnight in that case, and printing it as a real kick-off would be wrong.
- **During a live round a dash stands for 0-point players when there is no data on them.**
  There are two such cases: a player who has not played yet (his match has not even
  started), and — **on the NB1 only** — a player whose match is running. The MLSZ records the
  points only after the match (`livePoints: false`), so a 0 there does not mean "scored zero
  points" but "no data on him yet" — honest as a dash. On the PL it is the other way round:
  the FPL gives points minute by minute, so a 0 in a running match is a real 0 and stays
  **a number**. The explanation of the dash can be read with the mouse (`title`).

### Player profile
In both leagues. Clicking a name in the **Szezon játékosai** list opens the player's
profile. At the top the basic data (position, club, Hungarian/u21 marking, total points, how
many rounds there is data for, and in how many of them he was in someone's squad), below it
one row per round: **opponent, the match score** (always in home–away order, with whether he
played at home or away), the player's **own points**, and **which manager** had him — as a
starter, on the bench or as captain. In a salary cap league the same player can be with
**several managers** in one round: then all of them are listed, each with its own role. If
nobody had him, a short dash stands there — and for a future round nothing, because we do not
know who *will* have him.

At the end of the list come the **league-relative shares**: in what percentage of the round's
squads he was (*keret* (squad)), in how many he was a starter (*kezdő* (starter)) and in how
many captain (*kapitány* (captain)). The denominator is the round's **actual** number of
squads — as many as there are saved squads of managers —, not a hard-coded 8, so a missing
squad does not pull the share down. **The captain counts as a starter too**, so the three
numbers nest: squad ≥ starter ≥ captain. For a player nobody had, there is no share block.

**How far does the list go?** The **PL profile lists every round of the season**: the played
rows with points and result, the future ones with opponent and venue (from the `fixtures`
array of the Draft `element-summary`). The **NB1 profile shows only the rounds played**,
because there the future pairings are not available (see section 4) — empty rows without
opponent and date are not printed.

**Several matches in one round.** The row shows **all** of the club's matches in that round,
not the first one. In the PL this is the double gameweek (a club plays twice), in the NB1 a
rescheduled, earlier postponed match can bring it about. For one match the opponent and venue
are in the name cell and the score in its own column (so the numbers line up); for two, both
matches with their scores go into the name cell, and the score column stays empty. Better for
the rare case to wrap differently than for the second match to disappear.

**Where the data comes from, per league.** In the NB1 the per-round points come from the
squad history (for rounds when nobody had the player, from the MLSZ points breakdown), the
opponent from `meccsek.json`. In the PL both come **from a single request**: the Draft
`element-summary/{id}` gives the points per round and a field of the form `"BHA (A) 4-0"`,
which holds the opponent, the venue of the player's team, and the score in **home–away**
order. The latter was measured (`naplo/fpl-profile.txt`): on 25 away matches that were not
draws, all 25 confirmed it, and none the "player's team first" reading — with the wrong
choice every away result would have been reversed.

**If `element-summary` is not available**, the PL profile works from the **stored** points
per round (`draft_history.json` → `pts`): the points and the role (starter/bench) appear,
only the opponent stays empty. Without this fallback every row would be a dash and „Pont
összesen" (Total points) 0 — while the data is in the repository. The NB1 profile is built
from the stored data as well, and fills in the itemised breakdown from the API afterwards;
the two leagues work the same way in this.

**This share only appears in a salary cap league**, and the league's `type` field decides
that (`funtasy.js` → `LEAGUES`), not the league's id. In a draft league a player can be with
exactly one manager — or nobody —, so *keret* would always be 1/N or 0, and there is no
captain at all: the three numbers would say nothing. The name of the role (kezdő / pad /
kapitány — starter / bench / captain) still shows there. So the shared layer does not get
ready Hungarian text but the fields `{nev, kezdo, kapitany}` — that way both the wording and
the share calculation live in one place.

Clicking the row opens the usual accordion with the **itemised points breakdown** and the
club's match — the same request and the same cache as in the squad view.

Two things that are easy to misunderstand, so this is how we do them:

- **The points are the player's, not the team's.** The stored weekly points already contain
  the captain's doubling and the bench halving; the profile **reverses** them, because
  otherwise the same performance would show a different number depending on who had the
  player. For the bench the API rounds to two decimals after halving (0.75 → 0.38), so plain
  doubling would be off by 0.01 — so the result is rounded to the nearest quarter. This is
  measured to be correct: over 377 compared rounds the players' base points were **always a
  multiple of 0.25**.
- **When nobody had the player**, his points are not stored anywhere — then (and only then)
  a request goes to the MLSZ points breakdown endpoint. The profile **does not wait** for it:
  it appears at once with dashes, and the points are filled in in the background, **one
  after another**. Fired in parallel, the requests were dropped by the proxy — the profile
  kept loading for minutes, and the drop-down breakdown failed.

### The field's players (main page list)
On the main page of both leagues, at the bottom of the left column. The **whole field** is in
it (NB1: 385, PL: 612 players); by default the list shows the 40 highest scorers — but search
and filtering **always run over the whole field**, otherwise the list would be useless for
exactly what it is for: finding someone further down, and seeing who has him.

Columns: **#** (position in the current view — not a fixed ranking, it just counts after
re-sorting), **Poszt** (position), **Játékos** (player, with the u21 marking), **Klub**
(club), **Kinél van** (who has him now; in salary cap there can be several — a manager is
marked by **monogram**, so four fit, then `+N`), **Keret%** (squad %) and **Ár** (price)
(both NB1 only — in the draft a player is in one squad, and you do not buy players),
finally **Pont** (points).

- **The search** looks in the name *and* the club, and **finds without accents too**
  (`ljujic` → Ljujić): nobody will type a c with a háček into the search box.
- **Every column can be filtered** in its own way: position / club / who-has-him drop-down
  (the values come from the data itself, so a new club or manager shows up in them by
  itself), an upper limit for the price ("what fits"), a lower one for points and Keret%. In
  the „Kinél van" filter **Mindegy** (any) switches the filter off, **Valakinél** (with
  someone) asks whether he has an owner at all, and **Senkinél** (with nobody) brings the
  unowned ones — three different questions. An unowned player's cell shows a short dash, not
  a word: the column is narrow, a label only took space.
- **Every column can be sorted** by clicking its header; clicking again reverses it. Text
  columns sort ascending by default, numeric ones descending.
- **It is paged**: the footer shows where we are (`41–80 / 385`), and the arrows step
  forward and back. Filtering, searching and re-sorting jump back to the first page —
  otherwise a smaller result set could leave us stuck on an empty page.
- **On a phone no column disappears** — the list would then be impossible to filter and sort
  by it. Instead the row **breaks into two lines**: at the top the number, position, name and
  points, below them the club, Keret%, price and „kinél van", with written labels (the
  numbers alone would say nothing). The header cells wrap the same way, so sorting stays
  available for every column. The break is done by a separate element (`.jltores`): `order`
  alone does not break a line.
- **On a phone this is the last block.** There the grid switches to a one-column flex, the
  two wrapper `div`s disappear from the layout with `display:contents`, so the panels become
  direct flex items, and `order` affects them.

Clicking a row opens the player profile.

**The list's rows carry the same `.plr` class** as the rows of the squad view — so they look
the same, but a page-wide `.plr` query (e.g. in a test) counts them too. Queries about the
modal must therefore be narrowed to `#mBody`. (The differences test needs exactly this
scoping, because of the list.)

### Closing changes (both leagues)
According to the official rules, the points exist after every match, but the **weekly total
only becomes final at the end of the round's last match day** — in between, the MLSZ can
still adjust it. The collector applies these adjustments and also logs them
(`zarasok_nb1.json`), because they cannot be reconstructed afterwards.

Both leagues have a „Zárási változások" (Closing changes) panel, **in the same place, with the
same title and the same display**: right column, grouped by manager, each row a position
label, player name + club, the `előtte → utána` (before → after) value and the signed
difference. The player's name opens the profile, the manager's name the squad. Where nothing
changed, the panel says **nem történt változás** (no change) — the drop-down lists every round
so far, not only those with a change, and the pager starts on the **latest** round. The rounds
are in ascending order on both pages, so `‹` steps back and `›` forward. (The two panels must
not differ in this: with opposite orders the arrows of the two panels would lead in opposite
directions.)

**The HTML is built by the shared layer** (`funtasy.js` → `FunTasy.closingList`); the two
pages only pass normalised rows. The reason: written separately, the two panels drift apart
(different title, different layout, different empty text).

What the panel is **about** differs by league:

- **PL:** the FPL finalises the round on the morning after the last match — that is when the
  bonus is fixed and when the automatic substitutions take effect. That is why there is a
  view switcher row there (Mind / Pontváltozás / Cserék — All / Points changes /
  Substitutions).
- **NB1:** the points exist after every match, but the weekly total only becomes final at the
  end of the round's last match day — in between, the MLSZ can still adjust it. There are no
  automatic substitutions, so there is no view switcher row either.

In the NB1 the value is the player's **own** points (captain's doubling and bench halving
reversed), so the same change does not look different depending on who had him. It only
counts as a change for a player whose **match is over**: points ticking during a match are not
news. The same player appears in as many blocks as the squads he was in.

The exception is three known cases of the first three rounds, where only the **size of the
change** is known, not the player. Those rows stand there with the name „Ismeretlen játékos"
(Unknown player) (`nk:1` flag, not clickable, without `előtte → utána`, only with the signed
difference), with an explanation printed under them.

The panel only appears when it has data: a permanently empty box would suggest that something
is missing.

### The open points breakdown survives the refresh

The match and squad views **refresh after they are drawn**: the minute-fresh squad, the minutes
played and the live points arrive. Each time, the whole content of `#mBody` is rebuilt — and
an open accordion would disappear from under it. To the user it looks as if it **closed by
itself** after „Bontás betöltése…" (Loading the breakdown…), and has to be opened again.

So every such redraw goes through `FunTasy.accPreserve`: it remembers which row was open (by a
key built from its `data-*` flags, independent of order) and what was in the panel, and puts
it back after the redraw. So there is **no flash and no new request** either.

**Only a finished panel may be preserved.** Putting everything back — the error message too —
makes a transient network error **stick**: the row stays open, and the next click closes it
instead of retrying, so the breakdown only comes back after two clicks. So the panel **carries
its state in a flag** (`data-allapot`: `tolt` (loading) / `kesz` (done) / `hiba` (error)),
it is not guessed from its text:

- `kesz` → put back unchanged;
- `tolt` → the old request would land on a stale row, so loading **restarts**;
- `hiba` → **not** put back; the row closes, and one click retries.

**The error message gives the reason too.** The fetcher (`FunTasy.makeFetcher`) tries several
routes — the site's own Worker, a direct request and CORS proxies, see "The CORS proxies are
interchangeable" —, and writes into the error message which one failed and why
(`direkt:CORS · corsproxy:HTTP 429 · allorigins:időtúllépés` — időtúllépés = timeout).
Without it the accordion would only say „A bontás lekérése nem sikerült" (Fetching the
breakdown failed), from which neither the user nor the developer could tell whether it is the
network, a proxy or a changed API. The reason is shown faintly under the text.

This occurs in several places in both leagues (live squad, minutes refill, live points), so the
mechanism is in the shared layer — written separately, it would be missing in exactly one
place. Pinned by: `tests/accordion-preserve.test.js`.

### Navigation inside the modal
The modal works like a small browser: clicking the rows of the lists replaces the content
(e.g. Fordulók → the two squads of a match), and the **‹ vissza** (back) button that appears
in the header steps back to the previous view. ×, clicking outside and Escape always close the
whole thing. There is no modal in a modal. It works the same way on both pages.

### Mobile
Fully responsive: no horizontal sliding, and **every column is kept** — the tables scroll in
their own box, with a sticky name column. On a phone the modal is full-screen, with a sticky ×
button.

---

## 2. Files

| File | Role |
|---|---|
| `index.html` | **Home page: league picker.** It draws the cards from the `LEAGUES` list of `funtasy.js`, it loads no data of its own. |
| `nb1/index.html` | The FunTasy NB1 page (formerly the root `index.html`). Only the page-specific HTML + JS; the schedule is hard-coded in the `SCHEDULE` constant, the managers in `MEMBERS`. |
| `pl/index.html` | The FunTasy PL page (formerly `draft.html`). |
| `draft.html` | Redirect from the old PL address to `/pl/`. New links must not point here. |
| `funtasy.css` | The shared stylesheet (all three pages load it). |
| `funtasy.js` | The shared engine: table, match panels, matrix, live marking (`FunTasy.create(...)`), the points breakdown accordion and the **league list** (`LEAGUES`), from which the league switcher bar and the home page cards are made. |
| `results.json` | Archive of the H2H results: `{updated, provisional:[...], schedule:{"1":[[hazai,vendég,hp,vp],...]}}` (home, away, home points, away points). The page loads from it, overriding the hard-coded schedule. `provisional` is the list of rounds not closed yet. |
| `squads.json` | The squads of the latest available round (`{updated, round, squads:{név:[játékos,...]}}`) — the source of the „Aktuális keret” tab; `round` says which round they belong to. On top of the bookmarklet's fields, a player record holds `id` (MLSZ player id, for the points breakdown), `played` ("played yet?"), `start` (the kick-off of his match in that round), `vege: true` (his match is over, even if the points are not processed yet) and — if the club has no match in the round — `nogame: true`. The page tolerates older records without these fields, but the collector does not leave them that way: a round whose records have no `played` is fetched once more together with the match list, and the missing fields are filled in. |
| `squad_history.json` | Squad snapshots per round (`{updated, rounds:{"4":{név:[...]}}}`) — the source of the „Szezon játékosai” tab. The record format is the same as in `squads.json`. |
| `naplo/` | **Measurement archive and the article tools** (see `naplo/README.md`). It holds the raw logs of one-off measurements (`*-probe.py` + `*.txt`; their conclusions are in this README: 3/b, "Automatic substitutions at the round's close (PL)", "Who is still on the pitch (PL)", "The three states of bonus points (PL)"), and the ACTIVE tools of the Nemzethy Sport articles: `article-prep.py` (the first step of every piece), `colour-check.py`, the harvest scripts (`*-harvest.py`, `timeline.py`), the rule files (`round-pipeline.md`, `kele-janek.md`, `summary-voice.md`, `colour-taxonomy.md`), the per-round colour tables (`nb1-colour-<round>.json`, `pl-colour-<round>.json`) and the per-league background facts (`nb1-background.json`, `pl-background.json`). Every probe runs from `.github/workflows/naplo-meres.yml`. |
| `hatekonysag.json` | Line-up efficiency per round (`{updated, rounds:{"1":{név:{sz, le}}}}`) — the source of the NB1 KEZD% column and its match view. The collector recomputes it for every stored round on every run (deterministic). The PL has no such file: there the browser computes it from the squad history it has already loaded. |
| `guardiola.json` | The **Guardiola index** per round: `{rounds:{forduló:{szakvezető:{teny,alt,guard}}}}` (round → manager). `guard` = the current squad's points minus the points of last week's squad in the same round. The collector computes it, because last week's squad needs the raw points of **every** player of that round (`bontasok/<round>.json`, 40 KB per round) — this way the page only needs these few kilobytes. |
| `draft_pontok.json` | The points and minutes of the PL's **whole field** per round: `{rounds:{gw:{element:[pont,perc]}}}` (points, minutes). Needed for the Guardiola index: last week's squad can contain a player who is **no longer with anybody** (there were 11 such players from GW1 to GW2), and then his points would not be anywhere. The minutes are for the automatic substitutions. Only players who played or scored points are included. |
| `draft_guardiola.json` | The same as `guardiola.json`, for the PL, keyed by `liga_id` (league entry id). |
| `verzio.json` | A single number: the current `?v=`. From it the page knows whether it is **stale** — `?v=` busts the cache of `funtasy.js`/`css`, but not of the page's own HTML. If the file says a higher number, the page reloads **once** (`FunTasy.reloadIfStale`). |
| `keretvaltozasok.json` | The data of the **Változtatások** (Moves) tab per round: who went out (`ki`), who came in (`be`), whose role changed (`szerep`), and the difference of the Hungarian rule (`bonusz`) — each with **how much it was worth**. The items add up to exactly `guard`; the `stimmel` (adds up) field says so too. The page derives the number in the table from it. |
| `draft_keretvaltozasok.json` | The same for the PL, keyed by `liga_id` — plus `gepE`/`gepU`: what the **automatic substitution at closing** brought for the old and the new squad. The player items only contain what the **human** decided; the machine's contribution is separate. It stores no player names: the page resolves them from `draft_players.json`. |
| `zarasok.json` | The changes of the round close (`{updated, rounds:{"1":{csapat_id:{pont:[{e,elott,utan}], ki:[...], be:[...]}}}}`) — the source of the main page's „Zárási változások” panel. The collector writes it **exactly once**, in the finalising run: the difference between the stored snapshot before the close and the fresh state. An empty entry is a result too ("the close changed nothing"); without an old snapshot (backfill) it cannot be computed. `ki`/`be` (out/in) are separate lists — the bench flag does not tell who came on for whom, so **no pairing is claimed**; their elements have the form `{e, pts}`, because the incoming player's points tell what the substitution brought (the page still accepts the old, id-only form). GW1 was filled in from the git history. |
| `meccsek.json` | NB1 matches per round (`{updated, rounds:{"5":[{id,h,v,hp,vp,vege,start}]}}`) — the source of the match row above the points breakdown. The collector writes it from the match objects that travel in the squad responses; **a result only goes in for a finished match** (the collector, which runs hourly to every 3 hours, would otherwise preserve a partial score as final). A round with a missing or unfinished match is fetched again with the match list; a complete one only if the round's official points changed (this is the case of a **rescheduled match** — the postponed match is not in the list, so it would not show as "unfinished"). **Not every match of the round:** only those of the clubs that have a player in some squad — that is all the row above the breakdown needs. |
| `jatekosok.json` | **All** players of the field (`{players:{id:{n,t,p,u21,pts,ar}}}`) — the source of the main page list and search. The collector writes it, from one request. |
| `bontasok/<round>.json` | The **itemised points breakdown** of the round for every player (`{round, bontasok:{cp-id:[{n,v,p}]}}`): what made up the weekly points — goal, assist, minutes played… The collector fetches it **once**, when the round closes, for all 385 players, and again after an MLSZ correction. It deliberately has no `updated` field (see `keretek/`). |
| `zarasok_nb1.json` | Per round, the **post-match point adjustments** the MLSZ applied before finalising the round. Its shape follows the PL `zarasok.json`, so the same display can serve it: `{rounds:{forduló:{szakvezető:{pont:[{n,cp,pos,tm,elott,utan,d}]}}}}`. A row with the `nk:1` flag means the player is not known: it shows „Ismeretlen játékos" (Unknown player) instead of a name, and `dl` (the size of the change) instead of `elott`/`utan`. A rare event in practice: the file exists as an empty skeleton and only grows when an adjustment really happened — the panel, too, only appears then. |
| `arak.json` | The **changes** of the prices (`{arak:{id:[[dátum, ár], …]}}` — date, price). It only grows when a price really changed. |
| `articles.json` | The league's **published** pieces (`{updated, leagues:{liga:{forduló:{summary|preview|elemzes:{kulcs:{text:[bekezdés,…], short, source, kozzetett}}}}}}`). **There are three kinds.** The `summary` and the `preview` each belong to a pairing; their key is `"Hazai|Vendég"` (Home|Away). The `elemzes` — *Kele Janek elemez* (Kele Janek analyses), the weekly column — belongs to the round, not to a pairing: its key is **its own title**, without `|`, and that is exactly how it is known to have no opponent (`FunTasy.articleList`). `text` is the full text by paragraph. `short` is the one sentence shown in the closed strip — the column **has none**: there the lead would be the subtitle itself and would break the arc of the text; then the first paragraph takes its place. `kozzetett` (published) is the ISO timestamp of going live, and **it is the page's order**: the paper does not go by round but by time (see *5/a7. The magazine is in publication order*). Machine guard: **D15** — a published piece cannot be without it. On the match sheet a **closed** strip reads it (`FunTasy.matchArticle`): the text is a one-off entertainment, the numbers under it are what matters, so it must not push them down. **The summary only appears for a closed round** — until then the points can still move (NB1: post-match adjustments, Draft: separate finalisation), and an "X won by this much" text would lie. This does not apply to the preview. The gate **is closed by default**: a caller that does not say the round has closed cannot let out an early summary. The pieces are currently **written by hand** (`source: "manual"`); the field is there so that later generated text can be told apart. **An article may only be made from CLOSED data**: a summary only of a final round, a preview only of the coming one. A text written DURING a round works from numbers that are still moving — a preview made that way claimed that someone had won the match he lost in the end. Machine guard: `tests/doc_checks.py` **D11**. Unpublished text does not go into the repository: the article is written straight here after approval. |
| — | **Rating the pieces.** At the bottom of an opened article the piece can be rated from one to four. The two top grades are a single tap — whoever is satisfied should not have to work for it. The two lower ones **ask for a reason, in the viewer's own words**: a text box opens in place. Ready-made reasons are deliberately not offered — they would give back our own categories, and exactly the sentence we did not think of would be left out. „Elküldöm” (Send) does not offer itself while there is nothing to send; next to it, more quietly, the way out („Kötekszem, de indokolni már nem fogok” — "I'm nitpicking, but I won't give a reason"), which takes the grade but not the reason. The panel opens **inside** the strip, not in a new layer: the opinion is about what is under it, which must not be covered. The rating goes to the Worker (`POST /ertekeles`), and is kept in KV under the key `ert/<cikk>/<eszköz>` (article / device) — one device rates a piece once, a re-rating overwrites its own. To read them back: `GET /ertekelesek`. |
| `valtozasok.json` | The entries of the changelog (`{bejegyzesek:[{datum, tipus, ligak, cim, leiras}]}`). **Written by hand**, not filled by a collector. **One feature = one entry**: what the viewer sees as one thing is one entry, even if it has several parts and was finished in several steps — it is not split into as many posts as the parts that were done. So `leiras` (description) can be **several paragraphs** (separated by an empty line), and the changelog page displays it that way. Until the feature is finished, the entry waits in `valtozasok-vazlat.json`. Splitting is checked by case **D4/b** of `tests/doc_checks.py`. |
| `valtozasok-vazlat.json` | **Not yet published** changelog entries, in the same form. The changelog page does not read it; a finished entry moves from here to `valtozasok.json`. |
| `nemzethy/index.html` | The **Nemzethy Sport** — *Heti Funtasy Magazin* (Weekly Funtasy Magazine). **It has two modes.** `?liga=nb1` (or `pl`) is **that league's paper**: in the league's own colours, with its name in the header, and only its pieces — it is opened from the league page's top bar, so the reader does not drop out of the league's world. Without a parameter it is the **combined edition**, with a league filter; the home page points to it in a highlighted row. In both, every piece in full text, **in publication order** — the most recently published first, regardless of league and round; so there is no league heading, the league's name is in the piece's header. Within a piece: kind, the pairing (for the column its own title), the short version as the lead, then the body. Filters in a single bar: **league, manager, round, kind — four separate controls**, freely combined (one person can be asked about within one league), next to them the hit count and a clear button; each only offers the values that really exist next to the other filters, so it cannot be set to an empty result. In the league's own paper the league filter drops out by itself (with one value the drop-down stays empty). Managers are listed **per person**, not per name: the two leagues know the same person by a different name (a nickname in the NB1, a team name in the PL), and someone who plays in both stands in a single row with both names — filtering on them brings up the pieces of both leagues. The linking is in the shared layer (`FunTasy.PEOPLE` + `FunTasy.personLookup`); the combined edition reads the PL team names from `draft.json` for it; in the league's own paper there is nothing to link, and that request is skipped. **The same gate** as on the match sheet: the summary of a round not closed does not show here either — the selection is done by `FunTasy.articleList`, so the two views cannot drift apart in what may be shown. Under every piece there is the rating strip, and a „Másolom” (Copy) button that puts the **full article** and the link to it on the clipboard (not just the lead — whoever copies takes the text). The text column's width is set in pixels (`ch` depends on the font, so the whole page would re-wrap when the web font arrives). **It has no `content-visibility`, deliberately**: while scrolling, the real height replaces the estimated one, and the page's height changes under your finger — measured eight times during one scroll to the end, up to 361 pixels at once. The top bar shows **two levels**: the leagues are alternatives to each other, but the paper is part of a league — so exactly one item is always lit (where you are), the paper's button does not disappear when you are on it, and from there the league's dot takes you back to the league page. |
| `valtozasok/index.html` | The changelog page („Mi újult meg?" — What's new?). |
| `collect.py` | GitHub Actions: collects the H2H results (rankings endpoint) **and** the squads (squad endpoint), determines the round close, fills in missed rounds. |
| `collect_draft.py` | GitHub Actions: the data of the FPL Draft league. It filters out the participants' real names and the `entry_id` (the repository is public). |
| `collector_common.py` | What **both** collectors do identically, in one copy: `stamp`, `write_compact` (atomic write) and `read_stored` (a missing file and a damaged one are not the same). Not a drawer for shared things - exactly these three live here, and all three are about one thing: that the **accumulating** files survive an interrupted run. While there were two copies, one could forget the guarantee, and it would only have shown **after** an interrupted run. See *An interrupted write cannot be read as "no history"*. |
| `draft.json` | The data of the FPL Draft league (participants, schedule, results) — the source of `pl/index.html`. |
| `draft_picks.json` | **The draft itself**: who picked whom, in which round and at which place (`{updated, league, rounds, picks:[{r, p, i, e, t, auto, sec}]}`). `i` is the overall pick number (1–150), `t` is our team id, `auto` says that **the machine picked** instead of the manager. The draft happened once and never changes, so it is not written by the collector but made by hand (`naplo/draft-picks-harvest.py`). There are two ids: in the response a team appears under its real FPL entry id, while ours is the league-entry id — the mapping comes from the league data, and the real id **does not go into the file**, just like the names. It is for colour: the first-round pick that was sold, or the goal of the draft's last pick. |
| `draft_players.json` | FPL player master data: `{players: {id: {n: név, t: klub, p: poszt, pts: pont}}, teams: {csapat_id: rövidnév}}` (name, club, position, season points; team id → short name). `pts` (the season points) is for the main page player list. `teams` is needed to resolve the team ids of the fixtures response (whose match has started). |
| `draft_squads.json` | The current FPL squads (ownership): `{updated, squads: {liga_id: [játékos_id,...]}}` (league entry id → player ids). |
| `draft_history.json` | FPL squads per round, with points (`{updated, rounds:{gw:{liga_id:[{e,b,pts},...]}}, veglegesek:[...]}`) — accumulating from the start of GW1. The **`veglegesek`** (finals) list says which OLD rounds are final: the collector does not fetch those any more. It fetches the current round on every run, after the close too (see "3/b. CLOSING"). |
| `keretek/<round>.json` | The squads of one round in a separate file (`{round, squads}`). The match view downloads **this**, not the whole history. |
| `.github/workflows/archive.yml` | The collector's workflow: `collect.py` + commit. **On match days (Thursday–Monday) hourly at :17, on Tuesday–Wednesday every 3 hours at :17** (UTC) — see *Why hourly on match days*. |
| `.github/workflows/draft.yml` | Workflow running `collect_draft.py` + commit: **every 3 hours at :47, plus hourly at :37 between 07:00 and 13:00 UTC** (and it can be started by hand) — see *The FPL Draft data*. |
| `.github/workflows/naplo-meres.yml` | **Manual probe runner**: runs one `naplo/*.py` from Actions (the development environment's network blocks every external source), and commits what the probe wrote to the given branch. Its inputs: `script`, `branch`, `environment` (one `NAME=value` per line, e.g. `HARVEST_EVENT=5`). **This one workflow serves every probe** — no separate file is made per probe: that approach produced fourteen near-identical copies, three of them with a mistyped `git add` path, which silently lost the probe's result. |
| `wrangler.toml` | The deploy config of the site's own Cloudflare Worker (`tartalek/proxy-worker.js`): Cloudflare runs `npx wrangler deploy` after every push to `main`, which reads this file. It also holds the binding of the Workers KV namespace (`TAROLT`) for the stored responses; the namespace id is not a secret (see "The last known score"). |
| `tartalek/` | Not a spare-parts drawer only. **`tartalek/proxy-worker.js` is the LIVE Cloudflare Worker**: the site's own CORS proxy (the first route of every live fetch), the store of stored responses (`/tarolt`) and the ratings endpoint (`POST /ertekeles`, `GET /ertekelesek`) — deployed from `wrangler.toml`. `tartalek/kele/` holds the voice corpus of the model writer of the weekly column (the author's own football texts, saved by `naplo/kele-voice-probe.py`). The rest is the fallback: the bookmarklet (`bookmarklet.txt`, its source `bookmarklet-source.js` and its builder `bookmarklet-build.py`), its guide (`SQUAD-SAVE.md`) and the description of the obsolete manual backfill (`BACKFILL.md`). The website and the collectors read no data from here. |
| `tests/` | The test suite: Python collector tests, browser tests and the documentation checks (`tests/doc_checks.py`), run together by `tests/run_all.sh` — see `tests/README.md` and section 5/b. |

---

## 3. How the data is updated

### Everything runs automatically (GitHub Actions, hourly on match days)

`archive.yml` runs `collect.py`, which updates **everything**, with nothing to do by hand:

1. **H2H results** from the rankings endpoint (official round scores — the table's only
   source).
2. **Rechecking old rounds**: by default the rankings only return the two latest rounds, so
   we would not learn of a later correction of an old round by ourselves. So every run
   fetches **four old rounds** again, in rotating order (see *Self-repair: when the MLSZ corrects, the collector corrects too* below).
3. **Squads** from the squad endpoint: the current round (with live player points), the last
   closed one, every missing round — and every old round whose score changed in this run
   (because then the squad snapshot is out of date too). **An old round fetched again cannot
   become "provisional" because of this**: only the round being played now or the one that
   has just closed can become provisional. Without this, a single failed squad fetch could
   take a round played weeks earlier out of the table.

   **Incomplete data does not mean "still running".** The collector treats "we know the round
   is still running" and "we could not fetch it" separately. Where it could not evaluate
   (403, failed squad fetch), the round's **earlier** provisional state stays in force — it
   neither makes up a new one nor deletes an existing one on a guess. Without this the data
   could go wrong in two directions: a faulty run either took a closed round out of the
   table, or — worse — emptied the `provisional` list, and then the live round's **partial
   result would have counted as final**.
4. **Round close**: a round is final when every player **who has a match** has finished his
   match. This takes two signals together: `is_played` **and** the match list's `completed`
   status. Relying on `is_played` alone is wrong: the MLSZ flips it to true already *during*
   the match, so as soon as the round's last match started, everybody "played" — the
   collector would judge the round closed, and the **half-finished result would go into the
   table as final**. A player **with no match** in the round (postponement) does not count —
   see below why. Behind it there is a safety net: if the player-level picture does not come
   together but the MLSZ has already moved past the round, the collector closes it anyway.
   While the round is not final, it is in the `provisional` list, and the page does not count
   it in the table.
5. **Cross-check**: the score computed from the squads is compared with the official one. If
   they differ, it **does not write a warning, it corrects**: it fetches the official value
   for that round again, and applies it.

#### Why hourly on match days (measured)

`collect.py` **can fetch a squad at the earliest at the moment the market closes** — until
then the squad endpoint answers 403, and the collector rightly skips the round. The market
closes roughly two hours before the round's first match. If the run after that is missed, the
round's squads are not published until the next one comes.

A measured case: round 9's market closed on Saturday around noon, the next scheduled run never
came, and the eight squads were not published for **four and a half hours** — while the page
said „Naprakész" (Up to date). The raw measurement: `naplo/nb1-round-state.txt`.

Two measurements set the schedule:

| what | what came out |
|---|---|
| NB1 kick-offs of rounds 1–8 (47 matches) | Sunday 43%, Saturday 32%, Friday 17%, Monday 6%, Thursday 2% — **not a single match fell on Tuesday or Wednesday**; kick-offs fall between 14:00 and 20:00 local time |
| how the `17 */3` schedule is actually kept | of the eight promised runs a day, **3–4** happened, with regular **7–9 hour** gaps — GitHub drops more than half of the scheduled starts |

So **Thursday to Monday hourly** (at :17 UTC), on Tuesday–Wednesday it stays every three hours
(at :17). The hourly schedule does not give 24 runs — what it gives is that **a dropped start
costs one hour, not three**. Tuesday–Wednesday stays sparse because there is nothing to catch
then.

### The FPL Draft data (draft.yml)

`draft.yml` runs **every 3 hours at :47**, plus **hourly at :37 between 07:00 and 13:00 UTC**.
Only a run can notice the close of a PL round (`current_event_finished`), and the FPL closes
the round on the day after the last match, **in the morning**: measured, it flipped between
08:03 and 08:23 UTC, and the collector recorded every close so far between 08:52 and
13:01 UTC. With a three-hour schedule alone — together with the starts GitHub skips — the close
would stay unapplied for hours, and the round would show as live on the page. For the rest of
the day there is nothing to catch often: the browser fetches the live score itself.

Besides the league data, `collect_draft.py` collects the player master data, the current
squads (ownership) and — from the start of GW1 — the squads per round, with points.
The participants' real names and `entry_id` can never go into the repository (a filter before
saving).

### Live refresh from the browser (both pages)

On load both pages fetch minute-fresh data through CORS proxies: the NB1 fetches the results
from the rankings endpoint (and the squads on click), the PL the live points per player, from
which it sums the match scores. On error the stored state (refreshed every few hours) stays.

**It fetches again when you return** (`FunTasy.onVisibleAgain`). Fetching only on load, once,
is not enough. On desktop it would not show, because there one usually returns with a fresh
load — **on mobile, however, one does not reload**, only switches back to the tab, which the
browser restores from memory. The main page's match list then stays frozen at the load-time
score (39 points), while the match sheet — which has its own fetch on opening — already shows
the fresh one (38). The helper reruns the refresh on the `visibilitychange` event, the
bfcache `pageshow` and `focus`, at most every 30 seconds, and never in parallel.

**There is deliberately no timed refresh:** a tab left open sends no requests through the
proxies (data and battery on mobile). If you want to watch it change, you have to return to
the tab — or reload it.

### The last known score — "if somebody has already fetched it, let me see that"

**The requirement:** *"let me not see older data than the latest fetch."* You open it on the
phone, it refreshes nicely; an hour later on the computer you have to wait through the same
refresh, and meanwhile you stare at an older score.

**Why it happens.** Our only shared state is the JSON files in the repository, which the
collector writes every few hours. The live number, however, is computed by every device in
its own browser, and the result stays there. The phone's work is not written back anywhere.

**What does NOT solve it: a cache.** An expiring cache only helps if you arrive within the
expiry; otherwise it discards the copy, and you start from scratch. Stale-while-revalidate is
wrong the other way round: after a long pause **the first to arrive** gets the old copy — that
is, exactly the one we would want to help.

**The solution: a store in the Worker.** Not an expiring cache but a store, which keeps the
response until a better one comes. The Worker — which already sits in the path of every fetch —
remembers the response that **it fetched itself** (so there is nothing to forge: the browser
does not send data up), and on load the page asks for all of it in **a single request**
(`/tarolt?url=..&url=..`), before the live fetch.

| | |
|---|---|
| What it stores | what changes **rarely**: NB1 live points (2-4× a day), PL squads and league data (fixed per round) |
| What it does not | the PL live points — they change every minute, the last response is worthless a minute later |
| When it writes | **only on change** — otherwise the KV's free allowance of 1000 writes a day would run out in a few hours |
| What it costs | NB1: ~30 writes/day · PL squads: 10-20 writes/round |

The status bar shows the time of the **fetch**, not the current time: „Élő állás — 8. forduló ·
frissítve 21:27" (Live score — round 8 · updated 21:27) states exactly that this is what
anybody last saw — not that we have just checked.

**Two lines of defence.** If the KV binding were ever missing (deleted namespace, another
account), the Worker works exactly as without the store, and the page goes the usual live way —
a separate test checks this, so that nothing stops because of it. And the stored score never
replaces the live fetch, it only comes before it: `refresh` runs after it just the same, and if
something changed in the meantime, it overwrites it.

The namespace id is in `wrangler.toml`. It is **not a secret**: by itself it grants nothing,
its content needs the Cloudflare account — just as the worker's URL is in the repository too.

**Where the rule would live in two places, it does not live twice.** The rankings URL is built
in a single place (`rankingUrl`), because the same URL is the address of the fetch **and** the
key of the store — if it were assembled in two places, it could drift apart unnoticed, and the
store would never hit. Reading the response (`readRanking`) and drawing it (`applyLive`) are
also shared by the live and the stored path.

**Measurement.** The Worker cannot be reached from the development environment (the network
does not let out to `workers.dev`), so its logic is checked with a fake KV
(`tests/worker-store.test.js`), the page side from a browser
(`tests/stored-score-first.test.js`), and the real end-to-end measurement runs from GitHub
Actions (`naplo/storage-probe.py` with the shared `.github/workflows/naplo-meres.yml`).

### The NB1 live fetch runs in two rounds, not eight (measured)

The NB1 live score is put together from **a separate MLSZ request per manager**: 8 people =
8 requests, and during a live round this reruns every minute. Sent **one after another**,
each awaited, that is eight round trips in a row. That is the main reason the page refreshes
"slowly", not the cache.

The ratio is especially bad because the MLSZ **gives no points during a match** (`livePoints:
false`): the points go in after the final whistle, so the eight round trips every minute
would be for data that changes 2-4 times a day.

Now the **first request goes alone**, the remaining seven **at once**. The first stays
separate because the fetcher learns from it which proxy route works (the "proven" route of
`FunTasy.makeFetcher`); if all eight started at once, on a bad day all eight would try the
whole route list — such days happen.

Whoever drops out of the parallel round is **fetched again one by one**: a rejection of a burst
of requests must not leave a hole in the score (the missing manager's match would otherwise be
without a score in that round).

Measured with the test, with a 250 ms delay per request: **513 ms** instead of ~2000 ms
sequentially. Pinned by: `nb1-parallel-fetch.test.js`.

### The CORS proxies are interchangeable — a free proxy can disappear (measured)

The browser cannot reach the MLSZ/FPL API directly (the response has no
`Access-Control-Allow-Origin` — measured, not assumed), so every live fetch goes through a
proxy. Two free proxies can **fail at the same time**: `corsproxy.io` switched to 401 (the
service was tied to registration), `allorigins` was overloaded (522). With every live request
depending on those two, the live part of **both leagues** — points breakdown, live points,
live squad — stopped at once. The stored data was not affected.

The lesson: a free proxy can disappear at any time, so **several independent routes are
needed**. The route order in `funtasy.js` (`makeFetcher`) is: `sajat` (the site's own
Cloudflare Worker, `OWN_PROXY`) → `direkt` → `proxy.cors.sh` → `allorigins /raw` →
`allorigins /get` (this one returns the response **wrapped**, `{contents: "..."}` — the fetcher
unwraps it) → `cors.lol` → `corsproxy.io` (at the end of the list, in case it is let back in).
The own Worker comes first, even before `direkt`, because the direct route to these two APIs
never works from a browser (they send no CORS headers) — trying it first would be wasted. The
order of the public proxies follows the run that measured nine candidates
(`naplo/proxy-probe.py` → `naplo/proxy-probe.txt`). After the first success the fetcher stays
on the proven route. The chain is pinned by `tests/fetcher-fallback.test.js` — including exactly this
failure: with corsproxy 401 + a silent allorigins, cors.sh has to serve.

If every route fails again, the points breakdown's error message lists which one failed and why
(`direkt:CORS · corsproxy:HTTP 401 · …`) — it can be diagnosed from this, handy in a screenshot
too.

**Own proxy (Cloudflare Worker).** The durable solution is our own intermediary: the Cloudflare
Worker in `tartalek/proxy-worker.js` (free plan, no bank card needed, the daily allowance of
100,000 requests is many times our traffic). The worker **is tied to the repository**: after
every push to `main`, Cloudflare runs `npx wrangler deploy`, which deploys the worker code
according to `wrangler.toml` in the root — code never has to be copied by hand, the worker
changes together with the site. It only serves the two known APIs and only for this site, so
it cannot be abused; MLSZ responses are cached for 60 seconds by Cloudflare's edge network, so
however many people watch the same thing, one request a minute goes to the MLSZ. The Worker's
URL is in the `OWN_PROXY` constant of `funtasy.js`, and it is the **first** route of the
fetcher. If the constant were empty, the fetcher would skip it and the public proxies would
carry the traffic — they stay in the list as fallbacks either way.

### The fonts cannot stop the page (measured)

The three font families (Inter, JetBrains Mono, Archivo Black) come from Google Fonts. A plain
`<link rel="stylesheet">` is **render-blocking**: until Google answers, there is *nothing* on
the page. Measured: if `fonts.googleapis.com` is unreachable, `DOMContentLoaded` comes at
**12,640 ms instead of 57 ms**. On mobile, on a weak network, that is exactly when one wants
to check the score.

So the stylesheet loads **asynchronously** (`media="print"` + `onload="this.media='all'"`,
with a `<noscript>` branch for those without JS), and `fonts.gstatic.com` gets a `preconnect`
too — the font files come from there. With the same measurement the page draws in **216 ms**
even if the font service does not answer at all.

The other half is in the CSS: the three families have **fallback stacks**, and each goes
through a variable (`--fo`, `--mono`, `--cim` in `:root`). Without them `display=swap` would
first paint with the browser default (serif Times), with different glyph widths — the table
would jump when the web font arrives. The variables also keep the font names in one place
instead of the **60+ places** they would otherwise be written in.

Pinned by: `tests/webfont-fallback.test.js`.

**Without JavaScript** only the empty skeleton would show — panel titles, empty tables,
without a word of explanation. So every page has a `<noscript>` warning at the top saying
that the browser fills the tables, so JS is needed. The same principle as with the status
line: if something is missing, the page **says so**, the visitor does not have to guess.

### Cache: why the score got stuck on an iPhone

Without cache busting on the live fetches, and with no `cache` option on `fetch`, an iPhone
got back the same player points *however many times it was reloaded*, while another device
already showed the fresh ones. That was a **shared** cache (the CORS proxies'), not the
device's — which is why reloading did not solve it.

It is busted in three layers:

| Layer | How |
|---|---|
| browser | `cache:'no-store'` on **every** live fetch (the JSON files from the repository already had a `?t=` stamp) |
| CORS proxy | the proxy URL gets `&_=<timestamp>`, so the proxy's cache key is always different |
| FPL | the **inner** URL gets `fpl_=<timestamp>` too (the FPL ignores an unknown parameter) |

**The MLSZ's own URL is deliberately left alone**: it is not verified that it tolerates an
unknown parameter, and there `no-store` is enough anyway — there is no shared cache between
the direct request and the MLSZ.

The NB1 points breakdown cache has an expiry too: **60 seconds in a live round** (the
breakdown of a closed round no longer changes), as on the PL.

### „frissítés… 1,2 mp" — against the silent number swap

The match sheet and (in a live round) the squad view **draw with the stored numbers first**,
and when the minute-fresh fetch arrives, they swap them. On a fast network this goes
unnoticed; on a slow one, however, you either look at old data without knowing it, or the
numbers jump under your nose.

No fixed threshold can be chosen well — the fetch time depends on the network and the CORS
proxy, and varies on the same device too. So the indicator **measures itself**: it only
appears if the fetch takes longer than half a second, and shows how long it has been running
(„frissítés… 1,2 mp" — refreshing… 1.2 s; `FunTasy.slowIndicator`). With a fast response it
never shows, so it does not flicker needlessly — with a slow one, the time shown is also a
measurement of what a fetch really costs.

There are three places with such a swap, and all three have the indicator: the NB1 live match
sheet, the NB1 squad view during a live round, and the PL match sheet.

### Round boundary and a closed PL round: the live layer must be dropped

If the round closed since you loaded the page (for example the tab was in the background), the
refresh on returning sets the status bar to up to date — but the match list would keep the
numbers of the last fetch **with the „élő" (live) label**, although a final result belongs
there. So in this case the live layer is cleared, and the list falls back to the stored result
(the collector writes it in on its next run).

The same is needed **at a round boundary**: when the API moves on to the next round, the
previous one has to be let go. Two problems would follow otherwise. First, the old round's
panel would stick with the „élő" marking. Second — and this is the worse one — `LIVEPTS` and
`LIVEFX` are only updated on a **successful** fetch, so if the new round's first fetch fails,
the *previous* round's points would appear as the new one's, labelled as a live score.

### The main page list and the match sheet cannot disagree

The match sheet starts its **own** live fetch on opening, while the main page list only
computes on load and on return. So the list could show 39 points while clicking it showed 38
(the player lost points in the meantime). What the sheet fetches therefore **also updates the
list behind it** (`updateLiveScores`) — two different numbers cannot come out of the same
data, and it costs no extra network request. The same applies to the team's **squad view**,
which also has its own live fetch.

### What is deliberately left inconsistent

After the match ends, until the MLSZ has put the points in, the **row shows 0**, while the
points breakdown tells the truth („a pontok feldolgozása még tart" — the points are still
being processed). A dash is not put there, because the row cannot know whether the breakdown
has arrived — finding out would take a fetch per player (15 players × 8 squads per round).
Since one click on the breakdown reveals the truth, it is not worth the complication.

**The status bar texts are shared** (`funtasy.js` → `FunTasy.statusLine`), so that the two
pages do not speak about the same state in two ways:

| State | Text |
|---|---|
| while fetching | *Élő állás lekérése…* |
| live round, with fresh data | *Élő állás — 5. forduló · frissítve 21:07 (a tabella csak lezárt fordulókból számol)* |
| no round in progress | *Naprakész · ellenőrizve 21:07* |
| the fetch failed, during a round | *Automata lekérés hiba: az állások a forduló végén frissülnek.* |
| the fetch failed, in a quiet period | *Az élő frissítés most nem elérhető — a tárolt állás látható (mentve: aug. 21. 19:14).* |

(In order: fetching the live score…; live score — round 5 · updated 21:07 (the table counts
closed rounds only); up to date · checked 21:07; automatic fetch error: the scores update at
the end of the round; the live refresh is not available now — the stored score is shown
(saved: 21 Aug 19:14).)

Here „frissítve" (updated) is **always the time of the live check**, and „mentve" (saved) the
age of the stored file. The two must not be mixed: if one page printed the file's age as
„Frissítve" and the other the time of the check, the same word would mean two different
things.

### Fallback: the browser bookmarklet

If server-side collection broke (e.g. the MLSZ really blocked data-centre IPs), the squads can
be saved from your browser with the `Keret mentés` (Save squad) bookmarklet — its setup:
[`tartalek/SQUAD-SAVE.md`](tartalek/SQUAD-SAVE.md). The bookmarklet uses a fine-grained
token (only for this repository, only `Contents: Read and write`); in the repository the token
is always a placeholder.

---

## 3/b. CLOSING — what means what, and where it is decided

**Read this before you touch any closing logic.** In this project the word "closed" means
**four different things**, with separate flags and separate consequences. Changing one of them
without knowing the others causes bugs.

| what is closed | league | what decides it | what it affects |
|---|---|---|---|
| **a match** | NB1 | the match list's `status == "completed"` — but only believable together with the time limits of `matchState` | the breakdown's message, the result in `meccsek.json`, the minutes-played row |
| **a match** | PL | `started` → `finished_provisional` → `finished` (three states) | the "vége" (over) of the minutes column, the bonus marking |
| **a round** | NB1 | everybody played (`played` or `nogame`) **and** every match is over; safety net: the MLSZ has moved on (`mlsz_round_over`) | whether it goes into the table or stays `provisional` |
| **a round** | PL | the **`current_event_finished`** field of the `game` endpoint | the automatic substitutions going in, the bonus being final, the status line |

**The PL round close is a single moment, with several flags.** Measured (between 08:03 and
08:23 UTC), all of them flip **at once**: `current_event_finished` → true, the H2H matches to
`finished`, the `event-status` `points` from `p` to `r`, `bonus_added` to true. That is why the
collector reads it from `current_event_finished` and the page's bonus marking from
`points === "r" || bonus_added` — **the same event**, from two endpoints (the Draft has no
`event-status`, it comes from classic FPL). If they ever differed, that calls for a
measurement, not a guess.

**At that moment `current_event` is STILL the old round** — the close is not a round change.
Whoever mixes the two up loses the substitutions (see below).

### What MUST still be updated after the close

| source | how long it is updated | why |
|---|---|---|
| NB1 squad + points | the current **and the previous** round on every run, plus a rotating check of four old rounds (`rounds_to_recheck`) | the MLSZ corrects afterwards |
| PL squad + points | the **current** round on every run (after the close too, until `current_event` moves on), plus every round not in the `veglegesek` list of `draft_history.json` | at the close the FPL makes automatic substitutions, and it can correct afterwards too |
| PL match result | `schedule`/`standings` of `draft.json` from the FPL's own response, on every run | this is the official result, we do not compute it |
| NB1 match result | `meccsek.json` fetches the round again as long as it has a match without a result | partial scores are not stored |

As a by-product, the finalising run **also saves the closing difference** (`zarasok.json`): the
difference between the stored snapshot before the close and the fresh state — the main page's
„Zárási változások" panel lives on it. The snapshot is at most 3 hours older than the close;
according to the measurement (GW1) nothing changes between the final whistle and the close, so
this difference really is the work of the lockdown.

**What you must never do:** do not remove the rule "the current round is fetched on every run"
on the grounds that the round has already closed. That rule is **not** about the close, it is
about later corrections — otherwise the week after the close would be blind. A test written
together with such a change can pin down the wrong behaviour instead of catching it, so a
passing test proves nothing here.

**Naming.** In `collect_draft.py` "finished" (`finished` in `transform_details`) belongs to a
**match**, so the list of final rounds has a different name: `veglegesek` (in the code
`finals`). The same trap existed with `.pos`/`.ppos` and `.meccsfej`: if a word already has a
meaning in the code, do not give it another one.

## 4. The MLSZ Fantasy API — what is known about it

Base URL: `https://fantasy-api.mlsz.hu/competitions/3/`
There is no official documentation; everything below was established by experiment.

### Rankings
```
GET /rankings?include=user_team.user.id,summary_statistics,ranking,rounds,competition_rank
    &page=1&per_page=20&filter[search]={felhasználónév}
```
Returns: `user_team.user.id`, `user_team.round_statistics[]` (`round_id`, `round_number`,
`points`), total points, rank. (`{felhasználónév}` = the username.)

**By default it only returns the last closed and the current round.** An older round can be
fetched with the `&filter[round_id]={rid}` parameter (the response contains that round **and**
the one before it) — so the official points of a missed round can be filled in afterwards.

### Squad (works from anywhere — if you ask the right way)
```
GET /user-team-players-history?include={INCLUDE}&filter[user_id]={id}&filter[round_id]={rid}
```

**Four pitfalls, each of which cost hours:**

1. **`filter[round_id]` is mandatory.** Without it, 403 Forbidden. (It used to work without it;
   the API was tightened mid-season, which is why it can look as if it "suddenly broke".)
2. **`round_id = 75 + 2 × round number`** (1→77, 2→79, 3→81, 4→83, 5→85). With this the
   **squads of earlier rounds can be fetched retroactively too**, not only the current one.
3. **The `position` relation only comes back if you request `position.alternatives` too.**
   Without it the `position` field is simply missing from the response, with no error message.
4. **The `competition_player.current_round` relation only comes back for a live round with an
   explicit include** (for a closed round it appears without it too). It supplies `is_played`
   (the "played yet?" flag and the round close) and `first_played_at` (the kick-off of the
   player's match in that round) — so it is a mandatory part of the include.

**Working include (verified):**
```
position,position.alternatives,competition_player,competition_player.team,
competition_player.countries,competition_player.current_round,summary_statistics
```

**Important:** the name is **directly in `competition_player`** (`first_name`/`last_name`),
NOT in a nested `player` object. The position is `position.monogram` (K/H/KP/CS).

### Who is not playing in the round (the match list)
The `competition_player.current_round.games` include gives, per player, the club's match **in
that round** (`start_at`, `status`, `round_number`). "No match" comes **in two forms**, and both
have to be handled:

1. **An empty list** — this is what comes for the live round (measured: Honvéd, round 5).
2. **A match of another round** — for an old round the API falls back to the club's **latest**
   match instead of the missing one. The match itself gives this away: its `round_number`
   field has the form `"3F"` / `"5F"`, and if it does not point to the requested round, the
   club has no match in it. (Measured: for ETO players fetched for round 3, the match's
   `round_number` is `"5F"`.)

**Important trap:** `first_played_at` is unusable in both cases. It either points to the club's
**next** match — this caused the "strange kick-off time" error (Csontos, round 5: 29 Aug 00:00,
which is in fact the date of round 6) —, or to a **midnight placeholder**, whose day may already
be over: for the round 3 ETO players `2026-08-15T00:00`, which made the page say weeks later
that „a meccs még nem kezdődött el — kezdés: aug. 15." (the match has not started yet —
kick-off: 15 Aug). If the placeholder's day has passed, the date is no longer a kick-off time;
it means the match was called off and no new date was set.

**The cost of the include depends on the round** (measured, 15 players):

| The round's state | Base | With `games` |
|---|---|---|
| live (matches `scheduled`) | 17.8 KB | 19.7 KB |
| closed (matches `completed`) | 17.5 KB | 118.8 KB |

The reason for the difference: next to a **played** match the API also includes both teams'
full objects, with the club logo as base64 image data. So in the normal case the collector
requests the match list **only for the live round**; for the closed ones the flags saved during
the round are kept (`collect.py` → `inherit_match_flags`). There is one exception: a round in the
old format (no `played` in the records) is fetched **once** together with the match list, so
that the missing flags get in.

#### The two clubs have to be requested separately (measured)

For a live round the match object is **only** `id`, `start_at`, `status`, `home_score`,
`away_score` and `round_number` — **without the clubs**. The collector then wrote `"?"` into
`meccsek.json`, and since the page looks up the match filtered by the player's club, the
profile showed a dash in place of the opponent, although the result was there. Rounds 1–5 do
not show this: they went into `meccsek.json` when they were already **closed**, so they were
fetched with the teams included.

The solution: the two teams are **requested explicitly** in the include. What the measurement
gave (`naplo/mlsz-live-match.txt`, live round 6):

| What was requested | Result |
|---|---|
| `games.home_team` + `games.away_team` | **works** — 22.3 KB → 24.8 KB (+2.5 KB) |
| `games.homeTeam` / `games.awayTeam` | the field does not even appear |
| `games.teams` | the field does not even appear |
| `games/<id>`, `matches/<id>`, `fixtures/<id>` at the root and under `competitions/3` | all ten forms **404** |
| derived from the owned players' own clubs | only 4/6 matches, and the home/away side not at all |

The team object here is **lean** (`id`, `name`, `short_name`, `color_hex`), **without a logo** —
so this is not the 118 KB bloat above, only +2.5 KB. The points breakdown endpoint (which is
called for the drop-down anyway) knows nothing about the match with any include.

**Protection that does not expire:** a match with a `"?"` club counts as incomplete too, so the
round stays among those to be fetched again until a real name arrives. Without this, if all
matches of a round finished while the names were still `"?"`, the round would have left the
list to be fetched again, and after the MLSZ moved on it would **never again** have been
fetched — the `"?"` would have stuck for good. Pinned by: `tests/collector_matches.py` M7 and
M8, both proven to fail on the old code.

### Points breakdown (game-player-stats)
The interface's player modal calls this (reverse-engineered from the bundle):
```
GET https://fantasy-api.mlsz.hu/game-player-stats
    ?include=competition_stat_config
    &filter[competition_player_id]={cp_id}&filter[round_id]={rid}
```
**WITHOUT the `competitions/3/` prefix** — it lives directly at the API root. Per round it
gives 22 rows: `{value, points, round_id, competition_stat_config:{name}}` — `name` is the
Hungarian event name („Győzelem” (Win), „Kulcspasszok” (Key passes), „Percek a pályán (több,
mint 60 perc)” (Minutes on the pitch, more than 60)…). The interface hides the rows with 0
points, the captain ×2 / substitute ×0.5 row is added by the client — we do the same. `cp_id`
is the `competition_player.id` field of the squad response (stored as `id` in the new squad
records; for the old ones the page resolves it by name from the round's squad). It works from
anywhere, without logging in.

Also exists: `GET competitions/3/stat-configs` (the names of the 10 season statistics
categories) and `stat-leaders` (top lists) — neither is used at the moment.

### Player master data and the whole season (with measurements)
For the player profile two things were needed: the **full player master list** (for the
search) and every player's **points per round**. What the measurements gave
(`naplo/mlsz-player-list.txt`):

| Question | Answer |
|---|---|
| Is there a full player list? | **Yes:** `competitions/3/players?include=team,position,summary_statistics` — 385 players, club, position, `is_u21`, `injury_status`, `market_price`, `competition_points`. |
| In one request? | **Yes**, with `per_page=500` (by default 15/page, 26 pages). It ignores `page[size]`. |
| Does it give points per round? | **No.** `weekly_points` is always the **current** round's, and the endpoint answers **400** to `filter[round_id]`. |
| Can the points breakdown be fetched without a round filter? | **Yes**, then the whole season comes — **but only the first 50 rows.** |
| Can it be paged? | **No.** Neither `page`, `page[number]`, `offset`, `page[offset]`, nor `per_page`/`limit`/`page[size]` — all of them return the same first page. A season is ~109 rows, so **the whole season cannot be fetched in one request**; per round, however, it is ~22 rows, which fits on one page. So the profile asks per round, and only when it must. |

**The resolution of the points is 0.25.** For 377 (player, round) pairs the sum of the
breakdown rows was compared with the weekly points stored in the squad files: **238 matched
exactly**, in 123 cases the breakdown was empty — but in all 123 the stored value was 0 too
(this is the MLSZ's known behaviour: it gives an empty breakdown for a player with 0 points).
The remaining **16 differences were all exactly 0.01**, and all of them **bench** players:
because of rounding to two decimals after halving. It follows that the base points are always a
multiple of 0.25 — so the reversal rounds to a quarter.

### The player detail endpoint (measured)
`GET competitions/3/players/{competition_player_id}` — **there is no `data` wrapper**, the fields
are at the root (reading `data` makes the response look empty).
What it gives beyond the master-data row:

- `countries` — this tells whether the player is Hungarian (the list endpoint does not give
  it);
- `rounds` — a row per round with `market_price`, `is_played` and the round object: so **past
  prices are available retroactively**, with one request per player. `arak.json` is useful
  regardless: it has a finer resolution (it records the changes during a round too);
- `extended_summary_statistics` — home/away averages (not used at the moment).

**What it does NOT give: the future opponent.** `rounds` only lists the rounds so far, and there
is no opponent in it.

### The future schedule is not available (measured)
That is why the **NB1 profile only lists the rounds played** — the PL profile goes ahead too,
because there the Draft gives the remaining matches. Twenty-seven empty rows without opponent
and date are not information, only noise; if the schedule turns up, the NB1 will go ahead too.
The MLSZ fantasy interface shows such a table („Következő mérkőzések" — Next matches), so the
data exists — but its endpoint has not been found. What gave 404:
`games`, `matches`, `fixtures`, `competitions/3/games`, `competitions/3/schedule`,
`competitions/3/game-days`, `competitions/3/rounds`, `competitions/3/teams`,
`competitions/3/teams/{id}[/games]`, `teams/{id}[/games|/next-games]`,
`games?filter[team_id]`, `rounds?filter[competition_id]`. The squad endpoint answers HTTP 200
for a future `round_id`, but with an **empty list** (a squad only exists for a round that has
started), and `competitions?include=rounds` only lists the rounds **already started** (6 at
the time of the measurement), regardless of page size.

The next step would be reverse-engineering the interface's JS bundle — the same method that
found the points breakdown endpoint. The PL page does not have this problem: there the
`fixtures` array of the Draft `element-summary` gives the remaining matches, with the opponent's
id and the venue flag.

### There is no price history (measured)
The master data gives the **current** price in the `current_round.market_price` field. The MLSZ
gives price history **nowhere**: the `players` endpoint **silently swallows** the
`include=rounds` / `player_rounds` / `market_prices` / `price_history` / `prices` requests (the
response rows get no new field at all), and the standalone `market-prices`,
`player-market-prices`, `competition-player-rounds`, `player-rounds`, `price-history`
endpoints answer **404**.

So the collector logs the prices itself (`arak.json`), and **only the changes**: the collector
runs hourly on match days, and recording every run would mean twenty-four identical rows a day.
A player's row is `[[dátum, ár], …]` (date, price). A missing or zero price is not taken as a
change — otherwise an API error would write a false "dropped to 0" entry, which could not be
told apart from a real one afterwards (the same logic as the 0–0 protection in `results.json`).
**The list endpoint of the master data gives no price history** — the `rounds` array of the
*player detail*, however, does, broken down per round (see above), so the past can be filled in
with one request per player. `arak.json` is useful regardless: it watches on every collector
run, so it also records the change DURING a round, which the per-round breakdown does not.

### What the official rules state (fantasy.mlsz.hu)
The rules confirm several behaviours that were otherwise known only from measurement — and
they settle the question of "changes at closing" as well:

- **„A heti összpontszám az adott forduló utolsó játéknapjának végén válik véglegessé."**
  (The weekly total becomes final at the end of the round's last match day.) So in the NB1
  **nothing is planned to change** at the moment of closing — there is no next-day bonus
  finalisation as in the FPL. A later change could only be an error correction (the scoring
  comes from the STATS database), and none has been observed so far.
- **Postponed match:** the players get no points in the original week; the points are
  awarded **in the week** the match is actually played — based on whether the player is in
  the squad formed by the market close of **the week of the replay**. That is why someone
  can score points after two matches in one week — and that is why a profile's per-round
  row handles several matches.
- **Price changes only at market opening:** player prices „minden hétkezdet (piacnyitás)
  során változhat" (may change at every week start, i.e. market opening) — so once a week,
  not continuously. The market opens **at 10:00 on the day after** the previous round's last
  match day, and closes **2 hours** before the round's first match. The collector watches
  `arak.json` on every run — hourly from Thursday to Monday, every 3 hours on Tuesday and
  Wednesday — which catches this easily.
- **The mandatory bench** (1 goalkeeper + 1 defender + 1 midfielder + 1 forward), the
  formation limits of the line-up (1 goalkeeper, 3–5 defenders, 3–5 midfielders, 1–3
  forwards), the captain ×2, the bench ×0.5 and the Hungarian rule (+10, at least 5
  Hungarian starters, including a u21 player) — are all officially as the KEZD% calculation
  uses them.
- **At most 3 players from one real club** may be in a squad; **3 transfers** a week
  (unlimited in the winter and international breaks).

### The key to the points calculation
`weekly_points` is **already a finished value**: it includes the captain's doubling and the
bench halving. A team's round score is therefore:

```
összes játékos weekly_points összege + (magyarszabály teljesül ? 10 : 0)
```

(the sum of all players' `weekly_points` + 10 if the Hungarian rule is met, otherwise 0)

Checked on round 4 on two teams: 67.5 (starters) + 3.75 (bench) + 10 = **81.25** ✓,
and 63.25 + 2.5 + 10 = **75.75** ✓ — both exactly the official score.
**Never multiply the captain by 2 again, and never halve the bench.**

### The “blocked from servers” misconception
The squad endpoint is **not** blocked for data-centre IPs, although GitHub Actions, proxies
and Playwright all got 403 from it. **The 403 was caused by the missing
`filter[round_id]`** — those server-side attempts were made without the parameter. With a
correct request the endpoint works from anywhere, **without logging in** (evidence: from the
same machine, in the same second, 403 without the parameter, 200 with it). One restriction
remains: **the squads of a round that has not started yet give 403** — they are secret until
the market closes.

### Round closing and later MLSZ corrections

> An overview of the four different kinds of "closing" is in section **3/b** — it shows
> which flag affects what. This section only gives the details of closing an NB1 round.
- The `current_round.is_played` field of the squad response tells whether the player has
  played their match. **A round is closed when everyone who had a match has played** — and
  their match has `completed` status.

#### A player without a match cannot hold up the close

It is tempting to assume that the MLSZ marks the players of a postponed match as played with
0 points, so a postponement would resolve itself. **Measurement shows otherwise:**

| case | `is_played` | match list |
|---|---|---|
| round 5, Honvéd (no match, live round) | `false` | empty |
| round 3, ETO (had no match, old round) | `true`, with 0 points | the club's **latest** match |

So the `true` seen for the old round does not come from the round closing: if the club had
no match in that round, the API falls back to the club's **latest** match (the same fallback
that caused the "odd kick-off time" error), and inherits the flag from there too. So
`is_played` does not flip when the round ends, but when **the club next takes the pitch** —
which can be a whole week later.

That is why the closing check skips anyone without a match (`nogame`). Without this, round 5
would have stayed in the `provisional` list until Honvéd's next match, for about a week,
although all of its matches had been played. The flag is read from the **stored squad**, not
from the fresh response: normally the match list is only requested for the live round (for a
closed one the response would be six times as large), after that `inherit_match_flags`
carries it over from the earlier snapshot.

#### Safety net: the MLSZ's own round object

If the player-level picture does not add up, the round still must not stay open forever.
The fallback signal is the MLSZ's own round object. **There is no separate round endpoint**
(`rounds`, `competitions/3/rounds`, `competition-rounds` — all 404); the round list comes
through the **competition list**, with the same call the MLSZ frontend uses:

```
GET https://fantasy-api.mlsz.hu/competitions?include=rounds,current_round
```

The fields of a round: `id`, `round_number`, `start_at`, `end_at`, `is_transfers_closed`,
`closed_transfers_at`. **There is no closed flag among them** — at the MLSZ a round is a
calendar boundary (one round's `end_at` is the next one's `start_at`), and `current_round`
moves on once `end_at` has passed. That is why it is only a safety net, not a primary source.

The rule: `current_round` is the stronger signal. If according to the MLSZ **this** is still
the current round, then even a passed `end_at` does not close it — closing a running round is
the worse mistake, because the half-finished result would silently get into the table.
`end_at` only decides if `current_round` did not arrive at all.
- **The MLSZ corrects after the fact** — there are three observed cases. In one of them
  fantasy.mlsz.hu already showed a different official round total for Csendi than the one
  recorded at closing (round 1 +1, round 2 +1, round 3 −2.5; confirmed by a screenshot).
  **Which player's points moved in these three cases cannot be traced back**, and never will
  be: the first player-level snapshot in `squad_history.json` is already from after the
  correction, and it — and every one after it — gives the CORRECTED totals (38.00 / 42.88 /
  42.88 base + 10 bonus = 48 / 52.88 / 52.88). The old values only lived in the team total of
  `results.json`, without a breakdown. That is why in `zarasok_nb1.json` they stand under the
  name „Ismeretlen játékos" (unknown player) (`nk:1`), with only the size of the change
  (`dl`: +1, +1, −2.5) — no name is made up for them. Since the stored results are compared
  with the official ones on every collector run (at least every 3 hours), no further such
  case has occurred.

#### A manager is identified by username — and when not, the log says so

The collector **searches by name** on the rankings endpoint (`filter[search]`), then takes
the hit whose `username` matches exactly. If no hit matches exactly, there are two cases:

- **The hits carry usernames, and none of them is ours:** the search matched somebody else.
  The collector records **nothing** for that manager in that run, and logs the names of the
  hits (`stderr`).
- **The hits carry no usernames at all:** the collector uses the first element of the list —
  this is needed because the response does not always include the `username` field.

That fallback path must not be **silent**: if it ever matched the wrong person, it would
write **another manager's points** into the table — exactly the "silent, plausible, wrong"
kind of error the other guards are against. So the run log states (`stderr`) when the
fallback was used, and how many hits there were.

#### Self-repair: when the MLSZ corrects, the collector corrects too

`collect.py` does not write a flag into the log; it **carries the change over — everywhere**.
It has three complementary mechanisms:

1. **Rolling re-check.** By default the rankings endpoint only returns the two most recent
   rounds, so every run **re-fetches four old rounds** (`rounds_to_recheck`), and the window
   **moves on every three hours** — not on every run. Eight windows a day × four rounds = 32
   checks, and the list has at most 31 elements (the last two rounds are fetched by every run
   anyway), so it comes full circle **within a day**. More frequent runs do not hurt this: on
   Thursday–Monday the collector runs hourly, so the same four rounds come up to three times,
   but the chance grows that every window gets at least one run — after a dropped start it
   would otherwise be missed. On Tuesday and Wednesday it runs every 3 hours, one run per
   window. The fetched value overwrites the stored one (assignment instead of `setdefault`):
   the endpoint is the truth.
2. **The corrected round's squads are refreshed too.** If an old round's score changed, its
   squad snapshot is stale as well, so the collector fetches that again too
   (`targets |= changed`) — this way the points breakdown and the arithmetic of the
   „Különbségek" (Differences) view come out with the corrected data.
3. **The cross-check repairs too.** If the total computed from the squad differs from the
   stored official one, the collector **fetches the official value again** for that round,
   and if it really changed, writes it into `results.json` (`set_result`). A fresh value of 0
   for a closed round is not taken as a correction: it is a transient answer, and writing it
   would record a zero for that manager. The MISMATCH warning only goes into the log if the
   two sources do **not** agree even after the re-fetch — that is a real contradiction, not a
   correction.

A related pitfall: `rankings` must append the `round_id` parameter to the URL by string
concatenation. With `"...filter%5Bround_id%5D=%d" % round_id` Python reads `%5B` as a
format directive (`ValueError`). The backfill branch alone runs too rarely to show this; the
rolling check uses it on every run.

### The three states of bonus points (PL)

> The third state comes from the **round's** close — the same event from which the collector
> takes the automatic substitutions (3/b). It is read from two endpoints, because the Draft
> has no `event-status`.

The bonus is not final the way the other points are. The FPL **computes it during the match
too** from the BPS table, and puts it into the `explain` field of the `live` endpoint
(`stat: "bonus"`) — so our page shows it while it can still change. There are three states,
from the match's flags:

| state | how it shows | what it means |
|---|---|---|
| still changing during the match | the match is `started`, but not yet `finished_provisional` | can change minute by minute |
| full time — can still change until the round's end | the match is `finished_provisional`, but the round is not closed yet | fixed, but Opta's review can still modify it |
| final | the round is closed (`points: "r"` or `bonus_added`) | does not change from here on |

In the points breakdown the bonus row gets **a colour and a short text** in the first two
states; the third is deliberately **unmarked**. For most of the season every bonus is final,
so the marking is rare, and that is why it stands out. Colour never stands alone: every
marking has a text too.

**The third state is told by the DAY, not by the match.** The FPL closes per day: on the
given evening it reviews all of that day's matches at once, and from then on the bonus is
fixed. There is a separate endpoint for this — but **only in the classic FPL**, in the Draft
`event-status` gives 404:

```
GET https://fantasy.premierleague.com/api/event-status/
{"status":[{"bonus_added":false,"date":"2026-08-21","event":1,"points":"p"}, ...]}
```

**The meaning of the fields was read from the source of the Draft frontend**, so it is not a
guess. This draws the per-day table that the Draft's "Current team" page shows:

```js
o7 = { "": ``, l: `Live`, p: `Provisional`, r: `Confirmed` }
<td>{ points === 'r' ? <Kiemelt>Confirmed</Kiemelt> : (o7[points] || <>&nbsp;</>) }</td>
<td>{ bonus_added && <span>Added</span> }</td>
```

| column | field | values |
|---|---|---|
| Match Points | `points` | `""` (empty) → `l` **Live** → `p` **Provisional** → `r` **Confirmed** |
| Bonus Points | `bonus_added` | **"Added"** when true |

**`"p"` (Provisional) is NOT the sign of finalisation, but the state before it.** This is the
easiest point to misread in the whole thing — the word "provisional" suggests that something
has already been settled.

**From 2026/27 there is no daily close.** The round's "lockdown" — when the points become
final — is at **09:00 UK on the day after** the last match; it used to be one hour after the
final whistle. The delay is there so that Opta's later review can still count towards the
bonus and the defensive points. That is why the marking lasts until the end of the
**round**, not of the day.

Measurement confirms this: on one evening, in four requests between 21:04 and 22:06 UTC, all
nine played matches were `finished_provisional`, none `finished`, every day was
`points: "p"`, and there was no `bonus_added` anywhere — although the Friday match had been
played two days earlier. GW1's close is on Tuesday at 09:00 UK.

According to the code, a round counts as final if **either** FPL flag says so: `points`
`"r"`, or `bonus_added`. Both are positive claims of finality. As a fallback the match's
`finished` field remains, if the daily data does not arrive — less precise (it keeps the
marking up longer), but it does not claim anything untrue.

**Measured and settled:** there is NO daily close — the days stood at `p` for days, and all
switched to `r` at the round's lockdown (08:03–08:23 UTC, in two steps: first the
points/bonus, ~15 minutes later `current_event_finished`). The raw log:
`naplo/fpl-state.txt` (archive).

**The daily request is not waited for.** It is a secondary signal, only needed to mark the
bonus row, which the user sees on a click — if the points refresh waited for it, a slow or
failed request would slow the main refresh too (the „frissítés…" (refreshing…) indicator
would flash even when the points had long arrived).

**The row is tied to its own match.** `explain` comes per round split by match, in the form
`[[stat-list, match_id]]` — the second element is the match id. This matters in a double
round, where a player has two matches and the two can be in different states (measured: one
over, the other still running). Merged per club this would blur, so the bonus state is kept
**per match** (`LIVE_MATCHES`), not per club (`LIVEFX`).

**Dead end, so it need not be walked again:** the match's own `stats` array also has a
`bonus` item (the three best BPS), but it is **always there**, so its presence does not
signal that the bonus has been finalised. In the Draft API this array has the shape
`{s, h, a}`, with no `identifier` key as in the classic FPL.

### Who is still on the pitch (PL)

Next to the points are the player's minutes and whether they started — in the squad and in
the match view, **with a header** (`perc · meccs · kezdő · pont`), because an unlabelled
number is a puzzle at first sight:

| column | what it shows | when |
|---|---|---|
| `perc` (minutes) | the player's minutes played (`stats.minutes`) | always |
| `meccs` (match) | the match clock, `vége` (over) after full time | **only in the live round** |
| `kezdő` (starter) | `K` if they started, otherwise `–` | always |

**In a closed round the match clock is left out** — every match there has been played, so
everyone would show `vége`. The header shrinks to two columns too. The source of the data is
then **not** the live request (`LIVE_MINUTES`), but the round's own `event/{gw}/live`
response (`loadPastMinutes` → `PAST_MINUTES[gw]`) — the same request the points detail comes
from, cached per round, so it costs no extra request. It is asynchronous, so the modal
**comes up before the minutes**, and redraws itself when the data arrives
(`backfillMinutes`); the redraw only runs if the viewer has not moved elsewhere in the
meantime. `draft_history.json` stores no minutes, which is why the request is needed.

**Where there is no data, the cells are empty, and this shifts nothing:** `.pts` is
right-aligned and last, `.nm` is `flex:1`, so the points column stays in place even if the
minute cells are missing (in a live round this shows for players whose match has not started
yet).

**Raw values are shown; nothing is interpreted for the viewer.** A „lecserélve"
(substituted off) label would need a tolerance, and a one-minute slip between the two
endpoints would produce a false claim. The two numbers show by themselves whether the player
is on the pitch: if they are equal, yes.

**The match clock is the maximum of the players' minutes**, collected per club — not the
fixtures' `minutes` field. Measured during a live match, that is **always 0**, even for
finished matches. The players' minutes, however, tick together: in 15 samples over half an
hour every starter on the pitch in the running match showed the same number. This is not an
estimate: with 11 starters and at most 5 substitutions there is always someone who plays the
whole match. In the mock of `minute-cells.test.js` the `minutes` is **deliberately 0** — if
someone put back the match's own field, the test fails.

**A substituted player's minutes stop** — measured: in a finished match the starters stood
at 81', 80', 75'… (when they were taken off), and those who came on at 28', 22', 20'…. In 15
samples over half an hour not a single number changed.

**The match clock stops at 45 and 90**, so 90 alone does not tell whether the match is over —
there the cell says `vége`.

**In a double round both matches' values appear**, separated by `|`. The `kezdő` column
cannot be split per match then: `explain` **only contains items worth points**, `starts`
never appears in it.

**The data lags ~3 minutes** behind real time (measured, steadily): at 19:14:47 it showed
12' instead of the real 14.8, at 19:43:00 40' instead of the real 43.0.

The header only appears where there is a minute cell (live round, started match) — in a
closed round there is nothing to label. The label must not be wider than its own column,
otherwise it slips away from the numbers; the test measures it by the centre point.

### The match score above the points breakdown (PL and NB1)

Clicking a player shows a row above the points: `ARS 2–1 BRE · 70. perc`. After full time
`vége`; for a match not yet started there is no score, only the two clubs — **0–0 is not
shown**, because it would be a claim, not data. In a double round each match gets its own
row.

The score comes from the `team_h_score` / `team_a_score` fields of the **fixtures** response:

- **in the live round** from the existing `LIVE_MATCHES`, so it costs no extra request;
- **in a closed round** from an `event/{gw}/fixtures` request cached per round
  (`gamesOfRound` → `PAST_FIXTURES`). No backfill is needed here as for the minute columns:
  `breakdownHTML` is asynchronous anyway, so by the time the dropdown's content is ready,
  this is there too.

The interpretation of the fixtures response lives **in one place** (`fixtureRecord`), so the
live and the closed round cannot drift apart.

**On the NB1 the same row** comes from `meccsek.json` (filled by the collector, see the file
table), and the right-hand label from the existing `matchState` (guarded by time limits) —
the drawing is shared (`FunTasy.breakdownMatchRow`), producing the data is a per-league
adapter. The NB1 detail also shows **the minutes played as the first row**: the „Játszott
perc" (minutes played) row used to be filtered out (it is worth 0 points), although it
arrives — for anyone who played less than 60 minutes the minutes never showed. The row is
**only added for a finished match**: it cannot bypass the state gate (before/running → a
text message). At 0 minutes the message stays („Nem lépett pályára" — did not come on),
because it says more.

**Why in the dropdown and not in a column.** Measured (360px): a score column would cut the
space left for the name from 112 → 70px, so the visible part of the names would be truncated;
a second row under the name would raise the row height from 31 → 51px. The dropdown on the
other hand is free, and there the score makes the breakdown readable too („Kapott gólok 3"
(goals conceded 3) means something under `AVL 0–3 BHA`). In the squad list the
*at-a-glance* question — did they start, are they still on the pitch — is answered by the
minute columns; this does not replace them.

### Automatic substitutions at the round's close (PL)

At the end of the round the FPL makes **automatic substitutions**: in place of a starter who
did not play it brings in the first bench player who fits — that is why the bench order
matters. Measured (`naplo/fpl-subs.txt`):

- **The FPL rewrites the pick's `position` field** (the one coming on moves 12→ to 11 or
  below, the one going off takes their place on the bench), and **also gives a separate
  `subs` list** (`{element_in, element_out, event}`). Our collector computes the `b` (bench)
  flag from `position`, so it sets itself right — **if it fetches the round again in time.**
- **This happens at lockdown**, not after the match: between 08:03 and 08:23 UTC everything
  flipped at once (H2H `finished`, `points` → `r`, `bonus_added`, `current_event_finished`).
- **At that point `current_event` is STILL the old round** — the close is signalled by the
  **`current_event_finished`** field of the `game` endpoint. (`processing_status` and
  `waivers_processed` stayed unchanged throughout; they mean something else.)

That is why the collector keeps fetching the round again until it knows for certain that it
has closed: the **`veglegesek`** list in `draft_history.json` keeps track of the finalised
rounds. A round gets into it if the FPL has already moved past it, **or** it is the current
one but `current_event_finished` — and only if in that run **every team's** squad arrived
(otherwise a failed request would record the pre-substitution state as final).

**The current round is fetched on every run regardless**, after the close too — the
`veglegesek` list only decides about the *old* rounds. See "3/b" on closing: this rule is not
about the close, but about later corrections. Pinned by: `collector_draft_closing.py`.

Without this rule, getting the substituted state recorded would depend on luck: on one
occasion it only worked because a run happened to fall six minutes after the close.

### The gap between closing and collection (PL)

The FPL closes the round all at once at **lockdown** — measured, everything flipped between
08:03 and 08:23 UTC: the H2H matches to `finished`, `points` from `p` to `r`, `bonus_added`
to true, `current_event_finished` to true. Our collector, however, does not run continuously
(hourly at :37 between 07:00 and 13:00 UTC, which covers the morning closing window; every
3 hours at :47 otherwise), so there is a gap in which the `game` endpoint already says
closed, but the stored `draft.json` still has the pre-close standings.

In this gap the status line must not say **„Naprakész · ellenőrizve <most>"** (up to date ·
checked <now>): the time shown would be that of the *request*, not of the *data* — so it
would claim to be up to date exactly when it provably was not. Instead it says that the round
has closed, that the result comes with the next data refresh, and it shows the time of the
**stored** standings. Pinned by: `closing-gap.test.js`.

On the NB1 this gap does not exist: there the collector itself decides the close, and writes
the result in the same run.

### The gap between the start and collection (PL) — the browser backfills the squads

The counterpart of the gap above, at the **start** of the round. The FPL starts the round at
the entry deadline (`current_event` moves on), but our collector does not run continuously —
**measured** while the collector ran only every 3 hours: the 16:43 UTC run still saw round 4
(the log said `fordulonkenti keret: GW4`), the next one was scheduled for 23:47, and in
between, at ~17:30, round 5 started. In that gap **no squad existed at all** in the
repository for round 5. The current schedule (every 3 hours at :47, plus hourly at :37
between 07:00 and 13:00 UTC) still leaves such a gap after an evening deadline.

Without a fix the page shows nothing during a live match — and misleadingly: it goes out to
the API, it even gets the live points, it just has nobody to *apply* them to
(`updateLiveScores` exits when `HIST[gw]` is missing), so instead of a live score the status
bar says **„Naprakész"** (up to date) while the match is on.

The fix: the **browser fetches** the missing squads — `entry/{eid}/event/{gw}`, which gives
404 until the round starts, `picks` after; we only call it for a live round. `draft.json`
stores the id within the league (`league_entry "id"`), the endpoint wants the FPL `entry_id`
— `league/{id}/details` links the two, and it is fetched once.

Two rules guard it:

- **The collector's is the stronger.** What the collector has already written, the backfill
  does not overwrite: its squad may already be the post-close state corrected by automatic
  substitutions, the browser's is always the pre-close snapshot. At a round boundary the
  backfilled squads are dropped.
- **A partial backfill does not make a false score.** A team whose squad did not arrive keeps
  its match without a live score — a 0 on a running match is not "no points yet", but a
  wrong number. (A squad can be partly missing from the collector too: it skips a failed
  team request.)

The routine is **shared** (`FunTasy.backfillSquads`), because the situation is the same in
both leagues; the endpoint differs per league, the caller supplies it. On the NB1 it does
not arise today, because there the collector writes the whole current squad on **every
run** (`squads.json`), and the page fills the running round's score from that — if that file
ever lags behind, the same backfill applies there too. Pinned by: `squad-backfill.test.js`.

### Name and monogram: the monogram is never cut off

The monogram next to the team name (`.mgr`) **is the identifier in a narrow space** — so it
is not cut at the end of the line; the name is shortened instead. The pair is shared
(`nameTagHTML` in `FunTasy.create` in `funtasy.js`): the name goes into `.nv` (ellipsis,
shrinks), the monogram is `flex:none`. The containers (`td.name`, `.match .h/.v`) are
flexboxes, they do not align with `text-align`.

On mobile the width limit is on the **name** (`td.name .nv{max-width:42vw}`), not on the
cell: a `td`'s `max-width` does not limit reliably under table layout, and a long name pushed
the monogram out of the cell (measured: one of the 30 monograms overflowed).

### Line-up efficiency (KEZD%)

**What it measures:** what percentage of the points available from the squad the actually
fielded line-up brought. `scored / possible`, where possible is the best valid line-up
computed from the squad's points **known after the fact**. The table's KEZD% column is the
total of the closed rounds (from the same set the table computes from — a live/provisional
round does not count); in the match view's header and in the head-to-head list it is shown
per round.

**NB1** (computed by the collector, `collect.py` → `efficiency()` → `hatekonysag.json`):
- The bench is mandatorily 1 goalkeeper + 1 defender + 1 midfielder + 1 forward — so there
  is no choice of formation. The optimum is **still not** a per-position minimum: the
  Hungarian rule (+10) depends on who sits on the bench, so all ~160 bench combinations are
  tried, and for each the captain is the best starter.
- The stored `week` is already a finished value (captain ×2, bench ×0.5) — the raw points
  are worked back from the `cap`/`sub` flags. The scored value is `squad_total` (= the
  official round score).

**PL** (computed by the browser, `plEfficiency` in `pl/index.html`):
- The best **valid** starting 11: exactly 1 goalkeeper, 3–5 defenders, 1–3 forwards, the
  midfielders are the rest (2–5). The Draft has no captain, bench points do not count.
- For a live round the table does not compute (it aggregates only played matches); the match
  modal computes from the fresh points during a live match, with an „élő" (live) marking.

The display is shared (the `opts.lineup` hook in `FunTasy.create`: table column, h2h mark,
`roundsHTML`; `FunTasy.lineupPairHTML` is the match header's row aligned to both sides) —
the computation is a per-league adapter. The **Fordulók (Rounds) tab is shared too**
(`T.roundsHTML`): PL and NB1 used to keep it in two nearly identical copies, which is how
the NB1 ended up without KEZD% — such duplication is exactly what the sharing rule in
chapter 6 (Making changes) is about. The same happened with the **closing changes** panel:
two separate copies turned into two different looks, so the HTML is now shared
(`FunTasy.closingList`), and the two pages only pass normalised rows.

**Opening a player profile** is shared too (`FunTasy.profileViewer`): the title, the
caption, the loading indicator, the staleness guard (while it loads, another one can be
opened — a response arriving later must not overwrite the newer one) and the error message
are in one place. The two pages only specify how a key becomes a name and data, and whether
there is still something to fill in after drawing (on the NB1 the points of the ownerless
rounds load afterwards, one by one).

### The bench order (PL) — and what is still open

**The bench order is the FPL's substitution order**, not decoration: at the end of the
round the FPL brings in, in place of a starter who did not play, the first bench player who
fits the formation. That is why the bench is **left as it came** — the starters, however, are
still sorted by position, where the order has no meaning. (Sorting the bench by position
would throw away exactly the information it is worth looking at. Pinned by
`bench-order.test.js`.)

The data has always been right: the collector writes the squad in the API order of `picks`,
so `draft_history.json` keeps places 12–15 in the FPL's order. It does not store the
`position` field itself, only the `b` (bench) flag — the order is carried by the **order of
the list**.

**Open question: what happens at the round's close.** The FPL then makes the automatic
substitutions. What is known for certain:

- **The table is not affected.** The `standings` and `schedule` fields of `draft.json` come
  from the FPL's own `league/{id}/details` endpoint, so they show the official result,
  substitutions included. We do not compute this.
- **The „Kezdők" (Starters) total, however, is our computation** from the stored `b` flag,
  and it only follows a substitution if the collector fetches the round again.
- **The collector only re-fetches the current round** (plus those with a team missing). As
  soon as `current_event` moves on, the closed round **freezes** — with the squad assignment
  and points it had at that moment. If the substitution or the bonus finalisation happens
  after the switch, that round shows the pre-switch state forever on our side, on the
  „Szezon játékosai" (Players of the season) tab too.

Measurement has since answered this question — see the section "Automatic substitutions at
the round's close": the FPL **rewrites** `position` (and gives a separate `subs` list too),
and the collector makes sure, with the `veglegesek` list, that the post-substitution state
gets in.

### The FPL Draft API (draft.premierleague.com/api/) — verified by measurement

- `league/{id}/details` — participants, schedule, results; **it contains the real names
  too**, so a raw response never goes into the repository
- `bootstrap-static` — player master data (599 players, clubs, positions)
- `league/{id}/element-status` — who owns a given player now; the id space of the `owner`
  field has to be recognised at run time (it can be the league id or the entry_id)
- `entry/{entry_id}/event/{gw}` — weekly squad (starters/bench); **it gives 404 until the
  round starts**, this is expected behaviour
- `event/{gw}/live` — weekly points per player; public, the live score comes from it.
  The elements' `explain` field is the finished points breakdown (event, value, points — with
  English names; the page translates it into Hungarian by the `stat` key). A player who has
  not played yet also has an `explain` (with 0 minutes), so it is not enough for the "has
  played yet?" flag — that is what the fixtures are for.
- `event/{gw}/fixtures` — the round's matches with `started` / `finished` state,
  `kickoff_time` and team ids; from this we know whose match has already started (dash vs 0)
  and when it starts. The page **merges** the states per club: "started" if any of its
  matches has begun, "done" if all have been played — in a double round a club has two
  matches. If a club **does not appear at all** among the round's matches, it has a blank
  gameweek: its players get a dash, and the breakdown says so too
- `element-summary/{element_id}` — **a player's whole season in ONE request** (measured):
  in the `history` array per round `event`, `total_points`, every statistic, and a `detail`
  field in the form `"AVL (H) 4-0"` — that is, the opponent, the venue and the final score
  together. `fixtures` gives the remaining matches. This is the source of the PL player
  profile; it costs the collector nothing, because the browser fetches it when needed.
  **The classic FPL (`fantasy.premierleague.com/api/element-summary/{id}/`) can NOT be used
  instead:** the same path exists, but the **ids do not match** the Draft's. In the
  measurement the points happened to match for four of five players, but for the fifth it was
  1 vs 14 — so a superficial check would have let it through. Always use the Draft's own
  endpoint.
- `game` — `current_event`: the number of the round in progress (or null)

---

## 4/c. A club can have two matches in one round

**A fantasy round is not the same as a match day.** The MLSZ puts a postponed match into the
round **of the replay day** — the points are awarded there too —, but keeps the **original
round number** on it. Measured (`naplo/mlsz-double-match.txt`), in round 7:

```
ETO   games: 2 elem
        round_number=3F   start=2026-09-03 19:30   ETO - FTC      ← halasztott
        round_number=7F   start=2026-09-06 20:00   ETO - HONVÉD
```

Every other club had one element.

**Reading only `games[0]` corrupts the live data.** If the collector looks only at
`games[0]` and says "no match" when its round number does not match, then: all nine ETO
players get `nogame: True` on the very day they took the pitch; the replayed match does not
get into `meccsek.json`; and the "every match has been played" check skips the club's real
match of the round — that is, the round could be closed with a match not yet played. The
collector made this error in three places.

**The split is not by the direction of the round number.** The *fallback* (the club has no
match in the requested round, so the API falls back to its other match) also brings a
different round number. The difference: next to the replayed match **the round's own match
is there too**, while in the fallback exactly that is missing. Therefore: if the list has a
match belonging to the requested round, the others belong here too; if not, the whole list
is a fallback (`games_of_round`).

**With several matches** the player's `start` is their nearest match **not yet played** —
that tells what they are still waiting for —, and `vege` is only true if **all** have been
played: until then their points can change.

**Known limitation:** if a club has *only* a replayed match in the round (its own was
postponed too), we see it as a fallback and say "no match". This is the earlier behaviour
too, so it is not a regression — the exact solution would be the rounds' **time bounds**
(whether the match is within the round's window), but that requires passing the round
boundaries to every call site. If it ever occurs, that is what has to be done.

**The fix would have blocked itself.** The collector inherits the `nogame` and `vege` flags
from the earlier record, because it requests the match list only for the live round —
without this they would be lost on the re-fetches after the close. But this way a wrongly
stuck `nogame` would have stayed in **forever**: the fresh response correctly said that ETO
has a match, and the inheritance restored the error. So the inheritance is **skipped when the
match list was just fetched** — then the fresh response is the truth.

**The browser implements the same separately.** The live squad fetch rebuilds the records on
the page (`squadRecord`) — the same rule is needed there. Without it the page **still**
says "the club has no match": the stored data is already right, the fresh fetch overwrites
it. If the rule changes, it has to be changed **in both places**.

Pinned by: `tests/collector_matches.py` M9–M11 (collector) and `tests/pre-kickoff-squads.test.js`
(browser, with the real shape of the measurement).

### The closing panel goes up to the CLOSED rounds

The PL „Zárási változások" (closing changes) panel must not list up to the largest round of
the stored squads (`draft_history`): the collector saves the squads of the **running** round
too, so during a live round that list goes one further, and the panel would open on a round
**not even closed yet**, empty (*„nem történt változás"* — no change). At that point the
close has not even happened.

So the **`veglegesek`** list in `draft_history.json` decides: it tells exactly what the
collector has closed.

### What the collector writes, the workflow commits too

The workflows add **manually listed** files to the commit — this is deliberate (it does not
sweep in rubbish), but **silent**: if an output file is missing from the list, the collector
computes it correctly on every run, and it **never gets into** the repository. This is how
`keretvaltozasok.json` was left out: the „Változtatások" (Changes) tab therefore showed
*„még nincs pontszám"* (no score yet) even for the already closed round 7 — the file kept the
pre-close state without points. Nothing flagged it.

A machine checks this: **D8** in `tests/doc_checks.py` compares the collectors'
`write_compact` / `write_if_changed` calls with the workflow's `git add` list (a folder
prefix and a `draft*.json`-like glob count too). If a new output file is left out, the test
names it.

### A stale page reloads itself

The `?v=` busts the cache of `funtasy.js`/`funtasy.css` — **not of the page's own HTML**.
But `nb1/index.html` holds live logic (pairing shared players, building the live squad
records, the match state), and an old HTML runs them by the **old rule**. Twice in one day the
fix was out, yet the viewer saw the old behaviour — and nothing flagged it.

So on load the page asks `verzio.json`, and if the page is older, it reloads **once**. A
`sessionStorage` gate protects against a loop: if it is still old after the reload (an
intermediary cache), it does not try again — it would rather stay quiet than reload back and
forth.

`verzio.json` and `?v=` **must move together**: **D6/b** in `tests/doc_checks.py` checks
this, because if they drift apart the protection either does not catch, or causes an endless
reload.

Pinned by: `tests/stale-page-reload.test.js`.

### Shared players are paired by ID, not by name

The live match view fetches the two squads **separately**, and if only one of them arrives,
the other stays the stored one. But the two sources give **different name forms** — the
stored one the Hungarian order (`Lehoczki Bendegúz`), the live fetch the first name–surname
form (`Bendegúz Lehoczki`). Paired by name, this gave **zero** shared players, when there
were two. The id (`competition_player.id`) is the same in both sources, so `roleKey` uses
that. The **role** (captain / bench) is still part of the key: the same player in a different
role is not shared — their points are not the same either.

Pinned by: `tests/squad-diff.test.js` — it must find the same number of shared players in
the stored, the mixed and the live form.

## 5. Known limitations and pitfalls

- **GitHub Pages caches** — after an upload the old file can come for 1–2 minutes. Ctrl+F5.
- **A 0–0 must not get into `results.json`**: a round not yet closed gives 0 points for every
  player, which the system would take for a played draw. `collect.py` has a guard against it
  (`if not hp and not vp: continue`). This was a data corruption that very nearly happened.
- **The saved `price` is the market price at the moment of the request**, not the round's.
  For rounds backfilled after the fact it is therefore not a historical value. The page does
  not show it at present, but price statistics must not be built on this field.
- **Postponed matches:** because of Ferencváros's European cup matches, its opponent's round
  match can be postponed. Then the affected club's players get 0 points.
- **NB1 club change during the season — the opponent column of the player profile.** The
  squad record stores the player's club (`team`) per round, so for the rounds when the player
  **was in someone's squad**, the profile uses the right club — and so the right opponent. The
  problem only remains for the rounds when they were **in nobody's squad**: there is no stored
  club there, and the rows of the points breakdown do not give it away either (they only tell
  the round), so the profile looks up the opponent from the player's **current** club. For
  someone who changes club during the season, such rounds — before the change, spent in
  nobody's squad — would show the wrong opponent. This cannot happen until the winter
  transfer window; **then, however, it has to be handled** — either from a data source that
  also records club changes, or if by then the MLSZ API itself gives the club per round. On
  the PL side this problem does not exist: there the Draft `element-summary` `detail` field
  (`"AVL (H) 4-0"`) brings the opponent with it.

- **The bookmarklet (fallback) runs from your browser's copy**, not from the repository. If
  `tartalek/bookmarklet.txt` changes, the bookmarklet in the browser has to be updated
  by hand.
- **On the PL, in the first hours of a GW**, until the collector first stores the round's
  squads, the live match score comes from squads the browser backfills (see "The gap between
  the start and collection (PL)" in chapter 4). A team whose squad the backfill could not
  fetch keeps its match without a live score until the collector writes the squads; after
  that it is accurate to the minute.
- **The old squad records had no `id`, `played`, `start` and `nogame` fields** (these were
  added later). Because of this the page had to start a live request for the points
  breakdown, and the "no match" marking was missing entirely — for the round 3 ETO players
  this made the page say, with a placeholder date already past, that the match had not
  started yet. The collector therefore **re-fetches** such a round **once**, together with
  the match list, and fills in the missing fields; after that the condition no longer holds,
  so it does not repeat.
- **The "no match in the round" flag is fixed during the round**, and after the close the
  match list is not requested again (the response would be six times as large); instead
  `inherit_match_flags` carries it over from the earlier snapshot.
- **The rows of the points breakdown are identified by the Hungarian event name** (e.g. the
  „nem lépett pályára" (did not come on) case comes from the 0 value of the „Játszott perc"
  (minutes played) row). The API gives no stable key for these, so if the MLSZ renames an
  event, the page falls back from the more detailed message to the more general one — it
  causes no error, but the texts become less precise.
- **Live request from the browser:** on load the page also fetches the fresh results directly
  (through CORS proxies). If this breaks, it is shown in the status bar (for the texts see
  chapter 3), and the stored data (refreshed at least every 3 hours) stays visible.

---

## 5/a4. The Guardiola measure

**How much more did changing the squad bring than not touching it at all?**
`guard` = the **current** squad's points minus **last week's** squad's points **in the same**
round. A negative value: the change cost points.

The alternative is literally "what would have happened if I had not touched it": the same 15
players, **in the same roles** — who was a starter stays a starter, who sat on the bench stays
there, the captain is the same. It is **not** the best line-up that could be made from the
old squad: that is what KEZD% measures, and the two would get mixed up.

**Both sides are computed with the same function** (`squad_total`), so the Hungarian rule and
the rounding play out the same way — the difference is purely the work of the squad change.
This is not a formality: the stored `week` for a bench player is the API's already
halved-and-rounded value (0.75 → 0.38), while the raw points computed from the breakdown are
not — if the two sides worked from different sources, even an **unchanged** squad would show
"+0.01". That is why `teny` can differ by one hundredth from the official round score; the
**measure**, however, is exact, and that is what is shown.

It deliberately does **not** subtract from the official round score: that would include a
later MLSZ correction as well, and that is not the manager's decision.

There is no value for the **first** round (nothing to compare with) and for a round **not yet
closed** (`bontasok/<round>.json` does not exist yet).

**The breakdown covers every player ever owned.** The player master data (`players`
endpoint) only gives the *current* field: whoever leaves the league drops out of it — but
stays in the squad history. If such players are left out of the breakdown, they count with 0
points in the measure, **although they played**: Skribek scored 3.25 raw points in rounds 1
and 3. The measure then tilts in favour of whoever has just got rid of them (in rounds 2–6 it
affected 6 of 94 sales). That is why the collector fetches the breakdown for **all** players in
`squad_history.json`, and **only supplements** the existing files with the few missing players
— it does not fetch all 385 again. If someone is still missing after that, it is a failed
request, not a missing player: the collector then writes their name to the error output.

**The measure is computed AFTER the breakdown collection, not before it.** Computed before,
a breakdown freshly backfilled in a run would not count in it: the measure would lag one run
behind, and only the next run would set it right — the backfill would go out, and
`guardiola.json` would stay unchanged. The size of the difference is not negligible: in round 2
Bence's value moved from +3.00 to −25.50 (the player missing from the breakdown was last week's
captain, so their points count double).

It appears next to the points of the **match rows**, as a column on the **Fordulók** (Rounds)
tab, and cumulatively in the **table** — from the same set the table computes from.

### The same on PL, with automatic substitutions

The Draft has no captain, and bench points do not count — but at the end of the round the FPL
makes an **automatic substitution**: in place of a starter who did not even come on, the first
bench player comes in who played **and** with whom the formation stays valid (1 goalkeeper,
3–5 defenders, 2–5 midfielders, 1–3 forwards). This is why a goalkeeper can only be replaced
by a goalkeeper: two goalkeepers is not a valid formation.

**This is applied to the alternative too.** The real result includes the substitutions (the
stored squad is already the post-close state); if the alternative were computed without
substitutions, last week's squad would be under-measured, and the measure would be
systematically biased in favour of the change.

The bench **order** decides, and it comes from the FPL (picks 12–15) — it is never reordered.

If the player position data is missing (a failed `bootstrap-static`), the collector **does not
recompute**: without it the formation check would always be false, not a single substitution
would happen, and the measure would silently give a wrong value. In that case the earlier file
stays in force.

Pinned by: `tests/collector_guardiola.py` (NB1) and `tests/collector_draft_guardiola.py` (PL).

## 5/a5. The „Változtatások" (Changes) tab

**The derivation of the Guardiola measure**, item by item: for every round it shows whom the
manager sold, whom they bought and whose role changed — and **how much each was worth**. At the
bottom of the block is the total, which is **exactly** the round's GUARD value. This is the
whole point of the tab: the number in the table should not have to be taken on trust, but be
checkable.

Four kinds of item:

| Item | Counted with |
|---|---|
| **eladva** (sold) | their **last week's** role (captain double, bench halved) — this is what they would have brought if left alone |
| **megvéve** (bought) | their **current** role |
| **szerepváltás** (role change) | in the squad throughout, but starter ↔ bench ↔ captain moved: the difference of the two values |
| **magyarszabály** (Hungarian rule) | if the change gained or lost the 10 points — that does not show on one player, but on the squad |

**Layout.** One column, rounds in **ascending** order — the same as on the Fordulók tab and
everywhere else. One card per round, inside it *Eladva / Megvéve / Szerepváltás* sections. The
two rightmost columns have a fixed width, so the numbers stand under each other. (Two columns
of blocks, newest first, with the points difference at a different place in every row, make
the eye jump in a zigzag, and the order goes against the other views.) On a phone a row breaks
into two lines: on top the position, the name and the points difference, below it the
explanation and the calculation.

The middle column is the player's **raw** round points; where the role modifies it (captain
doubled, bench halved), it is in the form `raw → worth this much` — otherwise next to the
captain's 28.50 it would not show where it came from.

**A round without changes shows too**, empty. If it were left out, the viewer would think the
data was missing — when the answer is exactly that the manager did not touch the squad, and so
their measure is 0.

### On PL, what the manager did and what the machine did stand apart

In the Draft the FPL makes an **automatic substitution** at the end of the round. That is not
the manager's merit or fault, but shown together it would look as if they had made good
changes — when the machine put the squad right (or the reverse). So on PL the calculation
splits in two:

- **manager:** every player counts with their **named** role — a starter with their points, a
  bench player with zero, even if they came on in the end;
- **machine:** the squad's actual points (with automatic substitutions) minus the total above.
  This is exactly the yield of the closing substitution, and it stands in a separate row:
  *„Automatikus csere a záráskor"* (automatic substitution at closing).

The sum of the two is the squad's points, so the derivation adds up without remainder. The tab
also shows the subtotal (*„A te döntéseid"* — your decisions), so it shows at a glance what is
whose doing.

### The round in progress is shown without points

After the entry deadline the squad is **fixed**, so the *change* is already known — its
**points** are not yet. The tab says so: the running round's block is there, with every sale,
purchase and role change in it, but **not a single number** — neither in the rows, nor as a
total; in the header instead of GUARD it says *„még nincs pontszám"* (no score yet). A `0` would
be a lie: it would claim that the change was worth nothing.

The collector then gives the items with `pontok: false` and `guard: null`
(`squad_changes_without_points`, and `draft_squad_changes_without_points`). On PL the
**machine substitution** row is not included either: the automatic substitution happens at the
end of the round, so it has not even happened yet.

**The Guardiola measure is not produced earlier because of this.** `guardiola.json` still only
contains values for closed rounds, and the table does not compute from it either.

### One gate decides when there is a score

The tab uses **the same condition** as the Fordulók tab and the table: a live or not yet closed
round has no value. The condition lives in one place (`guardValue` on the object
`FunTasy.create` returns, used as `T.guardValue`), because three places use it — and when they
decided separately, PL round 2 was still empty on the Fordulók tab while the Változtatások tab
already had a number in it. If the collector's file did contain a number for a round not yet
closed, the page **deliberately ignores** it — when there is a value is decided in one place.

### On horizontal scroll, the position and the name stay put

The table does not fit on a phone, so it scrolls sideways — but the **position** and the
**name** columns stay in place (`position: sticky`), otherwise it would vanish from beside the
number whom it belongs to. The two cannot both sit at `left: 0`: the position (higher
`z-index`) lies over the name, and the start of the name disappears under it. So the position
has a fixed width (34 px), and the name is offset by exactly that much.

Tables with sticky cells need **`border-collapse: separate`**: WebKit (that is, every browser on
iPhone, Chrome included) does not reliably stick table cells with `collapse`. Measured:
`separate` + `border-spacing: 0` changes nothing in the drawing (table 310×652 px, row height
35 px in both modes) — the borders come from the `td`/`th` cells' own `border-bottom`, there is
no top border, so there is nothing to double.

**The name cell must remain a real table cell.** While `td.name` itself was the flex container
(to protect the monogram), the cell dropped out of the table layout — the browser wraps it in an
anonymous cell —, and **on iPhone it did not stick**: on scrolling the SZAKVEZETŐ (manager)
header stayed put (it has no flex), but the names slid under the numbers. In Chromium this does
not show, there sticky holds on the flex cell too. The flex is therefore **inside** the cell, on
the `.nevsor` span. Pinned by: `tests/standings-recount.test.js` — without Safari too, because it does not
measure the appearance of sticking, but the cause (the cell's `display`, and that the flex is one
level further in).

### The shared layer understands both data shapes — and this is not a convenience

The `?v=` only busts the cache of `funtasy.js`/`funtasy.css`, **not of `nb1/index.html`** — and
the server answers a request with an old `?v=` with the **current** `funtasy.js` too. So an old
page in the browser (one that still passed the items in one piece, as unlabelled `sorok`) can
meet the **new** renderer: in the round header the GUARD stands, but under it *„Nem változtatott
a keretén."* (made no change to the squad) — although three players were changed.

That is why `FunTasy.changesList` accepts, besides the labelled `reszek`, the **old `sorok`
shape passed in one piece** too. The same rule holds for every future contract change: if the
input of the shared layer changes, the old shape has to be understood for as long as the pages'
cache can still run out. Pinned in the last section of `squad-moves.test.js`.

Pinned by: `tests/collector_squad_moves.py` (NB1), `tests/collector_draft_squad_moves.py` (PL)
and `tests/squad-moves.test.js` — the latter compares, **for every manager and every round**,
the sum of the rows, the block's „Összesen" (total) row, the GUARD column of the Fordulók tab
and the GUA cell of the table.

## 5/a6. The squads are visible before kick-off

After the entry deadline the squad is **fixed**, and the collector saves it
(`keretek/<round>.json`). On the NB1 the match view would otherwise only say *„A forduló még nem
kezdődött el."* (the round has not started yet) — although this is the most exciting question:
**whom the opponent is fielding.** So both squads are drawn, with a dash instead of points.

No secret is broken: under any manager's name the **Aktuális keret** (current squad) shows the
same anyway, and the squad can no longer be changed after the deadline.

**At this point the round is already LIVE, and the view says so.** The entry deadline has
passed, the squad is fixed, and the score is not 0:0 either — **the Hungarian rule's +10 is
already worth points** if the line-up is right. So this state gets no separate branch: the
**existing live view** draws it (`showLiveMatch`), with the „élő" (live) marking and the squad's
current total. A separate branch without the „élő" marking would be a wrong decision, and two
nearly identical pieces of code.

The **subtitle** follows the state: while not a single match has started, *„a forduló él, de még
egy meccs sem kezdődött el"* (the round is live, but no match has started yet); after that the
usual *„élő állás — a meccs még tart"* (live score — the match is still on). A player whose match
is missing (no start) does **not** count as started: their state is "unknown", and it does not
follow from it that the round has begun.

The **KEZD% row**, however, stays hidden — as in every live round: the value still changes, and
the collector recomputes it anyway.

**The home page list shows this number too.** The MLSZ rankings say 0 before the first whistle,
and the list drops a 0-0 as "not even started" — so it would show `— : —` although the squad is
already fixed. In that case the page computes from the **squads** (`fillFromSquads`), with the
same `squadTotal` as the match panel: this way the two views cannot say different things. It
only **fills in**, it does not overwrite — as soon as the MLSZ gives real (non-zero) points,
`refresh` puts those in its place.

**For a real future round the message stays.** There is no saved squad for it, and nothing is
made up. On the PL side this gate never existed: `showMatch` always draws the squad if there is
stored data for the round.

Pinned by: `tests/pre-kickoff-squads.test.js`.

## 5/a. Why there is a separate squad file per round

`squad_history.json` grows by ~19 KB per round: 95 KB after 5 rounds, **~630 KB** by the end of
the 33-round season. But to open one match the page needs the squads of **a single round** —
downloading the whole thing is a waste, noticeably so on mobile data.

So the collector also writes the squads per round (`keretek/<round>.json`), and the match view
reads from there. Now 24 KB instead of 95 KB, at the end of the season **still ~24 KB** instead
of 630 KB.

Two details that matter:

- **The per-round files have no timestamp.** If they had one, all 33 files would change on every
  collector run, and the repository would grow needlessly. This way a round's file only changes
  if the squads really changed.
- **There is a fallback path.** If the per-round file is missing (old commit, mistyped path), the
  page falls back to the full history — it gets slower, but does not break. A test covers both
  branches.

The full history is kept: the collector uses it to know what is missing, and the „Szezon
játékosai" (Players of the season) tab needs all of it too — but that is a rarely opened,
deliberately heavy view.

**The PL side does not have this yet:** `draft_history.json` is downloaded on every load (now
4 KB, ~159 KB by round 38). The stakes are lower, and there `HIST` is used synchronously in
several places, so it is a more invasive change — worth a separate round of work.

**What is still open on the NB1 too:** the *player profile* still downloads the whole
`squad_history.json` (now 121 KB, ~797 KB at the end of the season), because it needs every
round. What it actually uses from it is five fields per player per round — a separate index of
that would be ~162 KB for the whole season, that is **80% less**. This is a new data file, so
the format has to be decided first; until then the current solution stays.

## 5/a3. A closed round's breakdown comes from the repository

Without a stored copy, the **itemised breakdown** ("what made up the 9.75 points") can only come
from the browser, on a click, with a live MLSZ call. That has two problems:

- **network-dependent**: if the MLSZ or the proxy is not answering, the dropdown shows an error —
  although a closed round's breakdown never changes again;
- **slow in the profile**: for a player never owned, the profile fires a separate request per
  round, one after the other (that is why the points "fill in" afterwards).

So the collector, **once, at the round's close**, fetches the breakdown of all 385 players
(`bontasok/<round>.json`), and for a closed round the page reads from there — immediately,
independent of the network. **The live round stays on the live path**: there the breakdown is
still changing.

Why the whole field, and not only the owned players: anyone's profile can be opened from the home
page list. **This burdens none of our quotas**: the collector calls the MLSZ directly from the
GitHub server (CORS only exists in a browser, there is no proxy here) — the cost is a one-off
~3 minutes of run time per round and ~40 KB in the repository.

**Only the rows worth points are stored** — plus the „Játszott perc" (minutes played) row. The
MLSZ returns all **22** statistic rows for every player who played, the zero ones too; with 385
players that is 141 KB per round, 4.5 MB by the end of the season. The page, however, only shows
the rows worth points, and the „Játszott perc" separately (it also decides the „nem lépett
pályára" (did not come on) / „lejátszotta, pont nélkül" (played, without points) message).
Filtered it is **40 KB** per round, 1.3 MB for the season. This filtering is **reversible**:
`game-player-stats` answers for old rounds too (the whole breakdown depends on exactly this), so
the raw values left out can be fetched again at any time — the price log could *not* be filtered
for exactly this reason: nobody gives back the price after the fact.

**What counts as closed** is decided from the **stored** state (every match has a result, and
the round is not among the provisional ones) — not from which round's squads the collector
happened to fetch in this run. Otherwise, on introduction, a breakdown would only have been made
for the last round, and never for the earlier ones.

Two details that matter:

- **A half-finished file is not written.** If more than 10% of the requests fail, the file is not
  produced, and the next run tries again. An incomplete file is worse than a missing one — it
  would never be retried.
- **A correction does not lapse here either.** If the rolling re-check corrects an old round's
  result, it redraws that round's breakdown too.

If the file is missing (a round before the introduction, or the collector has not run yet), the
page silently falls back to the live request. Pinned by: `tests/collector_breakdowns.py` and
`tests/stored-breakdown.test.js`.

### Live points are summed from the itemised breakdown (PL)

**The failure this prevents (GW2):** a player's row showed 1 point and 9 minutes, while their
points detail showed 90 minutes, a goal and a bonus — 8 in all. The matches had been played by
then, so the **detail** was the truth.

The fault was not ours: **the official FPL app showed the same contradiction** — 1 point on the
pitch view, 8 on clicking the player. The FPL keeps `stats.total_points` and the `explain` event
list **separately**, and the total got stuck.

Two things tell that `explain` is the authoritative one. One: **the matches had been played by
then**. Two: **90 minutes played** can only come from a played match, while the 9 minutes of
`stats` can occur at any moment of the match — the minute count only grows, so the smaller one
is the one lagging behind.

> **What is NOT an argument: the bonus.** It is tempting to reason that "the bonus is only
> awarded after full time", so a bonus row proves a finished match. That is **wrong**: the FPL
> computes the bonus during the match too from the BPS table, and puts it into `explain` — see
> the section "The three states of bonus points (PL)" above, which documents exactly this.

So the live points (and the minutes) are **summed by us from `explain`**, not taken over from
the total. Normally the two agree, so this changes nothing; when they differ, however, the
event-based value wins — and this carries through to the team's total and the live match score.
If a player has no `explain` (they have not come on yet), `stats` remains.

**The same rule applies in the collector.** This is not cosmetic: the collector **never fetches**
a closed round **again** (`veglegesek`), and from then on the page does not compute live but
shows the **saved** number. Whatever went in at the moment of closing stays in for good — the
FPL does not give back an old round. If only the page were fixed, the right number would show
today, but after the close the stuck value would come back, forever.

In the collector this is `collect_draft.py` → `player_points`, on the page `fetchLivePts` — the
two **must give the same number**: what the visitor sees is what has to be archived. When they
differ, the collector **writes loudly** to the run's log how many players the two sources
differed for; if this becomes regular, that is where it shows.

**Fallback in both places:** if `explain` is empty (the player did not come on) or the FPL
changes its structure, not a single row is found, and the `stats` total remains. An API change
thus gives back the **old behaviour**, not zeros. Points and minutes are tracked separately:
there can be a row worth points without a minutes row, and there 0 minutes would be false.

Pinned by: `tests/live-points-from-breakdown.test.js` (page) and `tests/collector_points_source.py` (collector)
— with a stuck total, 8 points and 90 minutes, the live score 88 (11 starters), the wrong 11
nowhere; for an empty or unknown-structure breakdown `stats` remains; in a double round the two
matches are added up. Both provably fail on the old code.

### During a live round the page refreshes itself

**The failure this prevents (PL):** a page left open showed the standings **from load time**.
The LEE–BRE match was at the 9th minute when the page loaded, and the rows stayed there —
minutes, match clock and points alike. The dropdown breakdown, however, starts its own fresh
request **on a click**, so it already showed 90 minutes: on the same screen the row (9 minutes,
1 point) and its panel (90 minutes, 2 points) contradicted each other. **The panel was right.**

Without a timer only three things refresh the live layer: loading, switching back to the page
(`FunTasy.onVisibleAgain`), and opening a match or a squad. A timed refresh was **deliberately**
left out while the live requests went through public proxies: a page left open would have
hammered them with per-minute requests.

**Our own Cloudflare Worker's 60-second edge cache removes that reason:** however many people
watch the same round, one request per minute goes out to the API. So `FunTasy.liveRefresher`
re-runs the live request every minute on both pages — but **only** if there is a round in
progress, and **only** on a visible page. Between rounds and on a page put in the background not
a single request goes out.

Pinned by: `tests/live-auto-refresh.test.js` — in a live round the score shown changes from 44 to 99
without a click; in a closed round not a single repeated request goes out. It provably fails on
the old code.

### Write only when something really changed

The same rule holds for every output file: **the `updated` field is no reason to write**. If only
the timestamp would change, the file is not rewritten — otherwise the repository would grow on
every collector run for nothing, and in the git history it could not be found when something
really changed.

Two conditions have broken this rule:

- the condition for `results.json` **compared a list with a set** (`provisional != old_prov`),
  which are never equal — in 30 of its last 36 commits only the timestamp had changed;
- writing `squads.json` was triggered by a change of the **whole history**, although the file
  only contains the last round's squads — a correction of an old round thus rewrote it with
  unchanged content (2 times out of 14).

Both are covered by a test (`tests/collector_provisional.py`, C3 and C4): C3 runs the collector
twice on unchanged data, and **not a single** output file may change — not only `results.json`,
but everything it finds after the run. `stamp` is replaced by a counter, otherwise the
second-precision timestamp would hide the unnecessary write.

### An interrupted write cannot be read as "no history"

The **accumulating** files — price log, squad history, results, matches, closing adjustments —
hold something the run cannot recompute: the past. The collector reads them in on every run, adds
today's data, and writes them back.

This cycle could be cut at two points, and the two **together** caused data loss:

- writing with `open(path, "w")` empties the file before the first byte — a run interrupted there
  (the workflow's six-hour limit, a restart, a full disk) leaves a cut-off JSON on disk;
- reading under `except Exception` falls back to an **empty default**. From the cut-off file this
  makes "no history", the run adds today's round to nothing, and writes that back.

One interrupted run plus one clean run would thus **erase every earlier round** — the output is
valid JSON, only its past is missing, so nothing would flag it. The price log is the most serious
case: measurement shows that the MLSZ **provides no price history at all**
(`naplo/mlsz-price-history.txt`), so whatever the log loses cannot be recovered after the fact.

So the write goes to a temporary file next to the target (`<path>.tmp`; `results.json` is written
to `results.json.uj`) with `flush` + `fsync`, and `os.replace` puts it in place: this is atomic,
so the reader sees either the old file or the new one, never a half-finished one. Reading goes
through `read_stored`, which gives the default **only** for `FileNotFoundError` (first run); for
a damaged file the exception propagates, the run stops, and the file is not touched — on the next
run there is a chance to read it intact. `stamp`, `write_compact` and `read_stored` live in
`collector_common.py`, in one copy shared by both collectors.

Test: `tests/collector_storage.py`, with thirteen assertions covering both collectors and the
shared module. Among them one at the **source-code level**: every `open(..., "w")` must get a
temporary name. Without it the next new output would silently bring back the old path.

## 5/a2. Changelog („Mi újult meg?" — What's new?)

A user-facing log, not a technical one: **only what the user sees or notices goes into it**.
Purely background work (reorganisation, collector internals, tests) does not.

- **Two types:** *new feature* and *fix*.
- **The league is a tag, not a category.** An entry can belong to several leagues, and it **shows
  up when filtering for any of them**. This matters because not everyone plays in every league —
  and the more leagues there are, the less so.
- **The leagues can be toggled separately, several at once.** Someone who plays in two leagues
  can select both, and then sees the entries of both (the selected ones are combined with OR).
  The „Mind" (All) button is not a choice next to the others, but clears the selection. The type,
  on the other hand, is a single choice, because the two types exclude each other.
- **One day, one topic, one entry.** If a solution came together in several attempts, only the
  final state goes in; the intermediate attempts do not interest the user. **This holds for later
  adjustments too:** an adjustment to a freshly released feature on the same day (or the next day,
  after the first feedback) is not a separate bugfix entry — the feature's entry describes the
  final state. (A separate entry such as „a panel a helyére állt" (the panel settled into place)
  is exactly what this rule excludes.)
- **But the feature's entry is not a catch-all.** Only what belongs TO THE FEATURE ITSELF goes
  into it. What affects something else — even if it was finished in the same round of work — is
  **either a separate fix entry, or nothing**: if it is so small that the viewer does not notice
  it, it does not go into the log at all. The two rules together: a feature is not split up, and
  nothing else is hung on it either.
- **Dated**, grouped by day, newest first. The log starts at the beginning of the season; earlier
  changes are not in it.
- **When merging, the entry has to be REWRITTEN, not appended to.** If a new part is added to an
  existing entry, the description is not extended with a tacked-on sentence: the whole thing has
  to be rewritten so that it reads as one text. A series of appended sentences becomes a list from
  which the user cannot tell what matters.
- **For a feature built in several stages the entry goes out at the END**, not per stage. Unless
  instructed otherwise, this is the default. If a feature is split into stages so that it can be
  seen in the meantime — that is not yet a finished feature: a log rewritten per stage would show
  a half-finished state to whoever happens to open it. Until then the text being written stands in
  `valtozasok-vazlat.json` (the log page does not read it), and when the last stage is done too,
  it is moved over in one go. The same formal check applies to it (`tests/doc_checks.py`, D5), so
  it cannot fall asleep half-written.

The data is in `valtozasok.json`, extended by hand (text not yet published is in
`valtozasok-vazlat.json`). The filters are built from the `LEAGUES` list, so adding a new league
needs no separate work here either.

**How to phrase an entry**

- **The title says what is true from now on**, and the sentence what this means for the user and
  where they see it. Example: *„Az elmaradt meccs játékosainál kötőjel áll 0 helyett"* (players
  of a postponed match show a dash instead of 0).
- **No first person, and no reference to how the development went.** The log is not about who
  said what or how something came to light — only about what changed on the page. (A log entry
  about where the same thing was said earlier does not interest the user — what interests them is
  what changed on the page.)
- **Matter-of-fact, not dramatic.** Not *„nem kapnak többé hamis 0-t"* (they no longer get a
  false 0), but what actually shows on the row.
- **Words used in the conversation are not taken over verbatim.** The way an error is talked about
  is not the way it has to be written into the log; the wording has to be thought through again
  for every entry.

Access: from the home page (a card) and from the **footer** of every page
(`FunTasy.renderFooter`). The log itself has no footer, because it would point to itself.

### The frame of the two pages is written twice by hand

There is no build and no template, so the `<head>`, the header, the panel frames and the footer
**stand separately on both league pages**. This can drift apart — and has: the closing changes
panel stood for a while with a different title, in a different column and with a different layout
on the two pages. "Paying attention" is not enough here: `tests/league-page-skeleton.test.js` checks by machine
that the `<head>` is identical on all four pages (apart from the title and the path prefix), that
the order and column of the panels are the same on desktop and mobile, and that the table header
matches too — only the participant column runs under a different name (Szakvezető / Csapat —
manager / team).

If a new panel is added to one page, the test fails until it is added to the other as well. This
is the intent: **what is in both leagues should look the same.**

## 5/a7. The magazine is in publication order

The paper **does not go by round, but by time**. What came out today is on top, even if it is
about an older round — and even if a newer round has closed in the other league in the meantime.
This is the logic of an issue: the reader sees in front what they have not read yet.

Listed in blocks per round and per league, a freshly published preview would turn up in the middle
of the page — under round 8, because round 9's summary was already out —, and the freshest piece
would land where nobody looks.

The sort key is the per-article `kozzetett` ISO timestamp (`FunTasy.articleList`). For the earlier
pieces it was backfilled from the **git history** of `articles.json`: not guessed, but looked up
from the commit that published them.

Two things worth knowing about it:

- **Identical timestamps are common**, because several pieces go out in one commit. Within such a
  group the order of insertion does not decide (that is accidental), but: newer round first, and
  within it column → summary → preview.

Machine guard: **D15** (`tests/doc_checks.py`) — a published piece cannot be without `kozzetett`,
otherwise it would silently fall to the bottom of the page.

### The weekly column does not belong to a pairing

The third column — *Kele Janek elemez* (Kele Janek analyses) — is written for the **round**, not
for a match: an outside journalist writes about our league. Therefore:

- its key is its **own title**, without `|` — from this `articleList` knows that it has no
  opponent, and does not try to split a pairing out of it;
- **it has no closing gate**. The summary waits for the final round because it states results;
  the column does not state results, so it can look ahead as well as back;
- **it has no `short`**. With it the lead would take the role of a subtitle and break the arc of
  the text; in the collapsed strip and in copying, the first paragraph takes its place.

The column does not appear on the match pages (there is nowhere to put it), only in the paper —
but there it stands at the top of the list within the round.

## 5/b. Tests

```bash
tests/run_all.sh
```

It starts a local server on the repository root, runs everything — the documentation consistency
check (`tests/doc_checks.py`), the data consistency check (`tests/data_consistency.py`), the
collector tests (`tests/collector_*.py`), then the browser tests **in parallel** (3 workers; the
two timing-sensitive tests run at the end, alone) —, and sums up; the exit code is the number of
failed tests. `WORKERS=1` is the serial mode. The number of tests is deliberately not written here:
it would go stale. Per-test breakdown: `tests/README.md`.

Two principles worth keeping:

- **No fixture copies** — every test runs on the **real** data in the repository. Copied JSON files
  in separate directories go stale, and the test stays green even when the real data has changed
  in the meantime.
- **Special states are produced by the test on the fly** (Playwright intercepts the request and
  rewrites the response), not from a stored file. This way it measures the same thing tomorrow too.

Two tests give the most: `zero-points-state-space.test.js` runs **all 672 combinations** of the "0 points"
logic with five invariants (this is what finds errors nobody thought to write a test for), and
`standings-recount.test.js` **independently recomputes** the table and the matrix from the raw data.

## 6. Making changes

**Before you touch the closing logic, read section 3/b.** Four different things are called
"closing", with separate flags; rewriting one of them without knowing the others has already
caused an error — and the test written for it pinned the wrong behaviour instead of catching it.
If you adjust a test to fit the code, stop: probably the expectation is wrong, not the code.

**Updating the documentation is not an optional step, and no longer a matter of trust:**
`tests/doc_checks.py`, as part of the test suite, checks that every test and data file is
documented, that the file table does not reference a deleted file, and that the changelog entries
are complete. (It exists because editing the docs failed silently twice.)

There is no build step and no dependency. The code lives in three layers:

- **`funtasy.css`** — the shared stylesheet (both pages load it; every colour, grid, table and modal
  style is here).
- **`funtasy.js`** — the shared layer. **Whatever is not league-specific belongs here**, and this is
  not cosmetic: with twelve same-named functions in separate copies on the two league pages, the
  same error has to be fixed several times (the cache busting in two differently shaped `apiGet`s;
  the "39 on the list, 38 after switching" discrepancy first on the match page, then separately in
  the squad view). A third league would triple this. **Two** remain separate now
  (`breakdownHTML`, `noPointsMessage`) — those really differ per league, because they come from
  different APIs.

  The league-independent pieces in the shared layer:

  | Call | What it gives |
  |---|---|
  | `FunTasy.makeFetcher({...})` | fetching through CORS proxies: several routes in order (our own Worker first when configured, then direct, then the public proxies), remembering the one that worked, cache busting in three layers. Configurable: whether the **inner** URL gets a timestamp too (`innerStamp`; the FPL tolerates it, at the MLSZ it is not verified), what counts as a valid response (`isValid`), and whether it throws on total failure (`onFail`). |
  | `FunTasy.viewStack({...})` | the modal and the paging inside it (`show` / `back` / `open` / `close`). |
  | `FunTasy.scoreHTML(...)` | the box of the score row. |
  | `FunTasy.liveLookup(LIVE)` | looking up the live score in the live layer. |
  | `FunTasy.errorReporter({...})` | the status bar's error message; the caller decides the "is there a live round" question. |
  | `FunTasy.h2hViewer({...})` | the head-to-head view; the name resolution is configurable. |
  | `FunTasy.onVisibleAgain(fn)` | refresh when the page is visible again. |
  | `FunTasy.slowIndicator(target)` | the „frissítés… N mp" (refreshing… N s) indicator for a slow request. |
  | `FunTasy.accToggle/accTable` | the accordion mechanics of the points breakdown. |

  In addition `FunTasy.create({...})` takes the configuration (schedule, participants, element
  ids), and gives the `computeTable`, `renderTable`, `renderMatches`, `renderMatrix` functions, the
  live marking and the builder of the head-to-head list (`h2hHTML` — opened by a click on a matrix
  cell, `onMatrixClick`). Outside `create`, the shared accordion mechanics of the points breakdown
  live here too (`FunTasy.accToggle` — open/close/one panel at a time; `FunTasy.accTable` — the
  breakdown's table); the content comes from the pages' own `breakdownHTML`, because the source
  differs (NB1: MLSZ `game-player-stats`, PL: FPL `event/{gw}/live` explain). Also here is
  `FunTasy.onVisibleAgain(refresh)`: on returning to the page it re-runs the live request
  (throttled, without parallel runs) — without it the score freezes on mobile.
- **`nb1/index.html` / `pl/index.html`** — only the page-specific part: configuration, loading and
  live refresh, plus the page's own modal (on the NB1 page `showSquad` / `showMatchRound` /
  `squadHTML` / `playersHTML`, on PL `showTeam` / `showMatch` / `squadHTML` / `T.roundsHTML` /
  `playersHTML`). Paging inside the modal is carried by the same small view stack on both pages
  (`vShow` / `vBack`): the entry point is `root`, a tab switch is `replace`, a view opened from a
  list is `push` — the back button lives on this.

### Adding a new league

The site's structure is one league per folder, so that the address is about the league and can be
extended:

```
/            index.html      – kezdőlap (ligaválasztó)
/nb1/        index.html      – FunTasy NB1
/pl/         index.html      – FunTasy PL
             funtasy.css/js  – közös réteg (a gyökérben)
             *.json          – adatfájlok (a gyökérben, az oldalak ../ úton érik el)
```

(`/` is the home page with the league switcher; `funtasy.css/js` is the shared layer, in the root;
`*.json` are the data files, in the root, which the pages reach via `../`.)

Adding a new league:

1. A new entry in the **`LEAGUES`** list of `funtasy.js`. From this **one** list are built the
   league switcher bar at the top of every page, the home page card and the league page's subtitle
   — nothing else needs touching. Fields:

   | Field | What it is for |
   |---|---|
   | `id` | short identifier, also the basis of the body classes and the card (`nb1`, `pl`) |
   | `name` | short name in the league switcher bar and at the top of the card (`NB1`) |
   | `path` | relative to the site root (`nb1/`) |
   | `title` | the start of the league page's subtitle (`NB1 salary cap fantasy`) |
   | `description` | the continuation: participants, rounds (`privát head-to-head · 8 csapat · 33 forduló`) |
   | `teams` | the number of teams; the table draws this many placeholder rows before the data arrives (`8`) |
   | `type` | **game mode** — `salary-cap` or `draft`, see below |
   | `typeName` | its readable name on the card (`Salary cap`) |
   | `theme` | the `body` class for the colour scheme (`liga-nb1`) |
   | `livePoints` | whether the source gives points **during a match** (FPL: yes, MLSZ: only after the match). What may be written about a 0-point player during the match depends on this. |
   | `midnightPlaceholder` | whether a midnight kick-off time means "not scheduled yet" (MLSZ: `true`, FPL: `false`); then no clock time is printed. |
2. A new folder with its own `index.html`. It references the shared files as `../funtasy.css?v=N`
   and `../funtasy.js?v=N`, the data as `../something.json`, and one line draws the bar:
   `FunTasy.renderNav('<id>','../')`.
3. If new theme colours are needed: a `body.liga-<id>` block in `funtasy.css` (the variable names
   stay, only their values differ), and the card's colour in the
   `.ligakartya[data-liga="<id>"]` rules.

The links are **relative** (`../pl/`), because GitHub Pages serves from a subpath
(`/Funtasy-Liga/`), so an absolute `/pl/` path would point to the wrong place.

**The league type is not a label, but a property.** There are two game modes, and their rules
differ substantially — the pages can handle this separately:

| Type | What it means |
|---|---|
| `salary-cap` | shared player market with a budget; the same player can be in several teams; there is a captain (×2) and bench halving (NB1) |
| `draft` | exclusive ownership: one player in one team; no captain, bench points do not count (PL) |

The type can be reached in two places: the `body` gets the `tipus-<value>` class (usable from
CSS), and from JS `FunTasy.leagueById('nb1').type` can be queried. Both are set by
`FunTasy.renderNav(...)`, the same call that draws the league switcher bar.

**The home page has its own, neutral colour scheme** (`body.kezdolap`: graphite base, silvery
highlight). Without it, it would use the default palette, that is, it would look like the NB1 page.
This way the two league colours (green / purple) are the only spots of colour on the page.

**Versioning:** the pages load the shared files as `funtasy.css?v=N` / `funtasy.js?v=N`. **If
`funtasy.css` or `funtasy.js` changes, the `?v=` number has to be raised on every page that loads
them** (and in `verzio.json`; **D6** and **D6/b** in `tests/doc_checks.py` check this) — otherwise
browsers may load the old engine under the new page (page/engine version skew: the new HTML runs
with old JS, with errors that are hard to recognise).

**Watch the CSS class names:** `.pos` is the *green colour of positive numbers*, the position label
is `.ppos`. When the two clash, the W/L results show up as little boxes.

**Changing the fallback bookmarklet:** edit `tartalek/bookmarklet-source.js`, run
`python3 bookmarklet-build.py` in that folder, then update the bookmarklet in the browser with the
new content. Never edit `bookmarklet.txt` by hand (**D18** in `tests/doc_checks.py` checks that
it is freshly built from the source).

---

## 7. Planned, not yet built

- A summary page for following the two leagues (NB1 + PL) together — the linking of the
  participants (`FunTasy.PEOPLE` in the shared layer and the shared monograms) is already there
- Captain efficiency leaderboard
- "Points left on the bench" leaderboard
- Ownership percentages within the league
- **The NB1 next opponents in the profile.** The PL side has the opponents of the remaining rounds,
  the NB1 does not: no future schedule has been found in the MLSZ API (~25 endpoint forms, all
  404), although fantasy.mlsz.hu's own player page shows it. The next step is reverse-engineering
  the frontend bundle, to find where it fetches it from.
- **Identifying the „Ismeretlen játékos" (unknown player) rows** on the points adjustment panel
  (rounds 1–3). They cannot be traced back from the repository; if someone has a screenshot from
  that time, they can be from that.
