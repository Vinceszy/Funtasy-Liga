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

Output per claim: `{player, minute, tag, phrase, anchor}`.

The anchor decides what may be done with the claim:

- **`event`** - the (player, minute) pair matches an entry in the structured block *and*
  our own data. The claim may be stated as fact.
- **`article_only`** - the prose says it but no structured counterpart exists, which is
  normal for whole categories: a missed chance, a save and the pattern of play are never
  in event data. Publishable only as attributed ("a beszámoló szerint"), and only for the
  tags where that is legitimate: `big_miss`, `keeper_save`, `match_picture`.
- **`none`** - the claim contradicts the structured block, or names a player who did not
  play. **Dropped.**

Two rules on top:

1. **Opinion is always attributed.** `disputed` is a judgement, not an observation. Even
   when it anchors to a real event, it is published as "a beszámoló szerint vitatott",
   never as our own assertion.
2. **Only our own players.** A claim is kept only if the player is in somebody's squad
   that round. The rest is noise for us however interesting it is.

## Why this cannot invent an event

The generator may only refer to players it finds in our own squad data, and a claim about
a goal must match a goal we already know happened. The model can therefore fail to
describe something - it cannot describe something that did not happen. The failure
direction is the safe one: a missing sentence, not a false one.

## How to tell whether it works

Run the extraction over a finished round and count the claims by anchor. A non-trivial
number of `none` means the extraction is unreliable and the rules have to tighten before
anything is published.
