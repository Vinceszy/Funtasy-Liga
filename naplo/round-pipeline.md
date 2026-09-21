# How a round summary is built: three layers, one table

Written down because it lived only in the flow of one session, and the next
run started inventing a new source instead of using the one we have.

A summary is assembled from **three layers**. Each has a different source, a
different reliability, and a different licence for what may be written.

## 1. Fantasy data - ours, exact

Everything the collector stores: squads by round with role (captain, bench),
weekly points per player, transfers with what they cost or gained (`guard`),
the Hungarian-rule bonus, the head-to-head score, and the running total after
each real fixture (who led, and when it turned).

`naplo/round-colour-harvest.py <round>` prints this for a whole round,
including the checksum against the stored score. **Always run it first** - a
claim about points that this does not support is not published.

## 2. The match record - the report's structured block

The Nemzeti Sport report of every NB1 match carries a formal block: line-ups
with substitution minutes, scorers with minutes, cards, attendance, referee,
venue. It is deterministic, and it is parsed as text, never summarised by a
model. This is where a goal's minute, a red card or the crowd figure comes
from.

The site allows it: `robots.txt` disallows only `/hirdetesek`,
`/cikk-elonezet` and `/publicapi`, and `sitemapindex.xml` is the machine
index of the articles (measured - `naplo/beszamolo-forras.txt`).

`naplo/nso-content-probe.py` fetches the reports of one round:

    PROBE_SINCE=<a forduló első napja> PROBE_LIMIT=<meccsek száma>

Run it from Actions (`.github/workflows/naplo-meres.yml`) - the development
network blocks every external host. **The article text goes to the run log
only, never into the repository.**

## 3. Colour - the filled table

The prose of the report is the only source for how a goal was scored, what
was disputed, which big chance was missed. The categories and the contract
are in `colour-taxonomy.md`; what matters here is that colour is not read
and remembered, it is **written into a table**, one row per claim:

    {player, minute, tag, phrase, anchor}

and the table is a file: `naplo/nb1-colour-<round>.json`. The article is
written from the table, not from the article text - so every sentence can be
traced back to a row, and a row carries the anchor that decides how it may
be phrased (fact / attributed / dropped).

## A fourth source: what a manager says

The three layers are what happened. A manager's own words are a fourth, and
they arrive by hand rather than by script: somebody tells us what he said
after the match. Such a line goes into the round's colour table as a row with
the anchor `nyilatkozat`, the speaker and the context, and it is written into
the piece as a quotation - the only place in a summary where a sentence is
attributed, because there the attribution IS the fact.

A quote may name another team, which the rest of a match piece may not. The
rule it must still obey: it belongs in the piece of the manager who said it,
not in the piece of the one it is about.

**Record who a nickname refers to, do not infer it.** A quote calls a rival
something - "az illegitim bajnok" - and the nearest-looking club name is not
the answer: that one was a different team entirely. The referent is asked
for and written into the row (`cel`), because a piece built on a guessed
target says something about a manager who was never mentioned.

## The order

1. `round-colour-harvest.py <round>` - the fantasy layer.
2. `nso-content-probe.py` from Actions - the reports of that round.
3. Fill `nb1-colour-<round>.json` from the reports: structured block first
   (anchor `event` where our own data agrees), then the prose claims.
4. Write the pieces from the two files, in the voice of `summary-voice.md`.
5. Nothing is published before the text has been approved.

## What each layer may say

| anchor | where it comes from | licence |
|---|---|---|
| `event` | the structured block AND our own data agree | stated as fact |
| `record` | the structured block only - a player nobody owns, or one sold before the round, so we hold no data on him | stated as fact |
| `article_only` | the prose alone (a save, a big miss, the pattern of play) | stated as fact, in our own words - never sourced in the text |
| `nyilatkozat` | a manager said it to us | quoted verbatim, named as his words - a quote is attribution by nature, not hedging |
| `none` | contradicts our data, or names a player who did not play | dropped |

The anchors are checked by machine, not by memory: every `event` row must
find its goal, card, assist or minute in `bontasok/<round>.json`. Writing the
round 8 table, that check moved two rows - a scorer who had been sold before
the round (no squad holds him, so `record`) and a substitution minute that
looked wrong until it was read as "came on in the 56th, played 34".
