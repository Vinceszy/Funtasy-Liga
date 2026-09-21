# Kele Janek elemez - the weekly column

A column, not a match report. One a week for each league, belonging to the
round rather than to a fixture: it may look back at what closed or forward at
what is coming, whichever holds the better story.

This file is a recipe. Two columns were published from it, and it is written
so that a third comes out like them rather than like the four drafts that
had to be thrown away first.

## Who is writing

**A journalist covering this league from the outside.** He does not play in
it: no squad, no armband, no bench, no rivals. He reads the standings the way
a reporter reads a competition he is paid to watch.

This is the easiest thing here to get wrong and it ruins a piece invisibly,
one pronoun at a time. Banned: "mi", "nálunk", "a kereteinkben", "megvettük",
"nyolcunkból", "a kispadjaink", "a hétvégénk". The managers are "a mezőny",
"a nyolc szakvezető", "ők"; the squads are "a keretek".

The first person SINGULAR is his and stays - what he watches, what he finds,
what he thinks of it. "Nézem csütörtökönként a nyolc keretet" is the voice.
"Mi megvettük" is a different person.

He is not neutral, and he can be harsher than a participant, because nothing
he writes costs him a point on Sunday.

## Before a word is written

1. **Pick a subject no single fixture can hold.** A habit across the league,
   one manager's whole season, a rule that has quietly stopped working. If it
   fits inside one head-to-head it belongs in that piece instead.
2. **Check what is spent.** Read every published lead of that round in
   `articles.json`. A subject or an anecdote already used as the spine of a
   match piece is gone, and so is its best phrase. Both published columns had
   to route around material the summaries had already told.
3. **Get the numbers from a harvest, never from memory** -
   `karszalag-harvest.py` for the armband, `kispad-harvest.py` for the Draft
   bench, the round harvests for everything else. Then check the arithmetic
   twice, because one rescaled figure usually IS the argument.
4. **Check the rules of the competition against the data**, not against
   intuition. The bench claim was wrong by a third until formation limits
   were applied: a goalkeeper cannot be fielded for a forward.

## The skeleton both published pieces share

Thirteen paragraphs, 220-270 characters on average, continuous prose. In
order:

1. **An image or a watched scene, one line.** "Nézem csütörtökönként a nyolc
   keretet, és azon kapom magam, hogy meg sem kell néznem őket." · "Van ennek
   a ligának egy sírkertje, és senki nem jár ki oda."
2. **The second beat takes it back or complicates it.** "Jó, ez persze
   csúsztatás. Dehogynem nézem meg."
3. **The state of affairs, named and then renamed.** "Ez már nem taktika. Ez
   berendezkedés."
4. **The hinge - a question he answers, or a promise of the evidence.** "Hol
   itt a látnivaló? Mindjárt megmondom." · "Egészen addig, amíg elő nem veszem
   a négy esetet."
5. **Two or three cases, told as scenes with named people** - who was on the
   pitch, who was sitting, what each of them did. Never as a table.
6. **A one-line beat that names the stake.** "És most jön az, amitől fáj." ·
   "Négy mérkőzés, amit nem az ellenfél nyert meg. A saját kispad."
7. **Feigned fairness, then the cut.** "Félreértés ne essék: Szalai kiváló
   futballista…" - and the next sentence takes it back with interest.
8. **The turn.** The obvious reading of the figures is shown to be false:
   "Sőt, van ennél kellemetlenebb is." · "Hát nem."
9. **The concessions, in full.** "Tudom: … Tudom azt is, hogy … És végképp
   tudom, hogy …" A column that only prosecutes is a press release with the
   sign flipped.
10. **The verdict as a two-part reframe** (below).
11. **Close on a number that is also the verdict**, standing alone.
    "Huszonnégy alkalom, öt meggondolás."

## The signature move: the two-part reframe

The thing both pieces are actually built out of. A short sentence denies what
the reader would call it, and a second, shorter one renames it:

- "Ez már nem taktika. Ez berendezkedés."
- "Nem elnézés ez már. Szokásjog."
- "Nem takarékosabb ez. Üresebb."
- "Nem biztosítás ez már. Gyámság."
- "Ettől még ez nem menedzselés. Ez előfizetés."

**Three or four per piece, and one of them is the closing verdict.** The
second half is one or two words. If it needs a clause, it is not a reframe,
it is an explanation.

## The numbers

**A figure appears when it is the punchline of a sentence.** One rescaled
number per piece is usually the whole budget: "hetvenkilenc futballista
fordult meg ezekben a keretekben, hétre került rá a szalag" · "húsz ember ült
odakint, és közülük kettő lépett egyáltalán pályára".

The worst draft this column produced was not a wrong figure but a pile of
right ones: a total, the share it represents, the same figure per manager,
the per-round trend, everybody's table position. Every line true, and
unreadable. **If a paragraph exists to hold a calculation, it does not
exist.** Read it aloud; where a sentence needs a second pass, the number is
doing the work the writing should.

Large numbers are spelled out in letters. Match statistics belong in the
match pieces: "pont" and its forms appear at most four times (D14).

## Rare words: three to five per piece

He does use them, and he mixes the registers inside one sentence: "az immáron
idestova 10+ éve adófizetői pénzben dagonyázó magyar futballklubok, és minden
földi jóval kistafírozott ún. kiemelt akadémiáik", closing the same passage
with "fizetheti maga után a cechet".

Old Hungarian and folksy: hóbelevanc, dzsembori, skrupulus, tobzódó, posvány,
dagonyázó, kistafírozott, eltapsikolás, cech, apportál, bicskanyitogató,
akarnok, lóhalálában, netalántán, idestova, voltaképpen, huncut,
megveszekedett, fittyet hány, kisvártatva, olybá tűnik, speciel, immáron,
mihelyst. International: oktrojál, pedigré, ethosz, volumen, szimbiotikus,
dehumanizál, legitimál, érdemesültség.

**Three to five per piece, fewer when the words are heavy** - one
"kistafírozott" costs more than two "idestova". His own rate is about one and
a third per three thousand characters, so this is roughly three times his,
which is the parody concentration. One per paragraph would be ten times and
reads as fancy dress.

## Hard limits

- **No sub-title and no standfirst.** The column stores no `short`: on a piece
  with no fixture that line only stands between the reader and the first
  sentence. The publication cannot render a heading inside an article either.
- **No numbered sections, no headings of any kind.** The argument is carried
  in one breath.
- **No politics beyond football.** The character has no party and no
  government to attack; the page is public. A sideways word about how the game
  is financed is a seasoning - once, never two weeks running.
- **No invented facts.** The rhetoric is free, the events are not.
- **Several devices per piece, never all of them.** A piece carrying the whole
  kit reads as a form filled in.
- **One rule, all pieces.** Every rate and limit here holds for every column,
  both leagues, both pieces of a week. Inventing a per-piece variation is a
  recurring failure of mine and produces differences nobody asked for.

## Still to improve

The arc. Both published pieces hold together, but they move in steps rather
than in one direction: a claim, its evidence, the next claim, its evidence.
The next one should read as a single line of travel from the first sentence
to the last, where every paragraph pushes the same central assertion further
instead of opening a new one beside it. Deliberately not attempted in the
first week; the pieces went out as they were.

## Where the corpus is, and what in here is measured

Twenty-one texts of his own under `tartalek/kele/`: eighteen fetched by
`kele-hang-meres.py` (the byline decides which pages are kept - the author
page also lists the publisher's latest news, and an earlier run came back
full of weather forecasts while reporting success) plus three supplied by
hand. Templates are excluded: the publisher's podcast trailers, which he did
not write, and the player-by-player match grading.

`kele-hang-elemzes.py` counts a device across those pieces. Two things recur:
an interjection between dashes, ten of eighteen, and an opening with no verb,
eight of eighteen. The rare-word rate above is measured. The register is
measured: against the publisher's own trailers for him he uses nearly twice
the density of numbers, half the superlatives and a third of the stated
emotion - he is not the grandiloquent one of the two.

**Chosen, not measured - and they win anyway.** The correction in the second
sentence, "Hol itt a látnivaló? Mindjárt megmondom", the aside in dashes to
the reader, "Félreértés ne essék", the three concessions: each appears in one
or two of the eighteen, always the same few essays. They are his newsletter
voice rather than his match-week voice, they are what makes the parody land,
and they stay. Recorded as an override so a later reading does not delete
them as unmeasured.
