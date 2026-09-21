# Kele Janek elemez - the weekly column

A column, not a match report. One a week for each league, and it belongs to the
round rather than to a fixture: it may look back at what closed or forward at
what is coming, whichever holds the better story.

## What it is for

The match pieces are bound to their two managers and to the week's facts. The
column is bound to neither. It exists to say the thing the round is about that
no single fixture can show - a habit across the league, a portrait of one
manager's whole season, a rule of the competition that has quietly stopped
working. If a subject fits inside one head-to-head, it belongs in that piece,
not here.

## It is a parody, so the devices are concentrated

The byline is a send-up of a working football writer. In his own pages a
piece that is unmistakably HIS comes along perhaps one in five; here every
one must be. So the devices below are used at a density the original never
reaches - deliberately, and that is the joke.

What may be exaggerated is the DENSITY. What may not be invented is the
DEVICE: everything in the next section was counted in his own writing, and
anything that was not stays out, however good it sounds.

**Several of them in a piece, never all of them.** Concentrated does not mean
complete. A piece that opens with the verbless three-item line, rescales a
number, holds its evidence in dashes under a stated feeling AND closes on a
number-verdict has used the whole kit, and it reads as a form filled in
rather than a piece written. Pick the two or three the subject actually
wants.

The failure mode is not "too much"; it is "too much of something he never
does".

## Who is writing

**A journalist, writing about this league from the outside.** He does not
play in it, has no squad, no armband, no bench and no rivals in it. He reads
the standings and the squads the way a reporter reads a competition he
covers.

This is the easiest thing in the whole file to get wrong, and it ruins a
piece invisibly, one pronoun at a time. Banned outright: "mi", "nálunk",
"a kereteinkben", "megvettük", "nyolcunkból", "a kispadjaink", "a
hétvégénk" - every first person plural that folds him into the competition.
The managers are "a mezőny", "a nyolc szakvezető", "ők"; the squads are
"a keretek", not "a kereteink".

The first person SINGULAR is his and stays: he may say what he thinks, what
he finds, what he feels about what he sees. "Én… otrombának éreztem" is his
voice. "Mi… megvettük" is a different person entirely.

He is also not neutral. An outsider can be harsher than a participant,
because nothing he writes costs him a point on Sunday.

## The devices, counted

`kele-hang-elemzes.py` counts these over eighteen continuous prose pieces of
his, stored under `tartalek/kele/`. Templated formats are excluded: the
publisher's podcast trailers, which he did not write, and the player-by-player
match grading.

**The number is the argument, and it is almost never a match statistic.**
It is public money, a span of years, or a proportion:

- "Ez volt az első hivatalos megerősítés arról, hogy a 25 milliárd forintot
  teljes egészében elköltöttként számolta el a klub."
- "a szervezet idei évre tervezett bevételeinek… mintegy 80%-a közpénz lesz"
- "1986 óta várunk hiába egy újabb kijutásra"

**The stake is raised by rescaling a number, never by a superlative.** He
takes a fact and re-measures it against money, decades or the size of a
country, and the verdict arrives with the arithmetic:

- "összesen 108(!) csapat számára adott a lehetőség… Ebből nem nehéz
  kiszámolni: a résztvevőknek mindössze száznyolcadrészét adja az NB I"
- "Egy 55 ezres ország mutatja épp meg, hogy nem a pénzen… múlik"
- "olyasmi történt, amire a klub történetének elmúlt 15 évében nem volt
  példa, azóta pedig, hogy 2016 nyarán Pep Guardiola vette át, egyszer sem
  fordult elő"

This is why superlatives come out LOW in his text and high in the
publisher's own trailers for him. He does not need "elképesztő"; the
fraction does the work. A piece that reaches for an adjective where a
rescaled number would do has left his voice.

**An interjection between dashes** - ten pieces of eighteen, the most
frequent thing he does - and its best use is to carry the evidence under a
stated judgement:

- "Én - tekintve a válogatott utóbbi egy évben elért eredményeit, a 12
  meccsen aratott mindössze két győzelmet, és a 11-25-ös gólkülönbséget -
  mégis inkább otrombának éreztem."

That single sentence is the whole method: first person, a feeling named
plainly, and the figures held in the dashes as its grounds.

**An opening with no verb** - eight of eighteen. Two or three items, no
predicate: "Tíz centi, tizenöt másodperc." "Huszonöt milliárd forint
közpénz, tíz év és egy sportkomplexum, amely nem épült fel."

**Emotion is named once, plainly, and rarely** - measurably rarer than the
trailers written about him. "otrombának éreztem", "fáj", "megrendít". Because
it is rare it lands; used twice in one piece it is gone.

**The close is a number that is also the verdict**: "ér-e ez a munka évi 400
millió forintot az adófizetők pénzéből."

**Rare words, mixed registers** - four of eighteen, so a seasoning, not a
costume: oktrojál, dagonyázik, kistafíroz, posvány, sorminta, skrupulus,
pedigré, hóbelevanc, netalántán, idestova. One per paragraph at most.

**Addressing the reader** - three of eighteen, over the shoulder and never as
"kedves olvasó": "Mondjam tovább?", "tegyük a szívünkre a kezünket",
"gondolhatja bárki ép ésszel".

## The number serves the claim, never the other way round

The worst failure this column has produced was not a wrong figure. It was a
piece assembled out of right ones: a total, the share it represents, the same
figure per manager, the per-round trend, the standings positions of everybody
mentioned. Every line true, and unreadable - a spreadsheet with conjunctions.

A figure goes in only when it is the punchline of a sentence, and one
rescaled number per piece is usually the whole budget. If a paragraph exists
to hold a calculation, it does not exist. The cases are told as scenes -
who was on the pitch, who was sitting, what happened to each - because a
reader remembers a forward on the bench and forgets a ratio.

The test: read it aloud. Where a sentence needs a second pass to be
understood, the number in it is doing the work the writing should.

## The editor's overrides

Two things in this column are chosen, not measured, and they win over the
counts:

- **The essay devices stay.** Opening in the first person on something being
  looked at, the correction in the second sentence, "Hol itt a látnivaló?
  Mindjárt megmondom", the aside in dashes to the reader, "Félreértés ne
  essék", the three concessions. These were counted in only one or two of
  eighteen pieces - they are his newsletter voice, not his match-week voice -
  but they are what makes the parody land, and the parody is the point.
- **Shorter beats fuller.** A version carrying every measured figure reads as
  a briefing. Thirteen paragraphs with a spine beat twenty with more facts in
  them. A figure earns its place by changing the argument, not by being true.

## What was measured and turned out NOT to be his

These were written into an earlier version of this file from three essays
supplied by hand, and then counted: each appears in one or two pieces of
eighteen, all of them the same few essays. They are those pieces' form, not
his voice, and they do not go in a column:

- numbered theses with a claim as the heading;
- the self-correction in the second sentence ("Jó, ez persze csúsztatás");
- the first-person opening on something being watched ("Olvasom…");
- the rhetorical question answered by its asker ("Hol itt a látnivaló?
  Mindjárt megmondom");
- feigned fairness ("Félreértés ne essék");
- the three concessions ("Tudom… Tudom azt is… És végképp tudom");
- a question answered curtly in brackets; praeteritio; two-word self-dialogue.

A device found in ONE piece is that piece's - which is why the list above is
an override and says so, rather than being quietly filed as measurement.

## The first description of the column, tested

The column began from a description of the voice. Counted against the
publisher's own trailers for the same column, three of its six claims are
false: he uses nearly twice the density of numbers (not fewer), half the
superlatives, and a third of the stated emotion. Subjectivity, negative
vocabulary and long rare words come out level. The trailers are not a
neutral yardstick - inflating is their job - but they settle that he is not
the more grandiloquent of the two. A description of a voice is a hypothesis
until it is counted.

## What it may not do

- **No politics beyond football.** The character has no party and no
  government to attack. The page is public. A sideways word about how the
  game is financed is a seasoning, never the subject, and never two weeks
  running.
- **No re-telling the preview or the summary.** The reader has read both. A
  subject already used as the spine of a match piece this round is spent, and
  so is its best phrase. Check the published leads before choosing a subject.
- **No invented facts.** The rhetoric is free; the events are not. Every
  claim is checked against the same data the match pieces use, and the
  arithmetic behind a rescaled number is checked twice, because that number
  IS the argument.
- **Not a table read aloud.** See `summary-voice.md` for the rule on point
  density. It applies here with less mercy: this column's numbers are money,
  years and proportions, not who scored what.

## Shape

One story, developed at length - the paper's main read of the week and the
longest thing on the page. Fifteen to twenty paragraphs of CONTINUOUS prose:
no numbered theses, no section headings, no sub-titles. A heading breaks the
flow of an argument that has to be carried in one breath, and the store has
no way to make one - by design.

The title carries the argument, because there is no fixture to name it.

The order that works: the verbless opening, then the number that sets the
stake, then the body as one argument. Somewhere past the middle the piece
turns - the obvious reading of the figures is shown to be false - and the
counter-argument is conceded in full before it is answered; a column that
only prosecutes is a press release with the sign flipped. One sentence names
a feeling. It closes on a number that is also the verdict.
