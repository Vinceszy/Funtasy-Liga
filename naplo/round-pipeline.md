# How a round summary is built: three layers, one table

## Before a piece is written

A round piece is written from files, not from recollection. Two are read in
full first, every time, because the faults they prevent are invisible from
inside a draft:

- `summary-voice.md` - the voice, and what may not appear in a piece.
- this file - the layers, the sources, the order, and which file holds what.

Then the round's own data: `draft-round-harvest.py` or
`round-colour-harvest.py` for a summary, `draft-preview-harvest.py` for a
preview, plus the round's colour table. Every number in a piece comes from
one of those, checked, not remembered.

The order of a round is fixed: the summary of the round that closed, then
the preview of the one coming. Neither is published before the text has
been approved.

A summary is assembled from **three layers**. Each has a different source, a
different reliability, and a different licence for what may be written.

## 1. Fantasy data - ours, exact

Everything the collector stores: squads by round with role (captain, bench),
weekly points per player, transfers with what they cost or gained (`guard`),
the Hungarian-rule bonus, the head-to-head score, and the running total after
each real fixture (who led, and when it turned).

`naplo/round-colour-harvest.py <round>` prints this for an NB1 round,
including the checksum against the stored score;
`naplo/draft-round-harvest.py <round>` does the same for the Draft.
**Always run it first** - a claim about points that this does not support is
not published.

The two leagues turn on different things, and the harvests say so. The NB1
has a captain, shared players and a bench that scores half. The Draft has
none of those: a footballer belongs to one squad only, and the bench scores
nothing by itself - but it is **not** dead weight, because of the automatic
substitution. At the close of the round the FPL replaces every starter who
did not play (nought minutes, not nought points - those are different) with
the first bench player who did, keeping the formation legal and swapping a
goalkeeper only for a goalkeeper. A Draft piece is therefore about the
line-up, the week's waiver moves and, often, which bench man the auto-sub
brought in - and never about a shared player.

### Where the automatic substitutions are actually written down

`zarasok.json`, and nowhere else. The stored line-up for a finished round is
the state **after** the close, so a starter who never took the field is no
longer visible in it: the swap cannot be read back out of the squad. Nor out
of `draft_keretvaltozasok.json`, whose `szerep` rows compare this round's
line-up to the PREVIOUS round's and so mix a manager's decision together
with the machine's substitution. `zarasok.json` holds only what the close
did: who came off with nought minutes, who came on, and what each scored.

A starter who does not play and is not in `zarasok.json` was not replaced -
the bench had nobody left who both played and fitted the formation, so the
place stayed empty. That is a different story from a bench that scored and
did not count, and the two must not be told as one.

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

## 2b. The Draft's own prose: the league's minute-by-minute commentary

The Premier League publishes its own text stream for every fixture - about a
hundred entries a match, two dozen of which describe how a goal was scored,
which penalty was saved, which goal the VAR took away:

    footballapi.pulselive.com/football/fixtures/<id>/textstream/EN

`naplo/pl-textstream.py <gameweek>` pulls it for a whole round and matches
the fixtures to ours by club name (the ALIAS table - "Man City" is not a
substring of "Manchester City", and four fixtures went missing the first
time for exactly that). FotMob supplies the structured side through
`naplo/pl-colour-harvest.py`: the shotmap with shot type, situation and xG,
the VAR events, the saves per goalkeeper, and the kick-off time.

**The text goes to the run log only** - as with the Hungarian reports. Which
is precisely why the next section is not optional.

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

## A measurement that is not written down did not happen

The prose sources print to the run log and nowhere else, so a round's colour
exists only as long as the run that fetched it. Nothing else holds it: not
the squad files, not the article, not anybody's recollection.

**The run and the rows are one step, not two.** The moment a fetch comes
back, its claims go into `naplo/<liga>-colour-<round>.json` - player, club,
minute, tag, sentence, anchor, match - and only then is anything else done
with them. A second run of the same measurement over the same round is a
defect, not a retry: it costs an Actions run, it risks a different snapshot,
and it means the first one produced nothing durable.

`naplo/colour-check.py <liga> <round>` verifies the table afterwards: every
`event` row must find its goal, assist, VAR decision or big chance in the
structured block of the same file, and every player must be in somebody's
squad that round (a player nobody owns is `record`). Two kinds of row fail
it regularly and both are worth knowing: a stoppage-time incident the two
sources minute differently, and a save that only the prose knows about -
that one is `article_only`, not `event`.

## What the minutes are for

Not for reciting. A minute in a piece has to do one of two jobs:

- **Mark a turn.** The round is one clock: with the kick-off times stored
  next to the goals, the head-to-head can be laid on a single timeline, and
  the interesting question is when a fixture changed hands and what changed
  it - not what time each goal happened to be scored.
- **Show two things happening at once.** Several matches run in parallel; a
  swing that took eleven minutes across three grounds is a fact worth
  writing, and it is only visible if the minutes are added to the kick-off
  times.

Everything else is decoration. Three minutes in one sentence is a fixture
list with commas.

## The order

1. `round-colour-harvest.py <round>` - the fantasy layer.
2. `nso-content-probe.py` from Actions - the reports of that round.
3. Fill `nb1-colour-<round>.json` from the reports: structured block first
   (anchor `event` where our own data agrees), then the prose claims.
4. Write the pieces from the two files, in the voice of `summary-voice.md`.
5. Nothing is published before the text has been approved.

For the Draft the same five steps, with its own scripts:

1. `draft-round-harvest.py <round>` - the fantasy layer, and it must say the
   round is final.
2. `pl-colour-harvest.py` and `pl-textstream.py` from Actions - the
   structured block with the kick-off times, and the prose.
3. Fill `pl-colour-<round>.json` **in the same step**, then run
   `colour-check.py pl <round>`.
4. Write the pieces.
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
find its goal, card, assist or minute in `bontasok/<round>.json`. Two cases
that check catches and that are easy to mis-file by hand: a scorer sold
before the round, whom no squad holds, so he is `record` rather than
`event`; and a substitute's minute count, which is time played and not the
minute he came on.
