# Colour taxonomy: which qualitative facts a match report yields, and how to take them

The structured block of a report (goals with minute and type, cards, substitutions,
attendance, referee) is easy and deterministic. The interesting part is the prose: how a
goal was scored, whether a decision was disputed, whether a goal was lucky. This file
records which categories actually occur - every example below is quoted from a real
report, not invented - and the contract under which such a claim may be published.

## Categories, with the sentence each was taken from

| tag | what it covers | seen in a report as |
|---|---|---|
| `goal_manner` | header, volley, long shot, free kick, penalty | "Németh András **fejesével** jutott vezetéshez" |
| `luck` | rebound, deflection, woodwork, off a defender | "Kujovic remek lövése utáni **kipattanóból** született a vezető gól" |
| `disputed` | referee decision, VAR, offside, penalty not given | "egyértelműen **kézzel ütött bele**… **nem fújt tizenegyest**… a VAR-kocsiban tétlenül ült" |
| `big_miss` | glaring chance missed | "**közvetlen közelről nem találta el a kaput**" |
| `keeper_save` | save, punch, one-on-one | "fejesét **ütötte ki magabiztosan** Gundel-Takács" |
| `milestone` | first goal, run, debut, fresh signing scoring | "**az idényben először** nem kapott gólt"; "**a héten igazolt** Machado góljával" |
| `match_picture` | dominance, tempo, pattern of play | "**inkább a mezőnyben folyt a játék**, a kapuk elvétve forogtak veszélyben" |
| `upset` | bottom side beats top side | "**az eddig utolsó** ZTE… legyőzte **az éllovast**" |
| `history` | head-to-head record, streaks | "13 év alatt kétszer verte meg a Fradit" |

## The contract

Input per match: the report's structured block (parsed with a regular expression, not a
model), the report's prose, and our own event data from the collector.

Output per claim: one row of the round's colour table, `naplo/<league>-colour-<round>.json`.
The full schema - every key and every value in use - is the next section; it is the one
place it is written down, and `round-pipeline.md` points here.

The anchor decides what may be done with the claim (the licence of each anchor is in
`round-pipeline.md`, *What each layer may say*):

- **`event`** - the (player, minute) pair matches an entry in the structured block *and*
  our own data. The claim may be stated as fact.
- **`record`** - the structured block carries it, but we hold no data on the player:
  nobody owns him, or he was sold before the round. Stated as fact all the same; the
  anchor only says that our own data could not confirm it.
- **`article_only`** - the prose says it but no structured counterpart exists, which is
  normal for whole categories: a missed chance, a save and the pattern of play are never
  in event data. Publishable for those tags (`big_miss`, `keeper_save`, `match_picture`),
  and **published as fact, in our own words**. The anchor governs what we are allowed to
  say, not how we hedge it: a paper states what happened, it does not cite where it read
  it. "A beszámoló szerint" never appears in a piece - if a claim is too thin to state
  plainly, it is too thin to publish.
- **`statement`** - a manager said it to us; quoted, never paraphrased.
- **`none`** - the claim contradicts the structured block, or names a player who did not
  play. **Dropped** - such a row is not written into the table at all.

Two rules on top:

1. **A judgement is rendered as the events underneath it.** `disputed` is not an
   observation, so it is not published as one - but it is not sourced either. Instead of
   "vitatott tizenegyes" the piece says what happened: handled the ball, the referee waved
   play on, the VAR stayed silent. The reader gets the facts and draws the conclusion.
2. **A player outside our squads is kept, as `record`.** Whether anybody owns him decides
   the anchor, not whether the claim is kept: our squads only add the confirmation an
   `event` row needs.

## The table schema

Top level:

| key | in | meaning |
|---|---|---|
| `league` | both | `nb1` or `pl` |
| `round` | both | the round number (int) |
| `source` | when filled from prose | free text: which reports / streams the claims came from |
| `event` | PL | the FPL gameweek as a string; written by `pl-colour-harvest.py` |
| `created` | PL | UTC time the harvest last wrote the file |
| `matches` | both | the structured block, one object per match, keyed by the match name |
| `claims` | both | the rows, one per claim (below); the harvest keeps them when it rewrites `matches` |

A row of `claims`:

| key | when | meaning |
|---|---|---|
| `player` | always (`null` for a statement) | the name as our squad data writes it |
| `minute` | always (`null` when it has none) | an int, or a string such as `"45+2"`; the base minute is what is compared |
| `tag` | always | one of the tags below |
| `sentence` | always | the report's phrase, in Hungarian |
| `anchor` | always | `event`, `record`, `article_only` or `statement` |
| `match` | always | the match name: a key of `matches`, or the result form of it (`"Man City 5-3 Sunderland"` for the key `"Man City - Sunderland"`); for a statement the fantasy pairing it was said about |
| `club` | PL rows about a footballer | the FPL short club name (`t` in `draft_players.json`); with it the squad check runs, and `timeline.py` finds the owner |
| `source_name` | when the names differ | the player's name in the report or in FotMob, when the squad calls him something else ("Yeremy" / "Yéremi Pino"); the structured block is searched for this name |
| `speaker` | `statement` rows (required) | who said it |
| `context` | `statement` rows | when and in answer to what it was said |
| `target` | `statement` rows naming someone | whom the quote is about, as told by whoever passed it on - never inferred |

Tags in use: `goal`, `assist`, `card`, `sub` (structured facts), `goal_manner`, `luck`,
`disputed`, `big_miss`, `keeper_save`, `milestone`, `match_picture`, `upset`, `history`
(the categories above) and `quote` (a `statement` row).

The structured block, `matches[<name>]`:

| key | league | meaning |
|---|---|---|
| `goals` | both | list of goals: `minute`, `player` (the scorer); NB1 optionally `team` and `manner` (`"11-es"`); PL also `assist` (`"assist by …"` or `null`), `description`, `manner` (shot type), `situation`, `own_goal`, `xG` |
| `venue`, `attendance`, `referee`, `note` | NB1 | from the report's formal block, filled by hand |
| `sent_off` | NB1 | list: `minute`, `player`, `team` |
| `kickoff` | PL | UTC kick-off time - what puts the minutes on one clock |
| `fotmob` | PL | FotMob's match id |
| `var` | PL | list: `minute`, `player`, `decision` |
| `big_chances_missed` | PL | shots with xG of at least 0.3 that were not goals: `minute`, `player`, `xG`, `manner`, `situation`, `on_target` |
| `saves_by_keeper` | PL | goalkeeper id -> saves |
| `shots` | PL | number of shots in the shotmap |

## What `colour-check.py` checks - and what it does not

`python3 naplo/colour-check.py <league> <round>` checks, offline:

- every `statement` row has a `speaker` (nothing else is checked on it);
- **PL rows that carry a `club`**: the (player, club) pair is in somebody's squad that
  round exactly when the anchor is not `record`. NB1 rows and PL rows without a club are
  not checked for squad membership;
- every `event` and `record` row: its `match` resolves to a key of `matches`, and, by tag -
  `goal`, `goal_manner`, `luck`: a goal with the same base minute whose `player` contains
  the row's name (`source_name` if set); `assist`: the same against the goals' `assist`,
  only where the block carries assists (the NB1's does not); `disputed`: a goal or a `var`
  entry; `big_miss`: an entry of `big_chances_missed`, only where the block has one.
  `card`, `sub`, `milestone`, `history`, `match_picture` and the rest are not checked:
  the block does not hold them;
- **NB1 only**: an `event` goal row that found its goal must also have a goal in our own
  breakdown, `bontasok/<round>.json` - skipped while the round has no stored breakdown;
- **PL only**: every match has its `kickoff`.

`article_only` rows are not checked against anything beyond the PL squad rule. A minute
is never compared with our own data except through the NB1 goal check.

## Why this cannot invent an event

An `event` or `record` row about a goal, an assist, a VAR decision or a big chance must
match an entry of the structured block, and an NB1 `event` goal must also match a goal in
our own breakdown. The prose can therefore fail to describe something - it cannot add a
goal that is not in the record. The failure direction is the safe one: a missing
sentence, not a false one. What the check cannot see - an `article_only` save, a
`milestone`, the pattern of play - rests on the report and on the writer; that is why
those tags are stated plainly or not at all.

## How to tell whether it works

Run the extraction over a finished round and count the claims by anchor. A non-trivial
number of `none` means the extraction is unreliable and the rules have to tighten before
anything is published.
