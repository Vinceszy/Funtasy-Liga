# Retroactive squad collection — **OBSOLETE, not needed**

This file used to hold a manual console script for filling in the squads of earlier
rounds: you pasted it into the browser console, copied out the JSON, and pasted it into
`squad_history.json` by hand.

**That process no longer exists.** The old script has been removed because it is not
only unnecessary but also broken — and leaving it in would have been misleading.

## Why it is not needed any more

The squad endpoint accepts a `filter[round_id]` parameter, and

```
round_id = 75 + 2 × round number      (1.→77, 2.→79, 3.→81, 4.→83, 5.→85)
```

With it **the squads of earlier rounds can be fetched
exactly too**, not only the current one — which removes the very limitation this file
was made for.

The backfill is done by `collect.py` on its own, server-side: on every run it checks
which rounds are missing from `squad_history.json`, and fetches them. Missed
**results** can be backfilled too (the rankings endpoint also accepts
`filter[round_id]`). The bookmarklet also remains as a fallback:
[`KERET-MENTES.md`](KERET-MENTES.md).

## Why the old script would not work

If someone dug it out of an old copy, it would not give usable data, for three reasons:

1. **It did not send `filter[round_id]`** — without it the endpoint answers
   **403 Forbidden**.
2. **It read the name from the wrong place.** It asked for the nested
   `competition_player.player` object, while the name is directly in
   `competition_player` (`first_name` / `last_name`).
3. **It produced incomplete records:** it did not collect the `pos`, `u21`, `hun` and
   `price` fields, which the page's „Aktuális keret" (Current squad) and „Szezon
   játékosai" (Players of the season) tabs use. The rounds saved with it would have
   been left without position and Hungarian-rule information.

## If it ever has to be done by hand after all

The working, proven fetch logic is here in readable form:
[`GOMB-forras.js`](GOMB-forras.js) — the `fetch` call with the correct `include` list
and `round_id` calculation can be copied from it.
