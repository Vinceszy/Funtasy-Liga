# How a Nemzethy Sport piece is made

This file is the method for every piece the paper runs: the summary and the
preview of a fixture, in both leagues, and Kele Janek's weekly column. The
voice is in `summary-voice.md` (fixture pieces) and `kele-janek.md` (the
column); what counts as colour, and how it may be stated, is in
`colour-taxonomy.md`.

## The first step, every time

    python3 naplo/article-prep.py <nb1|pl> <round> <summary|preview|column>

It refuses a summary of a round that is not final and a preview of a round
that is not the coming one, then prints, in this order:

- the rule files **in full** - this file, the voice, and the colour taxonomy
  for a summary. Printed rather than remembered: the faults they prevent are
  invisible from inside a draft, and a rule read once in an earlier session
  is a rule not applied;
- the **spent** material - the published pieces the new one may not repeat:
  the round's previews for a summary, the last round's summaries for a
  preview, the league's last column for a column;
- the **data** - the round harvest for a summary, the season mirror (and for
  the NB1 the last-round squads) for a preview.

Nothing is written before that output has been read, and every number in a
piece comes from it or from the files it names - checked, not remembered.

## The text goes to the conversation, then live

A piece is shown in the conversation, whole, and changed there until it is
approved. Only the approved text is written to `articles.json`, with its
`kozzetett` stamp, and published. There is no draft file: half-finished
text never enters the repository.

One piece at a time, in fixture order: the next one is shown when the one
before it is approved. Five pieces at once are five pieces nobody reads
closely.

## The summary: a story, found in the material

A piece needs a story with colour, and there is no single place it comes
from: a match that turned the fixture, a player's week, one manager's habit,
a shared match where both had men, a keeper on one bench, a quote, the
season behind the two of them. The running score match by match, which the
first step prints for the Draft, is one way of finding it, not the way.

One thing to watch whatever the story: the stored line-up is the state
after the close, so it may already contain the machine's substitutions. A
sentence about what a manager decided is checked against the line-up he
chose, which the first step also prints.

## The preview: a season, not a snapshot

A preview's spine often comes from the two managers' season, which the
season mirror prints - or from what the coming weekend holds: a derby, a
club one side leans on, a star who did not play last time. The season
mirror shows the margin of every match, where each finished in
every round's score order, the form (streaks, season best), the table, and
the previous meeting. In it, look for the contrast or the crossing of the two
lines - the man of the tight games against the man of the blowouts, the most
consistent against the luckiest, two curves that crossed since the last
meeting.

The squads are middle material: what the two shared last round, who wore the
armband, who sat. They are the state a manager decides from - the window is
open until the first kick-off - so they are written as choices, never as the
coming line-up (`summary-voice.md`).

The real fixtures of the round are part of the data. For the NB1 the
fantasy API does not serve future matches, so they are looked up - two
independent sources, pairings only, kick-off times are not needed - and
recorded in `naplo/nb1-fixtures-<round>.txt` before writing. The Draft's
own preview layer is `draft-preview-harvest.py`, which the first step runs.

## The summary: three layers, one table

A summary is assembled from **three layers**. Each has a different source, a
different reliability, and a different licence for what may be written.

### 1. Fantasy data - ours, exact

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

#### Where the automatic substitutions are actually written down

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

### 2. The match record - the report's structured block

The Nemzeti Sport report of every NB1 match carries a formal block: line-ups
with substitution minutes, scorers with minutes, cards, attendance, referee,
venue. It is deterministic, and it is parsed as text, never summarised by a
model. This is where a goal's minute, a red card or the crowd figure comes
from.

The site allows it: `robots.txt` disallows only `/hirdetesek`,
`/cikk-elonezet` and `/publicapi`, and `sitemapindex.xml` is the machine
index of the articles (measured - `naplo/report-source.txt`).

`naplo/nso-content-probe.py` fetches the reports of one round. It takes no
arguments; it reads its settings from the environment:

    PROBE_MONTH=<yyyy/mm>  PROBE_SINCE=<the round's first day, yyyy-mm-dd>  PROBE_LIMIT=<number of matches>

`PROBE_MONTH` is not optional in practice: an article is kept only if its url
carries that month, and the default is `2026/09` - an October round returns
nothing without `PROBE_MONTH=2026/10`. A round that spans two months needs a
run per month.

Run it from Actions (`.github/workflows/naplo-meres.yml`) - the development
network blocks every external host. The workflow's `script` input names the
probe, and its `environment` input takes the settings, one `NAME=value` per
line. **The article text goes to the run log only, never into the
repository.**

### 2b. The Draft's own prose: the league's minute-by-minute commentary

The Premier League publishes its own text stream for every fixture - about a
hundred entries a match, two dozen of which describe how a goal was scored,
which penalty was saved, which goal the VAR took away:

    footballapi.pulselive.com/football/fixtures/<id>/textstream/EN

`naplo/pl-textstream.py` pulls it for a whole round and matches
the fixtures to ours by club name (the ALIAS table - "Man City" is not a
substring of "Manchester City", and four fixtures went missing the first
time for exactly that). FotMob supplies the structured side through
`naplo/pl-colour-harvest.py`: the shotmap with shot type, situation and xG,
the VAR events, the saves per goalkeeper, and the kick-off time.

Neither script takes an argument - both ignore any. The gameweek comes from
the environment variable `HARVEST_EVENT`:

    HARVEST_EVENT=<gameweek> python3 naplo/pl-textstream.py
    HARVEST_EVENT=<gameweek> python3 naplo/pl-colour-harvest.py

From Actions it is the line `HARVEST_EVENT=<gameweek>` in the workflow's
`environment` input. Without it the scripts fall back to a fixed old
gameweek, not to the current one.

**The text goes to the run log only** - as with the Hungarian reports. Which
is precisely why the next section is not optional.

### 3. Colour - the filled table

The prose of the report is the only source for how a goal was scored, what
was disputed, which big chance was missed. The categories and the contract
are in `colour-taxonomy.md`; what matters here is that colour is not read
and remembered, it is **written into a table**, one row per claim:

    {player, minute, tag, phrase, anchor}

and the table is a file: `naplo/<league>-colour-<round>.json`, its rows under
`claims`. Every key a row or a match block can carry - `player`, `minute`,
`tag`, `sentence`, `anchor`, `match`, and `club`, `source_name`, `speaker`,
`context`, `target` where they apply - and every tag in use are listed in one
place: *The table schema* in `colour-taxonomy.md`. The
article is written from the table, not from the article text - so every
sentence can be traced back to a row, and the row's anchor decides whether
it may be stated at all (see *What each layer may say*).

### A fourth source: what a manager says

The three layers are what happened. A manager's own words are a fourth, and
they arrive by hand rather than by script: somebody tells us what he said
after the match. Such a line goes into the round's colour table as a row with
the anchor `statement`, the tag `quote`, the `speaker` and the `context`, and it is written into
the piece as a quotation - the only place in a summary where a sentence is
attributed, because there the attribution IS the fact.

A quote may name another team, which the rest of a match piece may not. The
rule it must still obey: it belongs in the piece of the manager who said it,
not in the piece of the one it is about.

**Record who a nickname refers to, do not infer it.** A quote calls a rival
something - "az illegitim bajnok" - and the nearest-looking club name is not
the answer: that one was a different team entirely. The referent is asked
for and written into the row (`target`), because a piece built on a guessed
target says something about a manager who was never mentioned.

### A fifth source: what the editor tells about a manager

Not a quote and not an event: a fact about a manager's season that only the
league knows - who drafted for whom, who took a column to heart. It belongs
to the season, not to a round, so it goes into
`naplo/<league>-background.json` (`manager` or `team`, `fact`,
`from_round`, `used_in`), never into a round's colour table, where nothing
reads it again. The first step prints the file for every piece. A fact that
carried a published piece is listed in its `used_in` and is spent from then
on. In the Draft the fact names the team, never the person behind it.

## A measurement that is not written down did not happen

The prose sources print to the run log and nowhere else, so a round's colour
exists only as long as the run that fetched it. Nothing else holds it: not
the squad files, not the article, not anybody's recollection.

**The run and the rows are one step, not two.** The moment a fetch comes
back, its claims go into `naplo/<league>-colour-<round>.json` - one row per
claim, keys as above - and only then is anything else done
with them. A second run of the same measurement over the same round is a
defect, not a retry: it costs an Actions run, it risks a different snapshot,
and it means the first one produced nothing durable.

`naplo/colour-check.py <league> <round>` verifies the table afterwards: every
`event` and `record` row about a goal, an assist, a VAR decision or a big
chance must find it in the structured block of the same file (as far as the
block holds such entries); for the NB1 an `event` goal must also be in our
stored breakdown; for the PL a row that carries a `club` must be in somebody's
squad that round exactly when it is not `record` (a player nobody owns is
`record`). What it does and does not check, in full: `colour-taxonomy.md`,
*What `colour-check.py` checks*. Two kinds of row fail
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

## The order of the work

1. `article-prep.py nb1 <round> summary` - the rules, the spent previews, and
   `round-colour-harvest.py <round>`, the fantasy layer.
2. `nso-content-probe.py` from Actions, with `PROBE_MONTH`, `PROBE_SINCE`
   and `PROBE_LIMIT` in the `environment` input - the reports of that round.
3. Fill `nb1-colour-<round>.json` from the reports: structured block first
   (anchor `event` where our own data agrees), then the prose claims.
4. Write the pieces from the two files, in the voice of `summary-voice.md`.
5. Nothing is published before the text has been approved.

For the Draft the same five steps, with its own scripts:

1. `article-prep.py pl <round> summary` - which runs `draft-round-harvest.py
   <round>`, the fantasy layer; it must say the round is final.
2. `pl-colour-harvest.py` and `pl-textstream.py` from Actions, each with
   `HARVEST_EVENT=<round>` in the `environment` input - the
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
| `statement` | a manager said it to us | quoted verbatim, named as his words - a quote is attribution by nature, not hedging |
| `none` | contradicts our data, or names a player who did not play | dropped |

The anchors are checked by machine where the data allows it
(`colour-check.py`): a goal, assist, VAR decision or big chance against the
structured block; for the NB1 an `event` goal against `bontasok/<round>.json`;
for the PL squad membership against `record`. Cards, substitutions and
minutes are not checked against our own data - those rows are checked by
hand. Two cases that are easy to mis-file by hand: a scorer sold
before the round, whom no squad holds, so he is `record` rather than
`event`; and a substitute's minute count, which is time played and not the
minute he came on.

## Three orders, kept apart

- **Writing:** the summary of the round that closed comes first, then the
  preview of the coming one.
- **Publication:** every published piece carries `kozzetett`, the moment it
  went live, and the magazine lists newest first. Pieces published in one
  commit share a stamp; among them the newer round comes first, and within
  a round the column, then the summary, then the preview.
- **Back-filling:** a piece published late gets the stamp of where it
  belongs editorially, not of the commit. Within a round the preview was
  published before the summary, and rounds follow each other in ascending
  order - a late preview stamped "now" would land above the summary that
  answered it.

A piece published on time is stamped with the moment it goes out, and needs
no further thought.
